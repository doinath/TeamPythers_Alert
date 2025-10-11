from django.contrib import admin

from .models import User, Citizen, Authority, Responder, Email, ContactInfo

# Register your models here.
admin.site.register(User)
admin.site.register(Citizen)
admin.site.register(Authority)
admin.site.register(Responder)
admin.site.register(Email)
admin.site.register(ContactInfo)