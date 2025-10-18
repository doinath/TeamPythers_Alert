from django.contrib import admin
from django.urls import path, include
from system.views import FrontendAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),  # updated path for login page
    path('', FrontendAppView.as_view(), name='index'),  # serve index.html
]
