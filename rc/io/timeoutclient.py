from rc.compatibility import xmlrpclib
from rc.compatibility import httplib
import socket
import sys

"""
XML-RPC client with configurable timeout.  See:
http://stackoverflow.com/questions/372365/set-timeout-for-xmlrpclib-serverproxy
"""

# Handle pre-2.6 python:
try:
    DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT
except AttributeError:  # no-coverage
    DEFAULT_TIMEOUT = 60


if sys.version_info < (2, 7):  # no-coverage

    class TimeoutHTTP(httplib.HTTP):
        def __init__(self, host="", port=None, strict=None, timeout=DEFAULT_TIMEOUT):
            if port == 0:
                port = None
            self._setup(self._connection_class(host, port, strict, timeout))

    class TimeoutTransport(xmlrpclib.Transport):
        def __init__(self, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
            xmlrpclib.Transport.__init__(self, *args, **kwargs)
            self.timeout = timeout

        def make_connection(self, host):
            host, extra_headers, x509 = self.get_host_info(host)
            conn = TimeoutHTTP(host, timeout=self.timeout)
            return conn

else:  # no-coverage

    class TimeoutTransport(xmlrpclib.Transport):
        def __init__(self, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
            xmlrpclib.Transport.__init__(self, *args, **kwargs)
            self.timeout = timeout

        def make_connection(self, host):
            chost, self._extra_headers, x509 = self.get_host_info(host)
            self._connection = (
                host,
                httplib.HTTPConnection(chost, timeout=self.timeout),
            )
            return self._connection[1]


class TimeoutServerProxy(xmlrpclib.ServerProxy):
    def __init__(self, uri, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
        kwargs["transport"] = TimeoutTransport(
            timeout=timeout, use_datetime=kwargs.get("use_datetime", 0)
        )
        xmlrpclib.ServerProxy.__init__(self, uri, *args, **kwargs)
