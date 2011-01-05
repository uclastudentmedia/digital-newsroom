from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = []

# Serve up newsroom static media if we're running the local development server.
if settings.LOCAL_DEV_SERVER:
    url = settings.NEWSROOM_MEDIA_URL[1:]
    root = settings.NEWSROOM_MEDIA_ROOT
    urlpatterns += patterns('django.views.static',
        (r'^%s(?P<path>.*)$' % url, 'serve', {'document_root': root}),
    )