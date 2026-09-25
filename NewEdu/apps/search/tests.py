from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Enrollment, TeacherAssignment, Chapter, Lesson
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.assignments.models import Assignment
from apps.quizzes.models import Quiz
from datetime import date

User = get_user_model()

class GlobalSearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(name='2026-2027', is_active=True, start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
        
        self.cls10 = Class.objects.create(name='Class 10', level=10)
        self.cls11 = Class.objects.create(name='Class 11', level=11)
        
        self.sec10A = Section.objects.create(class_level=self.cls10, name='A')
        self.sec10B = Section.objects.create(class_level=self.cls10, name='B')
        self.sec11A = Section.objects.create(class_level=self.cls11, name='A')
        
        self.subj_math = Subject.objects.create(name='Mathematics', code='MTH')
        self.subj_sci = Subject.objects.create(name='Science', code='SCI')
        
        self.cs_10_math = ClassSubject.objects.create(class_level=self.cls10, subject=self.subj_math)
        self.cs_10_sci = ClassSubject.objects.create(class_level=self.cls10, subject=self.subj_sci)
        self.cs_11_math = ClassSubject.objects.create(class_level=self.cls11, subject=self.subj_math)
        
        self.chap_math = Chapter.objects.create(class_subject=self.cs_10_math, title='Algebra 1', order=1)
        self.lesson_math = Lesson.objects.create(chapter=self.chap_math, title='Linear Equations', content='Solve for x', order=1)
        
        self.chap_sci = Chapter.objects.create(class_subject=self.cs_10_sci, title='Physics 1', order=1)
        self.lesson_sci = Lesson.objects.create(chapter=self.chap_sci, title='Motion', content='Velocity', order=1)
        
        # Users
        self.user_s1 = User.objects.create_user(email='s1@test.com', password='password', role='STUDENT', first_name='S1')
        self.student1 = StudentProfile.objects.create(user=self.user_s1)
        
        self.user_s2 = User.objects.create_user(email='s2@test.com', password='password', role='STUDENT', first_name='S2')
        self.student2 = StudentProfile.objects.create(user=self.user_s2)
        
        self.user_t1 = User.objects.create_user(email='t1@test.com', password='password', role='TEACHER', first_name='T1')
        self.teacher1 = TeacherProfile.objects.create(user=self.user_t1)
        
        self.user_t2 = User.objects.create_user(email='t2@test.com', password='password', role='TEACHER', first_name='T2')
        self.teacher2 = TeacherProfile.objects.create(user=self.user_t2)
        
        self.user_p1 = User.objects.create_user(email='p1@test.com', password='password', role='PARENT', first_name='P1')
        self.parent1 = ParentProfile.objects.create(user=self.user_p1)
        self.parent1.children.add(self.student1)
        
        # Enrollments
        # s1 -> 10A (Math, Sci)
        Enrollment.objects.create(student=self.student1, academic_year=self.year, class_level=self.cls10, section=self.sec10A)
        # s2 -> 11A (Math)
        Enrollment.objects.create(student=self.student2, academic_year=self.year, class_level=self.cls11, section=self.sec11A)
        
        # Teacher Assignments
        # t1 -> 10A Math
        TeacherAssignment.objects.create(teacher=self.teacher1, academic_year=self.year, section=self.sec10A, class_subject=self.cs_10_math)
        # t2 -> 10A Sci
        TeacherAssignment.objects.create(teacher=self.teacher2, academic_year=self.year, section=self.sec10A, class_subject=self.cs_10_sci)
        
        # Content
        self.assign_math = Assignment.objects.create(
            academic_year=self.year, class_subject=self.cs_10_math, section=self.sec10A, teacher=self.teacher1,
            title='Algebra Homework', description='Solve equations', due_date='2026-12-31 23:59'
        )
        self.assign_sci = Assignment.objects.create(
            academic_year=self.year, class_subject=self.cs_10_sci, section=self.sec10A, teacher=self.teacher2,
            title='Physics Homework', description='Calculate velocity', due_date='2026-12-31 23:59'
        )
        self.assign_11math = Assignment.objects.create(
            academic_year=self.year, class_subject=self.cs_11_math, section=self.sec11A, teacher=self.teacher1,
            title='Calculus Homework', description='Limits', due_date='2026-12-31 23:59'
        )
        
        self.quiz_math_pub = Quiz.objects.create(
            academic_year=self.year, class_subject=self.cs_10_math, section=self.sec10A, teacher=self.teacher1,
            title='Algebra Quiz', description='Solve equations', duration=10, passing_score=50, is_published=True
        )
        self.quiz_math_unpub = Quiz.objects.create(
            academic_year=self.year, class_subject=self.cs_10_math, section=self.sec10A, teacher=self.teacher1,
            title='Algebra Secret Quiz', description='Solve equations', duration=10, passing_score=50, is_published=False
        )

    def test_anonymous_user_redirects(self):
        response = self.client.get(reverse('global_search') + '?q=Algebra')
        self.assertRedirects(response, f"/accounts/login/?next=/search/%3Fq%3DAlgebra")
        
    def test_blank_and_whitespace_query(self):
        self.client.login(email='s1@test.com', password='password')
        response = self.client.get(reverse('global_search') + '?q=   ')
        self.assertContains(response, "Please enter a search query")
        self.assertFalse(response.context['has_results'])
        
    def test_student_isolation_across_classes(self):
        self.client.login(email='s1@test.com', password='password') # s1 is in 10A
        response = self.client.get(reverse('global_search') + '?q=Calculus')
        # Calculus is 11A Math assignment
        self.assertNotContains(response, "Calculus Homework")
        self.assertContains(response, "No results found for \"Calculus\"")
        
    def test_student_sees_own_class(self):
        self.client.login(email='s1@test.com', password='password')
        response = self.client.get(reverse('global_search') + '?q=Algebra')
        self.assertContains(response, "Algebra 1") # Chapter
        self.assertContains(response, "Algebra Homework") # Assignment
        self.assertContains(response, "Algebra Quiz") # Quiz
        # Secret quiz is unpublished
        self.assertNotContains(response, "Algebra Secret Quiz")
        
    def test_teacher_isolation_across_assignments(self):
        self.client.login(email='t1@test.com', password='password') # t1 teaches 10A Math
        response = self.client.get(reverse('global_search') + '?q=Physics')
        # Physics is 10A Sci (taught by t2)
        self.assertNotContains(response, "Physics 1")
        self.assertNotContains(response, "Physics Homework")
        self.assertContains(response, "No results found")
        
    def test_teacher_sees_own_content_including_unpublished(self):
        self.client.login(email='t1@test.com', password='password')
        response = self.client.get(reverse('global_search') + '?q=Algebra')
        self.assertContains(response, "Algebra 1")
        self.assertContains(response, "Algebra Homework")
        self.assertContains(response, "Algebra Quiz")
        self.assertContains(response, "Algebra Secret Quiz") # T1 can see their unpublished quiz
        
    def test_parent_sees_children_content(self):
        self.client.login(email='p1@test.com', password='password') # p1 child is s1
        response = self.client.get(reverse('global_search') + '?q=Algebra')
        self.assertContains(response, "Algebra Homework")
        self.assertContains(response, "Algebra Quiz")
        self.assertNotContains(response, "Algebra Secret Quiz")
        
        # Parent shouldn't see 11A stuff
        response = self.client.get(reverse('global_search') + '?q=Calculus')
        self.assertNotContains(response, "Calculus Homework")
