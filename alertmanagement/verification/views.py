from django.shortcuts import render
from django.views import View

# Create your views here.

class GovernmentDocument(View):
    def get(self, request):
        return render(request, "government_document.html")

class SubmittedDocument(View):
    def get(self, request):
        return render(request, "submitted_document.html")

class RoleVerification(View):
    def get(self, request):
        return render(request, "role_verification.html")
