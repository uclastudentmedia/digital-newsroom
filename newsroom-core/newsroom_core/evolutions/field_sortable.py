from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('CategoryField', 'sortable', models.PositiveSmallIntegerField, initial=0)
]
