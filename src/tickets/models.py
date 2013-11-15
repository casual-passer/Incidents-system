# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

from time import strftime
import uuid
import os

class AbstractModel(models.Model):

    def __unicode__(self):
        if hasattr(self, 'name'):
            return self.name
        if hasattr(self, 'theme'):
            return self.theme
        return u'Undefined'

    class Meta:
        abstract = True


class Status(AbstractModel):

    name = models.CharField(max_length = 128)


class Area(AbstractModel):

    name = models.CharField(max_length = 128)


class Department(AbstractModel):

    name = models.CharField(max_length = 128)


class Incident(AbstractModel):

    theme = models.CharField(max_length = 128, blank = False)
    description = models.TextField(blank = False)
    created_at = models.DateTimeField(auto_now = True)

    user = models.ForeignKey(User)
    fio = models.CharField(max_length = 128)
    phone = models.CharField(max_length = 128)
    pc = models.CharField(max_length = 128)
    room = models.CharField(max_length = 128, blank = True)

    status = models.ForeignKey(Status)
    area = models.ForeignKey(Area)
    department = models.ForeignKey(Department)

    def save(self, *args, **kwargs):
        in_db = True
        if not self.id:
            in_db = False
            if not hasattr(self, 'status'):
                (self.status, created) = Status.objects.get_or_create(pk = 1, defaults = {'name': u'Default status'})
        super(Incident, self).save(*args, **kwargs)
        # if incident did not exist in database, save first status change in incidenthistory table
        if not in_db:
            IncidentHistory.objects.create(incident = self, modified_at = self.created_at, status = self.status, user = self.user)

    def __unicode__(self):
        return self.theme

    class Meta:
        ordering = ('-pk', '-created_at', )


class IncidentHistory(models.Model):

    incident = models.ForeignKey(Incident)
    modified_at = models.DateTimeField()
    status = models.ForeignKey(Status)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return unicode(self.incident.pk) + ': ' + unicode(self.status.name)

    class Meta:
        ordering = ('-modified_at', )

