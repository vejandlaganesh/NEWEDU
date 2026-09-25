from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from apps.parents.models import ParentProfile
from apps.students.models import StudentProfile
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.academics.models import Enrollment, AcademicYear
from apps.quizzes.models import Quiz, QuizResult
from apps.notifications.models import Notification
from apps.accounts.models import User
from django.urls import reverse_lazy
from django.db.models import Q

class ParentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'PARENT'
        
    def get_parent_profile(self):
        return self.request.user.parent_profile
        
    def get_children(self):
        return self.get_parent_profile().children.all()
        
    def get_selected_child(self):
        children = self.get_children()
        
        if not children.exists():
            return None
            
        child_id = self.request.GET.get('child_id') or self.request.session.get('selected_child_id')
        
        if child_id:
            try:
                child = children.get(id=child_id)
                self.request.session['selected_child_id'] = child.id
                return child
            except StudentProfile.DoesNotExist:
                if 'child_id' in self.request.GET:
                    raise PermissionDenied("You are not authorized to view this child's information.")
                pass
                
        # Default to first child
        first_child = children.first()
        self.request.session['selected_child_id'] = first_child.id
        return first_child
        
    def get_child_enrollment(self, child):
        if not child:
            return None
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            return Enrollment.objects.get(student=child, academic_year=active_year)
        except (AcademicYear.DoesNotExist, Enrollment.DoesNotExist):
            return None

class ParentDashboardView(ParentAccessMixin, TemplateView):
    template_name = 'parents/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_child = self.get_selected_child()
        context['children'] = self.get_children()
        context['selected_child'] = selected_child
        enrollment = self.get_child_enrollment(selected_child)
        context['enrollment'] = enrollment
        if selected_child and enrollment:
            context['recent_results'] = QuizResult.objects.filter(attempt__student=selected_child, attempt__quiz__academic_year=enrollment.academic_year).select_related('attempt__quiz').order_by('-attempt__end_time')[:5]
            context['pending_assignments'] = Assignment.objects.filter(academic_year=enrollment.academic_year, section=enrollment.section).exclude(submissions__student=selected_child).count()
            context['upcoming_quizzes'] = Quiz.objects.filter(academic_year=enrollment.academic_year, class_subject__class_level=enrollment.class_level, is_published=True).filter(Q(section=enrollment.section) | Q(section__isnull=True)).count()
        return context

class ParentAssignmentListView(ParentAccessMixin, ListView):
    template_name = 'parents/assignment_list.html'
    context_object_name = 'assignments'
    
    def get_queryset(self):
        child = self.get_selected_child()
        if not child:
            return Assignment.objects.none()
            
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            enrollment = Enrollment.objects.get(student=child, academic_year=active_year)
            return Assignment.objects.filter(
                academic_year=active_year,
                section=enrollment.section,
                class_subject__class_level=enrollment.class_level
            )
        except (AcademicYear.DoesNotExist, Enrollment.DoesNotExist):
            return Assignment.objects.none()
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child = self.get_selected_child()
        if child:
            submissions = AssignmentSubmission.objects.filter(student=child)
            sub_map = {sub.assignment_id: sub for sub in submissions}
            context['submissions_map'] = sub_map
        context['children'] = self.get_children()
        context['selected_child'] = child
        return context

from apps.reports.services import get_student_performance, get_student_subject_performance, get_student_assessment_trend

class ParentReportsView(ParentAccessMixin, TemplateView):
    template_name = 'parents/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_child = self.get_selected_child()
        
        context['children'] = self.get_children()
        context['selected_child'] = selected_child
        
        if not selected_child:
            context['no_data'] = True
            return context
            
        enrollment = self.get_child_enrollment(selected_child)
        if not enrollment:
            context['no_data'] = True
            return context
            
        academic_year = enrollment.academic_year
        
        context['performance'] = get_student_performance(selected_child, academic_year)
        context['subject_performance'] = get_student_subject_performance(selected_child, academic_year)
        context['assessment_trend'] = get_student_assessment_trend(selected_child, academic_year)
        
        return context

class ParentResultsView(ParentAccessMixin, TemplateView):
    template_name = 'parents/results.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        child = self.get_selected_child(); context['children'] = self.get_children(); context['selected_child'] = child
        enrollment = self.get_child_enrollment(child)
        context['quiz_results'] = QuizResult.objects.filter(attempt__student=child, attempt__quiz__academic_year=enrollment.academic_year).select_related('attempt__quiz').order_by('-attempt__end_time') if child and enrollment else QuizResult.objects.none()
        context['graded_submissions'] = AssignmentSubmission.objects.filter(student=child, status='GRADED').select_related('assignment','assignment__class_subject__subject').order_by('-updated_at') if child else AssignmentSubmission.objects.none()
        return context

class ParentNotificationsView(ParentAccessMixin, ListView):
    template_name = 'parents/notifications.html'; context_object_name = 'notifications'; paginate_by = 20
    def get_queryset(self): return Notification.objects.filter(recipient=self.request.user)
    def get_context_data(self, **kwargs):
        c=super().get_context_data(**kwargs); c['children']=self.get_children(); c['selected_child']=self.get_selected_child(); return c

class ParentProfileView(ParentAccessMixin, UpdateView):
    model = User; fields = ['first_name','last_name']; template_name='parents/profile.html'; success_url=reverse_lazy('parent_profile')
    def get_object(self, queryset=None): return self.request.user

class ParentSettingsView(ParentAccessMixin, TemplateView):
    template_name='parents/settings.html'
    def get_context_data(self, **kwargs):
        c=super().get_context_data(**kwargs); c['children']=self.get_children(); c['selected_child']=self.get_selected_child(); return c
