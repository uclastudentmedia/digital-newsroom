import datetime
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.views.generic.simple import direct_to_template
from newsroom_core import forms
from newsroom_core import models
from newsroom_core.decorators import login_required, editor_required
from newsroom_core.utils.forms import form_kwargs


@login_required
def listing(request):
    """
    Show current requests. Can be filtered by section.
    """
    c = {
        'sections': models.Section.objects.all(),
    }

    requests = models.Assignment.objects.requests()

    section_slug = request.GET.get('section')
    if section_slug:
        try:
            section = models.Section.objects.get(slug=section_slug)
        except:
            pass
        else:
            requests = requests.filter(section=section)
            c['current_section'] = section

    sort = request.GET.get('sort')
    if sort == 'activity':
        requests = requests.order_by('-updated_on')
        c['sorted_by'] = sort

    c['requests'] = requests
    c['sub_categories'] = models.Category.objects.exclude(top_category=True)

    return direct_to_template(request, 'newsroom/requests.html', c)


@login_required
def add_request(request, category_slug):
    top_assignments = models.Assignment.objects.assignments()\
                        .filter(parent__isnull=True)
    sub_categories = models.Category.objects.exclude(top_category=True)
    category = get_object_or_404(sub_categories, slug=category_slug)
    c = {'category': category}
    widget = forms.recent_assignments_widget()
    if widget.choices:
        widget_html = widget.render(name='recent_assignment_id', value='')
        c['recent_assignments'] = mark_safe(widget_html)
    if request.method == 'POST':
        assignment_slug = request.POST.get('assignment_slug')
        assignment_id = (request.POST.get('recent_assignment_id') or
                         request.POST.get('assignment_id'))
        if assignment_slug:
            assignments = top_assignments.filter(
                                        title__icontains=assignment_slug)
            if not assignments:
                c['error'] = 'No assignments were found matching that slug.'
                c['assignment_slug'] = assignment_slug
            else:
                c['assignments_match'] = assignment_slug
                c['assignments'] = assignments
        elif assignment_id:
            try:
                assignment = models.Assignment.objects.get(pk=assignment_id)
            except:
                c['error'] = 'No matching assignment was found. Please try again.'
            else:
                url = reverse(add_request_to_assignment,
                              kwargs={'category_slug': category_slug,
                                      'assignment_slug': assignment.slug})
                return HttpResponseRedirect(url)
        else:
            if widget.choices:
                c['error'] = ('Please choose an assignment or enter an '
                              'assignment slug.')
            else:
                c['error'] = 'Please enter an assignment slug.'
    return direct_to_template(request, 'newsroom/add_request.html', c)


@login_required
def add_request_to_assignment(request, category_slug, assignment_slug):
    top_assignments = models.Assignment.objects.assignments()\
                        .filter(parent__isnull=True)
    sub_categories = models.Category.objects.exclude(top_category=True)
    category = get_object_or_404(sub_categories, slug=category_slug)
    parent = get_object_or_404(top_assignments, slug=assignment_slug)

    initial = {
        'pub_date': datetime.date.today().strftime('%Y-%m-%d'),
        'responsible': request.user.pk,
        'involved': [request.user.pk],
    }
    kwargs = form_kwargs(request)
    form = forms.RequestForm(initial=initial, category=category,
                             parent=parent, **kwargs)
    properties_form = forms.AssignmentPropertiesForm(category=category,
                                                     **kwargs)
    details_form = forms.AssignmentDetailsForm(category=category, **kwargs)

    if (form.is_valid() and properties_form.is_valid() and
                                        details_form.is_valid()):
        obj = form.save(commit=False)
        obj.parent = parent
        obj.created_by = request.user
        obj.save()
        form.save_m2m()
        properties_form.instance = obj
        details_form.instance = obj
        properties_form.save()
        details_form.save()
        return HttpResponseRedirect(obj.get_absolute_url())

    c = {
        'parent': parent,
        'form': form,
        'properties_form': properties_form,
        'details_form': details_form,
        'category': category,
    }
    return direct_to_template(request,
                              'newsroom/add_request_to_assignment.html', c)


@editor_required
def accept(request, slug, child_id):
    assignments = models.Assignment.objects.assignments()\
                                           .filter(parent__isnull=True)
    assignment = get_object_or_404(assignments, slug=slug)
    if child_id:
        children = assignment.children.requests()
        assignment = get_object_or_404(children, pk=child_id)

    initial = {'pub_date': assignment.parent.pub_date}
    form = forms.AcceptRequestForm(initial=initial, **form_kwargs(request))
    if form.is_valid():
        assignment.confirmed = True
        assignment.pub_date = form.cleaned_data['pub_date']
        assignment.save()
        return HttpResponseRedirect(assignment.get_absolute_url())

    c = {'assignment': assignment, 'accept_form': form}
    return direct_to_template(request, 'newsroom/accept_request.html', c)
