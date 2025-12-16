from django.contrib import admin
from .models import User, Citizen, Authority, Responder, ContactInfo, Notification

# -------------------------------------------------------------
#   ADMIN ACTIONS
# -------------------------------------------------------------

@admin.action(description="Verify selected Authority applications")
def verify_authority(modeladmin, request, queryset):
    for authority in queryset:
        # 1. Verify the Authority Profile
        authority.is_verified = True
        authority.save()

        # 2. Update the Main User Role to 'authority'
        # This ensures the Login logic redirects them correctly next time
        user_custom = authority.citizen.user_id
        user_custom.role = "authority"
        user_custom.save()

        # 3. Notify the user (Triggers the modal on their dashboard)
        Notification.objects.create(
            user=user_custom,
            message="Your application for Authority has been verified and approved."
        )

    modeladmin.message_user(request, "Selected authority applications have been verified and users updated.")

# -------------------------------------------------------------
#   ADMIN CONFIGURATION
# -------------------------------------------------------------

class AuthorityAdmin(admin.ModelAdmin):
    list_display = ["get_username", "agency_name", "get_verified"]
    list_filter = ["is_verified"]
    actions = [verify_authority]  # Register the action here

    @admin.display(description="Username")
    def get_username(self, obj):
        return obj.citizen.user_id.first_name + " " + obj.citizen.user_id.last_name

    @admin.display(description="Verified")
    def get_verified(self, obj):
        return "Yes" if obj.is_verified else "No"

# Register your models
admin.site.register(User)
admin.site.register(Citizen)
admin.site.register(Authority, AuthorityAdmin)
admin.site.register(Responder)
admin.site.register(ContactInfo)
admin.site.register(Notification)