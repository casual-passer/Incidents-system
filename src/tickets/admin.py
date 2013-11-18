from django.contrib import admin

from .models import Status, Area, Department, Incident, IncidentComment

admin.site.register(Status)
admin.site.register(Area)
admin.site.register(Department)
admin.site.register(Incident)
admin.site.register(IncidentComment)

# Register your models here.
