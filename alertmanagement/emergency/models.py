from django.db import models
from account.models import Citizen, Responder, Authority, User


class EmergencyEvent(models.Model):
    EVENT_CATEGORIES = [
        ("fire", "Fire"),
        ("flood", "Flood"),
        ("earthquake", "Earthquake"),
        ("medical", "Medical Emergency"),
        ("crime", "Crime/Violence"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("reported", "Reported"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    SEVERITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    eventID = models.AutoField(primary_key=True)

    authority = models.ForeignKey(Authority,on_delete=models.SET_NULL, null=True, blank=True, related_name="emergency_events")

    responder = models.ForeignKey(Responder, on_delete=models.SET_NULL, null=True, blank=True, related_name="emergency_events")

    userID = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name="emergency_events")

    category = models.CharField(max_length=50, choices=EVENT_CATEGORIES)
    description = models.TextField()
    gps_location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="reported")
    severity_level = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default="low")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} - {self.gps_location} ({self.status})"


class EventAssignment(models.Model):
    ROLE_CHOICES = [
        ("authority", "Authority"),
        ("responder", "Responder"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    assignment_id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    authority = models.ForeignKey(
        Authority,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_assignments"
    )
    responder = models.ForeignKey(
        Responder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_assignments"
    )
    emergency_event = models.ForeignKey(
        EmergencyEvent,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    def __str__(self):
        return f"Assignment {self.assignment_id} - {self.role} ({self.status})"
#Government Documents, Medical Condition

class MedicalCondition(models.Model):

    condition_id = models.AutoField(primary_key=True)
    condition_name = models.CharField(max_length=100)
    notes = models.TextField()

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
