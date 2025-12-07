from django import forms
from django.core.exceptions import ValidationError
from .models import EmergencyEvent, EventAssignment, MedicalCondition


class EmergencyEventForm(forms.ModelForm):
    # We explicitly define the field here to set required=False
    # This lets the user leave it empty in the UI
    gps_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Latitude, Longitude (Optional)'})
    )

    class Meta:
        model = EmergencyEvent
        fields = [
            'authority',
            'responder',
            'userID',
            'category',
            'description',
            'gps_location',
            'status',
            'severity_level'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the emergency...'}),
        }

    def clean_gps_location(self):
        data = self.cleaned_data.get('gps_location')

        # If the user left it empty, return a default placeholder
        if not data:
            return "0.0000, 0.0000"  # Default coordinates or text like "Location Pending"

        # Optional: Keep basic validation if they DO type something
        # if ',' not in data:
        #    raise ValidationError("GPS Location must be in 'Lat, Long' format.")

        return data


class EventAssignmentForm(forms.ModelForm):
    class Meta:
        model = EventAssignment
        fields = [
            'role',
            'status',
            'authority',
            'responder',
            'emergency_event'
        ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        authority = cleaned_data.get("authority")
        responder = cleaned_data.get("responder")

        if role == "authority" and not authority:
            raise ValidationError("You selected the role 'Authority' but did not select an Authority entity.")

        if role == "responder" and not responder:
            raise ValidationError("You selected the role 'Responder' but did not select a Responder entity.")

        if role == "authority" and responder:
            self.add_error('responder', "Role is Authority; Responder field should be empty.")

        if role == "responder" and authority:
            self.add_error('authority', "Role is Responder; Authority field should be empty.")

        return cleaned_data


class MedicalConditionForm(forms.ModelForm):
    class Meta:
        model = MedicalCondition
        fields = ['condition_name', 'notes', 'user_id']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }