import SimpleXMLRPCServer
import Numeric
import base64

def makeserver(emdict, host, port):
    class emserver(emdict):
        def _dispatch(self, method, params):
            try:
                func = getattr(self, method.replace("export", ""))
            except AttributeError:
                raise Exception('method "%s" is not supported' % method)
            else:
                result = apply(func, params)
                if isinstance(result, Numeric.arraytype):
                    result = base64.encodestring(result.tostring())
                return result

    server = SimpleXMLRPCServer.SimpleXMLRPCServer((host, port))
    server.register_instance(emserver())
    return server
