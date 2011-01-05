from django.db import models
from newsroom_core.models import BaseItem #, Section


class Page(BaseItem):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    summary = models.TextField()
    content = models.TextField()
    pinned = models.BooleanField()
    #section = models.ForeignKey(Section, blank=True, null=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return 'newsroom-page', [self.slug]

    class Meta:
        ordering = ('-pinned', '-created_at',)
