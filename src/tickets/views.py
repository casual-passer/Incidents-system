# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
import django.contrib.auth as auth
from django.utils.timezone import utc

from .models import Incident, IncidentHistory, Status, Area, Department
from .forms import AddIncidentForm, ModifyIncidentForm

import datetime


def paginate_records(records_list, page_id):
     paginator = Paginator(records_list, 20)
     try:
         paginated_list = paginator.page(page_id)
     except EmptyPage:
         # if page is out of range, show last one
         paginated_list = paginator.page(paginator.num_pages)
     return paginated_list


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

def main(request, page = 1):
    if request.user.is_authenticated():
        try:
            page = int(page)
        except:
            raise Http404
        context = {}
        try:
            # Administrators can see all incidents
            group_admin = auth.models.Group.objects.get(name = 'Administrators')
        except auth.models.Group.DoesNotExist:
            context['errors'] = [u'Группы пользователей не созданы.',]
            return render(request, 'tickets/base.html', context)
        if request.user in group_admin.user_set.all():
            incidents = Incident.objects.all()
        else:
            incidents = Incident.objects.filter(user = request.user)
        # show only subset of all incidents
        context['incidents'] = paginate_records(incidents, page)
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

def incident_history(request, incident_id = None):
    try:
        incident_id = int(incident_id)
    except:
        raise Http404
    history = IncidentHistory.objects.filter(incident = incident_id)
    context = {}
    context['history'] = history
    return render(request, 'tickets/incident_history.html', context)

def incident(request, incident_id = None):
    try:
        incident_id = int(incident_id)
    except:
        raise Http404
    incident = get_object_or_404(Incident, pk = incident_id)
    context = {}
    context.update(csrf(request))
    context['form'] = ModifyIncidentForm(request.POST or None, status = incident.status)
    if request.method == 'POST':
        if context['form'].is_valid():
            data = context['form'].cleaned_data
            status = data['status']
            incident.status = status
            incident.save()
            IncidentHistory.objects.create(
                incident = incident,
                modified_at = datetime.datetime.utcnow().replace(tzinfo = utc),
                status = status,
                user = request.user
            )
            return redirect(reverse('incident-view', kwargs = {'incident_id': incident_id}))
    else: # not POST
        context['incident'] = incident
    return render(request, 'tickets/incident.html', context)
