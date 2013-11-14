from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('tickets.views',
    url(r'^login/$', 'login', name = 'login-view'),
    url(r'^logout/$', 'logout', name = 'logout-view'),

    url(r'^main/$', 'main', name = 'main-view'),
    #url(r'^main/(?P<page>\d+)$', 'main', name = 'main-view'),

    #url(r'^incident/(?P<incident_id>\d+)/$', 'incident', name = 'incident-view'),
    #url(r'^incident/(?P<incident_id>\d+)/history/$', 'incident_history', name = 'incident-history-view'),
    url(r'^incident/add/$', 'incident_add', name = 'incident-add-view'),
    #url(r'^incident/filter/$', 'incident_filter', name = 'incident-filter-view'),
)
