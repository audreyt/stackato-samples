import os
import sys
import cherrypy

class HelloWorld:
    def index(self):
        pyver = '.'.join(map(str, tuple(sys.version_info)[:3]))
        return "Hello world! (from Python %s)" % pyver
    index.exposed = True


if __name__ == '__main__':
    port = int(os.getenv('VMC_APP_PORT', '8001'))
    cherrypy.quickstart(HelloWorld(), config={'global': {'server.socket_port': port}})
