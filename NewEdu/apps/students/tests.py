from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, Enrollment

class StudentModuleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup Academic Data
        self.year = AcademicYear.objects.create(name="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31), is_active=True)
        self.class_10 = Class.objects.create(level=10, name="Class 10")
        self.section_a = Section.objects.create(class_level=self.class_10, name="A")
        
        self.subject_math = Subject.objects.create(name="Mathematics", code="MATH101")
        self.class_subject_math = ClassSubject.objects.create(class_level=self.class_10, subject=self.subject_math)
        
        self.chapter = Chapter.objects.create(class_subject=self.class_subject_math, title="Algebra", order=1)
        self.lesson = Lesson.objects.create(chapter=self.chapter, title="Linear Equations", order=1, content="Learn linear equations.")

        # Setup Student 1 (Enrolled in Class 10 A)
        self.student1_user = User.objects.create_user(email="student1@test.com", password="pw", role="STUDENT", first_name="John", last_name="Doe")
        self.student1_profile = StudentProfile.objects.create(user=self.student1_user)
        self.enrollment1 = Enrollment.objects.create(student=self.student1_profile, academic_year=self.year, class_level=self.class_10, section=self.section_a)

        # Setup Student 2 (Not enrolled)
        self.student2_user = User.objects.create_user(email="student2@test.com", password="pw", role="STUDENT", first_name="Jane", last_name="Doe")
        self.student2_profile = StudentProfile.objects.create(user=self.student2_user)

    def test_dashboard_enrolled_student(self):
        self.client.login(username='student1@test.com', password='pw')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, John Doe')
        self.assertContains(response, 'Class 10')
        self.assertContains(response, 'Mathematics')

    def test_dashboard_unenrolled_student(self):
        self.client.login(username='student2@test.com', password='pw')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Not Enrolled')

    def test_subject_list_and_isolation(self):
        self.client.login(username='student1@test.com', password='pw')
        response = self.client.get(reverse('student_subjects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mathematics')
        
        self.client.login(username='student2@test.com', password='pw')
        response = self.client.get(reverse('student_subjects'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Mathematics') # Shouldn't see it since unenrolled

    def test_lesson_detail(self):
        self.client.login(username='student1@test.com', password='pw')
        response = self.client.get(reverse('student_lesson_detail', args=[self.lesson.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Learn linear equations.')

    def test_profile_update(self):
        self.client.login(username='student1@test.com', password='pw')
        response = self.client.post(reverse('student_profile'), {
            'first_name': 'Johnny',
            'last_name': 'Doe'
        })
        self.assertEqual(response.status_code, 302) # Redirects on success
        self.student1_user.refresh_from_db()
        self.assertEqual(self.student1_user.first_name, 'Johnny')
