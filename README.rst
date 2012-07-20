socketIO.client
===============

Here is a barebones socket.io_ client library for Python.

Thanks to rod_ for his `StackOverflow question and answer`__, on which this code
is based.

Thanks also to liris_ for his websocket-client_ and to guille_ for the
`socket.io specification`_.


Installation
------------

.. code-block:: bash

    # Prepare isolated environment
    ENV=$HOME/Projects/env
    virtualenv $ENV
    mkdir $ENV/opt

    # Activate isolated environment
    source $ENV/bin/activate

    # Install package
    easy_install -U socketIO-client


Usage
-----

.. code-block:: bash

    ENV=$HOME/Projects/env
    source $ENV/bin/activate

.. code-block:: python

    from socketIO import SocketIO
    s = SocketIO('localhost', 8000)
    s.emit('news', {'hello': 'world'})


License
-------

This software is available under the MIT License.  Please see LICENSE for the
full license text.

.. _socket.io: http://socket.io
.. _rod: http://stackoverflow.com/users/370115/rod
.. _so: http://stackoverflow.com/questions/6692908/formatting-messages-to-send-to-socket-io-node-js-server-from-python-client/
.. _liris: https://github.com/liris
.. _websocket-client: https://github.com/liris/websocket-client
.. _guille: https://github.com/guille
.. _socket.io specification: https://github.com/LearnBoost/socket.io-spec

__ so_
