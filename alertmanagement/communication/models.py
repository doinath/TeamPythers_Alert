from django.db import models
from emergency.models import EmergencyEvent
from account.models import User

class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.message_text


class CallLog(models.Model):
    CALL_TYPES = [
        ("incoming", "Incoming"),
        ("outgoing", "Outgoing"),
        ("missed", "Missed"),
    ]

    call_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.call_id)

    @property
    def formatted_duration(self):
        if self.duration is None:
            return "00:00"

        total_seconds = self.duration

        hours = total_seconds // 3600
        remaining_seconds = total_seconds % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        # Format the output based on whether there are hours, minutes, or just seconds.
        # Ensure two-digit formatting for minutes and seconds.
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
