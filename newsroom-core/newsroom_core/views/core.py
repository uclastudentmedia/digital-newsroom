from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import never_cache
from newsroom_core.decorators import login_required
from newsroom_core.utils.profile import get_profile


@login_required
def initial(request):
    """
    Redirect the user to either the assignments page or the personal assignments
    involved page (depending on their user preference).
    """
    profile = get_profile(request.user)
    if profile.my_assignments_default:
        url = reverse('newsroom-assignments-profile',
                      args=[request.user.username])
    else:
        url = reverse('newsroom-assignments')
    if profile.my_section_default:
        url = '%s?section=%s' % (url, profile.section.slug)
    return HttpResponseRedirect(url)


@never_cache
def login(request, template_name='newsroom/registration/login.html'):
    """
    Log in a user, honoring their choice of whether or not to "remember" them
    (i.e. whether to expire the user's session when their browser is closed).
    """
    response = auth_views.login(request, template_name)
    if isinstance(response, HttpResponseRedirect):
        # Successful login, honor the "remember me" setting.
        expire_at_close = not request.POST.get('remember_me')
        newsroom_login_age = getattr(settings, 'NEWSROOM_LOGIN_AGE', None)
        remember_time = newsroom_login_age
        if expire_at_close ^ settings.SESSION_EXPIRE_AT_BROWSER_CLOSE:
            if expire_at_close:
                remember_time = 0
            else:
                remember_time = (newsroom_login_age or
                                 settings.SESSION_COOKIE_AGE)
        if remember_time is not None:
            request.session.set_expiry(remember_time)
    return response
