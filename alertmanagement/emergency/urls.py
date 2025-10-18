from django.urls import path
from . import views

app_name = "EmergencyEvent"

urlpatterns = [
    # Homepage and login
    path("", views.HomepageView.as_view(), name="index"),
    path("account/", views.login_view, name="login"),

    # EventAssignment URLs
    path("assignment/create/", views.CreateAssignmentView.as_view(), name="create_assignment"),
    path("assignment/receive/", views.ReceiveAssignmentView.as_view(), name="receive_assignment"),

    # EmergencyEvent URLs
    path("message/receive/", views.ReceiveMessageView.as_view(), name="receive_message"),
    path("call/receive/", views.ReceiveCallView.as_view(), name="receive_call"),
]
