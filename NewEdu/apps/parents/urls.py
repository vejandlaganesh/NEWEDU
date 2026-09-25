from django.urls import path
from .views import (
    ParentDashboardView, ParentAssignmentListView, ParentReportsView, ParentResultsView, ParentNotificationsView, ParentProfileView, ParentSettingsView
)
from apps.quizzes.views import ParentQuizListView, ParentQuizResultView

urlpatterns = [
    path('dashboard/', ParentDashboardView.as_view(), name='parent_dashboard'),
    
    # Assignments
    path('assignments/', ParentAssignmentListView.as_view(), name='parent_assignments'),
    
    # Quizzes
    path('quizzes/', ParentQuizListView.as_view(), name='parent_quizzes'),
    path('quizzes/attempt/<int:pk>/result/', ParentQuizResultView.as_view(), name='parent_quiz_result'),
    
    path('reports/', ParentReportsView.as_view(), name='parent_reports'),
    path('results/', ParentResultsView.as_view(), name='parent_results'),
    path('notifications/', ParentNotificationsView.as_view(), name='parent_notifications'),
    path('profile/', ParentProfileView.as_view(), name='parent_profile'),
    path('settings/', ParentSettingsView.as_view(), name='parent_settings'),
]
