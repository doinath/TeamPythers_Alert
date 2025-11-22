from django.urls import path
from . import views
from .views import RoleVerification, GovernmentDocument, SubmittedDocument

app_name = 'verification'

# path('messages/', MessageListView.as_view(), name='message_list'),

urlpatterns = [
    path("role_verification/", RoleVerification.as_view(), name="verification"),
    path("government_document/", GovernmentDocument.as_view(), name="document"),
    path("submitted_document/", SubmittedDocument.as_view(), name="submitted"),
]