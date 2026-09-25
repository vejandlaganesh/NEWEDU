from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from apps.academics.models import AcademicYear, Enrollment, ClassSubject, Chapter, Lesson, TeacherAssignment, Class, Section, Subject
from apps.students.models import StudentProfile
from apps.notifications.services import NotificationService
from apps.notifications.models import Notification
from apps.accounts.models import User
from django.urls import reverse_lazy

class TeacherAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'TEACHER'
        
    def get_active_assignments(self):
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            return TeacherAssignment.objects.filter(teacher=self.request.user.teacher_profile, academic_year=active_year)
        except (AcademicYear.DoesNotExist):
            return TeacherAssignment.objects.none()

    def get_assigned_sections(self):
        return [a.section for a in self.get_active_assignments()]

    def get_assigned_class_subjects(self):
        return [a.class_subject for a in self.get_active_assignments()]

class TeacherDashboardView(TeacherAccessMixin, TemplateView):
    template_name = 'teachers/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = self.get_active_assignments()
        
        # Calculate KPIs
        assigned_sections = list(set([a.section for a in assignments]))
        assigned_subjects = list(set([a.class_subject.subject for a in assignments]))
        student_count = Enrollment.objects.filter(
            academic_year__is_active=True,
            section__in=assigned_sections
        ).count()
        
        context['classes_count'] = len(assigned_sections)
        context['subjects_count'] = len(assigned_subjects)
        context['student_count'] = student_count
        context['recent_notifications'] = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')[:5]
        return context

class TeacherClassListView(TeacherAccessMixin, ListView):
    template_name = 'teachers/class_list.html'
    context_object_name = 'sections'
    
    def get_queryset(self):
        return list(set(self.get_assigned_sections()))

class TeacherSubjectListView(TeacherAccessMixin, ListView):
    template_name = 'teachers/subject_list.html'
    context_object_name = 'subjects'
    
    def get_queryset(self):
        return list(set(self.get_assigned_class_subjects()))

class TeacherStudentListView(TeacherAccessMixin, ListView):
    template_name = 'teachers/student_list.html'
    context_object_name = 'enrollments'
    
    def get_queryset(self):
        assigned_sections = self.get_assigned_sections()
        return Enrollment.objects.filter(
            academic_year__is_active=True,
            section__in=assigned_sections
        ).select_related('student__user', 'class_level', 'section')

class TeacherMaterialListView(TeacherAccessMixin, ListView):
    template_name = 'teachers/material_list.html'
    context_object_name = 'class_subjects'
    
    def get_queryset(self):
        return list(set(self.get_assigned_class_subjects()))

