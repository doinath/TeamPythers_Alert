from django.db import models
from django.contrib.auth.models import User as AuthUser
from datetime import date

# -----------------------------------------------------------
#   USER (BASE ENTITY)
# -----------------------------------------------------------
class User(models.Model):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('authority', 'Authority'),
        ('responder', 'Responder'),
    )

    account = models.OneToOneField(
        AuthUser, on_delete=models.CASCADE, related_name='custom_profile', null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')

    type_gender = (('M', 'Male'), ('F', 'Female'))

    user_id = models.AutoField(primary_key=True)

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)

    email_address = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=type_gender, null=True, blank=True)

    street = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    municipality = models.CharField(max_length=50, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=4, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return (
            today.year - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -----------------------------------------------------------
#   EMERGENCY CONTACTS
# -----------------------------------------------------------
class ContactInfo(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_numbers')
    contact_info = models.CharField(max_length=15)
    relationship = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user_id} - {self.contact_info} ({self.relationship})"

# -----------------------------------------------------------
#   CITIZEN (SUBTYPE OF USER)
# -----------------------------------------------------------
class Citizen(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, related_name='citizen_profile')

    def __str__(self):
        return f"Citizen: {self.user_id.first_name} {self.user_id.last_name}"


# -----------------------------------------------------------
#   RESPONDER (SUBTYPE OF CITIZEN)
# -----------------------------------------------------------
class Responder(models.Model):
    role_type = (
        ('Medical', 'Medical Responders'),
        ('Fire', 'Fire Responders'),
        ('Law', 'Law Enforcement Responders'),
        ('Rescue', 'Rescue & Search Responders'),
        ('Logistics', 'Logistics & Support Responders'),
        ('Community', 'Community Responders'),
    )

    status_type = (
        ('ON', 'On Duty'),
        ('OFF', 'Off Duty'),
        ('CALL', 'On Call'),
        ('RES', 'Responding'),
        ('UNAV', 'Unavailable'),
        ('REL', 'Released'),
    )

    citizen = models.OneToOneField(Citizen, on_delete=models.CASCADE, related_name='responder_profile')
    department_unit = models.CharField(max_length=50)
    role = models.CharField(max_length=15, choices=role_type)
    service_area = models.CharField(max_length=50)
    duty_status = models.CharField(max_length=10, choices=status_type, default='OFF')

    def __str__(self):
        user = self.citizen.user_id
        return f"Responder: {user.first_name} {user.last_name}"


# -----------------------------------------------------------
#   AUTHORITY (SUBTYPE OF CITIZEN)
# -----------------------------------------------------------
class Authority(models.Model):
    citizen = models.OneToOneField(Citizen, on_delete=models.CASCADE, related_name='authority_profile')
    agency_name = models.CharField(max_length=50)
    jurisdiction_area = models.CharField(max_length=50)

    # NEW: track verification
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        user = self.citizen.user_id
        return f"Authority: {user.first_name} {user.last_name}"



# -----------------------------------------------------------
#   NOTIFICATIONS
# -----------------------------------------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.user.first_name} {self.user.last_name}"
