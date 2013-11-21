# -*- coding: utf-8 -*-
from django.forms import ModelForm
from django import forms

from models import Incident, IncidentComment, Status, Area, Performer

class AddIncidentForm(ModelForm):

    class Meta:
        model = Incident
        fields = ['theme', 'description', 'fio', 'phone', 'pc', 'room', 'area', 'department']
        labels = {
            'theme': u'Тема*',
            'description': u'Описание*',
            'fio': u'ФИО*',
            'phone': u'Номер телефона*',
            'pc': u'Номер компьютера',
            'room': u'Номер комнаты',
            'area': u'Тематика*',
            'department': u'Отдел*',
        }
        widgets = {
            'fio': forms.TextInput(attrs = {'class': 'input-block-level'}),
            'phone': forms.TextInput(attrs = {'class': 'input-block-level'}),
            'pc': forms.TextInput(attrs = {'class': 'input-block-level'}),
            'room': forms.TextInput(attrs = {'class': 'input-block-level'}),
            'area': forms.Select(attrs = {'class': 'span6'}),
            'department': forms.Select(attrs = {'class': 'span6'}),
            'theme': forms.TextInput(attrs = {'class': 'span12'}),
            'description': forms.Textarea(attrs = {'class': 'span12'}),
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
        widgets = {
            'comment': forms.Textarea(attrs = {'class': 'span12', 'placeholder': u'Комментарий'})
        }

class IncidentFilterForm(forms.Form):

   status = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple, label = u'Статус', required = False)
   area = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple, label = u'Тематика', required = False)

   def __init__(self, *args, **kwargs):
       super(IncidentFilterForm, self).__init__(*args, **kwargs)
       self.fields['status'].choices = [(x.pk, x.name) for x in Status.objects.all()]
       self.fields['area'].choices = [(x.pk, x.name) for x in Area.objects.all()]


class IncidentPerformersForm(ModelForm):


    def __init__(self, *args, **kwargs):
        super(IncidentPerformersForm, self).__init__(*args, **kwargs)
        self.fields['performers'] = forms.ModelMultipleChoiceField(
            queryset = Performer.objects.all(),
            initial = self.instance.performers.all(),
            widget = forms.CheckboxSelectMultiple()
            )

    class Meta:
        model = Incident
        fields = ['performers']
        labels = {
            'performers': u'Исполнители'
        }

class LoginForm(forms.Form):

    username = forms.CharField(label = u'Логин')
    password = forms.CharField(label = u'Пароль', widget = forms.PasswordInput())
