from anyjson import dumps
from threading import Thread, Event
from urllib import urlopen
from websocket import create_connection

__version__ = '0.1.3'


class SocketIO(object):

    def __init__(self, host, port, namespace=None, version=1):
        self.host = host
        self.port = int(port)
        self.namespace = namespace or 'socket.io'
        self.version = version or 1

        self.url_params = [
            self.host, self.port,
            self.namespace, self.version
        ]

        self.__do_handshake()
        self.__connect()

        self.heartbeatThread = RhythmicThread(self.heartbeatTimeout - 2, self.__send_heartbeat)
        self.heartbeatThread.start()

    def __do_handshake(self):
        try:
            response = urlopen('http://%s:%d/%s/%d/' % tuple(self.url_params))
        except IOError:
            raise SocketIOError('Could not start connection')

        if 200 != response.getcode():
            raise SocketIOError('Could not establish connection')

        self.sessionID, heartbeatTimeout, connectionTimeout, supportedTransports = response.readline().split(':')
        self.heartbeatTimeout = int(heartbeatTimeout)
        self.connectionTimeout = int(connectionTimeout)

        if 'websocket' not in supportedTransports.split(','):
            raise SocketIOError('Could not parse handshake')

    def __connect(self):
        ws_params = self.url_params + [self.sessionID]
        url = 'ws://%s:%d/%s/%d/websocket/%s' % tuple(ws_params)
        self.connection = create_connection(url)

    def __del__(self):
        try:
            self.heartbeatThread.cancel()
            self.connection.close()
        except AttributeError:
            pass

    def __send_heartbeat(self):
        return self.__send(2)

    def __send(self, msg_type, msg_id=None, endpoint=None, **kwargs):
        """
        Format and send a message over the socket.

        The ``kwargs`` in the invocation are JSON encoded and sent as the
        message data.

        * ``msg_type``: An integer representing what type of message is being
          sent.

          * ``0``: disconnect
          * ``1``: connect
          * ``2``: heartbeat
          * ``3``: message
          * ``4``: json
          * ``5``: event
          * ``6``: ack
          * ``7``: error
          * ``8``: noop

        * ``msg_id``: An integer ID for the message. Default: `None`
        * ``endpoint``: The endpoint to receive the message.  Default: `None`
        """

        data_str = dumps(kwargs)

        msg = ':'.join(map(str, [
            msg_type,
            msg_id or '',
            endpoint or '',
            data_str
        ]))

        return self.connection.send(msg)

    def emit(self, eventName, eventData, **kwargs):
        """Send an ``event`` message over the socket."""

        return self.__send(5, name=eventName, args=eventData, **kwargs)


class SocketIOError(Exception):
    pass


class RhythmicThread(Thread):
    'Execute function every few seconds'

    daemon = True

    def __init__(self, intervalInSeconds, function, *args, **kw):
        super(RhythmicThread, self).__init__()
        self.intervalInSeconds = intervalInSeconds
        self.function = function
        self.args = args
        self.kw = kw
        self.done = Event()

    def cancel(self):
        self.done.set()

    def run(self):
        self.done.wait(self.intervalInSeconds)
        while not self.done.is_set():
            self.function(*self.args, **self.kw)
            self.done.wait(self.intervalInSeconds)
