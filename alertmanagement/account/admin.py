from django.contrib import admin
from .models import User, Citizen, Authority, Responder, Email, ContactInfo, Notification

# -------------------------------------------------------------
#   ADMIN ACTIONS
# -------------------------------------------------------------

@admin.action(description="Verify selected Authority applications")
def verify_authority(modeladmin, request, queryset):
    for authority in queryset:
        authority.is_verified = True
        authority.save()

        # Update the user's role so login redirects correctly
        user = authority.citizen.user_id
        user.role = "authority"
        user.save()

        # Notify the user
        Notification.objects.create(
            user=user,
            message="Your application for Authority has been verified by the Administrator."
        )

    modeladmin.message_user(request, "Selected authority applications have been verified.")


# -------------------------------------------------------------
#   CITIZEN ADMIN PAGE
# -------------------------------------------------------------
class CitizenAdmin(admin.ModelAdmin):
    list_display = ["get_username", "get_role", "get_verified"]
    # Only allow default delete action
    actions = ["delete_selected"]

    @admin.display(description="Username")
    def get_username(self, obj):
        return obj.user_id.account.username

    @admin.display(description="Role")
    def get_role(self, obj):
        return obj.user_id.role.capitalize()  # citizen, authority, responder

    @admin.display(description="Verified")
    def get_verified(self, obj):
        return "Yes" if obj.user_id.account.is_active else "No"


# -------------------------------------------------------------
#   AUTHORITY ADMIN PAGE
# -------------------------------------------------------------
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ["get_username", "get_verified"]
    actions = [verify_authority]  # Admin can verify authority applications

    @admin.display(description="Username")
    def get_username(self, obj):
        return obj.citizen.user_id.account.username

    @admin.display(description="Verified")
    def get_verified(self, obj):
        return "Yes" if obj.is_verified else "No"


# -------------------------------------------------------------
#   REGISTER MODELS
# -------------------------------------------------------------
admin.site.register(User)
admin.site.register(Citizen, CitizenAdmin)
admin.site.register(Authority, AuthorityAdmin)
admin.site.register(Responder)
admin.site.register(Email)
admin.site.register(ContactInfo)
admin.site.register(Notification)
