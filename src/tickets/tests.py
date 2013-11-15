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


def _add_incident(self):
    response = self.client.get(reverse('incident-add-view'))
    csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
    response = self.client.post(reverse('incident-add-view'), {
        'theme': 'Theme',
        'description': 'Some text',
        'fio': u'Иванов А.А.',
        'room': '123',
        'phone': '111',
        'pc': '4567',
        'department': self.department.pk,
        'area': self.area.pk,
        'csrfmiddlewaretoken': csrf_token
    })

class IncidentStatusTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('admin', 'no@no.com', 'admin')
        self.client = Client(enforce_csrf_checks = True)
        self.client.login(username = 'admin', password = 'admin')
        self.area = models.Area(name = u'IT')
        self.area.save()
        self.department = models.Department(name = u'Отдел IT')
        self.department.save()
        self.statuses = [
            models.Status(name = u'Открыт'),
            models.Status(name = u'В работе'),
            models.Status(name = u'Закрыт')
        ]
        for s in self.statuses:
            s.save()
        group_admin = Group.objects.create(name = 'Administrators')
        group_admin.user_set.add(self.user)

    def tearDown(self):
        self.client.logout()

    def test_status_change(self):
        _add_incident(self)
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[0])
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[1].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[1])
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[2])
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 3)

    def test_user_can_not_change_status(self):
        self.client.logout()
        self.client = Client(enforce_csrf_checks = False)
        User.objects.create_user('1', 'no@no.com', '1')
        self.client.login(username = '1', password = '1')
        _add_incident(self)
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
        })
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        self.client.logout()

class TestMainPagePagination(TestCase):

    def setUp(self):
        User.objects.create_user('user', 'no@no.com', 'user')
        self.client = Client(enforce_csrf_checks = True)
        self.client.login(username = 'user', password = 'user')
        self.area = models.Area(name = u'IT')
        self.area.save()
        self.department = models.Department(name = u'Отдел IT')
        self.department.save()
        Group.objects.create(name = 'Administrators')

    def test_pagination(self):
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 0)
        _add_incident(self)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 1)
        for i in range(19):
            _add_incident(self)
        self.assertEqual(models.Incident.objects.count(), 20)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 20)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 2}))
        # page is out of range
        self.assertEqual(len(response.context['incidents'].object_list), 20)
        _add_incident(self)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 2}))
        self.assertEqual(len(response.context['incidents'].object_list), 1)
        for i in range(30):
            _add_incident(self)
        self.assertEqual(models.Incident.objects.count(), 51)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 3}))
        self.assertEqual(len(response.context['incidents'].object_list), 11)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 10}))
        self.assertEqual(len(response.context['incidents'].object_list), 11)

class IncidentDetailsTest(TestCase):

    def setUp(self):
        self.area = models.Area(name = u'IT')
        self.department = models.Department(name = u'Отдел IT')
        self.status = models.Status(name = u'Открыт')
        self.area.save()
        self.department.save()
        self.status.save()
        group_admin = Group(name = 'Administrators')
        group_user = Group(name = 'Users')
        group_admin.save()
        group_user.save()
        self.user_admin = User.objects.create_user('admin', 'no@no.com', 'admin')
        self.user_user = User.objects.create_user('user', 'no@no.com', 'user')
        self.user_user1 = User.objects.create_user('user1', 'no@no.com', 'user1')
        self.user_user2 = User.objects.create_user('user2', 'no@no.com', 'user2')
        self.user_admin.save()
        self.user_user.save()
        self.user_user1.save()
        self.user_user2.save()
        group_admin.user_set.add(self.user_admin)
        group_user.user_set.add(self.user_user)

    def _user_create_incident(self, username, password):
        self.client.login(username = username, password = password)
        response = self.client.get(reverse('incident-add-view'))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'room': '123',
            'phone': '111',
            'pc': '4567',
            'department': self.department.pk,
            'area': self.area.pk,
            'csrfmiddlewaretoken': csrf_token
        })
        self.client.logout()

    def test_incident_auth(self):
        self._user_create_incident('user', 'user')
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertRedirects(response, reverse('login-view'))

    def test_admin_can_see_all_incidents(self):
        self._user_create_incident('user', 'user')
        self._user_create_incident('admin', 'admin')
        self.client.login(username = 'user', password = 'user')
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 2}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_users_can_see_only_their_incidents(self):
        self._user_create_incident('user1', 'user1')
        self._user_create_incident('user2', 'user2')
        self.client.login(username = 'user1', password = 'user1')
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 2}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.login(username = 'user2', password = 'user2')
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 2}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_incident_history_auth(self):
        self._user_create_incident('user', 'user')
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 1}))
        self.assertRedirects(response, reverse('login-view'))

    def test_incident_history_access(self):
        self._user_create_incident('user1', 'user1')
        self._user_create_incident('user2', 'user2')
        self.client.login(username = 'user1', password = 'user1')
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 2}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.login(username = 'user2', password = 'user2')
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 2}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_incident_history_does_not_exist(self):
        self._user_create_incident('user', 'user')
        self.client.login(username = 'user', password = 'user')
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 200)
        models.IncidentHistory.objects.all().delete()
        response = self.client.get(reverse('incident-history-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.status_code, 404)
        self.client.logout()


class CommentTest(TestCase):

    def setUp(self):
        g1 = Group(name = 'Administrators')
        g1.save()
        self.user_admin = User.objects.create_user('admin', 'no@no.com', 'admin')
        self.user_user = User.objects.create_user('user', 'no@no.com', 'user')
        self.user_admin.save()
        self.user_user.save()
        g1.user_set.add(self.user_admin)
        self.area = models.Area(name = u'IT')
        self.area.save()
        self.department = models.Department(name = u'Отдел IT')
        self.department.save()
        self.client = Client(enforce_csrf_checks = True)

    def test_admin_can_comment(self):
        self.client.login(username = 'user', password = 'user')
        _add_incident(self)
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 0)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'comment': 'Comment from user.',
            'csrfmiddlewaretoken': csrf_token,
            'add_comment': 1
        })
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 0)
        self.client.logout()
        self.client.login(username = 'admin', password = 'admin')
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'comment': 'Comment from admin.',
            'csrfmiddlewaretoken': csrf_token,
            'add_comment': 1
        })
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 1)
        self.client.logout()
