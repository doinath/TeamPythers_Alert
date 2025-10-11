from django.db import models
from datetime import date

# Create your models here.
class User(models.Model):

    type_gender = (('M', 'Male'), ('F', 'Female'))

    user_id = models.AutoField(primary_key=True)

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)

    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=type_gender)
    street = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    municipality = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = date.today()
        return (
            today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

class ContactInfo(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_info = models.CharField(max_length=10)

class Email(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()

class Citizen(User):

    def __str__(self):
        return self

class Responder(User):

    role_type = (('Medical', 'Medical Responders'), ('Fire', 'Fire Responders'),
                 ('Law', ' Law Enforcement Responders'), ('Rescue', 'Rescue & Search Responders'),
                 ('Logistics', 'Logistics & Support Responders'), ('Community', 'Community Responders'))

    status_type = (('ON', 'On Duty'), ('OFF', 'Off Duty'), ('CALL', 'On Call'), ('RES', 'Responding'),
                   ('UNAV', 'Unavailable'), ('REL', 'Released'))

    department_unit = models.CharField(max_length=50)
    role = models.CharField(max_length=9, choices=role_type)
    service_area = models.CharField(max_length=50)
    duty_status = models.CharField(max_length=10, choices=status_type, default='OFF')

class Authority(User):
    agency_name = models.CharField(max_length=50)
    jurisdiction = models.CharField(max_length=50)