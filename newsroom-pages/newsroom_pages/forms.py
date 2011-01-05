from django import forms
from newsroom_pages import models


class PageForm(forms.ModelForm):
    class Meta:
        model = models.Page

