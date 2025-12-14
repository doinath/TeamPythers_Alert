from django.db import models
from django.conf import settings
from emergency.models import EmergencyEvent


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE)
    # Use settings.AUTH_USER_MODEL to avoid instance mismatch errors
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.message_text


class CallLog(models.Model):
    CALL_TYPES = [
        ("incoming", "Incoming"),  # From perspective of receiver
        ("outgoing", "Outgoing"),  # From perspective of initiator
        ("missed", "Missed"),
    ]

    STATUS_CHOICES = [
        ("ringing", "Ringing"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("declined", "Declined"),
        ("cancelled", "Cancelled"),
    ]

    call_id = models.AutoField(primary_key=True)

    # Citizen (Caller)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='initiated_calls')

    # Authority/Responder (Receiver)
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='received_calls')

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE, null=True, blank=True)

    start_time = models.DateTimeField(auto_now_add=True)  # Time initiated
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)

    # NEW FIELD
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ringing')

    def __str__(self):
        return f"Call {self.call_id} ({self.status})"

    @property
    def formatted_duration(self):
        if self.duration is None: return "00:00"
        total_seconds = self.duration
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"