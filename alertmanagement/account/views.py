from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User as AuthUser
from django.contrib.auth import logout
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import FileSystemStorage
from emergency.models import MedicalCondition
import json
import os
from django.http import JsonResponse


# --- MODELS IMPORT ---
from .models import Authority
from .models import User as CustomUser, Citizen, ContactInfo, Responder, Notification
from emergency.models import MedicalCondition
from verification.models import GovernmentDocument


class IndexView(View):
    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = request.user.custom_profile
                role = user_profile.role

                # DOUBLE CHECK: If role is citizen but Authority is verified, update DB
                if role == 'citizen':
                    citizen_p = getattr(user_profile, 'citizen_profile', None)
                    if citizen_p:
                        auth_p = Authority.objects.filter(citizen=citizen_p).first()
                        if auth_p and auth_p.is_verified:
                            role = 'authority'
                            user_profile.role = 'authority'
                            user_profile.save()

                return self.redirect_based_on_role(role)
            except Exception as e:
                print(f"Login Check Error: {e}")
                return redirect('account:citizen_dashboard')
        return render(request, "index.html")

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # 1. Call sp_login_check
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL sp_login_check(%s, @status, @stored_hash, @auth_id, @role, @fname, @lname)
                """, [email])

                cursor.execute("SELECT @status, @stored_hash, @auth_id, @role")
                result = cursor.fetchone()

                status = result[0]
                stored_hash = result[1]
                auth_id = result[2]
                role = result[3]

            # 2. Verify Logic
            if status == 'FOUND' and check_password(password, stored_hash):
                # Retrieve the Django Auth User object to create the session
                user = AuthUser.objects.get(pk=auth_id)
                login(request, user)

                # Redirect based on the role returned by the SP
                return self.redirect_based_on_role(role)
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, "index.html")

        except Exception as e:
            print(f"Login Error: {e}")
            messages.error(request, "An error occurred during login.")
            return render(request, "index.html")

    def redirect_based_on_role(self, role):
        if role == "authority":
            return redirect("account:authority_dashboard")
        elif role == "responder":
            return redirect("account:responder_dashboard")
        else:
            return redirect("account:citizen_dashboard")

class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Password validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        # 2. Email duplicate check (Django auth_user)
        if AuthUser.objects.filter(email=email).exists() or AuthUser.objects.filter(username=email).exists():
            messages.error(request, "This email address is already registered.")
            return render(request, "register.html")

        # 3. Phone duplicate check (CUSTOM user table, NOT auth_user)
        if CustomUser.objects.filter(phone_number=phone).exists():
            messages.error(request, "This phone number is already associated with an account.")
            return render(request, "register.html")

        # 4. Hash password (Django-compatible)
        password_hash = make_password(password)

        try:
            # 5. Call stored procedure
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL sp_register_citizen(%s, %s, %s, %s, %s, %s, @status, @message)
                """, [
                    first_name,
                    middle_name,
                    last_name,
                    email,
                    phone,
                    password_hash
                ])

                cursor.execute("SELECT @status, @message")
                status, db_message = cursor.fetchone()

            # 6. Handle SP response
            if status == 'SUCCESS':
                # Auto-login
                user = authenticate(request, username=email, password=password)

                if user:
                    login(request, user)
                    messages.success(
                        request,
                        "Account created successfully! Please complete your profile."
                    )
                    return redirect('account:citizen_profile_completion')
                else:
                    messages.warning(
                        request,
                        "Account created, but auto-login failed. Please login manually."
                    )
                    return redirect('account:index')

            else:
                messages.error(request, db_message)
                return render(request, "register.html")

        except Exception as e:
            print(f"Registration Error: {e}")
            messages.error(request, "An unexpected error occurred during registration.")
            return render(request, "register.html")

