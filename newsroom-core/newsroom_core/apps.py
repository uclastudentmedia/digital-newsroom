from django.conf import settings


tabs = secondary_tabs = None

def build_tabs():
    """
    Builds the tabs for the newsroom templates.

    Any installed application can provide  ``newsroom_tabs`` or
    ``newsroom_secondary_tabs`` attributes to add tabs to the newsroom
    templates.

    The tab format is a list of either tuple pairs of (tab_name, reverse_url) or
    tuple triplets of (tab_name, reverse_url, callback_function).

    The callback function should accept three parameters, tab_name, reverse_url
    and request, and return a tuple pair of (tab_name, url). If tab_name is
    returned as a false value then no tab will be added. If url is returned as a
    false value then calculated url from the original reverse_url will be used.
    """
    global tabs
    global secondary_tabs
    if tabs or secondary_tabs:
        return
    tabs = []
    secondary_tabs = []
    for app_name in settings.INSTALLED_APPS:
        mod = __import__(app_name, {}, {}, ['newsroom_tabs',
                                            'newsroom_secondary_tabs'])
        app_tabs = getattr(mod, 'newsroom_tabs', None) or []
        app_secondary_tabs = getattr(mod, 'newsroom_secondary_tabs', None) or []
        tabs.extend(list(app_tabs))
        secondary_tabs.extend(list(app_secondary_tabs))
