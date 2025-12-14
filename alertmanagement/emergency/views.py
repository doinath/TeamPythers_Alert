from django.db import connection
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User as DjangoAuthUser
from django.db.models import Q

# Import your models
from account.models import User as AccountUser, Citizen, Responder, ContactInfo
from .models import EmergencyEvent, EventAssignment, MedicalCondition


# --- HELPER FUNCTION FOR DEV MODE ---
def get_dev_user(original_user, dev_id):
    if dev_id:
        try:
            target_user = AccountUser.objects.get(user_id=dev_id)
            return target_user.account
        except Exception:
            return original_user
    return original_user


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

    def get(self, request, dev_id=None):
        # 1. Handle Dev Mode User
        context_user = get_dev_user(request.user, dev_id)

        events = EmergencyEvent.objects.select_related('userID__user_id').all().order_by('-created_at')

        context = {
            'events': events,
            'user': context_user  # Overrides request.user in template
        }
        return render(request, self.template_name, context)


class AssignmentListView(View):
    template_name = "EventAssignment/assignment_list.html"

    def get(self, request, dev_id=None):
        # Priority: URL param (dev_id) > GET param (?dev_id=)
        target_dev_id = dev_id or request.GET.get('dev_id')

        context_user = request.user  # Default to logged-in user
        responder_profile = None
        assignments = []

        if target_dev_id:
            try:
                target_account_user = AccountUser.objects.get(user_id=target_dev_id)
                context_user = target_account_user.account
                responder_profile = target_account_user.citizen_profile.responder_profile
            except AccountUser.DoesNotExist:
                messages.error(request, f"User with ID {target_dev_id} not found.")
            except Exception:
                messages.error(request, f"User ID {target_dev_id} does not have a Responder profile.")

        elif request.user.is_authenticated:
            try:
                responder_profile = request.user.custom_profile.citizen_profile.responder_profile
                context_user = request.user
            except AttributeError:
                messages.error(request, "User is authenticated but does not have a Responder profile.")
        if responder_profile:
            assignments = EventAssignment.objects.filter(
                responder=responder_profile
            ).select_related(
                'emergency_event__userID__user_id'
            ).order_by('-assigned_at')
        else:
            if not target_dev_id:
                messages.info(request, "Please log in or use the /viewlist/7/ url to view assignments.")

        context = {
            'assignments': assignments,
            'responder': responder_profile,
            'user': context_user
        }
        return render(request, self.template_name, context)


# --- VIEW FOR MEDICAL RECORD ---

class MedicalRecordView(View):
    template_name = "EmergencyEvent/medical_record.html"

    def get(self, request, event_id=None):
        # Fallback if no event_id is provided (just to prevent crashes, though URL enforces it usually)
        if not event_id:
            messages.error(request, "No Event ID specified for medical records.")
            return redirect('EmergencyEvent:event_list')

        event = get_object_or_404(EmergencyEvent, pk=event_id)
        citizen = event.userID
        user_profile = citizen.user_id
        medical_conditions = MedicalCondition.objects.filter(user_id=user_profile)
        contact_numbers = ContactInfo.objects.filter(user_id=user_profile)

        context = {
            'event': event,
            'citizen': citizen,
            'user_profile': user_profile,
            'medical_conditions': medical_conditions,
            'contact_numbers': contact_numbers,
            # We don't necessarily need dev_id swap here unless you want to see who is viewing the record
            'user': request.user
        }
        return render(request, self.template_name, context)


# --- DETAILS VIEWS ---

class EventDetailsResponderView(View):
    template_name = "EmergencyEvent/event_details_responder.html"

    def get(self, request, event_id=None, dev_id=None):
        # 1. Handle Dev Mode User
        context_user = get_dev_user(request.user, dev_id)

        event = None
        if event_id:
            event = get_object_or_404(EmergencyEvent, pk=event_id)
        else:
            event = EmergencyEvent.objects.order_by('-created_at').first()
            if not event:
                messages.error(request, "No events found.")
                return redirect('EmergencyEvent:event_list')

        context = {
            'event': event,
            'user': context_user
        }
        return render(request, self.template_name, context)

    def post(self, request, event_id=None, dev_id=None):
        if not event_id:
            return redirect('EmergencyEvent:event_list')

        event = get_object_or_404(EmergencyEvent, pk=event_id)
        action = request.POST.get('action')
        current_status = str(event.status).lower().strip()

        if action == 'acknowledge':
            if current_status in ['reported', 'pending', 'in_progress']:
                event.status = 'on the way'
                event.save()
                messages.success(request, "Status updated: ON THE WAY")
        elif action == 'on_scene':
            if current_status in ['reported', 'pending', 'in_progress', 'on the way', 'on_the_way']:
                event.status = 'on scene'
                event.save()
                messages.success(request, "Status updated: ON SCENE")
        elif action == 'resolved':
            if current_status not in ['completed', 'resolved', 'closed']:
                try:
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_ResolveEvent', [event.eventID])
                    messages.success(request, "Event Resolved (SP Executed). You are now AVAILABLE.")
                except Exception as e:
                    messages.error(request, f"Error resolving event: {e}")
            else:
                messages.info(request, "Event is already completed.")

        # Redirect back to the same view (preserving dev_id if it existed in the URL logic)
        # Note: 'redirect' usually takes the view name and args.
        if dev_id:
            return redirect('EmergencyEvent:event_details_responder_dev', event_id=event.eventID, dev_id=dev_id)
        return redirect('EmergencyEvent:event_details_responder', event_id=event.eventID)


