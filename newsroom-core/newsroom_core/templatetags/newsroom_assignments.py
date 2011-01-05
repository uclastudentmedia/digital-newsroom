import datetime
from django import template
from django.db.models import Count
from django.core.urlresolvers import reverse
from newsroom_core import models
from newsroom_core.utils.calendar import assignment_day_url


register = template.Library()


class GetStatusesNode(template.Node):
    def __init__(self, output_name, day_var, queryset_var):
        self.output_name = output_name
        self.day_var = day_var
        self.queryset_var = queryset_var
        super(GetStatusesNode, self).__init__()

    def render(self, context):
        if self.queryset_var:
            self.assignments = self.queryset_var.resolve(context)
            if self.assignments == '':
                return ''
        else:
            self.assignments = models.Assignment.objects.assignments()
        statuses = list(models.Status.objects.all())
        total = 0
        my_total = 0
        for status in statuses:
            all, my = self.count_assignments(status, context)
            status.assignments_count, status.my_assignments_count = all, my
            total += all
            my_total += my
        context[self.output_name] = statuses
        context['%s_assignments_total' % self.output_name] = total
        context['%s_my_assignments_total' % self.output_name] = my_total
        return ''

    def count_assignments(self, status, context):
        user = context['user']
        day = None
        assignments = self.assignments.filter(status=status)
        if self.day_var:
            day = self.day_var.resolve(context)
            if not isinstance(day, datetime.date):
                return 0, 0
            assignments = assignments.filter(pub_date=day)
        if user and user.is_authenticated():
            my_assignments_count = assignments.filter(involved=user).count()
        else:
            my_assignments_count = 0
        return assignments.count(), my_assignments_count


class AssignmentsUpcoming(template.Node):
    def __init__(self, count_var, output_name, queryset_var):
        self.count_var = count_var
        self.output_name = output_name
        self.queryset_var = queryset_var
        super(AssignmentsUpcoming, self).__init__()

    def render(self, context):
        count = self.count_var.resolve(context)
        try:
            count = int(count)
        except (TypeError, ValueError):
            return ''
        upcoming = []
        # Start from tomorrow
        day = datetime.date.today() + datetime.timedelta(days=1)
        if self.queryset_var:
            all_assignments = self.queryset_var.resolve(context)
            if all_assignments == '':
                return ''
        else:
            all_assignments = models.Assignment.objects.assignments()
        all_assignments = all_assignments.order_by('-created_at')
        current_days = 0
        i = 0
        # Get count days, looking forwards one week more than count in case of
        # blank days.
        while current_days < count and i < 7 + count:
            assignments = all_assignments.filter(pub_date=day)
            if assignments:
                url = assignment_day_url(day)
                upcoming.append((day, url, assignments))
                current_days += 1
            i += 1
            day += datetime.timedelta(days=1)
        context[self.output_name] = upcoming
        return ''


@register.tag
def get_statuses(parser, token):
    """
    Return a list of statuses to a context variable.

    The list is annotated with assignment totals and, if set, the assignment
    totals for the "user" context variable.

    Assignment totals are also set as context variables:
    ``[var]_assignments_total`` and, if "user" is set,
    ``[var]_my_assignments_total``.

    Example::

        {% get_statuses as statuses %}
        {% for status in statuses %}
        <p>{{ status }} ({{ status.my_assignments_count }} of {{ status.assignments_count }})</p>
        {% endfor %}
        <p>Total: {{ statuses_my_assignments_total }} of {{ statuses_assignments_total }}

    Also, you can also optionally specify a specific day you are retrieving
    assignments for and the assignments queryset::

        {% get_statuses as statuses for day from assignments %}

    """
    bits = token.split_contents()
    expected = {
        'as': ('output_name', False),
        'from': ('queryset_var', True),
        'for': ('day_var', True),
    }
    kwargs = {}
    ok = True
    if len(bits) < 3 or not len(bits) % 2:
        ok = False
    else:
        for i in range(1, len(bits), 2):
            arg, is_var = expected.get(bits[i], [None, None])
            if not arg or arg in kwargs:
                ok = False
                break
            value = bits[i+1]
            if is_var:
                value = parser.compile_filter(value)
            kwargs[arg] = value
    if not ok:
        raise template.TemplateSyntaxError(
            'valid arguments for {%% %s %%} are "as [statuses]", "for [day]" '
            'and "from [assignments]"' % bits[0])
    return GetStatusesNode(**kwargs)


@register.tag
def assignments_upcoming(parser, token):
    """
    Return a list of tuples containing a date, a url to assignments for only
    that day and a queryset of assignments for that day (ordered by most
    recently created).

    The number of days that are returned is determined by the one and only
    argument passed to this tag. For example::

        {% assignments_upcoming 5 as days %}
        {% for day, assignments in days %}
        ...

    Also, you can also optionally specify the assignments queryset::

        {% assignments_upcoming 5 as days from assignments %}
    """
    bits = token.split_contents()
    if len(bits) not in (4, 6) or bits[2] != 'as' or (len(bits) == 6 and
                                                      bits[4] != 'from'):
        raise template.TemplateSyntaxError(
            'expected {%% %s [days] as [output_name] %%} or '
            '{%% %s [days] as [output_name] from [assigments] %%}'
            % (bits[0], bits[0]))
    count_var = parser.compile_filter(bits[1])
    if len(bits) == 6:
        queryset_var = parser.compile_filter(bits[5])
    else:
        queryset_var = None
    return AssignmentsUpcoming(count_var, bits[3], queryset_var)


@register.inclusion_tag('newsroom/tags/list_assignments.html',
                        takes_context=True)
def list_assignments(context, assignments):
    return {
        'assignments': assignments,
        'more': context.get('more'),
        'current_section': context.get('current_section'),
        'request': context.get('request'),
        'url': context.get('url'),
        'compiled': context.get('compiled'),
        'assignments_profile': 'for_user' in context,
    }


@register.simple_tag
def url_assignments_day(day):
    if not day:
        return ''
    return reverse('newsroom-assignments-day',
                   args=[day.year, '%02d' % day.month, '%02d' % day.day])


@register.simple_tag
def url_assignments_compiled(day):
    if not day:
        return ''
    return reverse('newsroom-assignments-day-compiled',
                   args=[day.year, '%02d' % day.month, '%02d' % day.day])


class FakeStatusVariable:
    def resolve(self, *args, **kwargs):
        return models.Status.objects.all()


@register.tag
def for_statuses(parser, token):
    sequence = FakeStatusVariable()
    nodelist_loop = parser.parse('endfor')
    parser.next_token()
    return template.defaulttags.ForNode(loopvars=['status'], sequence=sequence,
                                        is_reversed=False,
                                        nodelist_loop=nodelist_loop)
