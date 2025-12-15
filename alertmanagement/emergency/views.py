from django.db import connection
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User as DjangoAuthUser
from django.core.exceptions import ObjectDoesNotExist

# Import your models
from account.models import User as AccountUser, Citizen, Responder, ContactInfo
from .models import EmergencyEvent, EventAssignment, MedicalCondition


# --- HELPER 1: FETCH DEV USER SAFELY ---
def get_dev_user(original_user, dev_id):
    if dev_id:
        try:
            target_user = AccountUser.objects.defer(
                'email_address', 'phone_number', 'role'
            ).get(user_id=dev_id)
            if target_user.account:
                return target_user.account
        except Exception:
            return original_user
    return original_user


# --- HELPER 2: FETCH EVENTS SAFELY ---
def get_safe_event_queryset():
    return EmergencyEvent.objects.select_related(
        'userID',
        'userID__user_id'
    ).defer(
        'userID__user_id__email_address',
        'userID__user_id__phone_number',
        'userID__user_id__role'
    )


# --- HELPER 3: FETCH CONTACT SAFELY ---
def get_safe_contact(user_obj):
    """Fetches contact info while ignoring the missing 'relationship' column."""
    try:
        return ContactInfo.objects.defer('relationship').filter(user_id=user_obj).first()
    except Exception:
        return None


class HomepageView(View):
    template_name = "EmergencyEvent/index.html"

    def get(self, request): return render(request, self.template_name)


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
        context_user = get_dev_user(request.user, dev_id)
        events = get_safe_event_queryset().all().order_by('-created_at')
        context = {'events': events, 'user': context_user}
        return render(request, self.template_name, context)


class AssignmentListView(View):
    template_name = "EventAssignment/assignment_list.html"

    def get(self, request, dev_id=None):
        target_dev_id = dev_id or request.GET.get('dev_id')
        context_user = request.user
        responder_profile = None
        assignments = []

        if target_dev_id:
            try:
                target_account_user = AccountUser.objects.defer(
                    'email_address', 'phone_number', 'role'
                ).get(user_id=target_dev_id)

                if target_account_user.account:
                    context_user = target_account_user.account

                try:
                    if hasattr(target_account_user, 'citizen_profile'):
                        citizen = target_account_user.citizen_profile
                        if hasattr(citizen, 'responder_profile'):
                            responder_profile = citizen.responder_profile
                        else:
                            messages.warning(request, f"User {target_dev_id} is not a Responder.")
                    else:
                        messages.error(request, f"User {target_dev_id} has no Citizen profile.")
                except ObjectDoesNotExist:
                    messages.error(request, f"Profile data missing for User {target_dev_id}.")

            except AccountUser.DoesNotExist:
                messages.error(request, f"User with ID {target_dev_id} not found.")

        elif request.user.is_authenticated:
            try:
                custom_profile = request.user.custom_profile
                if hasattr(custom_profile, 'citizen_profile') and hasattr(custom_profile.citizen_profile,
                                                                          'responder_profile'):
                    responder_profile = custom_profile.citizen_profile.responder_profile
            except AttributeError:
                pass

        if responder_profile:
            assignments = EventAssignment.objects.filter(
                responder=responder_profile
            ).select_related(
                'emergency_event',
                'emergency_event__userID__user_id'
            ).defer(
                'emergency_event__userID__user_id__email_address',
                'emergency_event__userID__user_id__phone_number',
                'emergency_event__userID__user_id__role'
            ).order_by('-assigned_at')
        else:
            if not target_dev_id and not assignments:
                messages.info(request, "Please log in or use the /viewlist/8/ url.")

        context = {'assignments': assignments, 'responder': responder_profile, 'user': context_user}
        return render(request, self.template_name, context)


# --- VIEW FOR MEDICAL RECORD (UPDATED) ---

