from django.conf.urls.defaults import *

# Copyright (c) 2011 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^bookbuzz/', include('amazon.urls')),
    # Example:
    # (r'^bookbuzz/', include('bookbuzz.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^$', 'amazon.views.index')
)
