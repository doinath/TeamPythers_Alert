from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login

# Import your models
from django.contrib.auth.models import User as AuthUser
from .models import User as CustomUser, Citizen, ContactInfo
from emergency.models import MedicalCondition
from verification.models import GovernmentDocument

class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        # 1. Retrieve data
        first_name = request.POST.get('firstName')
        middle_name = request.POST.get('middleName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        context = {
            'firstName': first_name,
            'middleName': middle_name,
            'lastName': last_name,
            'email': email
        }

        # 2. Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, "register.html", context)

        if AuthUser.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered.')
            return render(request, "register.html", context)

        # 3. Create Database Entries
        try:
            with transaction.atomic():
                # A. Create Auth User
                auth_user = AuthUser.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # B. Create Custom User
                custom_user = CustomUser.objects.create(
                    account=auth_user,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                )

                # C. Create Citizen Profile
                Citizen.objects.create(user_id=custom_user)

            # ---------------------------------------------------------
            # NEW STEP: Log the user in automatically
            # ---------------------------------------------------------
            # This ensures the next page knows who is logged in
            login(request, auth_user)

            messages.success(request, 'Account created successfully! Please complete your profile.')

            # ---------------------------------------------------------
            # CHANGED: Redirect to Citizen Profile Completion
            # ---------------------------------------------------------
            return redirect('account:citizen_profile_completion')

        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
            return render(request, "register.html", context)


class CitizenProfileCompletionView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "citizen_profile_completion.html")

    def post(self, request):
        try:
            # 1. Get the currently logged-in Custom User
            # We access the related_name 'custom_profile' defined in models.py
            custom_user = request.user.custom_profile

            with transaction.atomic():
                # ---------------------------------------------------
                # A. UPDATE PERSONAL INFORMATION (Account Database)
                # ---------------------------------------------------
                custom_user.date_of_birth = request.POST.get('dob')
                custom_user.gender = request.POST.get('gender')

                custom_user.street = request.POST.get('street')
                # Mapping form 'barangay' to model 'municipality' as requested
                custom_user.municipality = request.POST.get('barangay')
                custom_user.city = request.POST.get('city')
                custom_user.province = request.POST.get('province')
                custom_user.zip_code = request.POST.get('zipCode')
                custom_user.country = "Philippines"  # Default value

                custom_user.save()  # This updates the 'updated_at' field automatically

                # ---------------------------------------------------
                # B. SAVE EMERGENCY CONTACTS (Account Database)
                # ---------------------------------------------------
                # Get the number of contacts added from the hidden input
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

                # ---------------------------------------------------
                # C. SAVE MEDICAL INFORMATION (Emergency Database)
                # ---------------------------------------------------
                medical_count = int(request.POST.get('medical_count', 0))

                for i in range(1, medical_count + 1):
                    cond_name = request.POST.get(f'condition_name_{i}')
                    cond_notes = request.POST.get(f'condition_notes_{i}')

                    if cond_name:  # Notes are optional, but name is required to save
                        MedicalCondition.objects.create(
                            user_id=custom_user,
                            condition_name=cond_name,
                            notes=cond_notes if cond_notes else ""
                        )

                # ---------------------------------------------------
                # D. SAVE GOVERNMENT IDS (Verification Database)
                # ---------------------------------------------------
                id_count = int(request.POST.get('id_count', 0))

                for i in range(1, id_count + 1):
                    id_type_val = request.POST.get(f'id_type_{i}')
                    id_number_val = request.POST.get(f'id_number_{i}')
                    id_file_val = request.FILES.get(f'id_file_{i}')  # Use request.FILES

                    # Handle "Other" ID type
                    if id_type_val == 'other':
                        id_type_val = request.POST.get(f'id_type_other_{i}')

                    if id_type_val and id_number_val and id_file_val:
                        GovernmentDocument.objects.create(
                            user_id=custom_user,
                            id_type=id_type_val,
                            id_number=id_number_val,
                            filepath=id_file_val,
                            status='PENDING'  # Default status
                        )

            # ---------------------------------------------------
            # END TRANSACTION
            # ---------------------------------------------------
            messages.success(request, 'Profile completed successfully! Welcome to your Dashboard.')
            return redirect('account:citizen_dashboard')

        except Exception as e:
            # If anything fails, transaction rolls back
            print(f"Error: {e}")  # Print error to terminal for debugging
            messages.error(request, f'An error occurred while saving your profile: {e}')
            return render(request, "citizen_profile_completion.html")

class IndexView(View):
    def get(self, request):
        return render(request, "index.html")

class CitizenDashboardView(View):
    def get(self, request):
        return render(request, "citizen_dashboard.html")

class ResponderDashboardView(View):
    def get(self, request):
        return render(request, "responder_dashboard.html")

class AuthorityDashboardView(View):
    def get(self, request):
        return render(request, "authority_dashboard.html")

class CitizenProfileView(View):
    def get(self, request):
        return render(request, "citizen_profile.html")

class ResponderProfileView(View):
    def get(self, request):
        return render(request, "responder_profile.html")

class AuthorityProfileView(View):
    def get(self, request):
        return render(request, "authority_profile.html")