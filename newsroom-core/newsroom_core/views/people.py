import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from newsroom_core import models
from newsroom_core import forms
from newsroom_core.decorators import login_required
from newsroom_core.utils.forms import form_kwargs
from newsroom_core.utils.profile import get_profile


SHOW_ASSIGNMENTS = 3


@login_required
def listing(request, section=None):
    c = {}
    sections = models.Section.objects.annotate(
                                            people_count=Count('profile_set'))
    c['all_sections'] = sections
    if section:
        current_section = get_object_or_404(sections, slug=section)
        c['current_section'] = current_section
        sections = [current_section]
        other_profiles = []
    else:
        other_profiles = models.NewsroomProfile.objects.filter(
                                                        section__isnull=True)
    c['other_profiles'] = other_profiles
    c['sections'] = sections
    total = sum([section.people_count for section in sections])
    total += len(other_profiles)
    c['total'] = total
    return direct_to_template(request, 'newsroom/people.html', c)


@login_required
def detail(request, username):
    profile = get_object_or_404(models.NewsroomProfile, user__username=username)
    q_active = (Q(pub_date__gte=datetime.date.today())|
                Q(status__means_completed=False))
    assignments = models.Assignment.objects.assignments()
    assignments = assignments.filter(involved=profile.user).filter(q_active)
    requests = models.Assignment.objects.requests()
    requests = requests.filter(involved=profile.user).filter(q_active)
    c = {
        'profile': profile,
        'assignments': assignments[:SHOW_ASSIGNMENTS],
        'requests': requests,
        # The following context setting hides the sections in the
        # {% get_assignments %} tag.
        'current_section': 'x',
    }
    count = assignments.count()
    if count > SHOW_ASSIGNMENTS:
        c['assignments_count'] = count
    return direct_to_template(request, 'newsroom/person.html', c)


@login_required
def edit_profile(request, username=None):
    c = {}
    if not username:
        url = reverse(edit_profile, args=[request.user.username])
        return HttpResponseRedirect(url)
    user = get_object_or_404(User, username=username)
    profile = get_profile(user)
    kwargs = form_kwargs(request)
    user_form = forms.UserForm(instance=user, **kwargs)
    form = forms.ProfileForm(instance=profile, **kwargs)
    if not request.user.is_staff:
        del form.fields['is_editor']
    if username != request.user.username:
        del form.fields['email_notifications']
        del form.fields['my_assignments_default']
        del form.fields['my_section_default']
        valid = form.is_valid() and user_form.is_valid()
    else:
        password_form = forms.PasswordForm(user=user, **kwargs)
        c['password_form'] = password_form
        valid = form.is_valid() and user_form.is_valid() and \
                password_form.is_valid()
        if valid:
            password_form.save()
    if valid:
        user = user_form.save()
        if profile:
            profile = form.save()
        else:
            profile = form.save(commit=False)
            profile.user = user
        url = reverse(detail, args=[profile.user.username])
        return HttpResponseRedirect(url)
    c['form'] = form
    c['user_form'] = user_form
    return direct_to_template(request, 'newsroom/person_edit.html', c)
