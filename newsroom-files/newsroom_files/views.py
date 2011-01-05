from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import list_detail, create_update
from django.views.generic.simple import direct_to_template
from newsroom_files import models
from newsroom_files import forms
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

    files = models.File.objects.all()

    c = {
        'files_count': files.count(),
    }

    if section:
        c['current_section'] = section
        files = files.filter(section=section)

    sort = request.GET.get('sort')
    sort_by_size = sort == 'size'
    if sort_by_size:
        files = files.order_by('file_size', '-updated_on')

    c['sections'] = core_models.Section.objects.annotate(Count('file'))
    c['sort_by_size'] = sort_by_size

    return list_detail.object_list(
        request, queryset=files, paginate_by=10,
        template_name='newsroom/files/list.html', template_object_name='file',
        extra_context=c
    )


@login_required
def upload(request, object_id=None):
    """
    Upload a file. Also handles the uploading a new version of an existing file.
    """
    if object_id:
        instance = get_object_or_404(models.File, pk=object_id)
    else:
        instance = None

    form = forms.FileForm(instance=instance, **form_kwargs(request))
    if form.is_valid():
        file = form.save(commit=False)
        if instance:
            file.updated_by = request.user
            file.superceeds = unicode(instance)
            file.superceeds_date = instance.updated_on
        else:
            file.created_by = request.user
        file.save()
        url = reverse(listing)
        return HttpResponseRedirect(url)

    c = {'form': form}
    return direct_to_template(request, 'newsroom/files/upload.html', c)


@login_required
def delete(request, object_id):
    url = reverse('newsroom-files')
    return create_update.delete_object(
        request, models.File, post_delete_redirect=url, object_id=object_id,
        template_name='newsroom/files/delete.html', template_object_name='file'
    )
