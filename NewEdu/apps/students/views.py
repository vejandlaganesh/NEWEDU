from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from apps.academics.models import AcademicYear, Enrollment, ClassSubject, Chapter, Lesson
from apps.accounts.models import User
from apps.assignments.models import Assignment, AssignmentSubmission
from .forms import AssignmentSubmissionForm
from django.utils import timezone
from django.conf import settings

class StudentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'STUDENT'
        
    def get_current_enrollment(self):
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            return Enrollment.objects.get(student=self.request.user.student_profile, academic_year=active_year)
        except (AcademicYear.DoesNotExist, Enrollment.DoesNotExist):
            return None

class StudentDashboardView(StudentAccessMixin, TemplateView):
    template_name = 'students/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.get_current_enrollment()
        context['enrollment'] = enrollment
        if enrollment:
            context['subjects'] = ClassSubject.objects.filter(class_level=enrollment.class_level)
            
            # Fetch assignment and quiz counts for the dashboard
            from apps.assignments.models import Assignment
            context['assignment_count'] = Assignment.objects.filter(
                academic_year=enrollment.academic_year,
                section=enrollment.section,
                class_subject__class_level=enrollment.class_level
            ).count()

            from apps.quizzes.models import Quiz
            from django.db import models
            context['quiz_count'] = Quiz.objects.filter(
                is_published=True,
                academic_year=enrollment.academic_year,
                class_subject__class_level=enrollment.class_level
            ).filter(
                models.Q(section__isnull=True) | models.Q(section=enrollment.section)
            ).count()
            
            # Fetch latest recommendation for dashboard widget
            latest_rec = AIRecommendation.objects.filter(
                student=self.request.user.student_profile,
                academic_year=enrollment.academic_year
            ).first()
            context['latest_recommendation'] = latest_rec
            
        return context

class MySubjectsView(StudentAccessMixin, ListView):
    template_name = 'students/subject_list.html'
    context_object_name = 'subjects'
    
    def get_queryset(self):
        enrollment = self.get_current_enrollment()
        if enrollment:
            return ClassSubject.objects.filter(class_level=enrollment.class_level)
        return ClassSubject.objects.none()

class SubjectDetailView(StudentAccessMixin, DetailView):
    model = ClassSubject
    template_name = 'students/subject_detail.html'
    context_object_name = 'subject'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        enrollment = self.get_current_enrollment()
        if not enrollment or obj.class_level != enrollment.class_level:
            raise PermissionDenied("You are not enrolled in this class.")
        return obj

class ChapterDetailView(StudentAccessMixin, DetailView):
    template_name = 'students/chapter_detail.html'
    context_object_name = 'chapter'
    
    def get_queryset(self):
        enrollment = self.get_current_enrollment()
        if enrollment:
            return Chapter.objects.filter(class_subject__class_level=enrollment.class_level)
        return Chapter.objects.none()

class LessonDetailView(StudentAccessMixin, DetailView):
    model = Lesson
    template_name = 'students/lesson_detail.html'
    context_object_name = 'lesson'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        enrollment = self.get_current_enrollment()
        if not enrollment or obj.chapter.class_subject.class_level != enrollment.class_level:
            raise PermissionDenied("You are not enrolled in this class.")
        return obj

class StudentAssignmentListView(StudentAccessMixin, ListView):
    template_name = 'students/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        enrollment = self.get_current_enrollment()
        if not enrollment:
            return Assignment.objects.none()
        return Assignment.objects.filter(
            academic_year=enrollment.academic_year,
            section=enrollment.section,
            class_subject__class_level=enrollment.class_level
        )
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = AssignmentSubmission.objects.filter(student=self.request.user.student_profile)
        # Create map of assignment_id -> submission
        sub_map = {sub.assignment_id: sub for sub in submissions}
        context['submissions_map'] = sub_map
        return context

class StudentAssignmentDetailView(StudentAccessMixin, UpdateView):
    model = AssignmentSubmission
    form_class = AssignmentSubmissionForm
    template_name = 'students/assignment_detail.html'
    
    def get_object(self, queryset=None):
        assignment = get_object_or_404(Assignment, pk=self.kwargs['pk'])
        enrollment = self.get_current_enrollment()
        
        if not enrollment or assignment.academic_year != enrollment.academic_year or assignment.section != enrollment.section or assignment.class_subject.class_level != enrollment.class_level:
            raise PermissionDenied("You cannot access this assignment.")
            
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=self.request.user.student_profile,
            defaults={'status': 'PENDING'}
        )
        return submission
        
    def form_valid(self, form):
        if self.object.status == 'GRADED':
            raise PermissionDenied("This assignment has already been graded and cannot be modified.")
            
        form.instance.status = 'SUBMITTED'
        form.instance.submitted_at = timezone.now()
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('student_assignments')

