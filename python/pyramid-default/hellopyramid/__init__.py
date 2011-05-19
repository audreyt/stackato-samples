from pyramid.config import Configurator
from hellopyramid.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('hellopyramid.views.my_view',
                    context='hellopyramid:resources.Root',
                    renderer='hellopyramid:templates/mytemplate.pt')
    config.add_static_view('static', 'hellopyramid:static')
    return config.make_wsgi_app()

