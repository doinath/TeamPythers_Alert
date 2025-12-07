from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User as DjangoAuthUser
from django.db.models import Q

# Import your models
from account.models import User as AccountUser, Citizen, Responder
from .models import EmergencyEvent, EventAssignment


# --- VIEW CLASSES ---

class HomepageView(View):
    template_name = "EmergencyEvent/index.html"

    def get(self, request):
        return render(request, self.template_name)


def login_view(request):
    return render(request, "EmergencyEvent/login.html")


# --- Placeholders ---
class CreateAssignmentView(View):
    template_name = "EventAssignment/create_assignment.html"

    def get(self, request): return render(request, self.template_name)


class ReceiveAssignmentView(View):
    template_name = "EventAssignment/receive_assignment.html"

    def get(self, request): return render(request, self.template_name)


class ReceiveMessageView(View):
    template_name = "EmergencyEvent/receive_message.html"

    def get(self, request): return render(request, self.template_name)


class ReceiveCallView(View):
    template_name = "EmergencyEvent/receive_call.html"

    def get(self, request): return render(request, self.template_name)


# --- MAIN LIST VIEWS ---

class EventListView(View):
    template_name = "EventAssignment/event_list.html"

    def get(self, request):
        events = EmergencyEvent.objects.select_related('userID__user_id').all().order_by('-created_at')
        context = {'events': events}
        return render(request, self.template_name, context)


class AssignmentListView(View):
    """
    View for Responders to see ALL of THEIR assigned events (active, completed, cancelled)
    by querying the EventAssignment table directly.
    """
    template_name = "EventAssignment/assignment_list.html"

    def get(self, request):
        assignments = []

        # 1. IDENTIFY RESPONDER
        responder_profile = None

        # --- DEV FALLBACK LOGIC ---
        dev_id = request.GET.get('dev_id')
        if dev_id:
            try:
                # Use the ID from the URL parameter for development/testing
                responder_profile = Responder.objects.get(pk=dev_id)
            except Responder.DoesNotExist:
                messages.error(request, f"Responder with ID {dev_id} not found.")
        # --- AUTHENTICATED USER LOGIC ---
        elif request.user.is_authenticated:
            try:
                # Standard retrieval for logged-in user
                responder_profile = request.user.custom_profile.citizen_profile.responder_profile
            except AttributeError:
                messages.error(request, "User is authenticated but does not have a Responder profile.")

        # 2. FILTER ALL ASSIGNMENTS FOR THE RESPONDER
        if responder_profile:
            # Fetch ALL assignment records for this responder
            assignments = EventAssignment.objects.filter(
                responder=responder_profile
            ).select_related(
                'emergency_event__userID__user_id'
            ).order_by('-assigned_at')
        else:
            messages.info(request, "Please log in or use the ?dev_id=X parameter to view assignments.")

        context = {
            'assignments': assignments,
            # Add responder profile for debugging/display if needed
            'responder': responder_profile
        }
        return render(request, self.template_name, context)


# --- DETAILS VIEWS ---

class EventDetailsResponderView(View):
    template_name = "EmergencyEvent/event_details_responder.html"

    def get(self, request, event_id=None):
        event = None

        # FIX: The original code always queried the first event if event_id was None,
        # which would often happen if the URL config was slightly off or during dev testing.
        # This makes sure we only try to fetch if we have a valid ID.
        if event_id:
            event = get_object_or_404(EmergencyEvent, pk=event_id)
        else:
            # If no ID is provided, it's better to show an error or redirect,
            # or strictly rely on the ID being present in a proper URL configuration.
            # Keeping the old logic for now, but flagging it:
            event = EmergencyEvent.objects.order_by('-created_at').first()
            if not event:
                messages.error(request, "No events found in the database.")
                return redirect('EmergencyEvent:event_list')  # Redirect if no events exist

        context = {'event': event}
        return render(request, self.template_name, context)

    def post(self, request, event_id=None):
        if not event_id:
            # If POST happens without an event_id, redirect to the list view.
            return redirect('EmergencyEvent:event_list')

        event = get_object_or_404(EmergencyEvent, pk=event_id)
        action = request.POST.get('action')

        # Normalize status
        current_status = str(event.status).lower().strip()

        # --- STATUS LOGIC ---

        # 1. Acknowledge -> ON THE WAY
        if action == 'acknowledge':
            if current_status in ['reported', 'pending', 'in_progress']:
                event.status = 'on the way'
                event.save()
                messages.success(request, "Status updated: ON THE WAY")
            else:
                messages.warning(request, f"Cannot acknowledge: Event is '{current_status}'.")

        # 2. On Scene -> ON SCENE
        elif action == 'on_scene':
            if current_status in ['reported', 'pending', 'in_progress', 'on the way', 'on_the_way']:
                event.status = 'on scene'
                event.save()
                messages.success(request, "Status updated: ON SCENE")
            else:
                messages.warning(request, f"Cannot update to On Scene: Event is '{current_status}'.")

        # 3. Resolved -> COMPLETED
        elif action == 'resolved':
            if current_status not in ['completed', 'resolved', 'closed']:
                event.status = 'completed'
                event.save()

                if event.responder:
                    responder = event.responder
                    responder.duty_status = 'ON'
                    responder.save()

                    EventAssignment.objects.filter(
                        emergency_event=event,
                        responder=responder,
                        status='active'
                    ).update(status='completed')

                messages.success(request, "Event Resolved. You are now AVAILABLE.")
            else:
                messages.info(request, "Event is already completed.")

        return redirect('EmergencyEvent:event_details_responder', event_id=event.eventID)


