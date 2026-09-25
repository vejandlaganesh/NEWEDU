from django.urls import path
from .views import NotificationListView, MarkAsReadView, MarkAllAsReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', MarkAsReadView.as_view(), name='notification_mark_read'),
    path('read-all/', MarkAllAsReadView.as_view(), name='notification_mark_all_read'),
]
