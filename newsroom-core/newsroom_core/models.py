import datetime
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist
from newsroom_core import managers
from newsroom_core.utils.slugify import unique_slugify
from newsroom_core.utils.mail import send_mail_from_template


class NewsroomProfile(models.Model):
    """
    Settings and profile for an individual user.
    """
    user = models.OneToOneField(User)
    section = models.ForeignKey('Section', related_name='profile_set')
    title = models.CharField(max_length=100, blank=True)
    office_number = models.CharField(max_length=40, blank=True)
    office_number_ext = models.CharField(max_length=10, blank=True)
    home_number = models.CharField(max_length=50, blank=True)
    fax_number = models.CharField(max_length=50, blank=True)
    mobile_number = models.CharField(max_length=50, blank=True)
    additional_info = models.TextField(blank=True)
    photo = models.ImageField(blank=True, upload_to='uploads/newsroom/profiles')
    # Settings:
    is_editor = models.BooleanField()
    email_notifications = models.BooleanField()
    my_assignments_default = models.BooleanField()
    my_section_default = models.BooleanField()

    def __unicode__(self):
        try:
            return self.user.get_full_name() or self.user.username
        except User.DoesNotExist:
            return 'anonymous'

    @models.permalink
    def get_absolute_url(self):
        return 'newsroom-person', [self.user.username]


class BaseItem(models.Model):
    created_by = models.ForeignKey(User, editable=False,
                                   related_name='created_%s_set')
    created_at = models.DateTimeField(default=datetime.datetime.now,
                                      editable=False)
    updated_by = models.ForeignKey(User, editable=False, blank=True, null=True,
                                   related_name='updated_%s_set')
    updated_on = models.DateTimeField(editable=False)

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    def save(self, secret_update=False, *args, **kwargs):
        if self.pk:
            if not secret_update:
                self.updated_on = datetime.datetime.now()
        else:
            self.updated_on = self.created_at
        super(BaseItem, self).save(*args, **kwargs)


class Section(models.Model):
    """
    Assignments belong to a specific section.
    """
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title',)


class Status(models.Model):
    """
    Assignments are assigned a status to show current progress.
    """
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    means_completed = models.BooleanField()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('order', 'title')
        verbose_name_plural = 'statuses'


class Category(models.Model):
    """
    A category for assignments.
    """
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    top_category = models.BooleanField(
        help_text='Assignments in this category can contain assignments (which '
                  'are non-top categories).'
    )

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title',)
        verbose_name_plural = 'categories'

    @property
    def properties(self):
        """
        An ordered list of property fields for this category.
        """
        return [f.field for f in self.field_set.filter(is_property=True)]

    @property
    def details(self):
        """
        An ordered list of detail fields for this category.
        """
        return [f.field for f in self.field_set.filter(is_property=False)]


class CategoryField(models.Model):
    """
    A base class which helps provide extra fields for Assignments of a section.
    """
    category = models.ForeignKey(Category, related_name='field_set')
    is_property = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    required = models.BooleanField()
    name = models.CharField(max_length=40)
    sortable = models.PositiveSmallIntegerField(default=0, choices=(
        (0, 'Not sorted'),
        (1, 'Text sort'),
        (2, 'Numeric sort'),
    ))

    @property
    def field(self):
        """
        Get the actual field for this quasi base class.
        """
        if not self.__class__ == CategoryField:
            # We're already a subclass, just return the field.
            return self
        # Iterate the related objects (we'll assume they are all the one-to-one
        # relationships with the real fields) until we get a match.
        for f in [rel.var_name for rel in self._meta.get_all_related_objects()]:
            try:
                return getattr(self, f)
            except ObjectDoesNotExist:
                pass

    def __unicode__(self):
        field_type = self.is_property and 'Property' or 'Detail'
        return '%s (%s): %s' % (field_type, self.field._meta.verbose_name,
                                self.name)

    class Meta:
        ordering = ('-is_property', 'order')

    def save(self, *args, **kwargs):
        if not self.order:
            max_order = self.category.field_set.filter(
                            is_property=self.is_property).aggregate(
                            models.Max('order')).get('order__max')
            self.order = max_order is not None and max_order + 2 or 1
        return super(CategoryField, self).save(*args, **kwargs)


class CategoryTextField(CategoryField):
    length = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'text field'
        verbose_name_plural = 'category %ss' % verbose_name


class CategoryBigTextField(CategoryField):
    class Meta:
        verbose_name = 'multi-line text field'
        verbose_name_plural = 'category %ss' % verbose_name


class CategoryChoiceField(CategoryField):
    class Meta:
        verbose_name = 'choice field'
        verbose_name_plural = 'category %ss' % verbose_name


class CategoryChoiceFieldChoice(models.Model):
    field = models.ForeignKey(CategoryChoiceField, related_name='choices')
    option = models.CharField(max_length=100)

    def __unicode__(self):
        return self.option

    class Meta:
        verbose_name = 'option'
        ordering = ('option',)