class CitizenProfileCompletionView(LoginRequiredMixin, View):
    def get(self, request):
        # Render the profile completion template
        return render(request, "citizen_profile_completion.html")

    def post(self, request):
        # 1. GET THE CUSTOM USER ID
        try:
            # Check if the logged-in user has a linked custom profile
            if hasattr(request.user, 'custom_profile'):
                custom_user = request.user.custom_profile
                target_user_id = custom_user.user_id
            else:
                messages.error(request, "User profile not found. Please contact support.")
                return redirect("account:index")
        except Exception:
            messages.error(request, "Error accessing user profile.")
            return redirect("account:index")

        # --- 2. PERSONAL INFO ---
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        street = request.POST.get("street")
        barangay_input = request.POST.get("barangay")  # Will be stored as 'municipality'
        city = request.POST.get("city")
        province = request.POST.get("province")
        zip_code = request.POST.get("zipCode")

        # --- 3. EMERGENCY CONTACTS ---
        contact_count = int(request.POST.get("contact_count", 0))
        emergency_contacts = []

        for i in range(1, contact_count + 1):
            role = request.POST.get(f"contact_role_{i}")
            phone = request.POST.get(f"contact_phone_{i}")

            if not role or not phone:
                continue

            # Validate phone format
            if not phone.startswith("09"):
                messages.error(request, f"Phone number {phone} must start with 09.")
                return redirect("account:citizen_profile_completion")
            if len(phone) != 11:
                messages.error(request, f"Phone number {phone} length must be 11 digits.")
                return redirect("account:citizen_profile_completion")

            emergency_contacts.append({"role": role, "phone": phone})

        # Serialize to JSON
        emergency_contacts_json = json.dumps(emergency_contacts)

        # --- 4. MEDICAL INFORMATION ---
        medical_count = int(request.POST.get("medical_count", 0))
        medical_info = []

        for i in range(1, medical_count + 1):
            condition = request.POST.get(f"condition_name_{i}")
            notes = request.POST.get(f"condition_notes_{i}")

            if not condition:
                continue

            medical_info.append({"name": condition, "notes": notes if notes else ""})

        # Serialize to JSON
        medical_info_json = json.dumps(medical_info)

        # --- 5. GOVERNMENT IDs ---
        id_count = int(request.POST.get("id_count", 0))
        government_ids = []
        fs = FileSystemStorage()

        for i in range(1, id_count + 1):
            id_type_selection = request.POST.get(f"id_type_{i}")
            id_number = request.POST.get(f"id_number_{i}")
            id_file = request.FILES.get(f"id_file_{i}")

            if not id_type_selection or not id_number:
                continue

            # Handle "Other" text input
            final_id_type = id_type_selection
            if id_type_selection == "other":
                other_input = request.POST.get(f"id_type_other_{i}")
                if other_input:
                    final_id_type = other_input

            # Handle file upload
            file_path = ""
            if id_file:
                # Extract extension safely
                _, ext = os.path.splitext(id_file.name)
                ext = ext.replace('.', '')  # Clean dot

                safe_type = final_id_type.replace(" ", "_").lower()[:10]
                filename = f"ids/u{target_user_id}_{safe_type}_{i}.{ext}"

                # Delete existing file if it exists (to prevent duplicates)
                if fs.exists(filename):
                    fs.delete(filename)

                saved_filename = fs.save(filename, id_file)
                # Use .url() to get the relative path (e.g., /media/ids/...) which is safer for DB
                file_path = fs.url(saved_filename)

            government_ids.append({
                "type": final_id_type,
                "number": id_number,
                "file_path": file_path
            })

        # Serialize to JSON
        government_ids_json = json.dumps(government_ids)

        # --- 6. CALL STORED PROCEDURE ---
        status = 0
        message = "Unknown error"

        try:
            with connection.cursor() as cursor:
                # Execute the procedure
                cursor.execute("""
                    CALL sp_complete_citizen_profile(
                        %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, 
                        @p_status, @p_message
                    )
                """, [
                    target_user_id, dob, gender, street,
                    barangay_input,
                    city, province, zip_code,
                    emergency_contacts_json,
                    medical_info_json,
                    government_ids_json
                ])

                # Fetch output parameters
                cursor.execute("SELECT @p_status, @p_message")
                row = cursor.fetchone()
                if row:
                    status, message = row

        except Exception as e:
            # Catch DB errors
            messages.error(request, f"Database error: {str(e)}")
            return redirect("account:citizen_profile_completion")

        # --- 7. RETURN SUCCESS OR ERROR ---
        if status == 1:
            messages.success(request, message)
            # You might want to redirect to a dashboard or success page here
            return redirect("account:citizen_profile_completion")
        else:
            messages.error(request, message)
            return redirect("account:citizen_profile_completion")

class AuthorityDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Security: Double check verification status
        user_profile = request.user.custom_profile
        citizen_p = getattr(user_profile, 'citizen_profile', None)
        is_verified = False
        if citizen_p:
            auth_entry = Authority.objects.filter(citizen=citizen_p).first()
            if auth_entry and auth_entry.is_verified:
                is_verified = True

        if not is_verified:
            messages.error(request, "Access Denied.")
            return redirect('account:citizen_dashboard')

        return render(request, "authority_dashboard.html")

class CitizenDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            custom_user = request.user.custom_profile
        except AttributeError:
            return redirect('account:logout')

        # Logic: Check for Verification Notification
        approval_alert = False
        notifications = Notification.objects.filter(user_id=custom_user, is_read=False)
        for note in notifications:
            # If Admin verified, they created a notification. We check for it here.
            if "authority" in note.message.lower() and "verified" in note.message.lower():
                approval_alert = True
                note.is_read = True
                note.save()
                break

        # Check existing applications
        has_authority_app = False
        if hasattr(custom_user, 'citizen_profile'):
            has_authority_app = Authority.objects.filter(citizen=custom_user.citizen_profile).exists()
            # If we want to strictly use SPs or SQL for checking existence, we could.
            # But ORM is fine for simple SELECT checks.

        has_responder_app = hasattr(custom_user.citizen_profile, 'responder_profile')

        context = {
            "approval_alert": approval_alert,
            "has_authority_app": has_authority_app,
            "has_responder_app": has_responder_app
        }
        return render(request, "citizen_dashboard.html", context)

class ResponderDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "responder_dashboard.html")

class CitizenProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            user_profile = request.user.custom_profile
            context = {
                'user': user_profile,
                'medical_conditions': MedicalCondition.objects.filter(user_id=user_profile),
                'contacts': ContactInfo.objects.filter(user_id=user_profile),
                'gov_ids': GovernmentDocument.objects.filter(user_id=user_profile)
            }
            return render(request, "citizen_profile.html", context)
        except AttributeError:
            return redirect('account:logout')

    def post(self, request):
        user_profile = request.user.custom_profile

        # Extract Inputs
        email = request.POST.get('email_address')
        phone = request.POST.get('phone_number')
        dob = request.POST.get('date_of_birth') or None
        gender = request.POST.get('gender')
        street = request.POST.get('street')
        municipality = request.POST.get('municipality')
        city = request.POST.get('city')
        province = request.POST.get('province')
        zip_code = request.POST.get('zip_code')

        try:
            # 1. Call Stored Procedure for Main Profile
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL sp_update_citizen_profile(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        @status, @message
                    )""",
                               [user_profile.user_id, email, phone, dob, gender,
                                street, municipality, city, province, zip_code]
                               )
                cursor.execute("SELECT @status, @message")
                result = cursor.fetchone()
                status = result[0]
                db_message = result[1]

            if status == 'SUCCESS':
                # 2. Handle Related Data (Medical/Contacts) via ORM (Atomic Transaction)
                # Note: SPs are usually for the main entity; related lists are easier via ORM
                with transaction.atomic():
                    # Update Medical Conditions
                    cond_names = request.POST.getlist('medical_condition')
                    cond_notes = request.POST.getlist('medical_notes')
                    MedicalCondition.objects.filter(user_id=user_profile).delete()
                    for name, note in zip(cond_names, cond_notes):
                        if name.strip():
                            MedicalCondition.objects.create(user_id=user_profile, condition_name=name, notes=note)

                    # Update Contacts
                    contact_rels = request.POST.getlist('contact_relationship')
                    contact_nums = request.POST.getlist('contact_number')
                    ContactInfo.objects.filter(user_id=user_profile).delete()
                    for rel, num in zip(contact_rels, contact_nums):
                        if num.strip():
                            ContactInfo.objects.create(user_id=user_profile, contact_info=num, relationship=rel)

                messages.success(request, db_message)
            else:
                messages.error(request, db_message)

        except Exception as e:
            print(f"Profile Update Error: {e}")
            messages.error(request, "An error occurred while updating profile.")

        return redirect('account:citizen_profile')

class ResponderProfileView(LoginRequiredMixin, View):
    def get(self, request): return render(request, "responder_profile.html")

    def post(self, request): return redirect('account:responder_profile')  # Placeholder

class AuthorityProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            user_profile = request.user.custom_profile

            # Use the relationship to find the Authority entry
            # Authority -> Citizen -> User
            auth_profile = Authority.objects.filter(citizen__user_id=user_profile).first()

            if not auth_profile:
                messages.error(request, "Authority profile data missing.")
                return redirect('account:citizen_dashboard')

            context = {
                'authority_user': user_profile,  # Personal info (Address, Name)
                'authority_details': auth_profile,  # Agency, Jurisdiction
                'medical_conditions': MedicalCondition.objects.filter(user_id=user_profile),
                'emergency_contacts': ContactInfo.objects.filter(user_id=user_profile),
                'government_ids': GovernmentDocument.objects.filter(user_id=user_profile)
            }
            return render(request, "authority_profile.html", context)

        except AttributeError:
            return redirect('account:logout')

    def post(self, request):
        user_profile = request.user.custom_profile

        # 1. Extract Data
        email = request.POST.get('email_address')
        phone = request.POST.get('phone_number')
        dob = request.POST.get('date_of_birth') or None
        gender = request.POST.get('gender')

        street = request.POST.get('street')
        municipality = request.POST.get('municipality')
        city = request.POST.get('city')
        province = request.POST.get('province')
        zip_code = request.POST.get('zip_code')

        agency_name = request.POST.get('agency_name')
        jurisdiction_area = request.POST.get('jurisdiction_area')

        try:
            # 2. Call Stored Procedure
            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL sp_update_authority_profile(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        @status, @message
                    )""",
                               [user_profile.user_id, email, phone, dob, gender,
                                street, municipality, city, province, zip_code,
                                agency_name, jurisdiction_area]
                               )
                cursor.execute("SELECT @status, @message")
                result = cursor.fetchone()
                status = result[0]
                db_message = result[1]

            if status == 'SUCCESS':
                # 3. Handle Related Data (Medical & Contacts) via ORM
                with transaction.atomic():
                    # --- Medical ---
                    cond_names = request.POST.getlist('medical_condition')
                    cond_notes = request.POST.getlist('medical_notes')
                    MedicalCondition.objects.filter(user_id=user_profile).delete()
                    for name, note in zip(cond_names, cond_notes):
                        if name.strip():
                            MedicalCondition.objects.create(user_id=user_profile, condition_name=name, notes=note)

                    # --- Contacts ---
                    contact_rels = request.POST.getlist('contact_relationship')
                    contact_nums = request.POST.getlist('contact_number')
                    ContactInfo.objects.filter(user_id=user_profile).delete()
                    for rel, num in zip(contact_rels, contact_nums):
                        if num.strip():
                            ContactInfo.objects.create(user_id=user_profile, contact_info=num, relationship=rel)

                    # --- IDs (Add Only) ---
                    new_id_types = request.POST.getlist('new_id_type')
                    new_id_nums = request.POST.getlist('new_id_number')
                    new_id_files = request.FILES.getlist('new_id_file')

                    if new_id_files:
                        fs = FileSystemStorage()
                        for i, file_obj in enumerate(new_id_files):
                            if i < len(new_id_types):
                                filename = fs.save(f'gov_ids/{file_obj.name}', file_obj)
                                GovernmentDocument.objects.create(
                                    user_id=user_profile,
                                    id_type=new_id_types[i],
                                    id_number=new_id_nums[i],
                                    filepath=filename,
                                    status='PENDING'
                                )

                messages.success(request, db_message)
            else:
                messages.error(request, db_message)

        except Exception as e:
            print(f"Update Auth Error: {e}")
            messages.error(request, "An error occurred updating the profile.")

        return redirect('account:authority_profile')

