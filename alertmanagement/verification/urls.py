from django.urls import path, include
from . import views
from .views import RoleVerification, GovernmentDocument, SubmittedDocument

app_name = 'verification'

# path('messages/', MessageListView.as_view(), name='message_list'),

urlpatterns = [

    path("list/", RoleVerification.as_view(), name="verification"),
    path('role/review/', views.RoleVerificationView.as_view(), name='role_verification'),
    #path('account/', include('account.urls')),
    # path("goverment/", GovernmentDocument.as_view(), name="document"),
    # path("submitted/", SubmittedDocument.as_view(), name="submitted"),
]