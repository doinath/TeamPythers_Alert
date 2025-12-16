from django.urls import path
from . import views
from .views import QuickEmergencyReportView, CancelEmergencyReportView, CloseEventView  # Import CloseEventView
from emergency.views import CreateReportView

app_name = 'account'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('citizen_profile_completion/', views.CitizenProfileCompletionView.as_view(),
         name='citizen_profile_completion'),

    # --- Standard Dashboards ---
    path('citizen_dashboard/', views.CitizenDashboardView.as_view(), name='citizen_dashboard'),
    path('responder_dashboard/', views.ResponderDashboardView.as_view(), name='responder_dashboard'),
    path('authority_dashboard/', views.AuthorityDashboardView.as_view(), name='authority_dashboard'),

    # --- DEV MODE DASHBOARDS (Append ID) ---
    path('citizen_dashboard/<int:dev_id>/', views.CitizenDashboardView.as_view(), name='citizen_dashboard_dev'),
    path('responder_dashboard/<int:dev_id>/', views.ResponderDashboardView.as_view(), name='responder_dashboard_dev'),
    path('authority_dashboard/<int:dev_id>/', views.AuthorityDashboardView.as_view(), name='authority_dashboard_dev'),

    path('citizen_profile/', views.CitizenProfileView.as_view(), name='citizen_profile'),
    path('responder_profile/', views.ResponderProfileView.as_view(), name='responder_profile'),
    path('authority_profile/', views.AuthorityProfileView.as_view(), name='authority_profile'),

    # --- URLs for Applications ---
    path('apply/responder/', views.ApplyResponderView.as_view(), name='apply_responder'),
    path('apply/authority/', views.ApplyAuthorityView.as_view(), name='apply_authority'),

    # --- Quick Report Logic ---
    path('quick-report/', QuickEmergencyReportView.as_view(), name='quick_report'),
    path('cancel-report/', CancelEmergencyReportView.as_view(), name='cancel_report'),

    # --- Authority Actions ---
    path('close-event/<int:event_id>/', CloseEventView.as_view(), name='close_event'),  # NEW URL

    # --- Manual Report Forms ---
    path("report-incident/", CreateReportView.as_view(), name="report_form"),
    path("report-incident/<int:dev_id>/", CreateReportView.as_view(), name="report_form_dev"),
]