from werkzeug.wrappers import Request, Response
from werkzeug.debug import DebuggedApplication

@Request.application
def application(request):
    1/0 # <-- expected; hover and click the terminal icon to the right
    return Response('Hello World!')

application = DebuggedApplication(application, evalex=True)


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 4000, application)
