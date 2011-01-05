from django import forms
from django.db.models import Model
from django.db.models.fields import FieldDoesNotExist
from newsroom_core import models


def people_choices(user_id=None):
    section = None
    choices = []
    if user_id and isinstance(user_id, (list, tuple)):
        user_id = user_id[0]
    user_profile = None
    choice_group = []
    profiles = models.NewsroomProfile.objects.select_related().order_by(
        'section__title', 'user__first_name', 'user__last_name'
    )
    for profile in profiles:
        if profile.section != section:
            section = profile.section
            if choice_group and choice_group[1]:
                choices.append(choice_group)
            choice_group = [section, []]
        if user_id and user_id == profile.user_id:
            user_profile = profile
        else:
            choice_group[1].append((profile.user_id, unicode(profile)))
    if choice_group and choice_group[1]:
        choices.append(choice_group)
    # Shift the user's section to the top and insert the user
    if user_profile:
        found = False
        for i in range(len(choices)):
            if choices[i][0] == user_profile.section:
                choices.insert(0, choices.pop(i))
                found = True
                break
        if not found:
            choices.insert(0, [user_profile.section, []])
        choices[0][1].insert(0, (user_profile.user_id, unicode(user_profile)))
    return choices


def get_value_model(category_model):
    """
    Returns the matching generic field value model for the given category
    model/instance.
    """
    value_field = None
    for rel in category_model._meta.get_all_related_objects():
        try:
            rel.model._meta.get_field('assignment')
            return rel.model
        except FieldDoesNotExist:
            pass


def dynamic_form_field(db_field):
    value_field = get_value_model(db_field.field)._meta.get_field('value')

    kwargs = {'label': db_field.name, 'required': db_field.required}

    if isinstance(db_field.field, models.CategoryTextField):
        kwargs['max_length'] = min(db_field.length, 100)
    elif isinstance(db_field.field, models.CategoryChoiceField):
        queryset = value_field.rel.to._default_manager.complex_filter(
                                            value_field.rel.limit_choices_to)
        queryset = queryset.filter(field=db_field.field)
        kwargs['queryset'] = queryset

    return value_field.formfield(**kwargs)


class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'email']


class PasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
#        help_text='To change your password, enter your old password here and '
#                  'your new password in the two boxes below.'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False
    )
    new_password_again = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        old_pw = self.cleaned_data.get('old_password')
        new_pw = self.cleaned_data.get('new_password')
        new_pw2 = self.cleaned_data.get('new_password_again')
        if new_pw and not old_pw:
            raise forms.ValidationError(
                'If you want to change your password, you must enter your old '
                'password as well.'
            )
        if new_pw or new_pw2:
            if new_pw != new_pw2:
                raise forms.ValidationError(
                    "The two entries of your new password didn't match."
                )
            else:
                if not self.user.check_password(old_pw):
                    raise forms.ValidationError(
                                        "Oops, that wasn't your old password.")
                self.cleaned_data['password'] = new_pw
        return self.cleaned_data

    def save(self):
        password = self.cleaned_data.get('password')
        if password:
            self.user.set_password(password)
            self.user.save()
            return True


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.NewsroomProfile
        exclude = ['user']


class AcceptRequestForm(forms.Form):
    pub_date = forms.DateField()


class AssignmentForm(forms.ModelForm):
#    status = forms.ModelChoiceField(widget=forms.RadioSelect())
    confirmed = True

    def __init__(self, category=None, parent=None, instance=None, *args, **kwargs):
        if not category and not (instance and instance.category_id):
            raise KeyError('Either a category or an instance must be provided.')
        self.category = category or instance.category
        super(AssignmentForm, self).__init__(instance=instance, *args, **kwargs)
        if instance:
            del self.fields['status']
        else:
            field = self.fields['status']
            field.empty_label = None
            field.widget = forms.RadioSelect()
            field.widget.choices = field.choices
        user_id = self.initial and self.initial.get('involved')
        self.fields['involved'].choices = people_choices(user_id)
        user_id = self.initial and self.initial.get('responsible')
        self.fields['responsible'].choices = people_choices(user_id)

    class Meta:
        model = models.Assignment
        exclude = ['category', 'confirmed']

    def save(self, commit=True):
        obj = super(AssignmentForm, self).save(commit=False)
        obj.category = self.category
        obj.confirmed = self.confirmed
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class RequestForm(AssignmentForm):
    confirmed = False

    class Meta:
        model = models.Assignment
        exclude = ['category', 'confirmed', 'pub_date']


class AssignmentPropertiesForm(forms.Form):
    properties = True
    field_name = 'generic_property_%s'

    def __init__(self, category=None, instance=None, *args, **kwargs):
        if not category and not (instance and instance.category_id):
            raise KeyError('Either a category or an instance must be provided.')
        self.category = category or instance.category
        self.instance = instance
        super(AssignmentPropertiesForm, self).__init__(*args, **kwargs)
        if instance:
            values = self.get_values_dict()
        for field in self.dynamic_fields():
            self.fields[self.field_name % field.name] = dynamic_form_field(field)
            if instance:
                if field in values:
                    value = values[field]
                    if isinstance(value, Model):
                        value = value.pk
                    self.initial[self.field_name % field.name] = value
        #assert False, self.initial

    def get_values_dict(self):
        return dict(self.instance.properties)

    def dynamic_fields(self):
        if self.properties:
            return self.category.properties
        return self.category.details

    class Meta:
        model = models.Assignment

    def save(self, commit=True):
        if not self.instance:
            raise KeyError('Cannot save unless an instance is provided.')
        for field in self.dynamic_fields():
            value = self.cleaned_data.get(self.field_name % field.name)
            model = get_value_model(field)
            if value:
                obj, created = model.objects.get_or_create(
                    assignment=self.instance, field=field,
                    defaults={'value': value}
                )
                if not created:
                    obj.value = value
                    obj.save()
            else:
                model.objects.filter(assignment=self.instance, field=field)\
                                .delete()
    save.alters_data = True


class AssignmentDetailsForm(AssignmentPropertiesForm):
    properties = False
    field_name = 'generic_detail_%s'

    def get_values_dict(self):
        return dict(self.instance.details)


def recent_assignments_widget(widget=forms.Select, empty_label='--------',
                              **kwargs):
    assignments_choices = []
    if empty_label:
        assignments_choices.append(('', empty_label))
    for cat in models.Category.objects.filter(top_category=True):
        assignments = cat.assignment_set.assignments().order_by('-created_at')
        choices = assignments[:10].values_list('pk', 'title')
        if choices:
            assignments_choices.append([cat.title, list(choices)])
    kwargs['choices'] = assignments_choices
    return widget(**kwargs)


class CommentForm(forms.ModelForm):
    class Meta:
        model = models.AssignmentComment
        exclude = ['assignment']


class StatusForm(forms.Form):
    change_status = forms.ChoiceField(
        choices=[('', '(change)')]+\
                  list(models.Status.objects.values_list('slug', 'title')),
        required=True
    )
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': '2'}))
