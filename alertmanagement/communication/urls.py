from django.urls import path
from . import views
from .views import MessageListView, CallLogListView, ChatDetailView

app_name = 'communication'

urlpatterns = [
    # ==========================
    # PAGE VIEWS
    # ==========================
    path('messages/', MessageListView.as_view(), name='messages'),
    path('call-logs/', CallLogListView.as_view(), name='call_logs'),
    # path('chat/<int:user_id>/', ChatDetailView.as_view(), name='chat_detail'),

    # ==========================
    # 1. VIDEO/SOS CALL APIs
    # ==========================
    # Citizen: Start call
    path('call/initiate/', views.initiate_sos_call, name='initiate_sos_call'),
    # Citizen: Check if answered
    path('call/check-status/', views.check_call_status, name='check_call_status'),
    # Both: End call
    path('call/end/', views.end_emergency_call, name='end_emergency_call'),
    # Authority: Check for incoming calls
    path('call/check-incoming/', views.check_incoming_calls, name='check_incoming_calls'),
    # Authority: Accept call
    path('call/accept/', views.accept_call, name='accept_call'),

    # ==========================
    # 2. EMERGENCY EVENT APIs (New)
    # ==========================

    # --- Citizen Side ---
    # Creates an event with status 'reported' (Fire, Flood buttons)
    path('event/create/', views.create_emergency_event, name='create_emergency_event'),

    # Cancels the event request while timer is counting down
    path('event/cancel/', views.cancel_emergency_event, name='cancel_emergency_event'),

    # --- Authority Side ---
    # Polling endpoint to get list of 'reported' events
    path('event/list/', views.get_reported_events, name='get_reported_events'),

    # Triggered when clicking "Assign & Chat"
    # Runs the Stored Procedure to assign Authority and insert the first message
    path('event/assign/', views.authority_assign_event, name='authority_assign_event'),

    path('event/status/', views.check_event_status, name='check_event_status'),

    # Shows the list (and empty chat area)
    path('messages/', views.MessageListView.as_view(), name='messages'),

    # Shows the list AND the specific conversation for the event_id
    path('chat/<int:event_id>/', views.ChatDetailView.as_view(), name='chat_detail'),
]