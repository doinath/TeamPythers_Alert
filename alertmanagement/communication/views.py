
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Message, CallLog
from emergency.models import EmergencyEvent  # IMPORT ADDED
from account.models import Citizen, Authority  # IMPORT ADDED
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from django.db import connection
from django.contrib.auth.mixins import LoginRequiredMixin
import json

User = get_user_model()


# ====================
# TEMPLATE VIEWS
# ====================

# --- View 1: Default Message List (Empty Chat Area) ---
class MessageListView(LoginRequiredMixin, View):
    template_name = "messages_list.html"

    def get(self, request, *args, **kwargs):
        context = {
            'chat_conversations': get_sidebar_data(request.user),
            'selected_event': None,  # Triggers "Select a conversation" state
            'messages': None
        }
        return render(request, self.template_name, context)


# --- View 2: Chat Detail (Specific Conversation Active) ---
class ChatDetailView(LoginRequiredMixin, View):
    template_name = "messages_list.html"  # Reuses the same template

    def get(self, request, event_id, *args, **kwargs):
        # 1. Fetch the specific event
        selected_event = get_object_or_404(EmergencyEvent, pk=event_id)

        # 2. Security Check: Ensure user is actually part of this event
        user_citizen_profile = request.user.custom_profile.citizen_profile
        is_reporter = (selected_event.userID == user_citizen_profile)

        # Check if authority (safely handle if user isn't an authority)
        is_assigned_authority = False
        if hasattr(user_citizen_profile, 'authority_profile'):
            is_assigned_authority = (selected_event.authority == user_citizen_profile.authority_profile)

        if not (is_reporter or is_assigned_authority):
            # If user shouldn't see this chat, redirect to main list
            return redirect('communication:messages')

        # 3. Mark messages as read (Optional logic could go here)

        # 4. Fetch Messages for this event
        messages = Message.objects.filter(emergency_event=selected_event).order_by('timestamp')

        context = {
            'chat_conversations': get_sidebar_data(request.user),  # Keep sidebar populated
            'selected_event': selected_event,
            'messages': messages
        }
        return render(request, self.template_name, context)

    def post(self, request, event_id, *args, **kwargs):
        """ Handles sending a new message """
        selected_event = get_object_or_404(EmergencyEvent, pk=event_id)
        message_text = request.POST.get('message_text')

        if message_text:
            Message.objects.create(
                emergency_event=selected_event,
                user_id=request.user,
                message_text=message_text
            )

        # Refresh the page to show new message
        return redirect('communication:chat_detail', event_id=event_id)


class CallLogListView(View):
    template_name = "call_log_list.html"

    def get(self, request, *args, **kwargs):
        call_logs = CallLog.objects.filter(
            Q(user_id=request.user) | Q(responder=request.user)
        ).order_by('-start_time')

        return render(request, self.template_name, {'call_logs': call_logs})

# ====================
# CITIZEN SIDE APIS
# ====================

# --- 1. EMERGENCY EVENT REPORTING (Fire, Flood, etc.) ---

@csrf_exempt
def create_emergency_event(request):
    """
    Called when Citizen clicks a specific event button (Fire, Flood, etc.).
    Creates an event with 'reported' status.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = data.get('category')
            gps_location = data.get('location', 'Unknown Location')
            description = data.get('description', f"Emergency reported: {category}")

            # Get the Citizen instance associated with the logged-in User
            try:
                citizen_profile = request.user.custom_profile.citizen_profile
            except AttributeError:
                return JsonResponse({'status': 'error', 'message': 'User is not a Citizen'}, status=403)

            # Create the Event using Django ORM
            event = EmergencyEvent.objects.create(
                userID=citizen_profile,
                category=category,
                gps_location=gps_location,
                description=description,
                status='reported',  # Initial status for Authority dashboard
                severity_level='high'
            )

            return JsonResponse({'status': 'success', 'event_id': event.eventID})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error'}, status=400)


@csrf_exempt
def cancel_emergency_event(request):
    """
    Called if the Citizen cancels the request while the timer is running.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data.get('event_id')

            event = EmergencyEvent.objects.get(eventID=event_id)
            # Only cancel if it hasn't been picked up yet
            if event.status == 'reported':
                event.status = 'closed'
                event.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Event already in progress'}, status=400)

        except EmergencyEvent.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error'}, status=400)


# --- 2. VIDEO/SOS CALL LOGIC (Existing) ---

