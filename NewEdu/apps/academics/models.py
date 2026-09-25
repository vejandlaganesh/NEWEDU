from django.db import models
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile

class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True) # e.g. "2026-2027"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Class(models.Model):
    level = models.IntegerField(unique=True, choices=[(i, str(i)) for i in range(6, 13)]) # 6 to 12
    name = models.CharField(max_length=50) # e.g., "Class 6"

    def __str__(self):
        return self.name

class Section(models.Model):
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10) # e.g., "A", "B"

    class Meta:
        unique_together = ('class_level', 'name')

    def __str__(self):
        return f"{self.class_level.name} - {self.name}"

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., "Mathematics"
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class ClassSubject(models.Model):
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='class_subjects')
    
    class Meta:
        unique_together = ('class_level', 'subject')

    def __str__(self):
        return f"{self.class_level.name} - {self.subject.name}"

class Chapter(models.Model):
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.class_subject} - Chapter {self.order}: {self.title}"

class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.chapter} - Lesson {self.order}: {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'academic_year') # A student can only be in one class/section per academic year

    def __str__(self):
        return f"{self.student} enrolled in {self.section} ({self.academic_year})"

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'academic_year', 'section', 'class_subject')

    def __str__(self):
        return f"{self.teacher} teaches {self.class_subject} in {self.section} ({self.academic_year})"
