from django.urls import path, include
from . import views

app_name = 'account'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verification/', include('verification.urls')),
    path('citizen_profile_completion/', views.CitizenProfileCompletionView.as_view(), name='citizen_profile_completion'),
    path('citizen_dashboard/', views.CitizenDashboardView.as_view(), name='citizen_dashboard'),
    path('responder_dashboard/', views.ResponderDashboardView.as_view(), name='responder_dashboard'),
    path('authority_dashboard/', views.AuthorityDashboardView.as_view(), name='authority_dashboard'),
    path('citizen_profile/', views.CitizenProfileView.as_view(), name='citizen_profile'),
    path('responder_profile/', views.ResponderProfileView.as_view(), name='responder_profile'),
    path('authority_profile/', views.AuthorityProfileView.as_view(), name='authority_profile'),

]
