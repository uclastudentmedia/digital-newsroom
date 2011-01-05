import os
from django.db import models
from newsroom_core.models import BaseItem, Section


def _file_upload_path(instance, filename):
    return 'uploads/newsroom/files/%s/%s' % (instance.section.slug, filename)


class File(BaseItem):
    section = models.ForeignKey(Section)
    file = models.FileField(upload_to=_file_upload_path)
    file_size = models.PositiveIntegerField(null=True, editable=False)
    description = models.TextField(blank=True)
    superceeds = models.CharField(max_length=100, editable=False)
    superceeds_date = models.DateTimeField(null=True, editable=False)

    def get_absolute_url(self):
        return self.file.url

    def save(self, **kwargs):
        super(File, self).save(**kwargs)
        size = self.file.size
        if size != self.file_size:
            self.file_size = size
            super(File, self).save(**kwargs)

    def __unicode__(self):
        return os.path.basename(self.file.name)

    class Meta:
        ordering = ('-updated_on', 'file')