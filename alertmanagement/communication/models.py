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
