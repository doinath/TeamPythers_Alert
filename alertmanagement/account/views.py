from django.views import View
from django.shortcuts import render

class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

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