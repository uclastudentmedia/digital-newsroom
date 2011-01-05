import re
import datetime
from django import template
from newsroom_core import models
from newsroom_core.utils.calendar import assignment_day_url, assignment_day_url

register = template.Library()
RE_CAL = re.compile(r'^([a-z]{3})(\d{4})', re.IGNORECASE)
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct',
          'nov', 'dec']


@register.inclusion_tag('newsroom/tags/calendar.html', takes_context=True)
def newsroom_calendar(context, days, assignments=None):
    try:
        days = int(days)
    except (TypeError, ValueError):
        return {}
    month = None

    day = datetime.date.today()
    request = context.get('request')
    if request:
        match = RE_CAL.match(request.GET.get('cal', ''))
        if match and match.group(1).lower() in MONTHS:
            day = datetime.date(
                int(match.group(2)), MONTHS.index(match.group(1).lower())+1, 1
            )


    last_day = day + datetime.timedelta(days=days)

    if assignments is None:
        assignments = models.Assignment.objects.assignments()
    assignments = assignments.filter(pub_date__gte=day, pub_date__lte=last_day)

    assignment_days = {}
    for assignment in assignments:
        unfinished, finished = assignment_days.setdefault(assignment.pub_date,
                                                          ([], []))
        if assignment.status.means_completed:
            finished.append(assignment)
        else:
            unfinished.append(assignment)

    calendar = []
    day1 = None
    for i in range(days):
        if not day1 and day.day == 1:
            day1 = day
        url = assignment_day_url(day)
        unfinished, finished = assignment_days.get(day, ([], []))
        calendar.append((day, url, len(unfinished), len(finished)))
        day += datetime.timedelta(days=1)

    c = {'calendar': calendar, 'this_year': str(datetime.date.today().year),
         'request': context.get('request'), 'day1': day1}
    if day1:
        prev = day1 - datetime.timedelta(days=20)
        next = day1 + datetime.timedelta(days=40)
        c['m_prev'] = datetime.date(prev.year, prev.month, 1)
        c['m_next'] = datetime.date(next.year, next.month, 1)

    return c

@register.filter
def days_url(day):
    """
    Returns the url to show all assignments for a specific date.
    """
    if not isinstance(day, datetime.date):
        return ''
    return assignment_days_url(day)
