from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import list_detail, create_update
from django.views.generic.simple import direct_to_template
from newsroom_ideas import models
from newsroom_ideas import forms
from newsroom_core.decorators import login_required
from newsroom_core.utils.forms import form_kwargs
from newsroom_core import models as core_models


@login_required
def listing(request):
    # Check to see if we're filtering by section.
    section_slug = request.GET.get('section')
    section = None
    if section_slug:
        try:
            section = core_models.Section.objects.get(slug=section_slug)
        except core_models.Section.DoesNotExist:
            pass

    # Build form
    initial = {}
    if section:
        initial['section'] = section.pk
    form = forms.IdeaForm(initial=initial, **form_kwargs(request))
    if form.is_valid():
        idea = form.save(commit=False)
        idea.created_by = request.user
        idea.save()
        url = reverse(listing)
        return HttpResponseRedirect(url)

    ideas = models.Idea.objects.all()

    c = {
        'form': form,
        'ideas_count': ideas.count(),
    }

    if section:
        c['current_section'] = section
        ideas = ideas.filter(section=section)

    c['sections'] = core_models.Section.objects.annotate(Count('idea'))

    return list_detail.object_list(
        request, queryset=ideas, paginate_by=10,
        template_name='newsroom/ideas/list.html', template_object_name='idea',
        extra_context=c
    )


@login_required
def detail(request, object_id):
    idea = get_object_or_404(models.Idea, pk=object_id)

    form = forms.ReplyForm(**form_kwargs(request))
    if form.is_valid():
        reply = form.save(commit=False)
        reply.idea = idea
        reply.created_by = request.user
        reply.save()
        url = reverse(detail, args=[object_id])
        return HttpResponseRedirect(url)

    c = {
        'form': form,
        'idea': idea
    }
    return direct_to_template(request, 'newsroom/ideas/detail.html', c)


@login_required
def delete(request, object_id):
    url = reverse('newsroom-ideas')
    return create_update.delete_object(
        request, models.Idea, post_delete_redirect=url, object_id=object_id,
        template_name='newsroom/ideas/delete.html', template_object_name='idea'
    )


@login_required
def edit(request, object_id):
    idea = get_object_or_404(models.Idea, pk=object_id)

    form = forms.IdeaForm(instance=idea, **form_kwargs(request))
    if form.is_valid():
        idea = form.save(commit=False)
        idea.updated_by = request.user
        idea.save()
        url = reverse(listing)
        return HttpResponseRedirect(url)

    c = {
        'form': form,
        'idea': idea
    }
    return direct_to_template(request, 'newsroom/ideas/edit.html', c)
