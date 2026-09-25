from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from .models import Quiz, Question, QuizAttempt, QuizAnswer, QuizResult
from .forms import QuizForm, QuestionForm, QuizSubmissionForm
from .services import evaluate_quiz_attempt
from apps.academics.models import AcademicYear, Enrollment
from apps.teachers.views import TeacherAccessMixin
from apps.students.views import StudentAccessMixin
from apps.parents.views import ParentAccessMixin
from apps.notifications.services import NotificationService

# --- TEACHER VIEWS ---

class TeacherQuizListView(TeacherAccessMixin, ListView):
    template_name = 'quizzes/teacher_quiz_list.html'
    context_object_name = 'quizzes'
    
    def get_queryset(self):
        return Quiz.objects.filter(teacher=self.request.user.teacher_profile)

class TeacherQuizCreateView(TeacherAccessMixin, CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'quizzes/teacher_quiz_form.html'
    success_url = reverse_lazy('teacher_quizzes')
    
    def form_valid(self, form):
        active_year = AcademicYear.objects.get(is_active=True)
        form.instance.academic_year = active_year
        form.instance.teacher = self.request.user.teacher_profile
        
        # Verify the teacher is assigned to this specific class subject and section (if section is provided)
        assignments = self.get_active_assignments()
        is_assigned = False
        for assignment in assignments:
            if assignment.class_subject == form.instance.class_subject:
                if form.instance.section is None or assignment.section == form.instance.section:
                    is_assigned = True
                    break
        
        if not is_assigned:
            raise PermissionDenied("You are not assigned to this class and subject/section combination.")
            
        return super().form_valid(form)

class TeacherQuizDetailView(TeacherAccessMixin, DetailView):
    model = Quiz
    template_name = 'quizzes/teacher_quiz_detail.html'
    context_object_name = 'quiz'
    
    def get_object(self, queryset=None):
        quiz = super().get_object(queryset)
        if quiz.teacher != self.request.user.teacher_profile:
            raise PermissionDenied("You can only view your own quizzes.")
        return quiz
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        # Get attempts and results
        context['attempts'] = self.object.attempts.all()
        return context

class TeacherQuizPublishView(TeacherAccessMixin, View):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        if quiz.teacher != request.user.teacher_profile:
            raise PermissionDenied("You can only publish your own quizzes.")
            
        if not quiz.is_published:
            try:
                # model clean will validate that there are questions
                quiz.is_published = True
                quiz.clean()
                quiz.save()
                messages.success(request, "Quiz published successfully.")
                NotificationService.notify_quiz_published(quiz)
            except Exception as e:
                messages.error(request, str(e))
                
        return redirect('teacher_quiz_detail', pk=pk)

class TeacherQuestionCreateView(TeacherAccessMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'quizzes/teacher_question_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=kwargs['quiz_pk'])
        if self.quiz.teacher != request.user.teacher_profile:
            raise PermissionDenied("You can only modify your own quizzes.")
        if self.quiz.has_attempts():
            raise PermissionDenied("Cannot add questions to a quiz that has already been attempted.")
        return super().dispatch(request, *args, **kwargs)
        
    def form_valid(self, form):
        form.instance.quiz = self.quiz
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('teacher_quiz_detail', kwargs={'pk': self.quiz.pk})

# --- STUDENT VIEWS ---

class StudentQuizListView(StudentAccessMixin, ListView):
    template_name = 'quizzes/student_quiz_list.html'
    context_object_name = 'quizzes'
    
    def get_queryset(self):
        enrollment = self.get_current_enrollment()
        if not enrollment:
            return Quiz.objects.none()
            
        # Get published quizzes for the student's class subject and section
        return Quiz.objects.filter(
            is_published=True,
            academic_year=enrollment.academic_year,
            class_subject__class_level=enrollment.class_level
        ).filter(
            models.Q(section__isnull=True) | models.Q(section=enrollment.section)
        )
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass information about previous attempts
        attempts = QuizAttempt.objects.filter(student=self.request.user.student_profile)
        attempts_map = {}
        for attempt in attempts:
            if attempt.quiz_id not in attempts_map:
                attempts_map[attempt.quiz_id] = []
            attempts_map[attempt.quiz_id].append(attempt)
        context['attempts_map'] = attempts_map
        return context

class StudentQuizDetailView(StudentAccessMixin, DetailView):
    model = Quiz
    template_name = 'quizzes/student_quiz_detail.html'
    context_object_name = 'quiz'
    
    def get_object(self, queryset=None):
        quiz = super().get_object(queryset)
        enrollment = self.get_current_enrollment()
        
        if not quiz.is_published:
            raise PermissionDenied("This quiz is not published.")
            
        if not enrollment or quiz.academic_year != enrollment.academic_year or quiz.class_subject.class_level != enrollment.class_level:
            raise PermissionDenied("You cannot access this quiz.")
            
        if quiz.section and quiz.section != enrollment.section:
            raise PermissionDenied("You cannot access this quiz.")
            
        return quiz
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if student has remaining attempts
        attempts_count = QuizAttempt.objects.filter(
            quiz=self.object,
            student=self.request.user.student_profile
        ).count()
        context['can_attempt'] = attempts_count < self.object.max_attempts
        context['attempts'] = QuizAttempt.objects.filter(
            quiz=self.object,
            student=self.request.user.student_profile
        ).order_by('-attempt_number')
        return context

class StudentQuizAttemptStartView(StudentAccessMixin, DetailView):
    model = Quiz
    
    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        enrollment = self.get_current_enrollment()
        
        if not quiz.is_published:
            raise PermissionDenied("This quiz is not published.")
            
        if not enrollment or quiz.academic_year != enrollment.academic_year or quiz.class_subject.class_level != enrollment.class_level:
            raise PermissionDenied("You cannot access this quiz.")
            
        if quiz.section and quiz.section != enrollment.section:
            raise PermissionDenied("You cannot access this quiz.")
            
        attempts_count = QuizAttempt.objects.filter(
            quiz=quiz,
            student=self.request.user.student_profile
        ).count()
        
        if attempts_count >= quiz.max_attempts:
            raise PermissionDenied("Maximum attempts reached.")
            
        # Check for IN_PROGRESS attempt
        in_progress = QuizAttempt.objects.filter(
            quiz=quiz,
            student=self.request.user.student_profile,
            status='IN_PROGRESS'
        ).first()
        
        if in_progress:
            if not in_progress.is_expired():
                return redirect('student_quiz_take', pk=in_progress.pk)
            else:
                # Close expired attempt
                evaluate_quiz_attempt(in_progress)
                
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=self.request.user.student_profile,
            attempt_number=attempts_count + 1
        )
        
        return redirect('student_quiz_take', pk=attempt.pk)

class StudentQuizTakeView(StudentAccessMixin, FormView):
    template_name = 'quizzes/student_quiz_take.html'
    form_class = QuizSubmissionForm
    
    def dispatch(self, request, *args, **kwargs):
        self.attempt = get_object_or_404(QuizAttempt, pk=kwargs['pk'])
        
        if self.attempt.student != request.user.student_profile:
            raise PermissionDenied("You can only take your own quiz attempts.")
            
        if self.attempt.status != 'IN_PROGRESS':
            raise PermissionDenied("This attempt is no longer in progress.")
            
        if self.attempt.is_expired():
            evaluate_quiz_attempt(self.attempt)
            return redirect('student_quiz_result', pk=self.attempt.pk)
            
        return super().dispatch(request, *args, **kwargs)
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['quiz_attempt'] = self.attempt
        return kwargs
        
    def form_valid(self, form):
        # Save answers
        form.save()
        # Evaluate
        evaluate_quiz_attempt(self.attempt)
        return redirect('student_quiz_result', pk=self.attempt.pk)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attempt'] = self.attempt
        context['quiz'] = self.attempt.quiz
        return context

class StudentQuizResultView(StudentAccessMixin, DetailView):
    model = QuizAttempt
    template_name = 'quizzes/student_quiz_result.html'
    context_object_name = 'attempt'
    
    def get_object(self, queryset=None):
        attempt = super().get_object(queryset)
        if attempt.student != self.request.user.student_profile:
            raise PermissionDenied("You can only view your own results.")
        if attempt.status != 'COMPLETED':
             raise PermissionDenied("Result not ready.")
        return attempt

# --- PARENT VIEWS ---

class ParentQuizListView(ParentAccessMixin, ListView):
    template_name = 'quizzes/parent_quiz_list.html'
    context_object_name = 'attempts'
    
    def get_queryset(self):
        child = self.get_selected_child()
        if not child:
            return QuizAttempt.objects.none()
        # View only completed attempts for the selected child
        return QuizAttempt.objects.filter(
            student=child,
            status='COMPLETED'
        ).order_by('-end_time')
        
class ParentQuizResultView(ParentAccessMixin, DetailView):
    model = QuizAttempt
    template_name = 'quizzes/parent_quiz_result.html'
    context_object_name = 'attempt'
    
    def get_object(self, queryset=None):
        attempt = super().get_object(queryset)
        child = self.get_selected_child()
        if attempt.student != child:
            raise PermissionDenied("You can only view results for your child.")
        if attempt.status != 'COMPLETED':
             raise PermissionDenied("Result not ready.")
        return attempt
