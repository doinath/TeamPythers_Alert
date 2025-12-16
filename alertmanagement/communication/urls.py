from django.urls import path
from . import views
from .views import MessageListView, CallLogListView, ChatDetailView

app_name = 'communication'

urlpatterns = [
    # ==========================
    # PAGE VIEWS
    # ==========================
    path('messages/', MessageListView.as_view(), name='messages'),

    # Removed the duplicate line here. Only one is needed.
    path('call-logs/', CallLogListView.as_view(), name='call_logs'),

    path('chat/<int:user_id>/', ChatDetailView.as_view(), name='chat_detail'),

    # ==========================
    # CITIZEN APIs (SOS Logic)
    # ==========================
    # 1. Citizen starts the call -> Finds Authority -> Sets status to 'ringing'
    path('call/initiate/', views.initiate_sos_call, name='initiate_sos_call'),

    # 2. Citizen polls this to see if Authority accepted ('active')
    path('call/check-status/', views.check_call_status, name='check_call_status'),

    # 3. Citizen or Authority ends the call
    path('call/end/', views.end_emergency_call, name='end_emergency_call'),

    # ==========================
    # AUTHORITY APIs (Response Logic)
    # ==========================
    # 1. Authority polls this to see if a citizen is calling ('ringing')
    path('call/check-incoming/', views.check_incoming_calls, name='check_incoming_calls'),

    # 2. Authority accepts the call -> Sets status to 'active'
    path('call/accept/', views.accept_call, name='accept_call'),
]