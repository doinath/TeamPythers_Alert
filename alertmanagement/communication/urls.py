from django.urls import path
from .views import MessageListView, CallLogListView # Import the classes

# app_name helps Django distinguish URLs between different apps
app_name = 'communication'

urlpatterns = [
    # URL for viewing all messages, mapped to the MessageListView class
    path('messages/', MessageListView.as_view(), name='message_list'),

    # URL for viewing all call logs, mapped to the CallLogListView class
    path('call-logs/', CallLogListView.as_view(), name='call_log_list'),
]