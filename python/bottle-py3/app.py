import os
import sys
from bottle import route, run

@route('/hello/:name')
def index(name='World'):
    pyver = '.'.join(map(str, tuple(sys.version_info)[:3]))
    return 'Hello %s! (from <b>Python %s</b>)' % (name, pyver)


if __name__ == '__main__':
    port = int(os.getenv('VMC_APP_PORT', '8000'))
    run(host='localhost', port=port)

