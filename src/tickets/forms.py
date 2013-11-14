# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django import forms

from models import Incident

class AddIncidentForm(ModelForm):

    class Meta:
        model = Incident
        fields = ['theme', 'description', 'fio', 'phone', 'pc', 'room', 'area', 'department']
        labels = {
            'theme': u'Тема',
            'description': u'Описание',
            'fio': u'ФИО',
            'phone': u'Номер телефона',
            'pc': u'Номер компьютера',
            'room': u'Номер комнаты',
            'area': u'Тематика',
            'department': u'Отдел'
        }
        widgets = {
            'theme': forms.TextInput(attrs = {'class': 'span12'}),
            'description': forms.Textarea(attrs = {'class': 'span12'})
        }
