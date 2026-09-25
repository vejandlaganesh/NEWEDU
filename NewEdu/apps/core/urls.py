from django.urls import path
from .views import (
    AdminDashboardView, 
    UserListView, UserCreateView, UserToggleActiveView,
    AcademicYearListView, AcademicYearCreateView, AcademicYearUpdateView,
    ClassListView, ClassCreateView, ClassUpdateView,
    SectionListView, SectionCreateView, SectionUpdateView,
    SubjectListView, SubjectCreateView, SubjectUpdateView,
    ClassSubjectListView, ClassSubjectCreateView, ClassSubjectUpdateView,
    AdminChapterListView, AdminChapterCreateView, AdminChapterUpdateView, AdminLessonListView, AdminLessonCreateView, AdminLessonUpdateView,
    AdminMaterialListView, AdminMaterialCreateView, AdminMaterialUpdateView, AdminAssignmentListView, AdminQuizListView, AdminResultListView, AdminReportView, AdminNotificationListView, AdminSettingsView
)

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # User Management
    path('users/', UserListView.as_view(), name='admin_users'),
    path('users/create/', UserCreateView.as_view(), name='admin_user_create'),
    path('users/<int:pk>/toggle/', UserToggleActiveView.as_view(), name='admin_user_toggle'),
    
    # Academic Management
    path('academic-years/', AcademicYearListView.as_view(), name='admin_academic_years'),
    path('academic-years/create/', AcademicYearCreateView.as_view(), name='admin_academic_year_create'),
    path('academic-years/<int:pk>/edit/', AcademicYearUpdateView.as_view(), name='admin_academic_year_edit'),
    
    path('classes/', ClassListView.as_view(), name='admin_classes'),
    path('classes/create/', ClassCreateView.as_view(), name='admin_class_create'),
    path('classes/<int:pk>/edit/', ClassUpdateView.as_view(), name='admin_class_edit'),
    
    path('sections/', SectionListView.as_view(), name='admin_sections'),
    path('sections/create/', SectionCreateView.as_view(), name='admin_section_create'),
    path('sections/<int:pk>/edit/', SectionUpdateView.as_view(), name='admin_section_edit'),
    
    path('subjects/', SubjectListView.as_view(), name='admin_subjects'),
    path('subjects/create/', SubjectCreateView.as_view(), name='admin_subject_create'),
    path('subjects/<int:pk>/edit/', SubjectUpdateView.as_view(), name='admin_subject_edit'),
    
    path('class-subjects/', ClassSubjectListView.as_view(), name='admin_class_subjects'),
    path('class-subjects/create/', ClassSubjectCreateView.as_view(), name='admin_class_subject_create'),
    path('class-subjects/<int:pk>/edit/', ClassSubjectUpdateView.as_view(), name='admin_class_subject_edit'),
    
    path('chapters/', AdminChapterListView.as_view(), name='admin_chapters'),
    path('chapters/create/', AdminChapterCreateView.as_view(), name='admin_chapter_create'),
    path('chapters/<int:pk>/edit/', AdminChapterUpdateView.as_view(), name='admin_chapter_edit'),
    path('lessons/', AdminLessonListView.as_view(), name='admin_lessons'),
    path('lessons/create/', AdminLessonCreateView.as_view(), name='admin_lesson_create'),
    path('lessons/<int:pk>/edit/', AdminLessonUpdateView.as_view(), name='admin_lesson_edit'),
    path('materials/', AdminMaterialListView.as_view(), name='admin_materials'),
    path('materials/create/', AdminMaterialCreateView.as_view(), name='admin_material_create'),
    path('materials/<int:pk>/edit/', AdminMaterialUpdateView.as_view(), name='admin_material_edit'),
    path('assignments/', AdminAssignmentListView.as_view(), name='admin_assignments'),
    path('quizzes/', AdminQuizListView.as_view(), name='admin_quizzes'),
    path('results/', AdminResultListView.as_view(), name='admin_results'),
    path('reports/', AdminReportView.as_view(), name='admin_reports'),
    path('notifications/', AdminNotificationListView.as_view(), name='admin_notifications'),
    path('settings/', AdminSettingsView.as_view(), name='admin_settings'),
]
