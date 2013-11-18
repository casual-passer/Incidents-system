from django.contrib import admin

from .models import Status, Area, Department, Incident, IncidentComment, Performer

admin.site.register(Status)
admin.site.register(Area)
admin.site.register(Department)
admin.site.register(Incident)
admin.site.register(IncidentComment)
admin.site.register(Performer)

# Register your models here.
