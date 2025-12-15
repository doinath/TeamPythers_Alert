"""
URL configuration for alertmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('account/', include(('account.urls', 'account'), namespace='account')),
    path('', include(('account.urls', 'account_root'), namespace='account_root')),

    path('emergency/', include(('emergency.urls', 'emergency'), namespace='emergency')),
    path('communication/', include(('communication.urls', 'communication'), namespace='communication')),
    path('system_log/', include(('system_log.urls', 'system_log'), namespace='system_log')),
    path('verification/', include(('verification.urls', 'verification'), namespace='verification')),
]


# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

