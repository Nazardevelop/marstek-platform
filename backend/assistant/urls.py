from django.urls import path

from assistant import views

urlpatterns = [path("assistant/chat/", views.ChatView.as_view(), name="assistant-chat")]