class StudentProfileUpdateView(StudentAccessMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name']
    template_name = 'students/profile.html'
    success_url = reverse_lazy('student_profile')
    
    def get_object(self):
        return self.request.user

from apps.reports.services import get_student_performance, get_student_subject_performance, get_student_assessment_trend

from apps.ai_assistant.models import AIConversation, AIRecommendation
from apps.quizzes.models import QuizResult
from apps.notifications.models import Notification
from apps.reports.services import get_student_performance, get_student_weak_topics
from apps.ai_assistant.services.ai_service import GeminiService
from apps.notifications.services import NotificationService
from django.http import JsonResponse
import json

class StudentAIAssistantView(StudentAccessMixin, TemplateView):
    template_name = 'students/ai_assistant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.student_profile
        enrollment = self.get_current_enrollment()
        
        # ... (Existing chat logic can remain or be replaced by the recommendation UI)
        # We will keep chat for now, and just add the latest recommendation
        
        if enrollment:
            latest_rec = AIRecommendation.objects.filter(
                student=student_profile, 
                academic_year=enrollment.academic_year
            ).first()
            context['latest_recommendation'] = latest_rec
            
        return context

    def post(self, request, *args, **kwargs):
        student_profile = request.user.student_profile
        enrollment = self.get_current_enrollment()
        
        if not enrollment:
            return JsonResponse({'error': 'No active enrollment found.'}, status=400)
            
        academic_year = enrollment.academic_year
        
        # Check cooldown (e.g. limit to 1 per hour)
        latest_rec = AIRecommendation.objects.filter(
            student=student_profile, 
            academic_year=academic_year
        ).first()
        
        if latest_rec:
            time_since = timezone.now() - latest_rec.created_at
            if time_since.total_seconds() < 3600:
                return JsonResponse({'error': 'You can only generate a new recommendation once per hour. Please review your current plan.'}, status=429)
        
        # Gather facts
        perf = get_student_performance(student_profile, academic_year)
        weak_topics = get_student_weak_topics(student_profile, academic_year)
        
        if perf.get('assignments_completed', 0) + perf.get('quizzes_completed', 0) < getattr(settings, 'AI_RECOMMENDATION_MIN_DATA_POINTS', 3):
            return JsonResponse({'error': 'Not enough data yet. Complete more assignments and quizzes to get a personalized plan.'}, status=400)
            
        # Prepare context for AI
        context_data = {
            'overall_assignment_avg': perf.get('avg_assignment_score'),
            'overall_quiz_avg': perf.get('avg_quiz_score'),
            'weak_topics': [
                {
                    'subject': wt['subject_name'], 
                    'chapter': wt['chapter_name'], 
                    'score': wt['overall_avg']
                } for wt in weak_topics
            ]
        }
        
        # Call AI
        try:
            ai_service = GeminiService()
            rec_schema, _ = ai_service.generate_student_recommendation(context_data)
            
            # Validate output topics exist in context
            valid_weak_chapters = [wt['chapter_name'].lower() for wt in weak_topics]
            filtered_topics = []
            for t in rec_schema.recommended_topics:
                if t.lower() in valid_weak_chapters:
                    filtered_topics.append(t)
                    
            rec_schema.recommended_topics = filtered_topics
            
            # Save
            rec = AIRecommendation.objects.create(
                student=student_profile,
                academic_year=academic_year,
                recommendation=rec_schema.model_dump(),
                source_data=context_data,
                reason="Generated from recent performance data.",
                status='COMPLETED'
            )
            
            NotificationService.notify_ai_recommendation_ready(rec)
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'error': f'Failed to generate recommendation: {str(e)}'}, status=500)

class StudentReportsView(StudentAccessMixin, TemplateView):
    template_name = 'students/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.get_current_enrollment()
        if not enrollment:
            context['no_data'] = True
            return context
            
        student = self.request.user.student_profile
        academic_year = enrollment.academic_year
        
        context['performance'] = get_student_performance(student, academic_year)
        context['subject_performance'] = get_student_subject_performance(student, academic_year)
        context['assessment_trend'] = get_student_assessment_trend(student, academic_year)
        
        return context



class StudentResultsView(StudentAccessMixin, TemplateView):
    template_name = 'students/results.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.student_profile
        enrollment = self.get_current_enrollment()
        context['quiz_results'] = QuizResult.objects.filter(attempt__student=student, attempt__quiz__academic_year=enrollment.academic_year).select_related('attempt__quiz').order_by('-attempt__end_time') if enrollment else QuizResult.objects.none()
        context['graded_submissions'] = AssignmentSubmission.objects.filter(student=student, status='GRADED').select_related('assignment','assignment__class_subject__subject').order_by('-updated_at')
        return context

class StudentNotificationsView(StudentAccessMixin, ListView):
    template_name = 'students/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    def get_queryset(self): return Notification.objects.filter(recipient=self.request.user)

class StudentSettingsView(StudentAccessMixin, TemplateView):
    template_name = 'students/settings.html'

