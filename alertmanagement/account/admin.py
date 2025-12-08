from django.contrib import admin
from .models import User, Citizen, Authority, Responder, Email, ContactInfo, Notification

# -------------------------------------------------------------
#   ADMIN ACTIONS
# -------------------------------------------------------------
@admin.action(description="Verify selected Citizens")
def verify_citizens(modeladmin, request, queryset):
    for citizen in queryset:
        auth_user = citizen.user_id.account
        auth_user.is_active = True
        auth_user.save()

        Notification.objects.create(
            user=citizen.user_id,
            message="Your account has been verified by the Administrator."
        )

    modeladmin.message_user(request, "Selected citizens have been verified.")


@admin.action(description="Promote selected Citizens to AUTHORITY")
def promote_to_authority(modeladmin, request, queryset):
    for citizen in queryset:
        user = citizen.user_id

        # Create Authority profile if not exists
        Authority.objects.get_or_create(citizen=citizen)

        # Update role for login redirect
        user.role = "authority"
        user.save()

        Notification.objects.create(
            user=user,
            message="Congratulations! Your application for AUTHORITY has been approved."
        )

    modeladmin.message_user(request, "Selected citizens promoted to Authority and notified.")


# -------------------------------------------------------------
#   CITIZEN ADMIN PAGE
# -------------------------------------------------------------
class CitizenAdmin(admin.ModelAdmin):
    list_display = ["get_username", "get_role", "get_verified"]
    actions = [verify_citizens, promote_to_authority]  # Superadmin cannot promote responders

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
#   REGISTER MODELS
# -------------------------------------------------------------
admin.site.register(User)
admin.site.register(Citizen, CitizenAdmin)
admin.site.register(Authority)
admin.site.register(Responder)
admin.site.register(Email)
admin.site.register(ContactInfo)
admin.site.register(Notification)
