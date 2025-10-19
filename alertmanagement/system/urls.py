from django.urls import path
from . import views

app_name = "system"

urlpatterns = [
    path("", views.SystemView.as_view(), name="system_page"),
]
