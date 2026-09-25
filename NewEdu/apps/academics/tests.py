from django.test import TestCase
from django.db import IntegrityError
from datetime import date
from .models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, Enrollment, TeacherAssignment
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile

class AcademicModelTestCase(TestCase):
    def setUp(self):
        # Create an Academic Year
        self.year = AcademicYear.objects.create(
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
            is_active=True
        )

        # Create a Class
        self.class_10 = Class.objects.create(level=10, name="Class 10")
        
        # Create a Section
        self.section_a = Section.objects.create(class_level=self.class_10, name="A")

        # Create a Subject and ClassSubject
        self.subject_math = Subject.objects.create(name="Mathematics", code="MATH101")
        self.class_subject_math = ClassSubject.objects.create(
            class_level=self.class_10,
            subject=self.subject_math
        )

        # Create a Chapter and Lesson
        self.chapter = Chapter.objects.create(class_subject=self.class_subject_math, title="Algebra", order=1)
        self.lesson = Lesson.objects.create(chapter=self.chapter, title="Linear Equations", order=1)

        # Create Student and Teacher
        self.student_user = User.objects.create_user(email="student@test.com", password="pw", role="STUDENT")
        self.student_profile = StudentProfile.objects.create(user=self.student_user)

        self.teacher_user = User.objects.create_user(email="teacher@test.com", password="pw", role="TEACHER")
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user)

    def test_class_creation(self):
        self.assertEqual(Class.objects.count(), 1)
        self.assertEqual(self.class_10.name, "Class 10")

    def test_subject_creation_and_relationship(self):
        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(ClassSubject.objects.count(), 1)
        self.assertEqual(self.chapter.class_subject, self.class_subject_math)

    def test_lesson_relationships(self):
        self.assertEqual(self.lesson.chapter, self.chapter)

    def test_student_enrollment(self):
        enrollment = Enrollment.objects.create(
            student=self.student_profile,
            academic_year=self.year,
            class_level=self.class_10,
            section=self.section_a
        )
        self.assertEqual(Enrollment.objects.count(), 1)
        
        # Test unique together
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(
                student=self.student_profile,
                academic_year=self.year,
                class_level=self.class_10,
                section=Section.objects.create(class_level=self.class_10, name="B")
            )

    def test_teacher_assignment(self):
        assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_profile,
            academic_year=self.year,
            section=self.section_a,
            class_subject=self.class_subject_math
        )
        self.assertEqual(TeacherAssignment.objects.count(), 1)
        
        # Test unique together
        with self.assertRaises(IntegrityError):
            TeacherAssignment.objects.create(
                teacher=self.teacher_profile,
                academic_year=self.year,
                section=self.section_a,
                class_subject=self.class_subject_math
            )
