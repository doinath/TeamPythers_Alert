from django.contrib import admin
from .models import User, Citizen, Authority, Responder, Email, ContactInfo, Notification


# --- Custom Action ---
@admin.action(description='Approve selected citizens as AUTHORITY')
def make_authority(modeladmin, request, queryset):
    # Iterate through the selected CITIZEN objects
    for citizen in queryset:
        # Access the related CustomUser object
        user = citizen.user

        # Update the User's role and status
        user.role = 'authority'
        user.is_verified = True
        user.is_staff = True
        user.save()

        # Create the Notification
        Notification.objects.create(
            user=user,
            message="Congratulations! Your application for AUTHORITY has been approved."
        )

    modeladmin.message_user(request, "Selected citizens promoted to Authority and notified.")


class CitizenAdmin(admin.ModelAdmin):
    actions = [make_authority]
    # We use a custom method to display the username since it's in the related User model
    list_display = ['get_username', 'get_role', 'get_status']

    @admin.display(ordering='user__username', description='Username')
    def get_username(self, obj):
        return obj.user.username

    @admin.display(ordering='user__role', description='Role')
    def get_role(self, obj):
        return obj.user.role

    @admin.display(ordering='user__is_verified', description='Verified')
    def get_status(self, obj):
        return obj.user.is_verified


# Register models
admin.site.register(User)
admin.site.register(Citizen, CitizenAdmin)
admin.site.register(Authority)
admin.site.register(Responder)
admin.site.register(Email)
admin.site.register(ContactInfo)
# admin.site.register(Notification) # Optional