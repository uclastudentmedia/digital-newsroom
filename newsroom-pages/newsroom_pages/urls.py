from django.conf.urls.defaults import *

urlpatterns = patterns('newsroom_pages.views',
    url(r'^$', 'listing', name='newsroom-pages'),
    url(r'^do/add/$', 'edit', name='newsroom-page-add'),
    url(r'^([\w-]+)/$', 'detail', name='newsroom-page'),
    url(r'^([\w-]+)/delete/$', 'delete', name='newsroom-page-delete'),
    url(r'^([\w-]+)/edit/$', 'edit', name='newsroom-page-edit'),
)
