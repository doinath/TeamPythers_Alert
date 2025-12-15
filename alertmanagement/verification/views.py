from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect
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

class RoleVerificationView(LoginRequiredMixin, View):

    login_url =  '/'

    def get(self, request):
        if not hasattr(request.user.custom_profile, 'authority'):
            messages.error(request, "You are not authorized to view this page.")
            return redirect('account:citizen_dashboard')

        pending_verification = RoleVerification.objects.filter(status='PENDING').select_related('user_id')

        context = {
            'verification': pending_verification
        }

        return render(request, "role_verification.html", context)

    def post (self, request):
        if not hasattr(request.user.custom_profile, 'authority'):
            messages.error(request, "Access denied.")
            return redirect('account:citizen_dashboard')

        verification_id = request.POST.get('verification_id')
        action = request.POST.get('action')  # 'approve' or 'reject'

        try:
            authority_profile = request.user.custom_profile.authority
            verification = get_object_or_404(RoleVerificationModel, pk=verification_id)

            with transaction.atomic():
                if action == 'approve':
                    verification.status = 'APPROVED'

                    messages.success(request, f"Role verification for {verification.requested_role} approved!")
                elif action == 'reject':
                    verification.status = 'REJECTED'
                    messages.warning(request, f"Role verification for {verification.requested_role} rejected.")

                verification.verified_by = authority_profile
                verification.save()

            return redirect('verification:role_verification')

        except Exception as e:
            messages.error(request, f"Error processing verification: {e}")
            return redirect('verification:role_verification')