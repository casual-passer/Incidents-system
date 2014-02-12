# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
import django.contrib.auth as auth
from django.utils.timezone import utc
from django.conf import settings

from .models import Incident, IncidentHistory, Status, Area, Department, IncidentComment
from .forms import AddIncidentForm, ModifyIncidentForm, CommentIncidentForm, IncidentFilterForm, IncidentPerformersForm, LoginForm
from .utils import send_email

import datetime


def paginate_records(records_list, page_id):
    paginator = Paginator(records_list, per_page=20)
    try:
        paginated_list = paginator.page(page_id)
    except EmptyPage:
        # if page is out of range, show last one
        paginated_list = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        paginated_list = paginator.page(1)
    return paginated_list


def login(request):
    context = {}
    context.update(csrf(request))
    context['errors'] = []
    context['login_form'] = LoginForm(request.POST or None)
    if request.user.is_authenticated():
        return redirect(reverse('main-view'))
    if request.method == 'POST':
        if context['login_form'].is_valid():
            username = context['login_form'].cleaned_data.get('username')
            password = context['login_form'].cleaned_data.get('password')
            user = auth.authenticate(username = username, password = password)
            if user:
                if user.is_active:
                    auth.login(request, user)
                    return redirect(reverse('main-view'))
                else: # user is not active
                    context['errors'].append(u'Аккаунт отключен')
            else: # invalid login and/or password
                context['errors'].append(u'Неправильный логин и/или пароль')
        else: # for is not valid
            context['errors'].append(u'Заполните все поля')
    return render(request, 'tickets/login.html', context)

def logout(request):
    auth.logout(request)
    return redirect(reverse('login-view'))

def _group_exists(group_name):
    try:
        group = auth.models.Group.objects.get(name = group_name)
        return group
    except auth.models.Group.DoesNotExist:
        return False

def main(request, page = 1):
    if request.user.is_authenticated():
        try:
            page = int(page)
        except:
            raise Http404
        context = {}
        group_admin = _group_exists('Administrators')
        if not group_admin:
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
        if request.method == 'POST' and 'save' in request.POST:
            context['form'] = AddIncidentForm(request.POST)
            if context['form'].is_valid():
                incident = context['form'].save(commit = False)
                incident.user = request.user
                incident.save()
                path = ('http',
                    ('', 's')[request.is_secure()],
                    '://',
                    request.META.get('HTTP_HOST', 'unknown'),
                    reverse('incident-view', kwargs = {'incident_id': incident.pk}))
                path = ''.join(path)
                send_email(
                    subject = u'Новая запись',
                    body = u'Тема: %s.\n%s' % (incident.theme, path),
                    msg_to = settings.EMAIL_TO_NEW_INCIDENT,
                    msg_from = settings.EMAIL_FROM)
                return redirect(reverse('incident-view', kwargs = {'incident_id': incident.pk}))
            else: # form is not valid
                context['errors'].append(u'Заполните все требуемые поля')
                return render(request, 'tickets/incident_add.html', context)
        else:
            context['form'] = AddIncidentForm()
        return render(request, 'tickets/incident_add.html', context)
    else:
        return redirect(reverse('login-view'))

def incident_history(request, incident_id = None):
    if request.user.is_authenticated():
        try:
            incident_id = int(incident_id)
        except:
            raise Http404
        history = IncidentHistory.objects.filter(incident = incident_id)
        if not history:
            raise Http404
        group_admin = _group_exists('Administrators')
        if not group_admin:
            context['errors'] = [u'Группы пользователей не созданы.',]
            return render(request, 'tickets/base.html', context)
        if request.user in group_admin.user_set.all():
            pass
        else:
            if history[0].incident.user != request.user:
                raise PermissionDenied
        context = {}
        context['history'] = history
        return render(request, 'tickets/incident_history.html', context)
    else:
        return redirect(reverse('login-view'))

