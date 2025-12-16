from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

# Imports
from .models import RoleVerification
from account.models import User as CustomUser


class RoleReviewDashboard(LoginRequiredMixin, View):
    """Bypasses role checks and renders role_verification.html directly."""

    def get(self, request, role_type="Responder"):
        # Fetch applications from the database
        pending_apps = RoleVerification.objects.filter(
            status='PENDING',
            requested_role=role_type.lower()
        ).select_related('user_id')

        # PATH FIX: Looking directly for role_verification.html
        return render(request, "role_verification.html", {
            'pending_applications': pending_apps,
            'role_to_approve': role_type.capitalize()
        })


class VerificationActionView(LoginRequiredMixin, View):
    """Handles the Approve and Reject button logic."""

    def post(self, request, pk):
        verification = get_object_or_404(RoleVerification, pk=pk)
        action = request.POST.get('action')

        if action == 'approve':
            verification.status = 'APPROVED'
            user_obj = verification.user_id
            user_obj.role = verification.requested_role
            user_obj.save()
            messages.success(request, f"Successfully approved {user_obj.get_full_name()}.")
        else:
            verification.status = 'REJECTED'
            messages.warning(request, "Application has been declined.")

        verification.verified_at = timezone.now()
        verification.save()

        # Redirect back to the list
        return redirect(reverse('verification:role_review', kwargs={'role_type': verification.requested_role}))


class DefaultReviewRedirectView(LoginRequiredMixin, RedirectView):
    """Redirects /verification/list/ directly to the responder review page."""

    def get_redirect_url(self, *args, **kwargs):
        return reverse('verification:role_review', kwargs={'role_type': 'responder'})