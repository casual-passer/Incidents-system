# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

import models
from datetime import date


def _generate_default_data(self):
    self.area = models.Area.objects.create(name = u'Тематика')
    self.department = models.Department.objects.create(name = u'Отдел')
    self.status = models.Status.objects.create(name = u'Открыт')
    self.user = User.objects.create_user('user', 'no@no.com', 'user')
    self.admin = User.objects.create_user('admin', 'no@no.com', 'admin')
    self.client = Client(enforce_csrf_checks = True)
    self.today = date.today()


def _add_incident(self, area, till_date='1.1.2000'):
    response = self.client.get(reverse('incident-add-view'))
    csrf_token = '%s' % response.context['csrf_token'].encode('utf-8')
    response = self.client.post(reverse('incident-add-view'), {
        'theme': 'Тема',
        'description': 'Описание',
        'fio': u'ФИО',
        'room': '123',
        'phone': '123',
        'pc': '1234',
        'department': self.department.pk,
        'area': area.pk,
        'till_date': till_date,
        'save': '1',
        'csrfmiddlewaretoken': csrf_token
    })


def _get_csrf_token(self, url_name, kwargs = {}):
    response = self.client.get(reverse(url_name, kwargs = kwargs))
    return '%s' % response.context['csrf_token'].encode('utf-8')


def _create_group_with_users(group_name, users = []):
    g = Group.objects.create(name = 'Administrators')
    for u in users:
        g.user_set.add(User.objects.get(username = u))


