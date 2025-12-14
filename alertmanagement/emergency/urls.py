from django.urls import path
from . import views

app_name = "EmergencyEvent"

urlpatterns = [
    # Homepage and login
    path("", views.HomepageView.as_view(), name="index"),
    path("account/", views.login_view, name="login"),

    # --- MAIN LIST VIEWS (Updated with Dev IDs) ---

    # 1. Assignment List: /viewlist/ OR /viewlist/6/
    path("viewlist/", views.AssignmentListView.as_view(), name="assignment_list"),
    path("viewlist/<int:dev_id>/", views.AssignmentListView.as_view(), name="assignment_list_dev"),

    # 2. Event List: /event-list/ OR /event-list/6/
    path("event-list/", views.EventListView.as_view(), name="event_list"),
    path("event-list/<int:dev_id>/", views.EventListView.as_view(), name="event_list_dev"),

    # 3. Report Incident: /report-incident/ OR /report-incident/6/
    path("report-incident/", views.CreateReportView.as_view(), name="report_form"),
    path("report-incident/<int:dev_id>/", views.CreateReportView.as_view(), name="report_form_dev"),

    # 4. Responder Availability: /responder-availability/ OR /responder-availability/6/
    path("responder-availability/", views.ResponderAvailabilityView.as_view(), name="responder_availability"),
    path("responder-availability/<int:dev_id>/", views.ResponderAvailabilityView.as_view(),
         name="responder_availability_dev"),

    # --- DETAILS VIEWS (Updated Logic) ---

    # Authority View: /details-authority/event_id/ OR /details-authority/event_id/dev_id/
    path("details-authority/<int:event_id>/", views.EventDetailsAuthorityView.as_view(),
         name="event_details_authority"),
    path("details-authority/<int:event_id>/<int:dev_id>/", views.EventDetailsAuthorityView.as_view(),
         name="event_details_authority_dev"),

    # Responder View: /details-responder/event_id/ OR /details-responder/event_id/dev_id/
    path("details-responder/<int:event_id>/", views.EventDetailsResponderView.as_view(),
         name="event_details_responder"),
    path("details-responder/<int:event_id>/<int:dev_id>/", views.EventDetailsResponderView.as_view(),
         name="event_details_responder_dev"),

    # Defaults (No Event ID)
    path("details-authority/", views.EventDetailsAuthorityView.as_view(), name="event_details_authorit"),
    path("details-responder/", views.EventDetailsResponderView.as_view(), name="event_details_responder"),

    # --- MEDICAL RECORDS ---
    path("medical-record/", views.MedicalRecordView.as_view(), name="medical_records"),
    path("medical-record/<int:event_id>/", views.MedicalRecordView.as_view(), name="medical_record"),

    # --- Placeholders ---
    path("assignment/create/", views.CreateAssignmentView.as_view(), name="create_assignment"),
    path("assignment/receive/", views.ReceiveAssignmentView.as_view(), name="receive_assignment"),
    path("message/receive/", views.ReceiveMessageView.as_view(), name="receive_message"),
    path("call/receive/", views.ReceiveCallView.as_view(), name="receive_call"),
]