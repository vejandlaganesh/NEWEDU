from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Enrollment, TeacherAssignment, Chapter, Lesson
from .forms import UserCreationForm, AcademicYearForm, ClassForm, SectionForm, SubjectForm, ClassSubjectForm
from apps.content.models import LearningMaterial
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.quizzes.models import Quiz, QuizResult
from apps.notifications.models import Notification
from django.conf import settings

class AdminAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'ADMIN'

class AdminDashboardView(AdminAccessMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_students'] = User.objects.filter(role='STUDENT', is_active=True).count()
        context['total_teachers'] = User.objects.filter(role='TEACHER', is_active=True).count()
        context['total_parents'] = User.objects.filter(role='PARENT', is_active=True).count()
        context['total_classes'] = Class.objects.count()
        context['total_subjects'] = Subject.objects.count()
        return context

# User Management

class UserListView(AdminAccessMixin, ListView):
    model = User
    template_name = 'core/user_list.html'
    context_object_name = 'users'
    ordering = ['-created_at']
    
    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

class UserCreateView(AdminAccessMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('admin_users')

    @transaction.atomic
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Create corresponding profile
        if user.role == 'STUDENT':
            StudentProfile.objects.create(user=user)
        elif user.role == 'TEACHER':
            TeacherProfile.objects.create(user=user)
        elif user.role == 'PARENT':
            ParentProfile.objects.create(user=user)
            
        messages.success(self.request, f"User {user.email} created successfully.")
        return super().form_valid(form)

class UserToggleActiveView(AdminAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f"User {user.email} status changed.")
        return redirect('admin_users')


# Academic Management

class AcademicYearListView(AdminAccessMixin, ListView):
    model = AcademicYear
    template_name = 'core/academic_year_list.html'
    context_object_name = 'academic_years'

class AcademicYearCreateView(AdminAccessMixin, CreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'core/academic_year_form.html'
    success_url = reverse_lazy('admin_academic_years')
    
    @transaction.atomic
    def form_valid(self, form):
        if form.cleaned_data.get('is_active'):
            # Deactivate all others
            AcademicYear.objects.update(is_active=False)
        return super().form_valid(form)

class AcademicYearUpdateView(AdminAccessMixin, UpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'core/academic_year_form.html'
    success_url = reverse_lazy('admin_academic_years')

    @transaction.atomic
    def form_valid(self, form):
        if form.cleaned_data.get('is_active'):
            # Deactivate all others
            AcademicYear.objects.exclude(pk=self.object.pk).update(is_active=False)
        return super().form_valid(form)


class ClassListView(AdminAccessMixin, ListView):
    model = Class
    template_name = 'core/class_list.html'
    context_object_name = 'classes'

class ClassCreateView(AdminAccessMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = 'core/class_form.html'
    success_url = reverse_lazy('admin_classes')

class ClassUpdateView(AdminAccessMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = 'core/class_form.html'
    success_url = reverse_lazy('admin_classes')


class SectionListView(AdminAccessMixin, ListView):
    model = Section
    template_name = 'core/section_list.html'
    context_object_name = 'sections'

class SectionCreateView(AdminAccessMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'core/section_form.html'
    success_url = reverse_lazy('admin_sections')

class SectionUpdateView(AdminAccessMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'core/section_form.html'
    success_url = reverse_lazy('admin_sections')


class SubjectListView(AdminAccessMixin, ListView):
    model = Subject
    template_name = 'core/subject_list.html'
    context_object_name = 'subjects'

class SubjectCreateView(AdminAccessMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'core/subject_form.html'
    success_url = reverse_lazy('admin_subjects')

class SubjectUpdateView(AdminAccessMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'core/subject_form.html'
    success_url = reverse_lazy('admin_subjects')


class ClassSubjectListView(AdminAccessMixin, ListView):
    model = ClassSubject
    template_name = 'core/class_subject_list.html'
    context_object_name = 'class_subjects'

class ClassSubjectCreateView(AdminAccessMixin, CreateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'core/class_subject_form.html'
    success_url = reverse_lazy('admin_class_subjects')

class ClassSubjectUpdateView(AdminAccessMixin, UpdateView):
    model = ClassSubject
    form_class = ClassSubjectForm
    template_name = 'core/class_subject_form.html'
    success_url = reverse_lazy('admin_class_subjects')




class AdminChapterListView(AdminAccessMixin, ListView):
    model=Chapter; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return Chapter.objects.select_related('class_subject__class_level','class_subject__subject').order_by('class_subject__class_level__level','order')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Chapters', create_url=str(reverse_lazy('admin_chapter_create'))); return c

class AdminChapterCreateView(AdminAccessMixin, CreateView):
    model=Chapter; fields=['class_subject','title','order']; template_name='core/entity_form.html'; success_url=reverse_lazy('admin_chapters')

class AdminChapterUpdateView(AdminAccessMixin, UpdateView):
    model=Chapter; fields=['class_subject','title','order']; template_name='core/entity_form.html'; success_url=reverse_lazy('admin_chapters')

class AdminLessonListView(AdminAccessMixin, ListView):
    model=Lesson; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return Lesson.objects.select_related('chapter__class_subject__subject','chapter__class_subject__class_level').order_by('chapter__class_subject__class_level__level','chapter__order','order')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Lessons', create_url=str(reverse_lazy('admin_lesson_create'))); return c

class AdminLessonCreateView(AdminAccessMixin, CreateView):
    model=Lesson; fields=['chapter','title','content','order']; template_name='core/entity_form.html'; success_url=reverse_lazy('admin_lessons')

class AdminLessonUpdateView(AdminAccessMixin, UpdateView):
    model=Lesson; fields=['chapter','title','content','order']; template_name='core/entity_form.html'; success_url=reverse_lazy('admin_lessons')

class AdminMaterialCreateView(AdminAccessMixin, CreateView):
    model=LearningMaterial
    fields=['class_subject','chapter','lesson','teacher','title','description','material_type','file','external_url','text_content','is_published']
    template_name='core/entity_form.html'
    success_url=reverse_lazy('admin_materials')

class AdminMaterialUpdateView(AdminAccessMixin, UpdateView):
    model=LearningMaterial
    fields=['class_subject','chapter','lesson','teacher','title','description','material_type','file','external_url','text_content','is_published']
    template_name='core/entity_form.html'
    success_url=reverse_lazy('admin_materials')

class AdminMaterialListView(AdminAccessMixin, ListView):
    model=LearningMaterial; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return LearningMaterial.objects.select_related('class_subject__subject','teacher__user').order_by('-created_at')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Learning Materials', create_url=str(reverse_lazy('admin_material_create'))); return c

class AdminAssignmentListView(AdminAccessMixin, ListView):
    model=Assignment; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return Assignment.objects.select_related('class_subject__subject','teacher__user','section').order_by('-created_at')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Assignments', create_url=None); return c

class AdminQuizListView(AdminAccessMixin, ListView):
    model=Quiz; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return Quiz.objects.select_related('class_subject__subject','teacher__user').order_by('-created_at')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Quizzes', create_url=None); return c

class AdminResultListView(AdminAccessMixin, ListView):
    model=QuizResult; template_name='core/entity_list.html'; context_object_name='objects'
    def get_queryset(self): return QuizResult.objects.select_related('attempt__quiz','attempt__student__user').order_by('-attempt__end_time')
    def get_context_data(self, **kwargs): c=super().get_context_data(**kwargs); c.update(page_title='Quiz Results', create_url=None); return c

class AdminReportView(AdminAccessMixin, TemplateView):
    template_name='core/reports.html'
    def get_context_data(self, **kwargs):
        c=super().get_context_data(**kwargs); c['stats']={'students':User.objects.filter(role='STUDENT').count(),'teachers':User.objects.filter(role='TEACHER').count(),'parents':User.objects.filter(role='PARENT').count(),'assignments':Assignment.objects.count(),'quizzes':Quiz.objects.count(),'submissions':AssignmentSubmission.objects.count(),'quiz_results':QuizResult.objects.count()}; return c

class AdminNotificationListView(AdminAccessMixin, ListView):
    model=Notification; template_name='core/notifications.html'; context_object_name='notifications'; paginate_by=25
    def get_queryset(self): return Notification.objects.select_related('recipient').order_by('-created_at')

class AdminSettingsView(AdminAccessMixin, TemplateView):
    template_name='core/settings.html'
    def get_context_data(self, **kwargs):
        c=super().get_context_data(**kwargs); c['debug']=settings.DEBUG; c['database_engine']=settings.DATABASES['default']['ENGINE']; c['ai_model']=getattr(settings,'AI_MODEL','Not configured'); return c