class ApplyResponderView(LoginRequiredMixin, View):
    def post(self, request): return redirect('account:citizen_dashboard')  # Placeholder

class ApplyAuthorityView(LoginRequiredMixin, View):
    def post(self, request):
        fs = FileSystemStorage()
        try:
            # Check if user has a custom profile
            if not hasattr(request.user, 'custom_profile'):
                messages.error(request, "User profile not found.")
                return redirect('account:citizen_dashboard')

            user_profile = request.user.custom_profile

            # Extract Form Data
            agency_name = request.POST.get('agency_name')
            jurisdiction_area = request.POST.get('jurisdiction_area')
            id_type = request.POST.get('id_type')
            id_number = request.POST.get('id_number')
            id_file = request.FILES.get('id_file')

            # Validation
            if not agency_name or not jurisdiction_area or not id_number:
                messages.error(request, "Please fill in all required fields.")
                return redirect('account:citizen_dashboard')

            # File Upload Logic
            file_path = ""
            if id_file:
                # 1. Get extension safely
                _, ext = os.path.splitext(id_file.name)
                ext = ext.replace('.', '')  # Clean dot

                # 2. Create safe filename
                safe_agency = agency_name.replace(" ", "_").lower()[:10]
                filename = f"gov_ids/auth_{user_profile.user_id}_{safe_agency}.{ext}"

                # 3. Delete old file if exists
                if fs.exists(filename):
                    fs.delete(filename)

                # 4. Save and get URL
                saved_filename = fs.save(filename, id_file)
                file_path = fs.url(saved_filename)

            # Call Stored Procedure
            status = 'ERROR'
            db_message = 'Unknown error'

            with connection.cursor() as cursor:
                cursor.execute("""
                    CALL sp_apply_authority(
                        %s, %s, %s, %s, %s, %s, 
                        @status, @message
                    )""",
                               [
                                   user_profile.user_id,
                                   agency_name,
                                   jurisdiction_area,
                                   id_type,
                                   id_number,
                                   file_path
                               ]
                               )

                cursor.execute("SELECT @status, @message")
                row = cursor.fetchone()
                if row:
                    status, db_message = row

            if status == 'SUCCESS':
                messages.success(request, "Application for Authority has been sent and is ready for review.")
            else:
                messages.error(request, db_message)

        except Exception as e:
            # Print error to console for debugging
            print(f"Apply Auth Error: {e}")
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect('account:citizen_dashboard')

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('account:index')

