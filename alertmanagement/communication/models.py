from django.db import models

from emergency.models import EmergencyEvent

from account.models import User

# Create your models here.
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
        #Fk user
    def __str__(self):
        return self.message_text

class CallLog(models.Model): #needs user
    call_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(auto_now=True)
    duration = models.IntegerField()
    call_type = models.IntegerField() # needs a choice
    #fk user
    #fk emergency event
    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.call_id