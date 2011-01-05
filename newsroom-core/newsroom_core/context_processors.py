from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.defaultfilters import slugify
from newsroom_core import apps


def _build_tabs(tabs_list, request):
    tabs = []
    for bits in tabs_list:
        reverse_url = True
        try:
            tab, url_name, callback = bits
        except ValueError:
            tab, url_name = bits
            slug = slugify(tab)
        else:
            slug = slugify(tab)
            tab, url = callback(tab, url_name, request)
            if url:
                reverse_url = False
        if tab:
            if reverse_url:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    continue
            tabs.append((slug, tab, url))
    return tabs


def newsroom(request):
    return {
        'request': request,
        'newsroom_tabs': _build_tabs(apps.tabs, request),
        'newsroom_secondary_tabs': _build_tabs(apps.secondary_tabs, request),
        'NEWSROOM_MEDIA_URL': settings.NEWSROOM_MEDIA_URL,
    }