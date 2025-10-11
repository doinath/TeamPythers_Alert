from django.contrib import admin

from .models import Message, CallLog
# Register your models here.

admin.site.register(Message)
admin.site.register(CallLog)