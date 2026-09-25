from django.urls import path
from .views import ai_chat_endpoint, ai_archive_conversation_endpoint

urlpatterns = [
    path('chat/', ai_chat_endpoint, name='ai_chat'),
    path('chat/archive/', ai_archive_conversation_endpoint, name='ai_chat_archive'),
]
