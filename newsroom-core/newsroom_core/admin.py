from django.db import transaction
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from newsroom_core import models


class CategoryChoicesInline(admin.TabularInline):
    extra = 6
    model = models.CategoryChoiceFieldChoice


class CategoryBaseField(admin.ModelAdmin):
    exclude = ['order']
    list_display = ['name', 'category']
    list_filter = ['category']
    ordering = ['category', 'name']

    def redirect_to_category(self, request, response, obj):
        category_id = request.GET.get('category')
        if not category_id or request.POST.has_key("_continue"):
            return response
        if (request.POST.has_key("_addanother") or
            request.POST.has_key("_saveasnew")):
            loc = response['Location']
            loc = '%s%scategory=%s' % (loc, '?' in loc and '&' or '?',
                                       category_id)
            response['Location'] = loc
            return response
        url =  reverse('%sadmin_newsroom_core_category_change' %
                       self.admin_site.name, args=[obj.category_id])
        return HttpResponseRedirect(url)

    def response_add(self, request, obj, *args, **kwargs):
        response = super(CategoryBaseField, self).response_add(request, obj,
                                                        *args, **kwargs)
        return self.redirect_to_category(request, response, obj)

    def response_add(self, request, obj, *args, **kwargs):
        response = super(CategoryBaseField, self).response_change(request, obj,
                                                        *args, **kwargs)
        return self.redirect_to_category(request, response, obj)


class CategoryChoiceField(CategoryBaseField):
    inlines = [CategoryChoicesInline]


class CategoryFields(admin.TabularInline):
    model = models.CategoryField
    extra = 0


class SlugFromTitle(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ['title'],
    }


class Category(SlugFromTitle):
    inlines = [CategoryFields]

    def response_change(self, request, obj, *args, **kwargs):
        self.reorder_fields(category=obj)
        return super(Category, self).response_change(request, obj, *args,
                                                     **kwargs)

    @transaction.commit_on_success
    def reorder_fields(self, category):
        for i, obj in enumerate(category.properties):
            obj.order = i * 2 + 1
            obj.save()
        for i, obj in enumerate(category.details):
            obj.order = i * 2 + 1
            obj.save()


class BaseItem(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        obj.save()


class Assignment(BaseItem):
    pass

admin.site.register(models.Status, SlugFromTitle)
admin.site.register(models.Section, SlugFromTitle)
admin.site.register(models.Category, Category)
admin.site.register(models.CategoryChoiceField, CategoryChoiceField)
admin.site.register(models.CategoryTextField, CategoryBaseField)
admin.site.register(models.CategoryBigTextField, CategoryBaseField)
admin.site.register(models.Assignment, Assignment)
