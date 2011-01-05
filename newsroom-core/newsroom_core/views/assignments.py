import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.contrib.auth.models import User
from newsroom_core import forms
from newsroom_core import models
from newsroom_core.decorators import login_required
from newsroom_core.utils.calendar import assignment_day_url
from newsroom_core.utils.forms import form_kwargs
from newsroom_core.utils.mail import send_mail_from_template


def _filter(request, extra_context):
    assignments = models.Assignment.objects.assignments()

    section_slug = request.GET.get('section')
    if section_slug:
        try:
            section = models.Section.objects.get(slug=section_slug)
        except:
            pass
        else:
            assignments = assignments.filter(section=section)
            extra_context['current_section'] = section
    return assignments


def _sort(request, assignments, extra_context):
    if assignments:
        # Calculate sort options
        sort_options = [
            ('title', 'Title'),
            ('created_at', 'Created Date'),
            ('status', 'Status'),
        ]
        sort_keys = {
            'title': SortKey('title'),
            'created_at': SortKey('created_at'),
            'status': SortKey(['status', 'order']),
        }
        #Add in sortable properties, some of which may be numeric
        for field in models.CategoryField.objects.filter(is_property=True)\
                                                 .exclude(sortable=0):
            sort_options.append((str(field.pk), field.name))
            sort_keys[str(field.pk)] = PropertySortKey(field)
        extra_context['sort_options'] = sort_options

    default_sort = request.GET.get('default_sort')
    clear_keys = []
    if default_sort or request.GET.get('sort1') == '':
        clear_keys.extend(['newsroom-sort1', 'newsroom-sort1-reverse'])
    if default_sort or request.GET.get('sort2') == '':
        clear_keys.extend(['newsroom-sort2', 'newsroom-sort2-reverse'])
    for key in clear_keys:
        try:
            del request.session[key]
        except KeyError:
            pass
    if assignments and not default_sort:
        sorted_assignments = list(assignments)
        sort1 = (request.GET.get('sort1',
                                 request.session.get('newsroom-sort1')))
        sort2 = (request.GET.get('sort2',
                                 request.session.get('newsroom-sort2')))
        if sort2 and sort2 in sort_keys:
            if 'sort2' in request.GET:
                reverse = bool(request.GET.get('sort2_reverse'))
                request.session['newsroom-sort2'] = sort2
                request.session['newsroom-sort2-reverse'] = reverse
            else:
                reverse = bool(request.session.get('newsroom-sort2-reverse'))
            key = sort_keys[sort2]
            sorted_assignments.sort(key=key, reverse=reverse)
            extra_context['sort2'] = sort2
            extra_context['sort2_reverse'] = reverse
        if sort1 and sort1 in sort_keys:
            if 'sort1' in request.GET:
                reverse = bool(request.GET.get('sort1_reverse'))
                request.session['newsroom-sort1'] = sort1
                request.session['newsroom-sort1-reverse'] = reverse
            else:
                reverse = bool(request.session.get('newsroom-sort1-reverse'))
            key = sort_keys[sort1]
            sorted_assignments.sort(key=key, reverse=reverse)
            extra_context['sort1'] = sort1
            extra_context['sort1_reverse'] = reverse
        extra_context['sorted_assignments'] = sorted_assignments
        return
    extra_context['sorted_assignments'] = assignments


def _get_related(assignment):
    if assignment.parent:
        related_requests = models.Assignment.objects.requests()\
            .filter(Q(pk=assignment.parent.pk)|Q(parent=assignment.parent))\
            .exclude(pk=assignment.pk).order_by('parent', 'title')
        related_assignments = models.Assignment.objects.assignments()\
            .filter(Q(pk=assignment.parent.pk)|Q(parent=assignment.parent))\
            .exclude(pk=assignment.pk).order_by('parent', 'title')
    else:
        related_requests = assignment.children.requests().order_by('title')
        related_assignments = assignment.children.assignments()\
                                                        .order_by('title')
    return related_requests, related_assignments