def incident(request, incident_id = None):
    if request.user.is_authenticated():
        context = {}
        context.update(csrf(request))
        context['errors'] = []
        try:
            incident_id = int(incident_id)
        except:
            raise Http404
        group_admin = _group_exists('Administrators')
        if not group_admin:
            context['errors'].append(u'Группы пользователей не созданы.')
            return render(request, 'tickets/base.html', context)
        incident = get_object_or_404(Incident, pk = incident_id)
        context['incident'] = incident
        if request.user in group_admin.user_set.all():
            # Administrators can see everything
            if 'change' in request.POST:
                context['form'] = ModifyIncidentForm(request.POST or None, status = incident.status)
            else:
                context['form'] = ModifyIncidentForm(status = incident.status)
            if 'add_comment' in request.POST:
                context['form_comment'] = CommentIncidentForm(request.POST or None)
            else:
                context['form_comment'] = CommentIncidentForm()
            if request.user.is_superuser:
                if 'add_performers' in request.POST:
                    context['form_performers'] = IncidentPerformersForm(request.POST or None, instance = incident)
                else:
                    context['form_performers'] = IncidentPerformersForm(instance = incident)
            context['comments'] = IncidentComment.objects.filter(incident = incident)
            if request.method == 'POST':
                if 'change' in request.POST:
                    # change status
                    if context['form'].is_valid():
                        new_status = context['form'].cleaned_data['status']
                        if incident.status != new_status:
                            incident.status = new_status
                            incident.save()
                            IncidentHistory.objects.create(
                                incident = incident,
                                modified_at = datetime.datetime.utcnow().replace(tzinfo = utc),
                                status = incident.status,
                                user = request.user
                            )
                        return redirect(reverse('incident-view', kwargs = {'incident_id': incident_id}))
                    else: # form is not valid
                        context['errors'].append(u'Произошла ошибка при изменении статуса.')
                        return render(request, 'tickets/incident.html', context)
                if 'add_comment' in request.POST:
                    # add comment
                    if context['form_comment'].is_valid():
                        comment = context['form_comment'].save(commit = False)
                        comment.user = request.user
                        comment.incident = incident
                        comment.save()
                        return redirect(reverse('incident-view', kwargs = {'incident_id': incident_id}))
                    else:
                        context['errors'].append(u'Произошла ошибка при создании комментария. Поле должно быть заполнено.')
                        return render(request, 'tickets/incident.html', context)
                # only superuser can change this
                if request.user.is_superuser and 'add_performers' in request.POST:
                    if context['form_performers'].is_valid():
                        data = context['form_performers'].cleaned_data
                        performers = set(data['performers'])
                        # reassign performers
                        # first remove all which exists
                        incident.performers.clear()
                        # and add new
                        path = ('http',
                            ('', 's')[request.is_secure()],
                            '://',
                            request.META.get('HTTP_HOST', 'unknown'),
                            request.path)
                        path = ''.join(path)
                        context['email_messages'] = []
                        context['email_messages_errors'] = []
                        for p in performers:
                            incident.performers.add(p)
                            if p.email:
                                try:
                                    send_email(
                                        subject = u'Новая запись',
                                        body = u'Тема: %s.\n%s' % (incident.theme, path),
                                        msg_to = p.email,
                                        msg_from = settings.EMAIL_FROM)
                                    context['email_messages'].append(u'Отправлен e-mail для %s на %s' % (p.name, p.email))
                                except smtplib.SMTPException:
                                    context['email_messages_errors'].append(u'Ошибка отправки e-mail для %s на %s' % (p.name, p.email))
                        incident.save()
                        if len(context['email_messages']) or len(context['email_messages_errors']):
                            return render(request, 'tickets/incident.html', context)
                        return redirect(reverse('incident-view', kwargs = {'incident_id': incident_id}))
                    else:
                        context['errors'].append(u'Заполните форму исполнителей')
                        return render(request, 'tickets/incident.html', context)
        else: # user is not in Administrators group
            if incident.user != request.user:
                raise PermissionDenied
        return render(request, 'tickets/incident.html', context)
    else:
        return redirect(reverse('login-view'))

def incident_filter(request, page=1):
    if request.user.is_authenticated():
        context = {}
        context['errors'] = []
        context['form'] = IncidentFilterForm(request.GET or None)
        if request.method == 'GET':
            if 'filter' in context['form'].data:
                if context['form'].is_valid():
                    data = context['form'].cleaned_data
                    group_admin = _group_exists('Administrators')
                    if not group_admin:
                        context['errors'].append(u'Группы пользователей не созданы.')
                        return render(request, 'tickets/base.html', context)
                    if request.user in group_admin.user_set.all():
                        incidents = Incident.objects.all()
                    else:
                        incidents = Incident.objects.filter(user=request.user)
                    if 'status' in data and len(data['status']):
                        incidents = incidents.filter(status__in=data['status'])
                    if 'area' in data and len(data['area']):
                        incidents = incidents.filter(area__in=data['area'])
                    if 'till_date_start' in data and data['till_date_start']:
                        incidents = incidents.filter(till_date__gte=data['till_date_start'])
                    if 'till_date_end' in data and data['till_date_end']:
                        incidents = incidents.filter(till_date__lte=data['till_date_end'])
                    context['incidents'] = paginate_records(incidents, page)
                else:
                    context['errors'].append(u'Произошла ошибка')
        else: # not GET
            pass
        return render(request, 'tickets/incident_filter.html', context)
    else:
        return redirect(reverse('login-view'))