class ChapterCreateView(TeacherAccessMixin, CreateView):
    model = Chapter
    fields = ['title', 'order']
    template_name = 'teachers/chapter_form.html'
    success_url = reverse_lazy('teacher_materials')

    def dispatch(self, request, *args, **kwargs):
        self.class_subject = get_object_or_404(ClassSubject, pk=kwargs['class_subject_id'])
        if self.class_subject not in self.get_assigned_class_subjects():
            raise PermissionDenied("You are not assigned to this subject.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.class_subject = self.class_subject
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_subject'] = self.class_subject
        return context

class ChapterUpdateView(TeacherAccessMixin, UpdateView):
    model = Chapter
    fields = ['title', 'order']
    template_name = 'teachers/chapter_form.html'
    success_url = reverse_lazy('teacher_materials')
    
    def get_queryset(self):
        # Strict filtering to only allow chapters belonging to assigned subjects
        assigned_cs = self.get_assigned_class_subjects()
        return Chapter.objects.filter(class_subject__in=assigned_cs)

class LessonCreateView(TeacherAccessMixin, CreateView):
    model = Lesson
    fields = ['title', 'content', 'order']
    template_name = 'teachers/lesson_form.html'
    success_url = reverse_lazy('teacher_materials')

    def dispatch(self, request, *args, **kwargs):
        self.chapter = get_object_or_404(Chapter, pk=kwargs['chapter_id'])
        if self.chapter.class_subject not in self.get_assigned_class_subjects():
            raise PermissionDenied("You are not assigned to this subject.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.chapter = self.chapter
        response = super().form_valid(form)
        NotificationService.notify_lesson_created(form.instance)
        return response
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.chapter
        return context

class LessonUpdateView(TeacherAccessMixin, UpdateView):
    model = Lesson
    fields = ['title', 'content', 'order']
    template_name = 'teachers/lesson_form.html'
    success_url = reverse_lazy('teacher_materials')
    
    def get_queryset(self):
        # Strict filtering to only allow lessons belonging to assigned subjects
        assigned_cs = self.get_assigned_class_subjects()
        return Lesson.objects.filter(chapter__class_subject__in=assigned_cs)

from apps.content.models import LearningMaterial
from apps.content.forms import LearningMaterialForm

class TeacherMaterialCreateView(TeacherAccessMixin, CreateView):
    model = LearningMaterial
    form_class = LearningMaterialForm
    template_name = 'teachers/material_form.html'
    success_url = reverse_lazy('teacher_materials')
    def get_form_kwargs(self):
        kwargs=super().get_form_kwargs(); kwargs['teacher_profile']=self.request.user.teacher_profile; return kwargs
    def form_valid(self, form):
        if not self.get_active_assignments().filter(class_subject=form.cleaned_data['class_subject']).exists():
            raise PermissionDenied('You are not assigned to this subject.')
        form.instance.teacher=self.request.user.teacher_profile
        return super().form_valid(form)

class TeacherMaterialUpdateView(TeacherAccessMixin, UpdateView):
    model=LearningMaterial; form_class=LearningMaterialForm; template_name='teachers/material_form.html'; success_url=reverse_lazy('teacher_materials')
    def get_queryset(self): return LearningMaterial.objects.filter(teacher=self.request.user.teacher_profile)
    def get_form_kwargs(self):
        kwargs=super().get_form_kwargs(); kwargs['teacher_profile']=self.request.user.teacher_profile; return kwargs

class TeacherNotificationsView(TeacherAccessMixin, ListView):
    model=Notification; template_name='teachers/notifications.html'; context_object_name='notifications'; paginate_by=20
    def get_queryset(self): return Notification.objects.filter(recipient=self.request.user)

class TeacherProfileView(TeacherAccessMixin, UpdateView):
    model=User; fields=['first_name','last_name']; template_name='teachers/profile.html'; success_url=reverse_lazy('teacher_profile')
    def get_object(self, queryset=None): return self.request.user

class TeacherSettingsView(TeacherAccessMixin, TemplateView):
    template_name='teachers/settings.html'

# Assignment Views

from apps.assignments.models import Assignment, AssignmentSubmission
from .forms import AssignmentForm, AssignmentGradingForm

class TeacherAssignmentListView(TeacherAccessMixin, ListView):
    template_name = 'teachers/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            return Assignment.objects.filter(teacher=self.request.user.teacher_profile, academic_year=active_year)
        except AcademicYear.DoesNotExist:
            return Assignment.objects.none()

class TeacherAssignmentCreateView(TeacherAccessMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'teachers/assignment_form.html'
    success_url = reverse_lazy('teacher_assignments')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher_profile'] = self.request.user.teacher_profile
        return kwargs
        
    def form_valid(self, form):
        active_year = AcademicYear.objects.get(is_active=True)
        form.instance.academic_year = active_year
        form.instance.teacher = self.request.user.teacher_profile
        
        # Verify the teacher is assigned to this specific class subject and section
        assignments = self.get_active_assignments()
        is_assigned = assignments.filter(
            class_subject=form.instance.class_subject, 
            section=form.instance.section
        ).exists()
        
        if not is_assigned:
            raise PermissionDenied("You are not assigned to this class and subject combination.")
            
        response = super().form_valid(form)
        NotificationService.notify_assignment_created(form.instance)
        return response

class TeacherAssignmentDetailView(TeacherAccessMixin, ListView):
    # This view lists submissions for a specific assignment
    template_name = 'teachers/assignment_detail.html'
    context_object_name = 'enrollments'
    
    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(Assignment, pk=kwargs['pk'])
        if self.assignment.teacher != request.user.teacher_profile:
            raise PermissionDenied("You can only view your own assignments.")
        return super().dispatch(request, *args, **kwargs)
        
    def get_queryset(self):
        # Return all students enrolled in the assignment's section
        return Enrollment.objects.filter(
            academic_year=self.assignment.academic_year,
            section=self.assignment.section
        ).select_related('student__user')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.assignment
        
        # Build a mapping of student_id -> submission
        submissions = self.assignment.submissions.all()
        sub_map = {sub.student_id: sub for sub in submissions}
        context['submissions_map'] = sub_map
        return context

class TeacherSubmissionGradeView(TeacherAccessMixin, UpdateView):
    model = AssignmentSubmission
    form_class = AssignmentGradingForm
    template_name = 'teachers/submission_grade_form.html'
    
    def get_object(self, queryset=None):
        assignment = get_object_or_404(Assignment, pk=self.kwargs['assignment_pk'])
        if assignment.teacher != self.request.user.teacher_profile:
            raise PermissionDenied("You can only grade your own assignments.")
            
        student_profile = get_object_or_404(StudentProfile, pk=self.kwargs['student_pk'])
        
        # Ensure student is enrolled in the section
        enrolled = Enrollment.objects.filter(
            academic_year=assignment.academic_year,
            section=assignment.section,
            student=student_profile
        ).exists()
        
        if not enrolled:
            raise PermissionDenied("Student is not enrolled in this section.")
            
        # Get or create submission (it might be PENDING)
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=student_profile,
            defaults={'status': 'PENDING'}
        )
        return submission
        
    def form_valid(self, form):
        if form.cleaned_data.get('grade') is not None:
            form.instance.status = 'GRADED'
            response = super().form_valid(form)
            NotificationService.notify_assignment_graded(form.instance)
            return response
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('teacher_assignment_detail', kwargs={'pk': self.object.assignment.id})

from apps.reports.services import get_teacher_class_performance, get_teacher_assignment_stats, get_weak_topics

class TeacherReportsView(TeacherAccessMixin, TemplateView):
    template_name = 'teachers/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher_profile
        try:
            from apps.academics.models import AcademicYear
            academic_year = AcademicYear.objects.get(is_active=True)
            
            context['class_performance'] = get_teacher_class_performance(teacher, academic_year)
            context['assignment_stats'] = get_teacher_assignment_stats(teacher, academic_year)
            context['weak_topics'] = get_weak_topics(teacher, academic_year)
            
        except AcademicYear.DoesNotExist:
            context['no_data'] = True
            
        return context


import json
from django.http import JsonResponse
from django.views import View
from apps.ai_assistant.services.ai_service import GeminiService
from apps.ai_assistant.services.exceptions import AIConfigurationError, AIServiceUnavailable, AIRateLimitExceeded, AITimeoutError, AIInvalidResponse, AIValidationError
from django.db import transaction
from apps.content.models import GeneratedContent
from apps.quizzes.models import Quiz, Question

class TeacherAIToolsDashboardView(TeacherAccessMixin, TemplateView):
    template_name = 'teachers/ai_tools/dashboard.html'

# --- API Endpoints for Dropdowns ---

class TeacherAIApiSubjectsView(TeacherAccessMixin, View):
    def get(self, request, *args, **kwargs):
        assignments = self.get_active_assignments().select_related('class_subject__class_level', 'class_subject__subject')
        
        # Group unique class_subjects
        cs_map = {}
        for a in assignments:
            cs = a.class_subject
            if cs.id not in cs_map:
                cs_map[cs.id] = {
                    'id': cs.id,
                    'class_name': cs.class_level.name,
                    'subject_name': cs.subject.name,
                    'display': f"{cs.class_level.name} - {cs.subject.name}"
                }
                
        return JsonResponse({'subjects': list(cs_map.values())})

class TeacherAIApiChaptersView(TeacherAccessMixin, View):
    def get(self, request, *args, **kwargs):
        class_subject_id = request.GET.get('class_subject_id')
        if not class_subject_id:
            return JsonResponse({'chapters': []})
            
        # Validate teacher has access to this class_subject
        assignments = self.get_active_assignments()
        has_access = assignments.filter(class_subject_id=class_subject_id).exists()
        
        if not has_access:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        chapters = Chapter.objects.filter(class_subject_id=class_subject_id).order_by('order')
        data = [{'id': c.id, 'title': c.title} for c in chapters]
        return JsonResponse({'chapters': data})

# --- Generators ---

class TeacherAIContentGeneratorView(TeacherAccessMixin, TemplateView):
    template_name = 'teachers/ai_tools/content_generator.html'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            cs_id = data.get('class_subject_id')
            chapter_id = data.get('chapter_id')
            topic = data.get('topic')
            difficulty = data.get('difficulty')
            content_type = data.get('content_type')
            
            if not all([cs_id, topic, difficulty, content_type]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
                
            # Verify assignment
            if not self.get_active_assignments().filter(class_subject_id=cs_id).exists():
                return JsonResponse({'error': 'Unauthorized class/subject'}, status=403)
                
            cs = get_object_or_404(ClassSubject, id=cs_id)
            chapter_name = "General"
            if chapter_id:
                chapter = get_object_or_404(Chapter, id=chapter_id, class_subject_id=cs_id)
                chapter_name = chapter.title
                
            ai_service = GeminiService()
            structured_data, _ = ai_service.generate_teacher_content(
                class_name=cs.class_level.name,
                subject_name=cs.subject.name,
                chapter_name=chapter_name,
                topic=topic,
                difficulty=difficulty,
                content_type=content_type
            )
            
            return JsonResponse({'title': structured_data.title, 'content': structured_data.content})
            
        except (AIServiceUnavailable, AIRateLimitExceeded, AITimeoutError, AIInvalidResponse, AIValidationError) as e:
            return JsonResponse({'error': str(e)}, status=503)
        except Exception as e:
            return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

class TeacherAIQuizGeneratorView(TeacherAccessMixin, TemplateView):
    template_name = 'teachers/ai_tools/quiz_generator.html'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            cs_id = data.get('class_subject_id')
            chapter_id = data.get('chapter_id')
            difficulty = data.get('difficulty')
            question_count = int(data.get('question_count', 5))
            question_type = data.get('question_type', 'Multiple Choice')
            
            if not cs_id:
                return JsonResponse({'error': 'Missing class/subject'}, status=400)
                
            # Verify assignment
            if not self.get_active_assignments().filter(class_subject_id=cs_id).exists():
                return JsonResponse({'error': 'Unauthorized class/subject'}, status=403)
                
            cs = get_object_or_404(ClassSubject, id=cs_id)
            chapter_name = "General"
            if chapter_id:
                chapter = get_object_or_404(Chapter, id=chapter_id, class_subject_id=cs_id)
                chapter_name = chapter.title
                
            ai_service = GeminiService()
            structured_data, _ = ai_service.generate_teacher_quiz(
                class_name=cs.class_level.name,
                subject_name=cs.subject.name,
                chapter_name=chapter_name,
                difficulty=difficulty,
                question_count=question_count,
                question_type=question_type
            )
            
            # Serialize structured_data (GeneratedQuizSchema)
            response_data = structured_data.model_dump()
            return JsonResponse(response_data)
            
        except (AIServiceUnavailable, AIRateLimitExceeded, AITimeoutError, AIInvalidResponse, AIValidationError) as e:
            return JsonResponse({'error': str(e)}, status=503)
        except Exception as e:
            return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

# --- Save Handlers ---

class SaveGeneratedContentView(TeacherAccessMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            cs_id = data.get('class_subject_id')
            chapter_id = data.get('chapter_id')
            
            if not cs_id or not data.get('title') or not data.get('content'):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
                
            if not self.get_active_assignments().filter(class_subject_id=cs_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)
                
            with transaction.atomic():
                GeneratedContent.objects.create(
                    teacher=request.user.teacher_profile,
                    class_subject_id=cs_id,
                    chapter_id=chapter_id if chapter_id else None,
                    topic=data.get('topic', 'General'),
                    content_type=data.get('content_type', 'Unspecified'),
                    difficulty=data.get('difficulty', 'Medium'),
                    title=data.get('title'),
                    content=data.get('content'),
                    status='DRAFT'
                )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class SaveGeneratedQuizView(TeacherAccessMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            cs_id = data.get('class_subject_id')
            chapter_id = data.get('chapter_id')
            quiz_data = data.get('quiz_data')
            
            if not cs_id or not quiz_data or not quiz_data.get('questions'):
                return JsonResponse({'error': 'Invalid payload'}, status=400)
                
            if not self.get_active_assignments().filter(class_subject_id=cs_id).exists():
                return JsonResponse({'error': 'Unauthorized access'}, status=403)
                
            # Get the first active year to associate with the quiz
            active_year = AcademicYear.objects.get(is_active=True)
                
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    academic_year=active_year,
                    class_subject_id=cs_id,
                    chapter_id=chapter_id if chapter_id else None,
                    teacher=request.user.teacher_profile,
                    title=quiz_data.get('title', 'AI Generated Quiz'),
                    description=quiz_data.get('description', ''),
                    duration=quiz_data.get('duration', 30), # Default 30 mins
                    passing_score=quiz_data.get('passing_score', 50.0),
                    is_published=False
                )
                
                questions_to_create = []
                for q_data in quiz_data['questions']:
                    questions_to_create.append(Question(
                        quiz=quiz,
                        text=q_data['question_text'],
                        question_type='MULTIPLE_CHOICE',
                        option_a=q_data['option_a'],
                        option_b=q_data['option_b'],
                        option_c=q_data['option_c'],
                        option_d=q_data['option_d'],
                        correct_option=q_data['correct_option'],
                        marks=q_data.get('marks', 1),
                        explanation=q_data.get('explanation', '')
                    ))
                    
                Question.objects.bulk_create(questions_to_create)
                
            return JsonResponse({'status': 'success'})
        except AcademicYear.DoesNotExist:
            return JsonResponse({'error': 'No active academic year.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
