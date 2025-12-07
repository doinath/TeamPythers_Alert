from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect

from django.db import transaction # Needed to save multiple models safely
from django.contrib.auth.models import User as AuthUser
from .models import User as CustomUser, Citizen # Import your custom models

# class RegisterView(View):
#     def get(self, request):
#         return render(request, "register.html")
#
#     def post(self, request):
#         # 1. Retrieve data from the POST request
#         first_name = request.POST.get('firstName')
#         last_name = request.POST.get('lastName')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#
#         # NOTE: Middle name is typically optional and can be handled later.
#
#         # 2. Basic Validation: Check if a user with that email already exists
#         if User.objects.filter(email=email).exists():
#             messages.error(request, 'This email address is already registered.')
#
#             # Re-render the form with error message and previously entered data
#             context = {
#                 'error_message': 'This email address is already registered.',
#                 'firstName': first_name,
#                 'lastName': last_name,
#                 'email': email
#             }
#             return render(request, "register.html", context=context)
#
#         # 3. Create the New User Account
#         try:
#             user = User.objects.create_user(
#                 username=email,  # Use email as the unique username
#                 email=email,
#                 password=password,
#                 first_name=first_name,
#                 last_name=last_name
#             )
#             # You would also create the related Citizen model instance here if needed:
#             # Citizen.objects.create(user=user)
#
#             messages.success(request, 'Account created successfully! Please complete your profile.')
#
#             # 4. On SUCCESS, redirect to the profile completion page
#             return redirect('citizen_profile_completion')
#
#         except Exception as e:
#             # Handle any other exceptions during creation (e.g., database error)
#             messages.error(request, f'An unexpected error occurred: {e}')
#
#             context = {
#                 'error_message': 'An unexpected error occurred during registration.',
#                 'firstName': first_name,
#                 'lastName': last_name,
#                 'email': email
#             }
#             return render(request, "register.html", context=context)

class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        # 1. Retrieve data
        first_name = request.POST.get('firstName')
        middle_name = request.POST.get('middleName') # Get middle name
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')

        # Context to repopulate form if error occurs
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
            # Atomic ensures that if one step fails, nothing is saved (preventing broken data)
            with transaction.atomic():
                # A. Create the Standard Django Auth User (for Login)
                auth_user = AuthUser.objects.create_user(
                    username=email, # Using email as username
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                # B. Create the Custom User Profile (from your models.py)
                custom_user = CustomUser.objects.create(
                    account=auth_user, # Link to the Auth User
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    # Other fields like street/city remain null for now
                )

                # C. Create the Citizen Profile (Default role)
                Citizen.objects.create(
                    user_id=custom_user # Link to your Custom User
                )

            # 4. Success
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('account:index') # Redirect to login/home page

        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')
            return render(request, "register.html", context)

class CitizenProfileCompletionView(View):
    def get(self, request):
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