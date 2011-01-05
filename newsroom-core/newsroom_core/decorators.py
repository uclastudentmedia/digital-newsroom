from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.utils.functional import wraps
from newsroom_core.utils.profile import get_profile


def login_required(func):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the newsroom log-in page if necessary.
    """
    @wraps(func)
    def dec(request, *args, **kwargs):
        if request.user.is_authenticated():
            return func(request, *args, **kwargs)
        tup = reverse('newsroom-login'), REDIRECT_FIELD_NAME, request.path
        return HttpResponseRedirect('%s?%s=%s' % tup)
    return dec


def editor_required(func):
    """
    Decorator for views that checks that the user is a logged in editor,
    redirecting to the newsroom log-in page otherwise.
    """
    @wraps(func)
    def dec(request, *args, **kwargs):
        if request.user.is_authenticated():
            profile = get_profile(request.user)
            if profile.is_editor:
                return func(request, *args, **kwargs)
        tup = reverse('newsroom-login'), REDIRECT_FIELD_NAME, request.path
        return HttpResponseRedirect('%s?%s=%s' % tup)
    return dec