class IncidentModelTest(TestCase):

    def setUp(self):
        _generate_default_data(self)

    def test_incident_save_with_default_status(self):
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

    def test_incident_save_with_status_supplied(self):
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

    def test_incident_save_status_history(self):
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
        _generate_default_data(self)

    def test_login(self):
        csrf_token = _get_csrf_token(self, 'login-view')
        response = self.client.post(reverse('login-view'), {
            'username': 'user',
            'password': 'user',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertRedirects(response, reverse('main-view'))
        response = self.client.get(reverse('login-view'))
        self.assertRedirects(response, reverse('main-view'))

    def test_logout(self):
        csrf_token = _get_csrf_token(self, 'login-view')
        response = self.client.post(reverse('login-view'), {
            'username': 'user',
            'password': 'user',
            'csrfmiddlewaretoken': csrf_token
            })
        response = self.client.get(reverse('logout-view'))
        self.assertRedirects(response, reverse('login-view'))

    def test_login_required(self):
        response = self.client.get(reverse('main-view'))
        self.assertRedirects(response, reverse('login-view'))

    def test_login_incorrect_form_not_cleared(self):
        csrf_token = _get_csrf_token(self, 'login-view')
        response = self.client.post(reverse('login-view'), {
            'username': 'user',
            'password': '123',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(response.context['errors'], [u'Неправильный логин и/или пароль'])
        self.assertEqual(response.context['login_form']['username'].value(), 'user')
        response = self.client.post(reverse('login-view'), {
            'username': 'user123',
            'password': '',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(response.context['errors'], [u'Заполните все поля'])
        self.assertEqual(response.context['login_form']['username'].value(), 'user123')


class AddIncidentFormTest(TestCase):

    def setUp(self):
        _generate_default_data(self)
        self.client.login(username = 'user', password = 'user')
        self.csrf_token = _get_csrf_token(self, 'incident-add-view')

    def tearDown(self):
        self.client.logout()

    def test_filled_form(self):
        self.assertEqual(len(models.Incident.objects.all()), 0)
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'room': '123',
            'phone': '111',
            'pc': '4567',
            'department': self.department.pk,
            'till_date': '1.1.2000',
            'area': self.area.pk,
            'save': '1',
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertRedirects(response, reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(len(models.Incident.objects.all()), 1)

    def test_partially_filled_form(self):
        self.assertEqual(len(models.Incident.objects.all()), 0)
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            #'room': '123',
            'phone': '111',
            #'pc': '4567',
            'department': 1,
            'till_date': '1.1.2000',
            'area': 1,
            'save': 1,
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertRedirects(response, reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(len(models.Incident.objects.all()), 1)

    def test_incorrect_form(self):
        self.assertEqual(len(models.Incident.objects.all()), 0)
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'pc': '4567',
            'department': 1,
            'area': 1,
            'save': 1,
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(len(response.context['errors']), 1)
        self.assertEqual(len(models.Incident.objects.all()), 0)

    def test_filled_form_with_very_long_strings(self):
        self.assertEqual(len(models.Incident.objects.all()), 0)
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'x'*129,
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'room': '1'*129,
            'phone': '111',
            'pc': '4567',
            'department': self.department.pk,
            'till_date': '1.1.2000',
            'area': self.area.pk,
            'save': '1',
            'csrfmiddlewaretoken': self.csrf_token
        })
        self.assertEqual(len(response.context['errors']), 1)
        self.assertEqual(len(models.Incident.objects.all()), 0)


class GroupsTest(TestCase):

    def setUp(self):
        _generate_default_data(self)
        _create_group_with_users('Administrators', ['admin',])

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


class IncidentStatusTest(TestCase):

    def setUp(self):
        self.statuses = [
            models.Status(name = u'Открыт'),
            models.Status(name = u'В работе'),
            models.Status(name = u'Закрыт')
        ]
        for s in self.statuses:
            s.save()
        _generate_default_data(self)
        _create_group_with_users('Administrators', ['admin',])

    def test_status_change(self):
        self.client.login(username = 'admin', password = 'admin')
        # admin adds incident
        _add_incident(self, self.area)
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[0])
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        # admin changes incident status
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[1].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[1])
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        response = self.client.get(reverse('incident-view', kwargs = {'incident_id': 1}))
        self.assertEqual(response.context['form']['status'].field.initial, self.statuses[2])
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 3)
        self.client.logout()

    def test_user_can_not_change_status(self):
        self.client.login(username = 'user', password = 'user')
        _add_incident(self, self.area)
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 1)
        self.client.logout()

    def test_status_not_changed(self):
        self.client.login(username = 'admin', password = 'admin')
        _add_incident(self, self.area)
        self.assertEqual(models.Incident.objects.get(pk = 1).status, self.statuses[0])
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        self.assertEqual(models.Incident.objects.get(pk = 1).status, self.statuses[2])
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 2)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[2].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        self.assertEqual(models.Incident.objects.get(pk = 1).status, self.statuses[2])
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 2)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'status': self.statuses[1].pk,
            'csrfmiddlewaretoken': csrf_token,
            'change': 1
        })
        self.assertEqual(models.Incident.objects.get(pk = 1).status, self.statuses[1])
        self.assertEqual(models.IncidentHistory.objects.filter(incident = 1).count(), 3)
        self.client.logout()


class TestMainPagePagination(TestCase):

    def setUp(self):
        _generate_default_data(self)
        self.client.login(username = 'user', password = 'user')
        _create_group_with_users('Administrators')

    def tearDown(self):
        self.client.logout()

    def test_pagination(self):
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 0)
        _add_incident(self, self.area)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 1)
        for i in range(19):
            _add_incident(self, self.area)
        self.assertEqual(models.Incident.objects.count(), 20)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 1}))
        self.assertEqual(len(response.context['incidents'].object_list), 20)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 2}))
        # page is out of range, so display last page
        self.assertEqual(len(response.context['incidents'].object_list), 20)
        _add_incident(self, self.area)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 2}))
        self.assertEqual(len(response.context['incidents'].object_list), 1)
        for i in range(30):
            _add_incident(self, self.area)
        self.assertEqual(models.Incident.objects.count(), 51)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 3}))
        self.assertEqual(len(response.context['incidents'].object_list), 11)
        response = self.client.get(reverse('main-page-view', kwargs = {'page': 10}))
        self.assertEqual(len(response.context['incidents'].object_list), 11)


