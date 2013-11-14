# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
import django.contrib.auth as auth
from .models import Incident, IncidentHistory, Status, Area, Department
from .forms import AddIncidentForm


def login(request):
    context = {}
    context.update(csrf(request))
    context['errors'] = []
    if request.user.is_authenticated():
        return redirect(reverse('main-view'))
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username = username, password = password)
        if user:
            if user.is_active:
                auth.login(request, user)
                return redirect(reverse('main-view'))
            else: # user is not active
                context['errors'].append(u'Аккаунт отключен')
        else: # invalid login and/or password
            context['errors'].append(u'Неправильный логин и/или пароль')
            return render(request, 'tickets/login.html', context)
    else: # not POST
        return render(request, 'tickets/login.html', context)

def logout(request):
    auth.logout(request)
    return redirect(reverse('login-view'))

def main(request, page = None):
    if request.user.is_authenticated():
        context = {}
        return render(request, 'tickets/main.html', context)
    else:
        return redirect(reverse('login-view'))

def incident_add(request):
    if request.user.is_authenticated():
        context = {}
        context['errors'] = []
        context.update(csrf(request))
        if request.method == 'POST':
            context['form'] = AddIncidentForm(request.POST)
            if context['form'].is_valid():
                data = context['form'].cleaned_data
                theme = data['theme']
                description = data['description']
                user = request.user
                fio = data['fio']
                phone = data['phone']
                pc = data['pc']
                room = data['room']
                area = data['area']
                department = data['department']
                incident = Incident(
                    theme = theme,
                    description = description,
                    user = user,
                    fio = fio,
                    phone = phone,
                    pc = pc,
                    room = room,
                    area = area,
                    department = department
                )
                incident.save()
            else: # form is not valid
                context['errors'].append(u'Заполните все требуемые поля')
            return render(request, 'tickets/incident_add.html', context)
        else:
            context['form'] = AddIncidentForm()
        return render(request, 'tickets/incident_add.html', context)
    else:
        return redirect(reverse('login-view'))
