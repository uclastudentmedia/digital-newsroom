from django.contrib import admin
from newsroom_ideas import models


class IdeaComments(admin.TabularInline):
    model = models.Comment


class Idea(admin.ModelAdmin):
    inlines = [IdeaComments]


admin.site.register(models.Idea, Idea)
