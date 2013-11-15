# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django import forms

from models import Incident, IncidentComment

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

class ModifyIncidentForm(ModelForm):

    def __init__(self, *args, **kwargs):
        status = kwargs.pop('status')
        super(ModifyIncidentForm, self).__init__(*args, **kwargs)
        # set current status in form
        self.fields['status'].initial = status

    class Meta:
        model = Incident
        fields = ['status']
        labels = {
            'status': u'Статус'
        }


class CommentIncidentForm(ModelForm):

    class Meta:
        model = IncidentComment
        fields = ['comment']
        labels = {
            'comment': u'Комментарий'
        }
