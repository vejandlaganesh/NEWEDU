from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from apps.academics.models import ClassSubject, Chapter, Lesson
from apps.teachers.models import TeacherProfile
import uuid


def validate_material_size(value):
    if value.size > 25 * 1024 * 1024:
        raise ValidationError("Learning material must be 25 MB or smaller.")


def material_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'bin'
    return f"learning_materials/{instance.class_subject.class_level.level}/{instance.class_subject.subject.code}/{uuid.uuid4().hex}.{ext}"


class LearningMaterial(models.Model):
    TYPE_CHOICES = (
        ('PDF', 'PDF'), ('VIDEO', 'Video'), ('DOCUMENT', 'Document'),
        ('IMAGE', 'Image'), ('LINK', 'External Link'), ('TEXT', 'Text'),
    )
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='learning_materials')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='learning_materials')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='learning_materials')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='learning_materials')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    material_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='DOCUMENT')
    file = models.FileField(upload_to=material_upload_path, null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['pdf','doc','docx','txt','png','jpg','jpeg','mp4','webm','ppt','pptx']), validate_material_size])
    external_url = models.URLField(blank=True)
    text_content = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['class_subject', 'is_published']), models.Index(fields=['chapter', 'is_published'])]

    def clean(self):
        super().clean()
        if self.chapter and self.chapter.class_subject_id != self.class_subject_id:
            raise ValidationError({'chapter': 'Chapter must belong to the selected subject.'})
        if self.lesson and self.lesson.chapter.class_subject_id != self.class_subject_id:
            raise ValidationError({'lesson': 'Lesson must belong to the selected subject.'})
        if self.material_type == 'LINK' and not self.external_url:
            raise ValidationError({'external_url': 'An external URL is required for link materials.'})
        if self.material_type == 'TEXT' and not self.text_content.strip():
            raise ValidationError({'text_content': 'Text content is required for text materials.'})

    def __str__(self):
        return f"{self.title} - {self.class_subject}"


class GeneratedContent(models.Model):
    teacher = models.ForeignKey('teachers.TeacherProfile', on_delete=models.CASCADE)
    class_subject = models.ForeignKey('academics.ClassSubject', on_delete=models.CASCADE)
    chapter = models.ForeignKey('academics.Chapter', on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=255)
    content_type = models.CharField(max_length=50)
    difficulty = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=[('DRAFT','Draft'),('APPROVED','Approved'),('PUBLISHED','Published')], default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"
