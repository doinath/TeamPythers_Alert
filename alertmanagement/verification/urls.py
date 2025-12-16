from django.urls import path
from .views import RoleReviewDashboard, VerificationActionView, DefaultReviewRedirectView

app_name = 'verification'

urlpatterns = [
    # Entry point: http://127.0.0.1:8000/verification/list/
    path('list/', DefaultReviewRedirectView.as_view(), name='verification'),

    # Dashboard view
    path('review/<str:role_type>/', RoleReviewDashboard.as_view(), name='role_review'),

    # Action endpoint
    path('action/<int:pk>/', VerificationActionView.as_view(), name='verification_action'),
]