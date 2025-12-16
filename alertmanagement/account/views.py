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
from django.core.files.storage import default_storage
from django.db import connection


# ---------------------------
#  INDEX / LOGIN
# ---------------------------
class IndexView(View):
    def get(self, request):
        return render(request, "index.html")

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate using Django's built-in User
        auth_user = authenticate(request, username=email, password=password)

        if auth_user is not None:
            login(request, auth_user)

            try:
                # Get related custom profile
                custom_user = auth_user.custom_profile

                # --- LOG SYSTEM ACTION (Via Stored Procedure) ---

                # 1. Get the readable role name (e.g., "Citizen", "Authority", "Responder")
                # get_role_display() handles the conversion from 'citizen' to 'Citizen' based on your model choices
                user_role = custom_user.get_role_display()

                # 2. Prepare data for the Stored Procedure
                log_user_id = custom_user.user_id
                log_action = "User Login"
                # 3. Include the role in the detail message
                log_detail = f"{user_role} {custom_user.first_name} {custom_user.last_name} ({auth_user.email}) logged in successfully."

                # 4. Execute the Stored Procedure
                with connection.cursor() as cursor:
                    cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

            except CustomUser.DoesNotExist:
                messages.error(request, "Custom profile not found.")
                return render(request, "index.html")
            except Exception as e:
                print(f"Error logging system action: {e}")

            # Redirect based on role
            if hasattr(custom_user, 'role') and custom_user.role == "authority":
                return redirect("account:authority_dashboard")
            elif hasattr(custom_user, 'role') and custom_user.role == "responder":
                return redirect("account:responder_dashboard")
            else:
                return redirect("account:citizen_dashboard")
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
            # Removed local import of SystemLog model

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
                    phone_number=phone_number,
                    role='citizen'  # Explicitly setting role
                )

                Citizen.objects.create(user_id=custom_user)

                # --- LOG SYSTEM ACTION (Via Stored Procedure) ---
                log_user_id = custom_user.user_id
                log_action = "Account Registration"
                # Specifying it is a Citizen account
                log_detail = f"New Citizen account created for {first_name} {last_name} ({email})."

                with connection.cursor() as cursor:
                    cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

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
            # Removed local import of SystemLog

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

                # --- LOG SYSTEM ACTION (Via Stored Procedure) ---
                user_role = custom_user.get_role_display()  # Likely "Citizen"
                log_user_id = custom_user.user_id
                log_action = "Profile Completion"
                log_detail = f"{user_role} {custom_user.first_name} completed initial profile setup."

                with connection.cursor() as cursor:
                    cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

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
        try:
            # Access the custom profile linked to the Auth User
            user_profile = request.user.custom_profile

            # Fetch related data
            medical_conditions = MedicalCondition.objects.filter(user_id=user_profile)
            contacts = ContactInfo.objects.filter(user_id=user_profile)
            gov_ids = GovernmentDocument.objects.filter(user_id=user_profile)

            context = {
                'user': user_profile,
                'medical_conditions': medical_conditions,
                'contacts': contacts,
                'gov_ids': gov_ids,
            }
            return render(request, "citizen_profile.html", context)
        except CustomUser.DoesNotExist:
            messages.error(request, "Profile not found.")
            return redirect('account:citizen_dashboard')

    def post(self, request):
        try:
            user_profile = request.user.custom_profile

            # Local import to avoid circular dependency
            from system_log.models import SystemLog

            with transaction.atomic():
                # 1. Update Personal Details & Address
                user_profile.phone_number = request.POST.get('phone_number')
                user_profile.email_address = request.POST.get('email_address')
                user_profile.date_of_birth = request.POST.get('date_of_birth')
                user_profile.gender = request.POST.get('gender')
                user_profile.street = request.POST.get('street')
                user_profile.municipality = request.POST.get('municipality')
                user_profile.city = request.POST.get('city')
                user_profile.province = request.POST.get('province')
                user_profile.zip_code = request.POST.get('zip_code')
                user_profile.save()

                # 2. Update Medical Info
                MedicalCondition.objects.filter(user_id=user_profile).delete()
                conditions = request.POST.getlist('medical_condition')
                notes = request.POST.getlist('medical_notes')

                for i in range(len(conditions)):
                    if conditions[i].strip():
                        MedicalCondition.objects.create(
                            user_id=user_profile,
                            condition_name=conditions[i],
                            notes=notes[i] if i < len(notes) else ""
                        )

                # 3. Update Emergency Contacts
                ContactInfo.objects.filter(user_id=user_profile).delete()
                rels = request.POST.getlist('contact_relationship')
                nums = request.POST.getlist('contact_number')

                for i in range(len(rels)):
                    if rels[i].strip() and nums[i].strip():
                        ContactInfo.objects.create(
                            user_id=user_profile,
                            relationship=rels[i],
                            contact_info=nums[i]
                        )

                # 4. Handle Government IDs
                new_types = request.POST.getlist('new_id_type')
                new_numbers = request.POST.getlist('new_id_number')
                new_files = request.FILES.getlist('new_id_file')

                for i in range(len(new_types)):
                    if new_types[i] and new_numbers[i]:
                        current_file = new_files[i] if i < len(new_files) else None
                        if current_file:
                            GovernmentDocument.objects.create(
                                user_id=user_profile,
                                id_type=new_types[i],
                                id_number=new_numbers[i],
                                filepath=current_file,
                                status='PENDING'
                            )

                # --- LOG SYSTEM ACTION (Profile Update) ---
                SystemLog.objects.create(
                    action="Profile Update",
                    detail=f"User {user_profile.first_name} {user_profile.last_name} updated their profile information.",
                    user_id=user_profile
                )

            messages.success(request, "Profile updated successfully.")
            return redirect('account:citizen_profile')

        except Exception as e:
            print(f"Error Saving Profile: {e}")
            messages.error(request, "An error occurred while saving profile.")
            return redirect('account:citizen_profile')


class ResponderProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "responder_profile.html")


class AuthorityProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # 1. Access the main custom profile linked to the Auth User
            user_profile = request.user.custom_profile

            # 2. Access the Authority-specific details
            # We assume Authority is linked through Citizen -> Authority
            authority_details = Authority.objects.get(
                citizen__user_id=user_profile
            )

            # 3. Fetch related data
            medical_conditions = MedicalCondition.objects.filter(user_id=user_profile)
            contacts = ContactInfo.objects.filter(user_id=user_profile)
            gov_ids = GovernmentDocument.objects.filter(user_id=user_profile)

            context = {
                'authority_user': user_profile,  # General User data (Name, Contact, Address, DOB, Gender)
                'authority_details': authority_details,  # Authority-specific data (Agency, Jurisdiction)
                'medical_conditions': medical_conditions,
                'emergency_contacts': contacts,
                'government_ids': gov_ids,
            }
            return render(request, "authority_profile.html", context)

        except Authority.DoesNotExist:
            messages.error(request, "Authority profile details not found. Please ensure your application is approved.")
            return redirect('account:authority_dashboard')
        except CustomUser.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect('account:index')  # Redirect to index or login if base profile is missing


# ---------------------------
#  APPLY VIEWS
# ---------------------------
# ---------------------------------------------------------
#  APPLY VIEWS (Corrected & Consolidated)
# ---------------------------------------------------------

class ApplyResponderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            # Access the citizen profile linked to the logged-in user
            citizen = request.user.custom_profile.citizen_profile

            # Check if this citizen has already applied
            if hasattr(citizen, 'responder_profile'):
                messages.warning(request, "You have already applied as a Responder.")
                return redirect('account:citizen_dashboard')

            # Use atomic transaction to ensure data integrity
            with transaction.atomic():
                # 1. Create the Responder Profile
                Responder.objects.create(
                    citizen=citizen,
                    department_unit=request.POST.get('department_unit'),
                    role=request.POST.get('role'),
                    service_area=request.POST.get('service_area'),
                    duty_status='OFF'
                )

                # 2. Handle ID Document Upload
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

                # 3. Log System Action via Stored Procedure
                custom_user = request.user.custom_profile

                # FIX: Use the explicit primary key 'user_id' for consistency
                log_user_id = custom_user.user_id

                log_action = "Responder Application Submitted"
                log_detail = f"User {custom_user.first_name} applied for Responder role."

                with connection.cursor() as cursor:
                    # 'callproc' safely handles the SQL syntax for stored procedures
                    cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

            messages.success(request, "Responder application submitted successfully!")
            return redirect('account:citizen_dashboard')

        except Exception as e:
            # Print detailed error to console for debugging
            print(f"Error in ApplyResponderView: {e}")
            messages.error(request, f"Error submitting application: {e}")
            return redirect('account:citizen_dashboard')


class ApplyAuthorityView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            # Access the citizen profile
            citizen = request.user.custom_profile.citizen_profile

            # Check if already applied (ensure related_name in models matches 'authority_profile')
            if hasattr(citizen, 'authority_profile'):
                messages.warning(request, "You have already applied as an Authority.")
                return redirect('account:citizen_dashboard')

            with transaction.atomic():
                # 1. Create Authority Profile
                Authority.objects.create(
                    citizen=citizen,
                    agency_name=request.POST.get('agency_name'),
                    jurisdiction_area=request.POST.get('jurisdiction_area'),
                    is_verified=False
                )

                # 2. Handle ID Document Upload
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

                # 3. Log System Action via Stored Procedure
                custom_user = request.user.custom_profile

                # FIX: Use the explicit primary key 'user_id' for consistency
                log_user_id = custom_user.user_id

                log_action = "Authority Application Submitted"
                log_detail = f"User {custom_user.first_name} applied for Authority role."

                with connection.cursor() as cursor:
                    cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

            messages.success(request, "Authority application submitted successfully!")
            return redirect('account:citizen_dashboard')

        except Exception as e:
            print(f"Error in ApplyAuthorityView: {e}")
            messages.error(request, f"Error submitting application: {e}")
            return redirect('account:citizen_dashboard')


# ---------------------------
#  NEW LOCATION PIN VIEW
# ---------------------------
class LocationPinView(LoginRequiredMixin, View):
    def post(self, request):
        # We need to ensure the user is logged in (LoginRequiredMixin handles the redirect)
        custom_user = request.user.custom_profile

        # We grab the location data from the POST request, but only use it for logging detail
        latitude = request.POST.get('latitude', 'N/A')
        longitude = request.POST.get('longitude', 'N/A')

        try:
            # --- LOG SYSTEM ACTION (Via Stored Procedure) ---
            log_user_id = custom_user.user_id
            log_action = "Geolocation Pinned"

            # Log detail includes the coordinates, satisfying the "just posting in the database" requirement
            log_detail = f"User {custom_user.first_name} manually pinned location. Coords: Lat={latitude}, Lon={longitude}."

            with connection.cursor() as cursor:
                cursor.callproc('LogSystemAction', [log_user_id, log_action, log_detail])

            # Use Django messages to confirm the action, which the dashboard can display
            messages.info(request, "Location pinned and action logged successfully.")

        except Exception as e:
            print(f"Error logging location pin: {e}")
            messages.error(request, f"Error logging location pin: {e}")

        # Redirect back to the dashboard to show the map and the message
        return redirect('account:citizen_dashboard')