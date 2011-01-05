from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import list_detail, create_update
from django.views.generic.simple import direct_to_template
from newsroom_pages import models
from newsroom_pages import forms
from newsroom_core.decorators import login_required, editor_required
from newsroom_core.utils.forms import form_kwargs
from newsroom_core import models as core_models


@login_required
def listing(request):
    pages = models.Page.objects.all()

    # TODO: filter / ordering options

    return list_detail.object_list(
        request, queryset=pages, paginate_by=10,
        template_name='newsroom/pages/list.html', template_object_name='page'
    )


@login_required
def detail(request, slug):
    page = get_object_or_404(models.Page, slug=slug)
    c = {
        'page': page,
    }
    return direct_to_template(request, 'newsroom/pages/detail.html', c)


@editor_required
def delete(request, slug):
    url = reverse('newsroom-pages')
    return create_update.delete_object(
        request, models.Page, post_delete_redirect=url, slug=slug,
        template_name='newsroom/pages/delete.html', template_object_name='page'
    )


@editor_required
def edit(request, slug=None):
    """
    Add (if slug is not passed) or edit a page.
    """
    if slug:
        page = get_object_or_404(models.Page, slug=slug)
    else:
        page = None

    form = forms.PageForm(instance=page, **form_kwargs(request))
    if form.is_valid():
        page = form.save(commit=False)
        if slug:
            page.updated_by = request.user
        else:
            page.created_by = request.user
        page.save()
        url = reverse(detail, args=[page.slug])
        return HttpResponseRedirect(url)

    c = {
        'form': form,
        'add': not slug,
        'page': page,
    }
    return direct_to_template(request, 'newsroom/pages/edit.html', c)
