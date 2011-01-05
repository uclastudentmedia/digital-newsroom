from django import forms
from newsroom_files import models


class FileForm(forms.ModelForm):
    class Meta:
        model = models.File
