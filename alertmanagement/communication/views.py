from django.shortcuts import render
from django.views import View
from .models import Message, CallLog


class MessageListView(View):
    """
    A class-based view to display a list of all messages.
    """
    template_name = "communication/message_list.html"

    def get(self, request, *args, **kwargs):
        # Fetch all message objects from the database, ordering by the newest first
        messages = Message.objects.all().order_by('-timestamp')

        # Prepare the context dictionary to pass to the template
        context = {
            'messages': messages
        }

        # Render the template with the context data
        return render(request, self.template_name, context)


class CallLogListView(View):
    """
    A class-based view to display a list of all call logs.
    """
    template_name = "communication/call_log_list.html"

    def get(self, request, *args, **kwargs):
        # Fetch all call log objects, ordering by the most recent start time
        call_logs = CallLog.objects.all().order_by('-start_time')

        # Prepare the context dictionary
        context = {
            'call_logs': call_logs
        }

        # Render the template with the context data
        return render(request, self.template_name, context)
