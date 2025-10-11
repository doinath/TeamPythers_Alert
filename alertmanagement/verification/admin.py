from django.contrib import admin

from .models import RoleVerification, SubmittedDocument, GovernmentDocument
# Register your models here.
admin.site.register(RoleVerification)
admin.site.register(SubmittedDocument)
admin.site.register(GovernmentDocument)
