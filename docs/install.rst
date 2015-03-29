.. _install:

===================
Client Installation
===================

The client component of UManSysProp can be installed on any machine with Python
available. On Ubuntu, the waveform PPA can be used for simple installation::

    $ sudo add-apt-repository ppa:waveform/ppa
    $ sudo apt-get update
    $ sudo apt-get install python-umansysprop

On other platforms, the package can be installed from `PyPI`_. Specify the
``client`` option to pull in all dependencies required by the client
component::

    $ sudo pip install "umansysprop[client]"

===================
Server Installation
===================

The server component of UManSysProp is only tested on Linux platforms, although
it should theoretically work on others. The application uses the `WSGI`_
architecture for communication with web-servers; integration with your
web-server depends on understanding WSGI applications. The `Flask deployment
guide`_ may be helpful in this case.

The server component can be installed from `PyPI`_. Specify the ``server``
option to pull in all dependencies required by the server component::

    $ sudo pip install "umansysprop[server]"

Please be aware that `OpenBabel`_ is a requirement of the server component. As
this is SWIG based you will need a C/C++ build environment installed, along
with the necessary Python and OpenBabel headers. The following command should
suffice for this on Ubuntu::

    $ sudo apt-get install build-essential python-dev libopenbabel-dev

.. _OpenBabel: http://openbabel.org/
.. _PyPI: https://pypi.python.org/pypi
.. _WSGI: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
.. _Flask deployment guide: http://flask.pocoo.org/docs/0.10/deploying/
