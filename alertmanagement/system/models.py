from django.db import models
from account.models import User

# Create your models here.
class SystemLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    action = models.CharField(max_length=200)
    detail = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user_id.username} - {self.action} at {self.timestamp}"