@csrf_exempt
def initiate_sos_call(request):
    """ Creates a 'Ringing' CallLog using Stored Procedure. """
    if request.method == 'POST':
        try:
            user_id = request.user.id
            new_call_id = None
            with connection.cursor() as cursor:
                cursor.callproc('sp_create_call_log', [user_id])
                result = cursor.fetchone()
                if result: new_call_id = result[0]

            if new_call_id:
                return JsonResponse({'status': 'ringing', 'call_id': new_call_id})
            return JsonResponse({'status': 'error', 'message': 'DB Error'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)


def check_call_status(request):
    """ Citizen polls this for Video Call status. """
    call_id = request.GET.get('call_id')
    try:
        call = CallLog.objects.get(call_id=call_id)
        response_data = {'status': call.status}
        if call.status == 'active' and call.responder:
            # Logic to get agency name
            agency_name = "Authority"
            if hasattr(call.responder, 'custom_profile') and hasattr(call.responder.custom_profile,
                                                                     'authority_profile'):
                agency_name = call.responder.custom_profile.authority_profile.agency_name
            response_data['agency_name'] = agency_name
            response_data['responder_name'] = f"{call.responder.first_name} {call.responder.last_name}"
        return JsonResponse(response_data)
    except CallLog.DoesNotExist:
        return JsonResponse({'status': 'error'})


@csrf_exempt
def end_emergency_call(request):
    """ Ends Video Call using Stored Procedure. """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            call_id = data.get('call_id')
            call_log = CallLog.objects.get(call_id=call_id)
            final_status = 'declined' if call_log.status == 'ringing' else 'completed'

            with connection.cursor() as cursor:
                cursor.callproc('sp_end_call_log', [call_id, final_status])
            return JsonResponse({'status': 'success', 'new_status': final_status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)


# ====================
# AUTHORITY SIDE APIS
# ====================

# --- 1. EVENT ASSIGNMENT & CHAT INITIATION (Stored Procedure) ---

def get_reported_events(request):
    """
    Authority Dashboard polls this to populate the Event List.
    Returns only 'reported' events (pending assignment).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'events': []})

    # Fetch events with related reporter info
    events = EmergencyEvent.objects.filter(status='reported').select_related('userID__user_id').order_by('-created_at')

    events_data = []
    for e in events:
        # Navigate from EmergencyEvent -> Citizen -> User
        user = e.userID.user_id
        events_data.append({
            'eventID': e.eventID,
            'category': e.get_category_display(),  # Uses the tuple label
            'location': e.gps_location,
            'description': e.description,
            'reporter_name': f"{user.first_name} {user.last_name}",
            'created_at': e.created_at.strftime("%H:%M")
        })

    return JsonResponse({'events': events_data})


@csrf_exempt
def authority_assign_event(request):
    """
    Called when Authority clicks "Assign & Chat".
    USES STORED PROCEDURE: AssignAuthorityAndInitChat
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data.get('event_id')

            # 1. Get the Authority Profile ID (for the Event table foreign key)
            try:
                authority_profile = request.user.custom_profile.citizen_profile.authority_profile
                authority_profile_id = authority_profile.id
            except AttributeError:
                return JsonResponse({'status': 'error', 'message': 'User is not an Authority'}, status=403)

            # 2. Get the User ID (for the Message table foreign key)
            user_id = request.user.id

            # 3. Define the initial message
            initial_message = "I have accepted your emergency request. We are deploying a unit to your location immediately."

            current_time = timezone.now()

            # 4. Execute Stored Procedure
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL AssignAuthorityAndInitChat(%s, %s, %s, %s, %s)",
                    [event_id, authority_profile_id, user_id, initial_message, current_time]
                )

            return JsonResponse({'status': 'success', 'event_id': event_id})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)


# --- 2. VIDEO/SOS CALL LOGIC (Existing) ---

def check_incoming_calls(request):
    """ Authority polls this for incoming Video calls. """
    if not request.user.is_authenticated:
        return JsonResponse({'active_call': False})

    # Check for calls specifically assigned or unassigned
    incoming = CallLog.objects.filter(status='ringing').filter(
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
    """ Authority accepts Video Call using Stored Procedure. """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            call_id = data.get('call_id')
            responder_id = request.user.id

            with connection.cursor() as cursor:
                cursor.callproc('sp_accept_call_log', [call_id, responder_id])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)


def check_event_status(request):
    """
    Citizen polls this to check if an Authority has accepted (assigned) the event.
    """
    event_id = request.GET.get('event_id')

    if not event_id:
        return JsonResponse({'status': 'error', 'message': 'Missing event_id'}, status=400)

    try:
        event = EmergencyEvent.objects.get(eventID=event_id)

        # If the status changed to 'in_progress', it means authority assigned it
        return JsonResponse({
            'status': 'success',
            'event_status': event.status,
            'event_id': event.eventID
        })
    except EmergencyEvent.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)


# --- Helper Function to Get Sidebar Data ---
def get_sidebar_data(user):
    """
    Fetches the list of conversations for the logged-in user.
    - If Authority: Fetch events assigned to them.
    - If Citizen: Fetch events they reported.
    Returns a sorted list of dictionaries for the template.
    """
    events = EmergencyEvent.objects.none()

    # 1. Determine User Role & Filter Events
    if hasattr(user, 'custom_profile') and hasattr(user.custom_profile, 'citizen_profile'):
        citizen_profile = user.custom_profile.citizen_profile

        if hasattr(citizen_profile, 'authority_profile'):
            # --- ROLE: AUTHORITY ---
            # Show all events where this Authority is assigned
            # We exclude 'reported' because those are unassigned.
            # We want 'in_progress', 'resolved', 'closed'.
            events = EmergencyEvent.objects.filter(
                authority=citizen_profile.authority_profile
            ).exclude(status='reported')
        else:
            # --- ROLE: CITIZEN ---
            # Show events reported by this Citizen
            events = EmergencyEvent.objects.filter(
                userID=citizen_profile
            )

    # 2. Prepare Data for Sidebar (Last Message Preview)
    chat_conversations = []
    for event in events:
        last_msg = Message.objects.filter(emergency_event=event).order_by('-timestamp').first()

        # Determine the "Other Person" name for the label
        # If I am Authority -> Label is Citizen Name
        # If I am Citizen -> Label is Authority Agency Name (or "Waiting for Assignment")
        if hasattr(user.custom_profile.citizen_profile, 'authority_profile'):
            # I am Authority, showing Citizen Name
            display_name = f"{event.userID.user_id.first_name} {event.userID.user_id.last_name}"
        else:
            # I am Citizen, showing Authority Name
            if event.authority:
                display_name = event.authority.agency_name
            else:
                display_name = "Pending Authority..."

        chat_conversations.append({
            'emergency_event': event,
            'display_name': display_name,
            'last_message_text': last_msg.message_text if last_msg else "No messages yet.",
            'last_message_timestamp': last_msg.timestamp if last_msg else event.created_at
        })

    # Sort by newest activity first
    chat_conversations.sort(key=lambda x: x['last_message_timestamp'], reverse=True)
    return chat_conversations
