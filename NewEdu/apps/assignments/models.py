from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, FileExtensionValidator
from apps.academics.models import AcademicYear, ClassSubject, Section, Chapter
from apps.teachers.models import TeacherProfile
from apps.students.models import StudentProfile
import os
import uuid

def validate_file_size(value):
    limit = 10 * 1024 * 1024 # 10 MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 10 MB.')

SAFE_EXTENSIONS = ['pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'csv']

def assignment_attachment_path(instance, filename):
    ext = filename.split('.')[-1]
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    return f'assignments/{instance.academic_year.name}/{instance.class_subject.subject.code}/{safe_filename}'

class Assignment(models.fields.related.ForeignKey.__mro__[0] if False else models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='assignments')
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assignments')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='created_assignments')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    attachment = models.FileField(
        upload_to=assignment_attachment_path, 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=SAFE_EXTENSIONS), validate_file_size]
    )
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, validators=[MinValueValidator(0.00)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.class_subject.subject.name} ({self.section.name})"

def submission_attachment_path(instance, filename):
    ext = filename.split('.')[-1]
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    return f'submissions/{instance.assignment.id}/{instance.student.id}/{safe_filename}'

class AssignmentSubmission(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted'),
        ('GRADED', 'Graded')
    )
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    
    submitted_file = models.FileField(
        upload_to=submission_attachment_path, 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=SAFE_EXTENSIONS), validate_file_size]
    )
    submitted_text = models.TextField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'student'], name='unique_submission_per_student')
        ]

    def __str__(self):
        return f"Submission for {self.assignment.title} by {self.student.user.first_name}"
