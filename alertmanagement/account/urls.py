from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('citizen_dashboard/', views.CitizenDashboardView.as_view(), name='citizen_dashboard'),
    path('responder_dashboard/', views.ResponderDashboardView.as_view(), name='responder_dashboard'),
    path('authority_dashboard/', views.AuthorityDashboardView.as_view(), name='authority_dashboard')
]
