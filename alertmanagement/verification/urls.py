from django.urls import path
from . import views
from .views import RoleVerification, GovernmentDocument, SubmittedDocument

app_name = 'communication'

# path('messages/', MessageListView.as_view(), name='message_list'),

urlpatterns = [
    path("", RoleVerification.as_view(), name="verification"),
    path("", GovernmentDocument.as_view(), name="document"),
    path("", SubmittedDocument.as_view(), name="submitted"),
]