class IncidentDetailsTest(TestCase):

    def setUp(self):
        _generate_default_data(self)
        _create_group_with_users('Administrators', ['admin',])
        self.user1 = User.objects.create_user('user1', 'no@no.com', 'user1')
        self.user2 = User.objects.create_user('user2', 'no@no.com', 'user2')

    def _user_create_incident(self, username, password):
        self.client.login(username = username, password = password)
        csrf_token = _get_csrf_token(self, 'incident-add-view')
        response = self.client.post(reverse('incident-add-view'), {
            'theme': 'Theme',
            'description': 'Some text',
            'fio': u'Иванов А.А.',
            'room': '123',
            'phone': '111',
            'pc': '4567',
            'department': self.department.pk,
            'area': self.area.pk,
            'till_date': '1.1.2000',
            'save': '1',
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
        # user can not see incident, created by admin
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
        _generate_default_data(self)
        _create_group_with_users('Administrators', ['admin',])

    def test_admin_can_comment(self):
        self.client.login(username = 'user', password = 'user')
        _add_incident(self, self.area)
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 0)
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'comment': 'Comment from user.',
            'csrfmiddlewaretoken': csrf_token,
            'add_comment': 1
        })
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 0)
        self.client.logout()
        self.client.login(username = 'admin', password = 'admin')
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'comment': 'Comment from admin.',
            'csrfmiddlewaretoken': csrf_token,
            'add_comment': 1
        })
        self.assertEqual(models.IncidentComment.objects.filter(incident = 1).count(), 1)
        self.client.logout()


def _create_data(model, objects):
    for o in objects:
        model.objects.create(name = o)
    return model.objects.all()


