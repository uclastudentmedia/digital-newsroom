from django import forms
from newsroom_ideas import models


class IdeaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(IdeaForm, self).__init__(*args, **kwargs)
        self.fields['section'].empty_label = '(choose section) or Any'

    class Meta:
        model = models.Idea


class ReplyForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        exclude = ['idea']
