from django.urls import path
from .views import SecureFileDownloadView

urlpatterns = [
    path('download/<path:file_path>/', SecureFileDownloadView.as_view(), name='secure_download'),
]