class FilterTest(TestCase):

    def setUp(self):
        _generate_default_data(self)
        _create_group_with_users('Administrators', ['admin', ])
        self.statuses = _create_data(models.Status, [u'Открыт', u'В работе', u'Закрыт'])
        self.areas = _create_data(models.Area, [u'Тематика ', u'Тематика 2', u'Тематика 3'])

    def test_filter_auth(self):
        response = self.client.get(reverse('incident-filter-view'))
        self.assertRedirects(response, reverse('login-view'))
        self.client.login(username = 'user', password = 'user')
        response = self.client.get(reverse('incident-filter-view'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_filter_admin_user_permissions(self):
        self.client.login(username = 'admin', password = 'admin')
        _add_incident(self, area = self.areas[0])
        _add_incident(self, area = self.areas[1])
        _add_incident(self, area = self.areas[2])
        self.client.logout()
        self.client.login(username = 'user', password = 'user')
        _add_incident(self, area = self.areas[0])
        _add_incident(self, area = self.areas[1])
        _add_incident(self, area = self.areas[2])
        response = self.client.get(reverse('incident-filter-view'), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 3)
        self.client.logout()
        self.client.login(username = 'admin', password = 'admin')
        response = self.client.get(reverse('incident-filter-view'), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 6)
        self.client.logout()

    def test_filter(self):
        self.client.login(username = 'admin', password = 'admin')
        _add_incident(self, area = self.areas[0])
        i = models.Incident.objects.get(pk = 1)
        i.status = self.statuses[2]
        i.save()
        _add_incident(self, area = self.areas[1])
        i = models.Incident.objects.get(pk = 2)
        i.status = self.statuses[1]
        i.save()
        _add_incident(self, area = self.areas[2])
        i = models.Incident.objects.get(pk = 3)
        i.status = self.statuses[0]
        i.save()
        response = self.client.get(reverse('incident-filter-view'), {
            'area': [1, 2, 3],
            'status' : [1, 2, 3],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 3)
        response = self.client.get(reverse('incident-filter-view'), {
            'area': [1, 2],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 2)
        response = self.client.get(reverse('incident-filter-view'), {
            'status': [2, 3],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 2)
        response = self.client.get(reverse('incident-filter-view'), {
            'area': [1],
            'status': [1, 2],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 0)
        self.client.logout()
        self.client.login(username = 'user', password = 'user')
        _add_incident(self, area = self.areas[0])
        i = models.Incident.objects.get(pk = 4)
        i.status = self.statuses[0]
        i.save()
        _add_incident(self, area = self.areas[1])
        i = models.Incident.objects.get(pk = 5)
        i.status = self.statuses[1]
        i.save()
        response = self.client.get(reverse('incident-filter-view'), {
            'area': [1],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 1)
        response = self.client.get(reverse('incident-filter-view'), {
            'area': [3],
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 0)
        self.client.logout()

    def test_filter_date_range(self):
        self.client.login(username = 'admin', password = 'admin')
        _add_incident(self, area = self.areas[0], till_date='1.1.2010')
        _add_incident(self, area = self.areas[0], till_date='1.2.2010')
        _add_incident(self, area = self.areas[0], till_date='1.1.2011')
        _add_incident(self, area = self.areas[0], till_date='1.2.2011')
        response = self.client.get(reverse('incident-filter-view'), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 4)
        response = self.client.get(reverse('incident-filter-view'), {
            'till_date_start': '1.1.2011',
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 2)
        response = self.client.get(reverse('incident-filter-view'), {
            'till_date_start': '1.2.2011',
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 1)
        response = self.client.get(reverse('incident-filter-view'), {
            'till_date_start': '1.1.2011',
            'till_date_end': '1.1.2011',
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 1)
        response = self.client.get(reverse('incident-filter-view'), {
            'till_date_start': '2.1.2011',
            'till_date_end': '2.1.2011',
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 0)
        self.client.logout()

    def test_filter_pagination(self):
        self.client.login(username = 'admin', password = 'admin')
        for i in range(45):
            _add_incident(self, area = self.areas[0], till_date='1.1.2010')
        response = self.client.get(reverse('incident-filter-view', kwargs={'page': 1}), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 20)
        response = self.client.get(reverse('incident-filter-view', kwargs={'page': 2}), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 20)
        response = self.client.get(reverse('incident-filter-view', kwargs={'page': 3}), {
            'filter': 1,
        })
        self.assertEqual(len(response.context['incidents']), 5)
        self.client.logout()

class PerformerTest(TestCase):

    def setUp(self):
        _generate_default_data(self)
        User.objects.create_superuser('superadmin','no@no.com', 'superadmin')
        _create_group_with_users('Administrators', ['superadmin',])
        models.Performer.objects.create(name = 'perf1', email = '1@1.com')
        models.Performer.objects.create(name = 'perf2', email = '2@2.com')
        models.Performer.objects.create(name = 'perf3', email = '3@3.com')

    def test_assign_performers(self):
        self.client.login(username = 'superadmin', password = 'superadmin')
        _add_incident(self, self.area)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 0)
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'performers': ('1', ),
            'add_performers': '1',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 1)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'performers': ('1', '2',),
            'add_performers': '1',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 2)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'performers': ('3', ),
            'add_performers': '1',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(len(mail.outbox), 5)
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 1)
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'add_performers': '1',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(len(response.context['errors']), 1)
        self.client.logout()

    def test_nonsuperuser_assign_performers(self):
        self.client.login(username = 'admin', password = 'admin')
        _add_incident(self, self.area)
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 0)
        csrf_token = _get_csrf_token(self, 'incident-view', kwargs = {'incident_id': 1})
        response = self.client.post(reverse('incident-view', kwargs = {'incident_id': 1}), {
            'performers': ('1', ),
            'add_performers': '1',
            'csrfmiddlewaretoken': csrf_token
            })
        self.assertEqual(models.Incident.objects.get(pk = 1).performers.count(), 0)
        self.client.logout()