class SortKey:
    def __init__(self, attr, numeric=False):
        self.attr = attr
        self.numeric = numeric

    def __call__(self, obj):
        value = self.get_value(obj)
        if self.numeric:
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = None
        return value

    def get_value(self, obj):
        if not isinstance(self.attr, (list, tuple)):
            self.attr = [self.attr]
        value = obj
        for attr in self.attr:
            value = getattr(value, attr)
        return value


class PropertySortKey(SortKey):
    def __init__(self, field):
        self.field = field
        self.numeric = field.sortable == 2

    def get_value(self, obj):
        properties = dict([(f.categoryfield_ptr.name, unicode(v)) for f, v in
                           obj.properties])
        p = properties.get(self.field.name)
        if p:
            return unicode(p)


@login_required
def listing(request):
    """
    Show assignments for the upcoming days. Can be filtered by section, status
    or any of the choice fields of a top category type.
    """
    c = {
        'sections': models.Section.objects.all(),
        'top_categories': models.Category.objects.filter(top_category=True),
    }

    assignments = _filter(request, c)
    c['assignments'] = assignments

    return direct_to_template(request, 'newsroom/assignments.html', c)


@login_required
def listing_day(request, year, month, day):
    """
    Show all assignments for a day.
    """
    try:
        day = datetime.date(int(year), int(month), int(day))
    except ValueError:
        raise Http404

    c = {
        'sections': models.Section.objects.all(),
        'top_categories': models.Category.objects.filter(top_category=True),
        'day': day,
        'prev_day_url': assignment_day_url(day-datetime.timedelta(days=1)),
        'next_day_url': assignment_day_url(day+datetime.timedelta(days=1)),
    }

    assignments = _filter(request, c)
    assignments = assignments.filter(pub_date=day)
    c['assignments'] = assignments

    _sort(request, assignments, c)

    return direct_to_template(request, 'newsroom/assignments_day.html', c)


@login_required
def compiled(request, year, month, day):
    """
    Show all assignments for a day in a compiled format.
    """
    try:
        day = datetime.date(int(year), int(month), int(day))
    except ValueError:
        raise Http404

    c = {'day': day, 'compiled': True}
    assignments = _filter(request, c)
    assignments = list(assignments.filter(pub_date=day))

    for assignment in assignments:
        r, a = _get_related(assignment)
        assignment.related_requests, assignment.related_assignments = r, a

    c['assignments'] = assignments

    return direct_to_template(request, 'newsroom/assignments_compiled.html', c)


@login_required
def assignments_involved(request, username):
    """
    Show all assignments which a user is involved in.
    """
    user = get_object_or_404(User, username=username)
    assignments = models.Assignment.objects.assignments().filter(involved=user)
    assignments = assignments.filter(
        Q(pub_date__gte=datetime.date.today())|Q(status__means_completed=False)
    )

    c = {
        'for_user': user,
        'my_assignments': user == request.user,
        'assignments': assignments,
        'sections': models.Section.objects.all(),
        'top_categories': models.Category.objects.filter(top_category=True),
        'assignments_link': reverse(listing)
    }

    _sort(request, assignments, c)

    return direct_to_template(request, 'newsroom/assignments_profile.html', c)


@login_required
def add_assignment(request, slug):
    top_categories = models.Category.objects.filter(top_category=True)
    category = get_object_or_404(top_categories, slug=slug)

    initial = {
        'pub_date': datetime.date.today().strftime('%Y-%m-%d'),
        'responsible': request.user.pk,
        'involved': [request.user.pk],
    }
    kwargs = form_kwargs(request)
    kwargs['category'] = category
    form = forms.AssignmentForm(initial=initial, **kwargs)
    properties_form = forms.AssignmentPropertiesForm(**kwargs)
    details_form = forms.AssignmentDetailsForm(**kwargs)

    if (form.is_valid() and properties_form.is_valid() and
                                        details_form.is_valid()):
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        form.save_m2m()
        properties_form.instance = obj
        details_form.instance = obj
        properties_form.save()
        details_form.save()
        # Send emails
        for user in obj.involved.exclude(pk=request.user.pk):
            c = {'assignment': obj, 'user': user}
            send_mail_from_template(user.email, 'new_assignment', c)
        return HttpResponseRedirect(obj.get_absolute_url())

    c = {
        'form': form,
        'properties_form': properties_form,
        'details_form': details_form,
        'category': category,
    }

    return direct_to_template(request, 'newsroom/add_assignment.html', c)


