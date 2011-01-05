import datetime
from django import template

register = template.Library()

@register.filter
def daysdiff(time, other_time=None):
    if not time:
        return ''
    now = other_time or datetime.datetime.now()
    if time > now:
        delta = time.date() - now.date()
    else:
        delta = now.date() - time.date()
    days = delta.days
    if days == 0:
        return other_time and 'the same day' or 'today'
    if days == 1 and not other_time:
        if time > now:
            return 'tomorrow'
        else:
            return 'yesterday'
    if time > now:
        return '%s%s day%s%s' % (future_word, days, days != 1 and 's' or '',
                                other_time and ' later' or '')
    else:
        return '%s day%s %s' % (days, days != 1 and 's' or '',
                               other_time and 'earlier' or 'ago')

@register.filter
def past(time):
    if not time:
        return False
    return time < datetime.datetime.now()

@register.filter
def fuzzydate(time):
    if not time:
        return ''
    now = datetime.datetime.now().date()
    time = time.date()
    if time > now:
        delta = time - now
    else:
        delta = now - time
    days = delta.days
    if days == 0:
        return 'today'
    if days == 1:
        return 'yesterday'
    if time > now:
        this_week = now + datetime.timedelta(days=6-now.weekday())
        if time <= this_week:
            return 'this week'
        if time <= this_week - datetime.timedelta(days=7):
            return 'last week'
    else:
        this_week = now - datetime.timedelta(days=now.weekday())
        if time >= this_week:
            return 'this week'
        if time >= this_week + datetime.timedelta(days=7):
            return 'next week'
    monthdiff = abs((now.year*12+now.month) - (time.year*12+time.month))
    if not monthdiff:
        return 'this month'
    if monthdiff == 1:
        if time > now:
            return 'next month'
        return 'last month'
    if now.year == time.year:
        output = time.strftime('%B')
    else:
        output = time.strftime('%B %Y')
    return 'in %s' % output

@register.filter
def fuzzytime(time):
    if not time:
        return ''
    now = datetime.datetime.now()
    if time > now:
        delta = time - now
    else:
        delta = now - time
    if delta.days:
        return fuzzydate(time)
    value = delta.seconds
    def output(unit, number):
        string = '%s %s%s' % (number, unit, number!=1 and 's' or '')
        if time > now:
            return 'in %s' % string
        return '%s ago' % string
    if value < 1:
        return 'just now'
    if value < 60:
        return output('second', value)
    value = value // 60
    if value < 60:
        return output('minute', value)
    value = value // 60
    return output('hour', value)