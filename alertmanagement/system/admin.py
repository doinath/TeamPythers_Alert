from django.contrib import admin

# Register your models here.
from .models import SystemLog

admin.site.register(SystemLog)