class EventDetailsAuthorityView(View):
    template_name = "EmergencyEvent/event_details_authority.html"

    def get(self, request, event_id=None):
        event = None
        if event_id:
            event = get_object_or_404(EmergencyEvent, pk=event_id)
        else:
            event = EmergencyEvent.objects.order_by('-created_at').first()
        context = {'event': event}
        return render(request, self.template_name, context)


# --- ACTION VIEWS ---

class CreateReportView(View):
    template_name = "EmergencyEvent/report_form.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # User / Citizen Logic
            citizen_obj = None
            if request.user.is_authenticated:
                try:
                    custom_user = request.user.custom_profile
                    citizen_obj = custom_user.citizen_profile
                except Exception:
                    messages.error(request, "Error: Your account is not linked to a Citizen profile.")
                    return render(request, self.template_name)
            else:
                # Dev Fallback (Ensures a Citizen exists for reporting)
                auth_user, _ = DjangoAuthUser.objects.get_or_create(username='julian_dev',
                                                                    defaults={'email': 'julian@dev.com',
                                                                              'first_name': 'Julian',
                                                                              'last_name': 'Andales',
                                                                              'is_active': True})
                account_user, _ = AccountUser.objects.get_or_create(account=auth_user, defaults={'first_name': 'Julian',
                                                                                                 'last_name': 'Andales',
                                                                                                 'date_of_birth': '2000-01-01',
                                                                                                 'gender': 'M',
                                                                                                 'street': 'Dev Street',
                                                                                                 'city': 'Cebu City'})
                citizen_obj, _ = Citizen.objects.get_or_create(user_id=account_user)

            # Form Data
            emergency_type = request.POST.get('emergencyType')
            other_specified = request.POST.get('other_specified')
            final_category = other_specified.upper() if (emergency_type == 'others' and other_specified) else str(
                emergency_type).upper()

            gps_location = request.POST.get('gps_location') or '0.0, 0.0'
            address_text = request.POST.get('address_text', 'No Address Provided')
            description_raw = request.POST.get('description', '')
            severity_input = request.POST.get('severity', 'low')

            severity_map = {'low': 1, 'medium': 2, 'high': 3}
            severity_int = severity_map.get(severity_input, 1)

            # Patient Info
            is_reporting_others = request.POST.get('reportingForOthers')
            patient_info = ""
            if is_reporting_others == 'yes':
                fname = request.POST.get('p_fname', '')
                mname = request.POST.get('p_mname', '')
                lname = request.POST.get('p_lname', '')
                patient_info = f"\n[PATIENT: {fname} {mname} {lname}]"

            final_description = f"{description_raw}\n[ADDRESS: {address_text}]{patient_info}"

            # Create Event
            EmergencyEvent.objects.create(
                userID=citizen_obj,
                category=final_category,
                description=final_description,
                gps_location=gps_location,
                status='PENDING',
                severity_level=severity_int
            )

            messages.success(request, "Report Submitted Successfully! Stay safe.")
            return redirect('EmergencyEvent:report_form')

        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            messages.error(request, f"Submission Failed: {str(e)}")
            return render(request, self.template_name)


class ResponderAvailabilityView(View):
    template_name = "EventAssignment/responder_availability_emergency.html"

    def get(self, request):
        event_id = request.GET.get('event_id')

        # 1. Fetch Responders
        responders = Responder.objects.select_related('citizen__user_id').all()

        # 2. Get Assigned IDs for THIS event (to show cancel buttons)
        assigned_ids = []
        if event_id:
            assigned_ids = list(EventAssignment.objects.filter(
                emergency_event_id=event_id,
                status='active'
            ).values_list('responder_id', flat=True))

        # 3. Counters
        total_count = responders.count()
        assigned_count = responders.filter(duty_status__in=['RES', 'BUSY']).count()

        context = {
            'responders': responders,
            'total_count': total_count,
            'assigned_count': assigned_count,
            'event_id': event_id,
            'assigned_ids': assigned_ids,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        action = request.POST.get('action')
        responder_id = request.POST.get('responder_id')
        event_id = request.POST.get('event_id')

        if not responder_id or not event_id:
            messages.error(request, "Missing information.")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')

        try:
            responder = get_object_or_404(Responder, pk=responder_id)
            event = get_object_or_404(EmergencyEvent, pk=event_id)

            if action == 'assign':
                if responder.duty_status in ['RES', 'BUSY']:
                    messages.error(request, "Responder is already busy.")
                else:
                    # Update Status
                    responder.duty_status = 'RES'
                    responder.save()

                    # Update Event (Latest responder gets linked directly)
                    event.responder = responder
                    event.status = 'in_progress'
                    event.save()

                    # Create Assignment Record (This is what AssignmentListView looks for!)
                    EventAssignment.objects.create(
                        role='responder',
                        status='active',
                        responder=responder,
                        emergency_event=event
                    )
                    messages.success(request, f"Assigned {responder.citizen.user_id.last_name}.")

            elif action == 'remove':
                # Cancel Assignment
                assignment = EventAssignment.objects.filter(
                    emergency_event=event, responder=responder, status='active'
                ).first()

                if assignment:
                    assignment.status = 'cancelled'
                    assignment.save()

                    responder.duty_status = 'ON'
                    responder.save()
                    messages.warning(request, "Responder removed.")
                else:
                    messages.error(request, "Could not find active assignment to remove.")

            return redirect(f'/emergency/responder-availability/?event_id={event_id}')

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, "Assignment failed.")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')