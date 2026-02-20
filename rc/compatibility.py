import sys


PY3 = sys.version_info[0] > 2


if PY3:  # no-coverage
    import xmlrpc.client as xmlrpclib
    from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
    import http.client as httplib
    import queue as Queue

    # nested not supported - WIP
else:
    import xmlrpclib
    from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
    import httplib
    import Queue
    from contextlib import nested
