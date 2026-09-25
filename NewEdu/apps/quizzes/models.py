from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.academics.models import AcademicYear, ClassSubject, Section, Chapter, TeacherAssignment
from apps.teachers.models import TeacherProfile
from apps.students.models import StudentProfile

class Quiz(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='quizzes')
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='quizzes')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name='quizzes', help_text="Leave blank to assign to all sections")
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='created_quizzes')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Passing score percentage (0-100)")
    max_attempts = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.class_subject}"
        
    def clean(self):
        super().clean()
        if self.passing_score and (self.passing_score < 0 or self.passing_score > 100):
            raise ValidationError({'passing_score': 'Passing score must be between 0 and 100.'})
            
        if self.section and self.section.class_level != self.class_subject.class_level:
            raise ValidationError({'section': 'Section must belong to the same class as the ClassSubject.'})
            
        if self.chapter and self.chapter.class_subject != self.class_subject:
            raise ValidationError({'chapter': 'Chapter must belong to the selected ClassSubject.'})
            
        if self.is_published:
            if not self.questions.exists():
                raise ValidationError("Cannot publish a quiz with no questions.")
            
    def has_attempts(self):
        return self.attempts.exists()

class Question(models.Model):
    QUESTION_TYPES = (
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
    )
    OPTION_CHOICES = (
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='MULTIPLE_CHOICE')
    
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    explanation = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Q: {self.text[:50]}"
        
    def clean(self):
        super().clean()
        if self.marks and self.marks <= 0:
            raise ValidationError({'marks': 'Marks must be greater than zero.'})
        
        if getattr(self, 'quiz_id', None) and self.quiz.has_attempts():
             # When updating an existing question or adding one to a locked quiz
             raise ValidationError("Cannot modify questions for a quiz that has already been attempted.")
             
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        if self.quiz.has_attempts():
            raise ValidationError("Cannot delete questions from a quiz that has already been attempted.")
        super().delete(*args, **kwargs)

class QuizAttempt(models.Model):
    STATUS_CHOICES = (
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='quiz_attempts')
    attempt_number = models.PositiveIntegerField(default=1)
    
    start_time = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    
    class Meta:
        unique_together = ('quiz', 'student', 'attempt_number')
        
    def __str__(self):
        return f"{self.student} - {self.quiz.title} (Attempt {self.attempt_number})"
        
    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            # New attempt, set expires_at based on duration + small grace period
            self.expires_at = timezone.now() + timezone.timedelta(minutes=self.quiz.duration, seconds=5)
        super().save(*args, **kwargs)
        
    def is_expired(self):
        return timezone.now() > self.expires_at

class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.CharField(max_length=1, choices=Question.OPTION_CHOICES)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attempt', 'question'], name='unique_attempt_question_answer')
        ]
        
    def clean(self):
        super().clean()
        if getattr(self, 'question_id', None) and getattr(self, 'attempt_id', None):
            if self.question.quiz_id != self.attempt.quiz_id:
                raise ValidationError("Question does not belong to the quiz being attempted.")
                
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class QuizResult(models.Model):
    attempt = models.OneToOneField(QuizAttempt, on_delete=models.CASCADE, related_name='result')
    score = models.DecimalField(max_digits=7, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField()
    
    correct_answers = models.PositiveIntegerField()
    incorrect_answers = models.PositiveIntegerField()
    attempted_questions = models.PositiveIntegerField()
    completion_time = models.DurationField()
    
    def __str__(self):
        return f"Result: {self.attempt.student} - {self.percentage}%"