class EventDetailsAuthorityView(View):
    template_name = "EmergencyEvent/event_details_authority.html"

    def get(self, request, event_id=None, dev_id=None):
        # 1. Handle Dev Mode User
        context_user = get_dev_user(request.user, dev_id)

        event = None
        if event_id:
            event = get_object_or_404(EmergencyEvent, pk=event_id)
        else:
            event = EmergencyEvent.objects.order_by('-created_at').first()

        context = {
            'event': event,
            'user': context_user
        }
        return render(request, self.template_name, context)


# --- ACTION VIEWS ---

class CreateReportView(View):
    template_name = "EmergencyEvent/report_form.html"

    def get(self, request, dev_id=None):
        # 1. Handle Dev Mode User
        context_user = get_dev_user(request.user, dev_id)
        return render(request, self.template_name, {'user': context_user})

    def post(self, request, dev_id=None):
        # We need the context user for the form logic too
        context_user = get_dev_user(request.user, dev_id)

        try:
            citizen_obj = None
            # Use context_user to determine the citizen, not just request.user
            if context_user.is_authenticated:
                try:
                    custom_user = context_user.custom_profile
                    citizen_obj = custom_user.citizen_profile
                except Exception:
                    messages.error(request, "Error: Your account is not linked to a Citizen profile.")
                    return render(request, self.template_name, {'user': context_user})
            else:
                # Default fallback for unauthenticated users
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

            emergency_type = request.POST.get('emergencyType', '')
            other_specified = request.POST.get('other_specified', '')
            reporting_for_others = request.POST.get('reportingForOthers', 'no')
            gps_location = request.POST.get('gps_location', '')
            fname = request.POST.get('p_fname', '')
            mname = request.POST.get('p_mname', '')
            lname = request.POST.get('p_lname', '')
            patient_full_name = f"{fname} {mname} {lname}".strip()
            address_text = request.POST.get('address_text', 'No Address Provided')
            description_raw = request.POST.get('description', '')
            description_for_sp = f"{description_raw}\n[ADDRESS: {address_text}]"

            # --- Call the Stored Procedure ---
            with connection.cursor() as cursor:
                cursor.callproc('sp_SubmitEmergencyReport', [
                    citizen_obj.pk,
                    emergency_type,
                    other_specified,
                    reporting_for_others,
                    patient_full_name,
                    description_for_sp,
                    gps_location
                ])

            messages.success(request, "Report Submitted Successfully via Secure SP!")
            return redirect('EmergencyEvent:report_form')

        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            messages.error(request, f"Submission Failed: {str(e)}")
            return render(request, self.template_name, {'user': context_user})


class ResponderAvailabilityView(View):
    template_name = "EventAssignment/responder_availability_emergency.html"

    def get(self, request, dev_id=None):
        # 1. Handle Dev Mode User
        context_user = get_dev_user(request.user, dev_id)

        event_id = request.GET.get('event_id')
        responders = Responder.objects.select_related('citizen__user_id').all()
        assigned_ids = []
        if event_id:
            assigned_ids = list(EventAssignment.objects.filter(
                emergency_event_id=event_id,
                status='active'
            ).values_list('responder_id', flat=True))
        total_count = responders.count()
        assigned_count = responders.filter(duty_status__in=['RES', 'BUSY']).count()

        context = {
            'responders': responders,
            'total_count': total_count,
            'assigned_count': assigned_count,
            'event_id': event_id,
            'assigned_ids': assigned_ids,
            'user': context_user
        }
        return render(request, self.template_name, context)

    def post(self, request, dev_id=None):
        # Note: POST usually doesn't need to spoof the user unless we are logging who performed the action.
        # But if you want to redirect back to the dev URL, you'd need to handle that here.

        action = request.POST.get('action')
        responder_id = request.POST.get('responder_id')
        event_id = request.POST.get('event_id')

        if not responder_id or not event_id:
            messages.error(request, "Missing information.")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')

        try:
            with connection.cursor() as cursor:
                if action == 'assign':
                    responder = Responder.objects.get(pk=responder_id)
                    if responder.duty_status in ['RES', 'BUSY']:
                        messages.error(request, "Responder is already busy.")
                    else:
                        cursor.callproc('sp_AssignResponder', [responder_id, event_id])
                        messages.success(request, "Responder Assigned Successfully via SP.")

                elif action == 'remove':
                    cursor.callproc('sp_RemoveResponder', [responder_id, event_id])
                    messages.warning(request, "Responder Removed via SP.")

            return redirect(f'/emergency/responder-availability/?event_id={event_id}')

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, f"Operation failed: {e}")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')