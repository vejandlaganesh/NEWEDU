from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

from django.shortcuts import render

def home_view(request):
    return render(request, "home.html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('student/', include('apps.students.urls')),
    path('teacher/', include('apps.teachers.urls')),
    path('parent/', include('apps.parents.urls')),
    path('assignments/', include('apps.assignments.urls')),
    path('admin-dashboard/', include('apps.core.urls')),
    path('ai/api/', include('apps.ai_assistant.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('search/', include('apps.search.urls')),
    path('', home_view, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
