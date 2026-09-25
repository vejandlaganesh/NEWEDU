from django.contrib import admin
from .models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, Enrollment, TeacherAssignment

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_level')
    list_filter = ('class_level',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_level', 'subject')
    list_filter = ('class_level', 'subject')

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_subject', 'order')
    list_filter = ('class_subject__class_level', 'class_subject__subject')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'order')
    list_filter = ('chapter__class_subject__class_level', 'chapter__class_subject__subject')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'class_level', 'section')
    list_filter = ('academic_year', 'class_level', 'section')

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'academic_year', 'section', 'class_subject')
    list_filter = ('academic_year', 'section__class_level', 'section', 'class_subject__subject')
