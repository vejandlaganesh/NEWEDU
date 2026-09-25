from django.urls import path
from .views import (
    StudentDashboardView, MySubjectsView, SubjectDetailView,
    ChapterDetailView, LessonDetailView, StudentProfileUpdateView, 
    StudentAssignmentListView, StudentAssignmentDetailView,
    StudentReportsView, StudentAIAssistantView, StudentResultsView, StudentNotificationsView, StudentSettingsView
)
from apps.quizzes.views import (
    StudentQuizListView, StudentQuizDetailView, StudentQuizAttemptStartView,
    StudentQuizTakeView, StudentQuizResultView
)

urlpatterns = [
    path('dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('subjects/', MySubjectsView.as_view(), name='student_subjects'),
    path('subjects/<int:pk>/', SubjectDetailView.as_view(), name='student_subject_detail'),
    path('chapters/<int:pk>/', ChapterDetailView.as_view(), name='student_chapter_detail'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='student_lesson_detail'),
    
    # Assignments
    path('assignments/', StudentAssignmentListView.as_view(), name='student_assignments'),
    path('assignments/<int:pk>/', StudentAssignmentDetailView.as_view(), name='student_assignment_detail'),
    
    # Quizzes
    path('quizzes/', StudentQuizListView.as_view(), name='student_quizzes'),
    path('quizzes/<int:pk>/', StudentQuizDetailView.as_view(), name='student_quiz_detail'),
    path('quizzes/<int:pk>/start/', StudentQuizAttemptStartView.as_view(), name='student_quiz_start'),
    path('quizzes/attempt/<int:pk>/take/', StudentQuizTakeView.as_view(), name='student_quiz_take'),
    path('quizzes/attempt/<int:pk>/result/', StudentQuizResultView.as_view(), name='student_quiz_result'),
    
    path('profile/', StudentProfileUpdateView.as_view(), name='student_profile'),
    
    # AI Assistant
    path('ai-assistant/', StudentAIAssistantView.as_view(), name='student_ai_assistant'),
    
    path('results/', StudentResultsView.as_view(), name='student_results'),
    path('reports/', StudentReportsView.as_view(), name='student_reports'),
    path('notifications/', StudentNotificationsView.as_view(), name='student_notifications'),
    path('settings/', StudentSettingsView.as_view(), name='student_settings'),
]
