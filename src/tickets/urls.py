from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('tickets.views',
    url(r'^login/$', 'login', name = 'login-view'),
    url(r'^logout/$', 'logout', name = 'logout-view'),

    url(r'^$', 'main'),
    url(r'^main/$', 'main', name = 'main-view'),
    url(r'^main/(?P<page>\d+)/$', 'main', name = 'main-page-view'),

    url(r'^incident/(?P<incident_id>\d+)/$', 'incident', name = 'incident-view'),
    url(r'^incident/(?P<incident_id>\d+)/history/$', 'incident_history', name = 'incident-history-view'),
    url(r'^incident/add/$', 'incident_add', name = 'incident-add-view'),
    url(r'^incident/filter/(?P<page>\d+)?/$', 'incident_filter', name = 'incident-filter-view'),
)
