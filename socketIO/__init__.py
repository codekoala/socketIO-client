from anyjson import dumps, loads
from collections import defaultdict
from functools import partial
from threading import Thread, Event
from urllib import urlopen
from websocket import create_connection
import atexit
import time

__version__ = '0.1.4'


class SocketIO(object):

    def __init__(self, host, port, namespace=None, version=1,
                 default_endpoint=None):
        self.host = host
        self.port = int(port)
        self.namespace = namespace or 'socket.io'
        self.version = version or 1
        self.default_endpoint = default_endpoint or ''
        self.__connected = False

        self.url_params = [
            self.host, self.port,
            self.namespace, self.version
        ]

        self.__do_handshake()
        self.__connect()

        hb_interval = self.heartbeatTimeout - 2
        self.heartbeat = RhythmicThread(hb_interval, self.send_heartbeat)
        self.heartbeat.start()

        self.listener = MessageHandler(self.connection)
        self.listener.start()

        self.create_dynamic_message_handlers()

    @property
    def connected(self):
        """Read-only property to determine if the socket is connected."""

        return self.__connected

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
        self.__connected = True

        # the __del__ method would be preferable.. if it worked...
        atexit.register(self.send_disconnect)

    def __del__(self):
        try:
            self.send_disconnect()
        except AttributeError:
            pass

    def on(self, event, callback):
        """Pass the event callback thru to the thread"""

        return self.listener.on(event, callback)

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

        if kwargs:
            data_str = dumps(kwargs)
        else:
            data_str = ''

        if endpoint is None:
            endpoint = self.default_endpoint

        msg = ':'.join(map(str, [
            msg_type,
            msg_id or '',
            endpoint,
            unicode(data_str).encode("utf-8")
        ]))

        if msg_type != 2:
            print msg

        return self.connection.send(msg)

    def create_dynamic_message_handlers(self):
        """
        Attempt to dynamically generate methods for each message type.

        Tries to grab the supported message types from ``gevent-socketio``.  If
        it succeeds, a new ``send_*`` method should be created for each message
        type.  If ``gevent-socketio`` is not installed, the dynamic methods
        will not be created.

        For example, if a message type named ``foo`` is supported by
        ``gevent-socketio``, the current ``SocketIO`` instance will have a new
        method called ``send_foo``.

        """

        try:
            from socketio.packet import MSG_TYPES
        except ImportError:
            # TODO: require gevent-socketio?
            return

        for name, msg_type in MSG_TYPES.items():
            method_name = 'send_%s' % (name.lower(),)
            if hasattr(self, method_name):
                # don't create the method if it is already defined
                continue

            f = partial(self.__send, msg_type=msg_type)
            setattr(self, method_name, f)

    def emit(self, eventName, *eventData, **kwargs):
        """Compatibility wrapper around send_event."""

        return self.send_event(eventName, *eventData, **kwargs)

    def send_disconnect(self, **kwargs):
        """Disconnect and close connections a bit more gracefully."""

        # check to see if, by some stroke of luck, the __del__ method worked
        # for this instance
        if not self.connected:
            return

        self.heartbeat.cancel()
        self.listener.cancel()
        self.__send(0, **kwargs)
        self.heartbeat.join(20)
        self.listener.join(20)
        self.connection.close()
        self.__connected = False

    def send_heartbeat(self):
        return self.__send(2)

    def send_event(self, name, *args, **kwargs):
        """Send an event message over the socket."""

        return self.__send(5, name=name, args=args, **kwargs)


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


class MessageHandler(Thread):

    def __init__(self, socket, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)

        self.socket = socket
        self.listeners = defaultdict(set)
        self.event = Event()

    def cancel(self):
        self.event.set()

    def run(self):
        """
        Wait for data to be received on the socket and do something about it.

        Currently, this is only really useful to handle event messages received
        via the socket.

        """

        while not self.event.is_set():
            data = self.socket.recv()
            bits = data.split(':', 3)
            msg_type, msg_id, endpoint = bits[:3]

            # handle event messages
            if int(msg_type) == 5:
                data = loads(bits[3])
                handlers = self.listeners.get(data['name'], [])
                for handler in handlers:
                    handler(*data['args'])

            # wait a bit before asking for more data
            time.sleep(0.1)

    def on(self, event, callback):
        self.listeners[event].add(callback)

