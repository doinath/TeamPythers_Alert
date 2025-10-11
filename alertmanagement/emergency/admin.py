from django.contrib import admin

from .models import EmergencyEvent, EventAssignment, MedicalCondition
# Register your models here.
admin.site.register(EmergencyEvent)
admin.site.register(EventAssignment)
admin.site.register(MedicalCondition)