class MedicalRecordView(View):
    template_name = "EmergencyEvent/medical_record.html"

    # Updated to accept dev_id
    def get(self, request, event_id=None, dev_id=None):
        if not event_id:
            messages.error(request, "No Event ID specified.")
            return redirect('EmergencyEvent:event_list')

        # FIX: Get the simulated user so the navbar name persists
        context_user = get_dev_user(request.user, dev_id)

        event = get_object_or_404(get_safe_event_queryset(), pk=event_id)
        citizen = event.userID
        user_profile = citizen.user_id

        # FIX: Defer relationship column
        medical_conditions = MedicalCondition.objects.filter(user_id=user_profile)
        contact_numbers = ContactInfo.objects.defer('relationship').filter(user_id=user_profile)

        context = {
            'event': event,
            'citizen': citizen,
            'user_profile': user_profile,
            'medical_conditions': medical_conditions,
            'contact_numbers': contact_numbers,
            'user': context_user # Pass the simulated user
        }
        return render(request, self.template_name, context)


# --- DETAILS VIEWS ---

class EventDetailsResponderView(View):
    template_name = "EmergencyEvent/event_details_responder.html"

    def get(self, request, event_id=None, dev_id=None):
        context_user = get_dev_user(request.user, dev_id)
        citizen_contact = None

        if event_id:
            event = get_object_or_404(get_safe_event_queryset(), pk=event_id)
        else:
            event = get_safe_event_queryset().order_by('-created_at').first()
            if not event:
                return redirect('EmergencyEvent:event_list')

        if event:
            citizen_contact = get_safe_contact(event.userID.user_id)

        context = {'event': event, 'user': context_user, 'citizen_contact': citizen_contact}
        return render(request, self.template_name, context)

    def post(self, request, event_id=None, dev_id=None):
        if not event_id: return redirect('EmergencyEvent:event_list')
        event = get_object_or_404(get_safe_event_queryset(), pk=event_id)
        action = request.POST.get('action')

        if action == 'acknowledge':
            if event.status in ['reported', 'pending', 'in_progress']:
                event.status = 'on the way'
                event.save()
                messages.success(request, "Status: ON THE WAY")
        elif action == 'on_scene':
            if event.status in ['reported', 'pending', 'in_progress', 'on the way', 'on_the_way']:
                event.status = 'on scene'
                event.save()
                messages.success(request, "Status: ON SCENE")
        elif action == 'resolved':
            if event.status not in ['completed', 'resolved', 'closed']:
                try:
                    with connection.cursor() as cursor:
                        cursor.callproc('sp_ResolveEvent', [event.eventID])
                    messages.success(request, "Event Resolved.")
                except Exception as e:
                    messages.error(request, f"Error: {e}")

        if dev_id:
            return redirect('EmergencyEvent:event_details_responder_dev', event_id=event.eventID, dev_id=dev_id)
        return redirect('EmergencyEvent:event_details_responder', event_id=event.eventID)


class EventDetailsAuthorityView(View):
    template_name = "EmergencyEvent/event_details_authority.html"

    def get(self, request, event_id=None, dev_id=None):
        context_user = get_dev_user(request.user, dev_id)
        citizen_contact = None

        if event_id:
            event = get_object_or_404(get_safe_event_queryset(), pk=event_id)
        else:
            event = get_safe_event_queryset().order_by('-created_at').first()

        if event:
            citizen_contact = get_safe_contact(event.userID.user_id)

        context = {'event': event, 'user': context_user, 'citizen_contact': citizen_contact}
        return render(request, self.template_name, context)


# --- ACTION VIEWS ---

