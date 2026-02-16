from rc.compatibility import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from rc.io.timeoutclient import TimeoutServerProxy
from rc.threading import threaded
import contextlib
import select
import threading


class StoppableRPCServer(SimpleXMLRPCServer):
    """
    Adapted from http://bit.ly/nkXWKH, except that we actually wait
    for last request to complete since otherwise this fails sometimes,
    at least on Ubuntu
    """

    allow_reuse_address = True

    def __init__(self, address, timeout=0.1):
        SimpleXMLRPCServer.__init__(
            self,
            address,
            requestHandler=SimpleXMLRPCRequestHandler,
            logRequests=False,
            allow_none=True,
        )
        self.__is_shut_down = threading.Event()
        self.__is_shut_down.clear()
        self.timeout = timeout
        self.__stopped = False

    def serve_forever(self):
        while not self.__stopped:
            try:
                self.handle_request()
            except select.error:  # no-coverage
                return
        self.__is_shut_down.set()

    def stop(self):
        self.__stopped = True
        self.__is_shut_down.wait()
        self.server_close()


@contextlib.contextmanager
def rpc_server(host="", port=6000, funcs={}, timeout=0.01):
    server = StoppableRPCServer((host, port), timeout=timeout)
    with threaded(target=server.serve_forever, name="rpc-server-%s-%d" % (host, port)):
        for name, func in funcs.items():
            server.register_function(func, name)
        try:
            yield
        finally:
            server.stop()


@contextlib.contextmanager
def rpc_client(host="localhost", port=6000, timeout=30):
    client = TimeoutServerProxy("http://%s:%s" % (host, port), timeout)
    yield client
