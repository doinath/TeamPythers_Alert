from django.urls import path
from . import views
from .views import QuickEmergencyReportView, CancelEmergencyReportView
from emergency.views import CreateReportView

app_name = 'account'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('citizen_profile_completion/', views.CitizenProfileCompletionView.as_view(), name='citizen_profile_completion'),
    path('citizen_dashboard/', views.CitizenDashboardView.as_view(), name='citizen_dashboard'),
    path('responder_dashboard/', views.ResponderDashboardView.as_view(), name='responder_dashboard'),
    path('authority_dashboard/', views.AuthorityDashboardView.as_view(), name='authority_dashboard'),

    path('citizen_profile/', views.CitizenProfileView.as_view(), name='citizen_profile'),
    path('responder_profile/', views.ResponderProfileView.as_view(), name='responder_profile'),
    path('authority_profile/', views.AuthorityProfileView.as_view(), name='authority_profile'),

    # --- URLs for Applications ---
    path('apply/responder/', views.ApplyResponderView.as_view(), name='apply_responder'),
    path('apply/authority/', views.ApplyAuthorityView.as_view(), name='apply_authority'),

    # --- Quick Report Logic ---
    path('quick-report/', QuickEmergencyReportView.as_view(), name='quick_report'),
    path('cancel-report/', CancelEmergencyReportView.as_view(), name='cancel_report'),

    # --- Manual Report Forms ---
    path("report-incident/", CreateReportView.as_view(), name="report_form"),
    path("report-incident/<int:dev_id>/", CreateReportView.as_view(), name="report_form_dev"),
]