class CreateReportView(View):
    template_name = "EmergencyEvent/report_form.html"

    def get(self, request, dev_id=None):
        context_user = get_dev_user(request.user, dev_id)
        reporter_name = "Guest"
        if context_user and context_user.is_authenticated:
            try:
                if hasattr(context_user, 'custom_profile'):
                    p = AccountUser.objects.defer('email_address', 'phone_number', 'role').get(account=context_user)
                    reporter_name = f"{p.first_name} {p.last_name}"
            except Exception:
                pass
        return render(request, self.template_name, {'user': context_user, 'reporter_name': reporter_name})

    def post(self, request, dev_id=None):
        context_user = get_dev_user(request.user, dev_id)
        citizen_obj = None
        try:
            if dev_id:
                acc = AccountUser.objects.defer('email_address', 'phone_number', 'role').get(user_id=dev_id)
                if hasattr(acc, 'citizen_profile'): citizen_obj = acc.citizen_profile
            if not citizen_obj and context_user.is_authenticated:
                acc = AccountUser.objects.defer('email_address', 'phone_number', 'role').get(account=context_user)
                if hasattr(acc, 'citizen_profile'): citizen_obj = acc.citizen_profile
        except Exception as e:
            print(f"Profile fetch error: {e}")

        if not citizen_obj:
            try:
                auth_user, _ = DjangoAuthUser.objects.get_or_create(username='julian_dev',
                                                                    defaults={'first_name': 'Julian'})
                account_user, _ = AccountUser.objects.get_or_create(account=auth_user,
                                                                    defaults={'first_name': 'Julian'})
                citizen_obj, _ = Citizen.objects.get_or_create(user_id=account_user)
            except Exception:
                pass

        try:
            emergency_type = request.POST.get('emergencyType', '')
            other_specified = request.POST.get('other_specified', '')
            reporting_for_others = request.POST.get('reportingForOthers', 'no')
            gps_location = request.POST.get('gps_location', '')
            severity_input = request.POST.get('severity', 'low')

            fname = request.POST.get('p_fname', '')
            mname = request.POST.get('p_mname', '')
            lname = request.POST.get('p_lname', '')
            patient_full_name = f"{fname} {mname} {lname}".strip()

            address_text = request.POST.get('address_text', 'No Address Provided')
            description_raw = request.POST.get('description', '')
            description_for_sp = f"{description_raw}\n[ADDRESS: {address_text}]"

            citizen_pk = citizen_obj.pk if citizen_obj else 1

            with connection.cursor() as cursor:
                cursor.callproc('sp_SubmitEmergencyReport', [
                    citizen_pk, emergency_type, other_specified,
                    reporting_for_others, patient_full_name,
                    description_for_sp, gps_location, severity_input
                ])

            messages.success(request, "Report Submitted!")
            if dev_id:
                return redirect('EmergencyEvent:report_form_dev', dev_id=dev_id)
            else:
                return redirect('EmergencyEvent:report_form')

        except Exception as e:
            messages.error(request, f"Submission Failed: {str(e)}")
            return render(request, self.template_name, {'user': context_user, 'reporter_name': "Guest"})


class ResponderAvailabilityView(View):
    template_name = "EventAssignment/responder_availability_emergency.html"

    def get(self, request, dev_id=None):
        context_user = get_dev_user(request.user, dev_id)
        event_id = request.GET.get('event_id')

        responders = Responder.objects.select_related('citizen__user_id').defer(
            'citizen__user_id__email_address',
            'citizen__user_id__phone_number',
            'citizen__user_id__role'
        ).all()

        assigned_ids = []
        if event_id:
            assigned_ids = list(EventAssignment.objects.filter(
                emergency_event_id=event_id, status='active'
            ).values_list('responder_id', flat=True))

        context = {
            'responders': responders,
            'total_count': responders.count(),
            'assigned_count': responders.filter(duty_status__in=['RES', 'BUSY']).count(),
            'event_id': event_id,
            'assigned_ids': assigned_ids,
            'user': context_user
        }
        return render(request, self.template_name, context)

    def post(self, request, dev_id=None):
        action = request.POST.get('action')
        responder_id = request.POST.get('responder_id')
        event_id = request.POST.get('event_id')

        if not responder_id or not event_id:
            messages.error(request, "Missing information.")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')

        try:
            with connection.cursor() as cursor:
                if action == 'assign':
                    cursor.callproc('sp_AssignResponder', [responder_id, event_id])
                    messages.success(request, "Responder Assigned.")
                elif action == 'remove':
                    cursor.callproc('sp_RemoveResponder', [responder_id, event_id])
                    messages.warning(request, "Responder Removed.")

            if dev_id:
                return redirect(f'/emergency/responder-availability/{dev_id}/?event_id={event_id}')
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')
        except Exception as e:
            messages.error(request, f"Operation failed: {e}")
            return redirect(f'/emergency/responder-availability/?event_id={event_id}')