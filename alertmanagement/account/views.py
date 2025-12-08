from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User as AuthUser
from .models import User as CustomUser, Citizen, ContactInfo, Responder, Authority, Notification
from emergency.models import MedicalCondition
from verification.models import GovernmentDocument


# ---------------------------
#  INDEX / LOGIN
# ---------------------------
class IndexView(View):
    def get(self, request):
        return render(request, "index.html")

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('account:citizen_dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "index.html")


# ---------------------------
#  REGISTER
# ---------------------------
class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        first_name = request.POST.get('firstName')
        middle_name = request.POST.get('middleName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        phone_number = request.POST.get('phoneNumber')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        context = {
            'firstName': first_name,
            'middleName': middle_name,
            'lastName': last_name,
            'email': email,
            'phoneNumber': phone_number
        }

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, "register.html", context)

        if AuthUser.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered.')
            return render(request, "register.html", context)

        try:
            with transaction.atomic():
                auth_user = AuthUser.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                custom_user = CustomUser.objects.create(
                    account=auth_user,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    email_address=email,
                    phone_number=phone_number
                )

                Citizen.objects.create(user_id=custom_user)

            login(request, auth_user)
            messages.success(request, 'Account created successfully! Please complete your profile.')
            return redirect('account:citizen_profile_completion')

        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
            return render(request, "register.html", context)


# ---------------------------
#  CITIZEN PROFILE COMPLETION
# ---------------------------
class CitizenProfileCompletionView(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):
        return render(request, "citizen_profile_completion.html")

    def post(self, request):
        try:
            custom_user = request.user.custom_profile
        except AttributeError:
            messages.error(request, "User profile not found. Please contact support.")
            return redirect('account:index')

        try:
            with transaction.atomic():
                dob = request.POST.get('dob')
                if dob:
                    custom_user.date_of_birth = dob

                custom_user.gender = request.POST.get('gender')
                custom_user.street = request.POST.get('street')
                custom_user.municipality = request.POST.get('barangay')
                custom_user.city = request.POST.get('city')
                custom_user.province = request.POST.get('province')
                custom_user.zip_code = request.POST.get('zipCode')
                custom_user.country = "Philippines"
                custom_user.save()

                # Contacts
                ContactInfo.objects.filter(user_id=custom_user).delete()
                contact_count = int(request.POST.get('contact_count', 0))
                for i in range(1, contact_count + 1):
                    role = request.POST.get(f'contact_role_{i}')
                    phone = request.POST.get(f'contact_phone_{i}')
                    if role and phone:
                        ContactInfo.objects.create(
                            user_id=custom_user,
                            relationship=role,
                            contact_info=phone
                        )

                # Medical Conditions
                MedicalCondition.objects.filter(user_id=custom_user).delete()
                medical_count = int(request.POST.get('medical_count', 0))
                for i in range(1, medical_count + 1):
                    cond_name = request.POST.get(f'condition_name_{i}')
                    cond_notes = request.POST.get(f'condition_notes_{i}')
                    if cond_name:
                        MedicalCondition.objects.create(
                            user_id=custom_user,
                            condition_name=cond_name,
                            notes=cond_notes if cond_notes else ""
                        )

                # Government IDs
                id_count = int(request.POST.get('id_count', 0))
                for i in range(1, id_count + 1):
                    id_type_val = request.POST.get(f'id_type_{i}')
                    id_number_val = request.POST.get(f'id_number_{i}')
                    id_file_val = request.FILES.get(f'id_file_{i}')

                    if id_type_val == 'other':
                        id_type_val = request.POST.get(f'id_type_other_{i}')

                    if id_type_val and id_number_val and id_file_val:
                        GovernmentDocument.objects.create(
                            user_id=custom_user,
                            id_type=id_type_val,
                            id_number=id_number_val,
                            filepath=id_file_val,
                            status='PENDING'
                        )

            messages.success(request, 'Profile completed successfully! Welcome to your Dashboard.')
            return redirect('account:citizen_dashboard')

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, "citizen_profile_completion.html")


# ---------------------------
#  DASHBOARDS
# ---------------------------
class CitizenDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        custom_user = CustomUser.objects.get(account=request.user)
        approval_alert = False

        notifications = Notification.objects.filter(user=custom_user, is_read=False)
        for note in notifications:
            if "authority" in note.message.lower() and "approved" in note.message.lower():
                approval_alert = True
                note.is_read = True
                note.save()
                break

        return render(request, "citizen_dashboard.html", {"approval_alert": approval_alert})


class ResponderDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "responder_dashboard.html")


class AuthorityDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "authority_dashboard.html")


# ---------------------------
#  PROFILE VIEWS
# ---------------------------
class CitizenProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "citizen_profile.html")


class ResponderProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "responder_profile.html")


class AuthorityProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "authority_profile.html")


# ---------------------------
#  APPLY VIEWS
# ---------------------------
class ApplyResponderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            citizen = request.user.custom_profile.citizen_profile
            if hasattr(citizen, 'responder_profile'):
                messages.warning(request, "You have already applied as a Responder.")
                return redirect('account:citizen_dashboard')

            with transaction.atomic():
                Responder.objects.create(
                    citizen=citizen,
                    department_unit=request.POST.get('department_unit'),
                    role=request.POST.get('role'),
                    service_area=request.POST.get('service_area'),
                    duty_status='OFF'
                )

                id_type = request.POST.get('id_type')
                id_number = request.POST.get('id_number')
                id_file = request.FILES.get('id_file')

                if id_type and id_number and id_file:
                    GovernmentDocument.objects.create(
                        user_id=request.user.custom_profile,
                        id_type=id_type,
                        id_number=id_number,
                        filepath=id_file,
                        status='PENDING'
                    )

            messages.success(request, "Responder application submitted successfully!")
            return redirect('account:citizen_dashboard')

        except Exception as e:
            messages.error(request, f"Error submitting application: {e}")
            return redirect('account:citizen_dashboard')


class ApplyAuthorityView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            citizen = request.user.custom_profile.citizen_profile
            if hasattr(citizen, 'authority'):
                messages.warning(request, "You have already applied as an Authority.")
                return redirect('account:citizen_dashboard')

            with transaction.atomic():
                Authority.objects.create(
                    citizen=citizen,
                    agency_name=request.POST.get('agency_name'),
                    jurisdiction_area=request.POST.get('jurisdiction_area')
                )

                id_type = request.POST.get('id_type')
                id_number = request.POST.get('id_number')
                id_file = request.FILES.get('id_file')

                if id_type and id_number and id_file:
                    GovernmentDocument.objects.create(
                        user_id=request.user.custom_profile,
                        id_type=id_type,
                        id_number=id_number,
                        filepath=id_file,
                        status='PENDING'
                    )

            messages.success(request, "Authority application submitted successfully!")
            return redirect('account:citizen_dashboard')

        except Exception as e:
            messages.error(request, f"Error submitting application: {e}")
            return redirect('account:citizen_dashboard')
