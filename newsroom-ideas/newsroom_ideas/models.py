from django.db import models
from newsroom_core.models import BaseItem, Section


class Idea(BaseItem):
    idea = models.TextField()
    section = models.ForeignKey(Section, blank=True, null=True)
    file = models.FileField(upload_to='uploads/newsroom/ideas', blank=True)

    @models.permalink
    def get_absolute_url(self):
        return 'newsroom-idea', [self.pk]


class Comment(BaseItem):
    idea = models.ForeignKey(Idea)
    comment = models.TextField()
    file = models.FileField(upload_to='uploads/newsroom/ideas', blank=True)

    class Meta:
        ordering = ('created_at',)