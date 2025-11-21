from django.shortcuts import render
from django.views import View

class HomepageView(View):
    template_name = "EmergencyEvent/index.html"

    def get(self, request):
        return render(request, self.template_name)


def login_view(request):
    return render(request, "EmergencyEvent/login.html")


# --- EventAssignment Views ---
class CreateAssignmentView(View):
    template_name = "EventAssignment/create_assignment.html"

    def get(self, request):
        return render(request, self.template_name)


class ReceiveAssignmentView(View):
    template_name = "EventAssignment/receive_assignment.html"

    def get(self, request):
        return render(request, self.template_name)


# --- EmergencyEvent Views ---
class ReceiveMessageView(View):
    template_name = "EmergencyEvent/receive_message.html"

    def get(self, request):
        return render(request, self.template_name)


class ReceiveCallView(View):
    template_name = "EmergencyEvent/receive_call.html"

    def get(self, request):
        return render(request, self.template_name)

#Actual htmls
class AssignmentListView(View):
    template_name = "EventAssignment/assignment_list.html"
    def get(self, request):
        return render(request, self.template_name)

class EventDetailsResponderView(View):
    template_name = "EmergencyEvent/event_details_responder.html"
    def get(self, request):
        return render(request, self.template_name)

class EventDetailsAuthorityView(View):
    template_name = "EmergencyEvent/event_details_authority.html"
    def get(self, request):
        return render(request, self.template_name)
class EventListView(View):
    template_name = "EventAssignment/event_list.html"
    def get(self, request):
        return render(request, self.template_name)
class CreateReportView(View):
    template_name = "EmergencyEvent/report_form.html"
    def get(self, request):
        return render(request, self.template_name)
class ResponderAvailabilityView(View):
    template_name = "EventAssignment/responder_availability_emergency.html"
    def get(self, request):
        return render(request, self.template_name)