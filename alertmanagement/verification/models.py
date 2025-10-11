from django.db import models

from account.models import Authority, User

class RoleVerification(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    verification_id = models.AutoField(primary_key=True)
    requested_role = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    verified_by = models.ForeignKey(
        Authority,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # fk user
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")

    verified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification {self.verification_id} for role {self.requested_role}"


class SubmittedDocument(models.Model):
    role_verification = models.ForeignKey(
        RoleVerification,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    document_name = models.CharField(max_length=255)
    document_file = models.FileField(upload_to="verification_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_name} (Verification {self.role_verification.verification_id})"

class GovernmentDocument(models.Model):
    document_id = models.AutoField(primary_key=True)
    id_type = models.CharField(max_length=255)
    id_number = models.CharField(max_length=255)
    filepath = models.FileField(upload_to="verification_documents/")
    status = models.CharField(max_length=20)

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id_type} ({self.id_number})"
