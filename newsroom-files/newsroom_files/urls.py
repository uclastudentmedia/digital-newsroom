from django.conf.urls.defaults import *

urlpatterns = patterns('newsroom_files.views',
    url(r'^$', 'listing', name='newsroom-files'),
    url(r'^upload/$', 'upload', name='newsroom-file-upload'),
    url(r'^upload/(\d+)/$', 'upload', name='newsroom-file-replace'),
    url(r'^(\d+)/delete/$', 'delete', name='newsroom-file-delete'),
)
