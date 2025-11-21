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

    #Actual Htmls
    path("assignment/viewlist/", views.AssignmentListView.as_view(), name="assignment_list"),
    path("emergency/details-authority",views.EventDetailsAuthorityView.as_view(), name="event_details_authority"),
    path("emergency/details-responder/", views.EventDetailsResponderView.as_view(), name="event_details_responder"),
    path("emergency/event-list/", views.EventListView.as_view(), name="event_list"),
    path("emergency/report-incident/", views.CreateReportView.as_view(), name="report_form"),
    path("emergency/responder-availability/", views.ResponderAvailabilityView.as_view(), name="responder_availability"),
]
