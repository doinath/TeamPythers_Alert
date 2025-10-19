from django.shortcuts import render
from django.views import View

# Create your views here.

class GovernmentDocument(View):
    def get(self, request):
        return render(request, "Government.html")

class SubmittedDocument(View):
    def get(self, request):
        return render(request, "Submitted.html")

class RoleVerification(View):
    def get(self, request):
        return render(request, "RoleVerification.html")