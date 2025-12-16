from django.db import models
from django.shortcuts import get_object_or_404
# IMPORTANT: Ensure 'account.models' is correctly imported
from account.models import Authority, User


class RoleVerification(models.Model):
    """
    Tracks the application and verification status for users applying for
    Authority or Responder roles.
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    ROLE_CHOICES = [
        ('authority', 'Authority'),
        ('responder', 'Responder'),
    ]

    verification_id = models.AutoField(primary_key=True)

    requested_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    verified_by = models.ForeignKey(
        Authority,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications_conducted'
    )

    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_applications"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create_verification_from_document(cls, user, role):
        """
        Creates a RoleVerification entry if one doesn't exist for the given role and user
        that is currently PENDING.
        """
        if not cls.objects.filter(user_id=user, requested_role=role, status='PENDING').exists():
            return cls.objects.create(
                user_id=user,
                requested_role=role,
                status='PENDING'
            )
        return None

    def __str__(self):
        return f"App for {self.requested_role} by {self.user_id} - {self.status}"


class SubmittedDocument(models.Model):
    # ... (remains unchanged) ...
    role_verification = models.ForeignKey(
        RoleVerification,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to="verification_documents/role_applications/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_name} ({self.role_verification.user_id.get_full_name})"


class GovernmentDocument(models.Model):
    # ... (remains unchanged) ...
    document_id = models.AutoField(primary_key=True)
    id_type = models.CharField(max_length=255)
    id_number = models.CharField(max_length=255)
    filepath = models.FileField(upload_to="verification_documents/")
    status = models.CharField(max_length=20, default='PENDING')

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    role_verification = models.ForeignKey(
        RoleVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_documents'
    )

    def __str__(self):
        return f"{self.id_type} ({self.id_number})"