from django.conf.urls.defaults import patterns

urlpatterns = patterns('amazon.views',
    (r'^$', 'index'),
    (r'^textBookList/$', 'textBookList'),
    (r'^showRanksForBook/(?P<asin>.*)$', 'showRanksForBook'),
    (r'^showRanksByDate/(?P<date>.*)$', 'showRanksByDate'),
    (r'^showBookRankGraph/', 'showBookRankGraph'),
    (r'^showTweetsForBook', 'showTweetsForBook'),
    (r'^getTweets', 'getTweets'),
    (r'^static/(?P<path>.*)$', 'serveStaticFile'),
)