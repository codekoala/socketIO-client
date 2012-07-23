0.1.4
-----

- Events can be received and handled (in a separate thread)

0.1.3
-----

- ``SocketIO.emit`` now accepts an ``endpoint`` and ``msg_id`` parameter
- Made the message sending a bit more generic
- SocketIO instances will have dynamic methods based on which message types are
  accepted (if ``gevent-socketio`` is installed)

0.1.2
-----

- Updated JSON import for newer versions of Python
- OCD attack

0.1.1
-----

- Added exception handling to destructor in case of connection failure

0.1.0
-----

- Wrapped code from StackOverflow_


.. _StackOverflow: http://stackoverflow.com/questions/6692908/formatting-messages-to-send-to-socket-io-node-js-server-from-python-client/
