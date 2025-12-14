from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.shortcuts import render
from django.shortcuts import render, redirect

class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        # 1. Retrieve data from the POST request
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # NOTE: Middle name is typically optional and can be handled later.

        # 2. Basic Validation: Check if a user with that email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email address is already registered.')

            # Re-render the form with error message and previously entered data
            context = {
                'error_message': 'This email address is already registered.',
                'firstName': first_name,
                'lastName': last_name,
                'email': email
            }
            return render(request, "register.html", context=context)

        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, 'Account created successfully! Please complete your profile.')
            return redirect('citizen_profile_completion')

        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {e}')

            context = {
                'error_message': 'An unexpected error occurred during registration.',
                'firstName': first_name,
                'lastName': last_name,
                'email': email
            }
            return render(request, "register.html", context=context)

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