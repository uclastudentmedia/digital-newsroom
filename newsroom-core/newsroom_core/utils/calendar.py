import datetime
from django.core.urlresolvers import reverse


def build_calendar(days=30):
    month = None
    day = datetime.date.today()
    calendar = []
    for i in range(days):
        url = '#'
        unfinished = day.day % 3
        finished = day.day % 2
        calendar.append((day, url, unfinished, finished))
        day += datetime.timedelta(days=1)
    return calendar


def assignment_day_url(day):
    args = [day.year, '%02d' % day.month, '%02d' % day.day]
    return reverse('newsroom-assignments-day', args=args)