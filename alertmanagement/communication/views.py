from django.shortcuts import render, get_object_or_404
from django.views import View
from .models import Message, CallLog
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
import json

User = get_user_model()


# ... (MessageListView, CallLogListView, ChatDetailView remain the same) ...

class MessageListView(View):
    template_name = "messages_list.html"

    def get(self, request, *args, **kwargs):
        messages = Message.objects.all().order_by('-timestamp')
        return render(request, self.template_name, {'messages': messages})


class CallLogListView(View):
    template_name = "call_log_list.html"

    def get(self, request, *args, **kwargs):
        # Show logs where user is EITHER the caller OR the responder
        call_logs = CallLog.objects.filter(
            Q(user_id=request.user) | Q(responder=request.user)
        ).order_by('-start_time')

        return render(request, self.template_name, {'call_logs': call_logs})


class ChatDetailView(View):
    template_name = "chat_detail.html"

    def get(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)
        return render(request, self.template_name, {'target_user': target_user})


# ====================
# CITIZEN SIDE APIS
# ====================

@csrf_exempt
def initiate_sos_call(request):
    """
    Creates a 'Ringing' CallLog.
    """
    if request.method == 'POST':
        try:
            call_log = CallLog.objects.create(
                user_id=request.user,
                responder=None,
                call_type='outgoing',
                status='ringing',
                start_time=timezone.now()
            )

            return JsonResponse({
                'status': 'ringing',
                'call_id': call_log.call_id,
                'authority_name': "Waiting for Responder..."
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error'}, status=400)


def check_call_status(request):
    """
    Citizen polls this.
    """
    call_id = request.GET.get('call_id')
    try:
        call = CallLog.objects.get(call_id=call_id)

        response_data = {'status': call.status}

        if call.status == 'active' and call.responder:
            agency_name = "Authority Unit"
            # Attempt to fetch Agency Name from profile
            if hasattr(call.responder, 'custom_profile') and hasattr(call.responder.custom_profile,
                                                                     'authority_profile'):
                agency_name = call.responder.custom_profile.authority_profile.agency_name
            elif hasattr(call.responder, 'authority_profile'):
                agency_name = call.responder.authority_profile.agency_name

            response_data['agency_name'] = agency_name
            response_data['responder_name'] = f"{call.responder.first_name} {call.responder.last_name}"

        return JsonResponse(response_data)
    except CallLog.DoesNotExist:
        return JsonResponse({'status': 'error'})


@csrf_exempt
def end_emergency_call(request):
    """
    Ends the call.
    - If status was 'ringing', it means it was DECLINED or CANCELLED (not Completed).
    - If status was 'active', it means it was COMPLETED.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            call_id = data.get('call_id')
            call_log = CallLog.objects.get(call_id=call_id)

            # --- LOGIC UPDATE HERE ---
            if call_log.status == 'ringing':
                # Call ended before being accepted -> Declined/Missed
                call_log.status = 'declined'
            else:
                # Call was active -> Completed
                call_log.status = 'completed'
            # -------------------------

            call_log.end_time = timezone.now()

            # Calculate duration
            if call_log.start_time:
                delta = call_log.end_time - call_log.start_time
                call_log.duration = int(delta.total_seconds())
            else:
                call_log.duration = 0

            call_log.save()
            return JsonResponse({'status': 'success', 'new_status': call_log.status})
        except CallLog.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)


# ====================
# AUTHORITY SIDE APIS
# ====================

def check_incoming_calls(request):
    if not request.user.is_authenticated:
        return JsonResponse({'active_call': False})

    incoming = CallLog.objects.filter(
        status='ringing'
    ).filter(
        Q(responder=request.user) | Q(responder__isnull=True)
    ).first()

    if incoming:
        return JsonResponse({
            'active_call': True,
            'call_id': incoming.call_id,
            'caller_name': f"{incoming.user_id.first_name} {incoming.user_id.last_name}",
            'caller_id': incoming.user_id.id
        })

    return JsonResponse({'active_call': False})


@csrf_exempt
def accept_call(request):
    """
    Authority accepts the call.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        call_id = data.get('call_id')
        try:
            call = CallLog.objects.get(call_id=call_id)

            # Lock the call to this authority
            call.responder = request.user
            call.status = 'active'
            call.start_time = timezone.now()  # Reset start time to when conversation actually starts
            call.save()

            return JsonResponse({'status': 'success'})
        except CallLog.DoesNotExist:
            return JsonResponse({'status': 'error'})

    return JsonResponse({'status': 'error'}, status=400)