class Assignment(BaseItem):
    """
    An assignment. If it is not yet confirmed, then it is a request.
    """
    title = models.CharField(max_length=250)
    slug = models.SlugField(blank=True, editable=False)
    status = models.ForeignKey(Status)
    section = models.ForeignKey(Section)
    category = models.ForeignKey(Category)
    involved = models.ManyToManyField(User, related_name='assignments_involved',
                                      blank=True)
    responsible = models.ForeignKey(User,
                                    related_name='assignments_responsible')
    pub_date = models.DateField(blank=True, null=True)
    parent = models.ForeignKey('self', related_name='children', blank=True,
                               null=True, editable=False)
    confirmed = models.BooleanField()

    objects = managers.AssignmentManager()

    def __unicode__(self, *args, **kwargs):
        return self.title

    def save(self, *args, **kwargs):
        if not self.parent:
            # All top-level assignments need slugs
            if not self.slug or self.title != Assignment.objects.get(pk=self.pk).title:
                unique_slugify(self, self.title)
        super(Assignment, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        url_name = 'newsroom-assignment'
        if self.parent:
            return url_name, [], {'slug': self.parent.slug, 'child_id': self.pk}
        return url_name, [], {'slug': self.slug}

    @models.permalink
    def get_edit_url(self):
        url_name = 'newsroom-%s-edit' % (self.confirmed and 'assignment' or
                                         'request')
        if self.parent:
            return url_name, [], {'slug': self.parent.slug, 'child_id': self.pk}
        return url_name, [], {'slug': self.slug}

    @models.permalink
    def get_accept_url(self):
        url_name = 'newsroom-request-accept'
        if self.parent:
            return url_name, [], {'slug': self.parent.slug, 'child_id': self.pk}
        return url_name, [], {'slug': self.slug}

    @property
    def properties(self):
        """
        Returns an ordered list of properties for this assignment, as
        designated by the category to which the assignment belongs.
        Only category properties with a value are added to the list.

        Each item of the list is a tuple of the field name and the value.
        """
        fields = []
        values = self._get_values()
        for field in self.category.properties:
            value = values.get(field, '')
            if value:
                fields.append((field, value))
        return fields

    @property
    def details(self):
        """
        Returns an ordered list of details for this assignment, as
        designated by the category to which the assignment belongs.
        Only category details with a value are added to the list.

        Each item of the list is a tuple of the field name and the value.
        """
        details = []
        values = self._get_values()
        for field in self.category.details:
            value = values.get(field, '')
            if value:
                details.append((field, value))
        return details

    def _get_values(self):
        if hasattr(self, '_values'):
            return self._values
        values = dict([(d.field, d.value) for d in self.textfield_set.all()])
        values.update([(d.field, d.value) for d in self.bigtextfield_set.all()])
        values.update([(d.field, d.value) for d in self.choicefield_set.all()])
        self._values = values
        return values

    def clear_values_cache(self):
        if hasattr(self, '_values'):
            del self._values

    def first_detail_text(self):
        """
        Returns the value of the first filled in detail field.

        Prefers to return big text details, but falls back to a single line text
        if no filled in big text details were found.
        """
        for field, value in self.details:
            if isinstance(field, CategoryBigTextField):
                return value
        for field, value in self.details:
            if isinstance(field, CategoryTextField):
                return value


class AssignmentTextField(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='textfield_set')
    field = models.ForeignKey(CategoryTextField, related_name='values')
    value = models.CharField(max_length=100)


class AssignmentBigTextField(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='bigtextfield_set')
    field = models.ForeignKey(CategoryBigTextField, related_name='values')
    value = models.TextField()


class AssignmentChoiceField(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='choicefield_set')
    field = models.ForeignKey(CategoryChoiceField, related_name='values')
    value = models.ForeignKey(CategoryChoiceFieldChoice)


class AssignmentComment(BaseItem):
    assignment = models.ForeignKey(Assignment, related_name='comments')
    comment = models.TextField()
    file = models.FileField(upload_to='uploads/newsroom/assignments', blank=True)

    class Meta:
        ordering = ('created_at',)

    def save(self, *args, **kwargs):
        email = not self.id
        super(AssignmentComment, self).save(*args, **kwargs)
        if email:
            for user in self.assignment.involved.exclude(
                                                        pk=self.created_by.pk):
                c = {'comment': self, 'user': user}
                send_mail_from_template(user.email, 'assignment_comment', c)


class StatusHistory(models.Model):
    assignment = models.ForeignKey(Assignment)
    status = models.ForeignKey(Status)
    user = models.ForeignKey(User, editable=False)
    comment = models.TextField(blank=True)
    date = models.DateTimeField(default=datetime.datetime.now, editable=False)

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return '%s changed to %s' % (self.assignment, self.status)

    def save(self, *args, **kwargs):
        email = not self.id
        super(StatusHistory, self).save(*args, **kwargs)
        if email:
            for user in self.assignment.involved.exclude(pk=self.user.pk):
                c = {'assignment': self.assignment, 'user': user}
                send_mail_from_template(user.email, 'assignment_status_change',
                                        c)