@login_required
def assignment_detail(request, slug, child_id=None, is_request=False):
    assignments = models.Assignment.objects.assignments()\
                                           .filter(parent__isnull=True)
    assignment = get_object_or_404(assignments, slug=slug)
    if child_id:
        children = assignment.children.all()
        assignment = get_object_or_404(children, pk=child_id)

    is_request = not assignment.confirmed

    c = {'assignment': assignment}

    form = forms.CommentForm(**form_kwargs(request))
    if form.is_valid():
        comment = form.save(commit=False)
        comment.assignment = assignment
        comment.created_by = request.user
        comment.save()
        return HttpResponseRedirect(assignment.get_absolute_url())
    c['comment_form'] = form

    c['status_form'] = forms.StatusForm()

    related_requests, related_assignments = _get_related(assignment)
    c['related_requests'] = related_requests
    c['related_assignments'] = related_assignments

    if not assignment.parent and not is_request:
        c['request_categories'] = models.Category.objects.filter(
            top_category=False
        )

    return direct_to_template(request, 'newsroom/assignment_detail.html', c)


@login_required
def edit_assignment(request, slug, child_id=None, is_request=False):
    if child_id or not is_request:
        assignments = models.Assignment.objects.assignments()
    else:
        assignments = models.Assignment.objects.requests()
    assignments = assignments.filter(parent__isnull=True)
    assignment = get_object_or_404(assignments, slug=slug)
    if child_id:
        if is_request:
            children = assignment.children.requests()
        else:
            children = assignment.children.assignments()
        assignment = get_object_or_404(children, pk=child_id)

    kwargs = form_kwargs(request)
    kwargs['instance'] = assignment
    kwargs['category'] = assignment.category
    form_class = is_request and forms.RequestForm or forms.AssignmentForm
    form = form_class(**kwargs)
    properties_form = forms.AssignmentPropertiesForm(**kwargs)
    details_form = forms.AssignmentDetailsForm(**kwargs)

    if (form.is_valid() and properties_form.is_valid() and
                                        details_form.is_valid()):
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        form.save_m2m()
        properties_form.instance = obj
        details_form.instance = obj
        properties_form.save()
        details_form.save()
        return HttpResponseRedirect(obj.get_absolute_url())

    c = {
        'edit': True,
        'form': form,
        'properties_form': properties_form,
        'details_form': details_form,
        'category': assignment.category,
        'is_request': is_request,
    }

    return direct_to_template(request, 'newsroom/add_assignment.html', c)


def change_status(request):
    if not request.user.is_authenticated():
        raise Http404
    errors = []
    pk = request.POST.get('assignment_id')
    change_status = request.POST.get('change_status')
    if not pk:
        errors.append('no assignment id')
    if not errors:
        assignment = None
        status = None
        try:
            assignment = models.Assignment.objects.assignments().get(pk=pk)
        except models.Assignment.DoesNotExist:
            errors.append('invalid assignment id')
        if not change_status:
            errors.append('no status slug provided')
        else:
            try:
                status = models.Status.objects.get(slug=change_status)
            except models.Status.DoesNotExist:
                errors.append('invalid status slug')
        if not errors:
            if assignment.status != status:
                assignment.status = status
                assignment.save()
                assignment.updated_by = request.user
                assignment.updated_on = datetime.datetime.now()
                assignment.statushistory_set.create(
                    status=status, user=request.user,
                    comment=request.POST.get('comment', '')
                )
            if request.is_ajax():
                return HttpResponse('%s,%s,%s' % (assignment.pk, status.slug, status))
            else:
                return HttpResponseRedirect(assignment.get_absolute_url())

    if assignment and not request.is_ajax():
        return HttpResponseRedirect(assignment.get_absolute_url())
    return HttpResponseBadRequest(', '.join(errors))