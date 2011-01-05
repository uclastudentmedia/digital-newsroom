from django.conf.urls.defaults import *

urlpatterns = patterns('newsroom_ideas.views',
    url(r'^$', 'listing', name='newsroom-ideas'),
    url(r'^(\d+)/$', 'detail', name='newsroom-idea'),
    url(r'^(\d+)/delete/$', 'delete', name='newsroom-idea-delete'),
    url(r'^(\d+)/edit/$', 'edit', name='newsroom-idea-edit'),
)
