# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

import models


class ModelsTest(TestCase):

    def setUp(self):
        self.area = models.Area(name = u'IT')
        self.department = models.Department(name = u'Отдел IT')
        self.status = models.Status(name = u'Открыт')
        self.area.save()
        self.department.save()
        self.status.save()
        self.user = User.objects.create_user('user', 'no@email.com', 'password')

    def test_incident_save(self):
        incident = models.Incident(
            theme = u'Проблема',
            area = self.area,
            department = self.department,
            user = self.user
        )
        self.assertEqual(hasattr(incident, 'status'), False)
        incident.save()
        self.assertEqual(hasattr(incident, 'status'), True)
        self.assertEqual(incident.status.pk, 1)

    def test_incident_create(self):
        incident = models.Incident(
            theme = u'Проблема',
            status = self.status,
            area = self.area,
            department = self.department,
            user = self.user
        )
        incident.save()
        self.assertEqual(incident.status.pk, self.status.pk)
        self.assertEqual(models.Incident.objects.count(), 1)
        incident.delete()
        self.assertEqual(models.Incident.objects.count(), 0)

    def test_incident_history_default(self):
        incident = models.Incident(
            theme = u'Проблема',
            status = self.status,
            area = self.area,
            department = self.department,
            user = self.user
        )
        self.assertEqual(models.IncidentHistory.objects.count(), 0)
        incident.save()
        self.assertEqual(models.IncidentHistory.objects.count(), 1)
        history = models.IncidentHistory.objects.get(incident = incident)
        self.assertEqual(incident.created_at, history.modified_at)

class LoginTest(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks = True)
        self.user = User.objects.create_user('user', 'no@email.com', 'password')

    def test_login(self):
        response = self.client.get(reverse('login-view'))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('login-view'), {
            'username': 'user', 'password': 'password', 'csrfmiddlewaretoken': csrf_token
            })
        self.assertRedirects(response, reverse('main-view'))
        response = self.client.get(reverse('login-view'))
        self.assertRedirects(response, reverse('main-view'))

    def test_logout(self):
        response = self.client.get(reverse('login-view'))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('login-view'), {
            'username': 'user', 'password': 'password', 'csrfmiddlewaretoken': csrf_token
            })
        response = self.client.get(reverse('logout-view'))
        self.assertRedirects(response, reverse('login-view'))

    def test_login_required(self):
        response = self.client.get(reverse('main-view'))
        self.assertRedirects(response, reverse('login-view'))
        response = self.client.get(reverse('incident-add-view'))
        self.assertRedirects(response, reverse('login-view'))

class AddIncidentFormTest(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks = True)
        self.user = User.objects.create_user('user', 'no@email.com', 'password')
        self.client.login(username = 'user', password = 'password')
        self.department = models.Department(name = 'dep')
        self.department.save()
        self.area = models.Area(name = 'area')
        self.area.save()
        response = self.client.get(reverse('incident-add-view'))
        self.csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')

    def test_filled_form(self):
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'room': '123',
            'phone': '111',
            'pc': '4567',
            'department': self.department.pk,
            'area': self.area.pk,
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(response.context['errors'], [])

    def test_partially_filled_form(self):
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            #'room': '123',
            'phone': '111',
            'pc': '4567',
            'department': 1,
            'area': 1,
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(response.context['errors'], [])

    def test_incorrect_form(self):
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'pc': '4567',
            'department': 1,
            'area': 1,
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(len(response.context['errors']), 1)


class GroupsTest(TestCase):

    def setUp(self):
        g1 = Group(name = 'Administrators')
        g2 = Group(name = 'Users')
        g1.save()
        g2.save()
        u1 = User.objects.create_user('admin', 'no@no.com', 'admin')
        u2 = User.objects.create_user('user', 'no@no.com', 'user')
        u1.save()
        u2.save()
        g1.user_set.add(u1)
        g2.user_set.add(u2)
        self.area = models.Area(name = u'IT')
        self.area.save()
        self.department = models.Department(name = u'Отдел IT')
        self.department.save()

    def test_groups_permissions(self):
        group = Group.objects.get(name = 'Administrators')
        self.client.login(username = 'user', password = 'user')
        user = User.objects.get(username = 'user')
        self.assertEqual(self.client.session['_auth_user_id'], user.pk)
        # user creates incident
        incident = models.Incident(
            theme = u'From user',
            area = self.area,
            department = self.department,
            user = user
        )
        incident.save()
        self.client.logout()
        self.client.login(username = 'admin', password = 'admin')
        user = User.objects.get(username = 'admin')
        self.assertEqual(self.client.session['_auth_user_id'], user.pk)
        # admin creates incident
        incident = models.Incident(
            theme = u'From admin',
            area = self.area,
            department = self.department,
            user = user
        )
        incident.save()
        response = self.client.get(reverse('main-view'))
        self.assertEqual(len(response.context['incidents']), 2)
        self.client.logout()
        # user must see only one incident
        self.client.login(username = 'user', password = 'user')
        user = User.objects.get(username = 'user')
        self.assertEqual(self.client.session['_auth_user_id'], user.pk)
        response = self.client.get(reverse('main-view'))
        self.assertEqual(len(response.context['incidents']), 1)
        self.client.logout()

class NoGroupsTest(TestCase):

    def setUp(self):
        User.objects.create_user('user', 'no@no.com', 'user')

    def test_no_groups(self):
        self.client.login(username = 'user', password = 'user')
        response = self.client.get(reverse('main-view'))
        self.assertEqual(response.context['errors'], [u'Группы пользователей не созданы.'])
        self.client.logout()
