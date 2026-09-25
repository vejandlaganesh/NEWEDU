from django.urls import path
from .views import (
    TeacherDashboardView, TeacherClassListView, TeacherSubjectListView,
    TeacherStudentListView, TeacherMaterialListView, TeacherMaterialCreateView, TeacherMaterialUpdateView, 
    ChapterCreateView, ChapterUpdateView, LessonCreateView, LessonUpdateView,
    TeacherAssignmentListView, TeacherAssignmentCreateView, 
    TeacherAssignmentDetailView, TeacherSubmissionGradeView,
    TeacherReportsView, TeacherNotificationsView, TeacherProfileView, TeacherSettingsView,
    TeacherAIToolsDashboardView, TeacherAIContentGeneratorView,
    TeacherAIQuizGeneratorView, SaveGeneratedContentView, SaveGeneratedQuizView,
    TeacherAIApiSubjectsView, TeacherAIApiChaptersView
)
from apps.quizzes.views import (
    TeacherQuizListView, TeacherQuizCreateView, TeacherQuizDetailView, TeacherQuestionCreateView, TeacherQuizPublishView
)

urlpatterns = [
    path('dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('classes/', TeacherClassListView.as_view(), name='teacher_classes'),
    path('subjects/', TeacherSubjectListView.as_view(), name='teacher_subjects'),
    path('students/', TeacherStudentListView.as_view(), name='teacher_students'),
    
    # Materials
    path('materials/', TeacherMaterialListView.as_view(), name='teacher_materials'),
    path('materials/create/', TeacherMaterialCreateView.as_view(), name='teacher_material_create'),
    path('materials/<int:pk>/edit/', TeacherMaterialUpdateView.as_view(), name='teacher_material_edit'),
    path('materials/subject/<int:class_subject_id>/chapter/new/', ChapterCreateView.as_view(), name='teacher_chapter_create'),
    path('materials/chapter/<int:pk>/edit/', ChapterUpdateView.as_view(), name='teacher_chapter_edit'),
    path('materials/chapter/<int:chapter_id>/lesson/new/', LessonCreateView.as_view(), name='teacher_lesson_create'),
    path('materials/lesson/<int:pk>/edit/', LessonUpdateView.as_view(), name='teacher_lesson_edit'),
    
    # Assignments
    path('assignments/', TeacherAssignmentListView.as_view(), name='teacher_assignments'),
    path('assignments/create/', TeacherAssignmentCreateView.as_view(), name='teacher_assignment_create'),
    path('assignments/<int:pk>/', TeacherAssignmentDetailView.as_view(), name='teacher_assignment_detail'),
    path('assignments/<int:assignment_pk>/grade/<int:student_pk>/', TeacherSubmissionGradeView.as_view(), name='teacher_submission_grade'),
    
    # Quizzes
    path('quizzes/', TeacherQuizListView.as_view(), name='teacher_quizzes'),
    path('quizzes/add/', TeacherQuizCreateView.as_view(), name='teacher_quiz_add'),
    path('quizzes/<int:pk>/', TeacherQuizDetailView.as_view(), name='teacher_quiz_detail'),
    path('quizzes/<int:pk>/publish/', TeacherQuizPublishView.as_view(), name='teacher_quiz_publish'),
    path('quizzes/<int:quiz_pk>/question/add/', TeacherQuestionCreateView.as_view(), name='teacher_question_add'),
    
    # Reports and supporting pages
    path('reports/', TeacherReportsView.as_view(), name='teacher_reports'),
    # AI Tools
    path('ai-tools/', TeacherAIToolsDashboardView.as_view(), name='teacher_ai_tools'),
    path('ai-tools/content/', TeacherAIContentGeneratorView.as_view(), name='teacher_ai_content'),
    path('ai-tools/content/save/', SaveGeneratedContentView.as_view(), name='teacher_ai_content_save'),
    path('ai-tools/quiz/', TeacherAIQuizGeneratorView.as_view(), name='teacher_ai_quiz'),
    path('ai-tools/quiz/save/', SaveGeneratedQuizView.as_view(), name='teacher_ai_quiz_save'),
    path('ai-tools/api/subjects/', TeacherAIApiSubjectsView.as_view(), name='teacher_ai_api_subjects'),
    path('ai-tools/api/chapters/', TeacherAIApiChaptersView.as_view(), name='teacher_ai_api_chapters'),
    path('notifications/', TeacherNotificationsView.as_view(), name='teacher_notifications'),
    path('profile/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('settings/', TeacherSettingsView.as_view(), name='teacher_settings'),
]
