from django.utils.safestring import mark_safe
from django.utils.html import escape


TAB = '%s <span class="number"><span>(</span>%s<span>)</span></span>'


def assignments_count(tab, url_name, request):
    from newsroom_core import models
    from newsroom_core.utils.profile import get_profile
    user = request.user
    if not user or not user.is_authenticated() or\
       not get_profile(request.user).my_assignments_default:
        return tab, None
    count = models.Assignment.objects.assignments().filter(
                    involved=user, status__means_completed=False).count()
    if not count:
        return tab, None
    tab = mark_safe(TAB % (escape(tab), count))
    return tab, None


def requests_count(tab, url_name, request):
    from newsroom_core import models
    from newsroom_core.utils.profile import get_profile
    user = request.user
    if not user or not user.is_authenticated():
        return tab, None
    count = models.Assignment.objects.requests().filter(involved=user)\
                                                .count()
    if not count:
        return tab, None
    tab = mark_safe(TAB % (escape(tab), count))
    return tab, None


newsroom_tabs = (
    ('Assignments', 'newsroom-home', assignments_count),
    ('Requests', 'newsroom-requests', requests_count),
)

newsroom_secondary_tabs = (
    ('People', 'newsroom-people'),
    #('Search', 'newsroom-search'),
)