from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import User
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, TeacherAssignment, Enrollment
from apps.teachers.models import TeacherProfile
from apps.students.models import StudentProfile
from apps.parents.models import ParentProfile
from apps.assignments.models import Assignment, AssignmentSubmission

class AssignmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.teacher_user = User.objects.create_user(email="teacher@test.com", password="pw", role="TEACHER")
        self.teacher2_user = User.objects.create_user(email="teacher2@test.com", password="pw", role="TEACHER")
        self.student_user = User.objects.create_user(email="student@test.com", password="pw", role="STUDENT")
        self.student2_user = User.objects.create_user(email="student2@test.com", password="pw", role="STUDENT")
        self.parent_user = User.objects.create_user(email="parent@test.com", password="pw", role="PARENT")
        
        # Create profiles
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        self.teacher2 = TeacherProfile.objects.create(user=self.teacher2_user)
        self.student = StudentProfile.objects.create(user=self.student_user)
        self.student2 = StudentProfile.objects.create(user=self.student2_user)
        self.parent = ParentProfile.objects.create(user=self.parent_user)
        
        # Link parent to student
        self.parent.children.add(self.student)
        
        # Setup Academics
        self.year = AcademicYear.objects.create(name="2026-2027", start_date="2026-01-01", end_date="2026-12-31", is_active=True)
        self.cls = Class.objects.create(level=10, name="Class 10")
        self.sec = Section.objects.create(class_level=self.cls, name="A")
        self.sec_b = Section.objects.create(class_level=self.cls, name="B")
        self.sub = Subject.objects.create(name="Math", code="M10")
        self.cs = ClassSubject.objects.create(class_level=self.cls, subject=self.sub)
        
        # Assign teacher
        TeacherAssignment.objects.create(teacher=self.teacher, academic_year=self.year, class_subject=self.cs, section=self.sec)
        # Assign teacher2 to section B
        TeacherAssignment.objects.create(teacher=self.teacher2, academic_year=self.year, class_subject=self.cs, section=self.sec_b)
        
        # Enroll student in section A, student2 in section B
        Enrollment.objects.create(student=self.student, academic_year=self.year, class_level=self.cls, section=self.sec)
        Enrollment.objects.create(student=self.student2, academic_year=self.year, class_level=self.cls, section=self.sec_b)
        
    def test_teacher_create_assignment(self):
        self.client.login(username="teacher@test.com", password="pw")
        response = self.client.post(reverse('teacher_assignment_create'), {
            'title': 'Math HW 1',
            'description': 'Solve algebra',
            'class_subject': self.cs.id,
            'section': self.sec.id,
            'due_date': timezone.now() + timezone.timedelta(days=7),
            'max_score': 100
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Assignment.objects.count(), 1)
        assignment = Assignment.objects.first()
        self.assertEqual(assignment.title, 'Math HW 1')
        self.assertEqual(assignment.teacher, self.teacher)
        
    def test_teacher_cannot_create_for_unassigned_section(self):
        self.client.login(username="teacher@test.com", password="pw")
        response = self.client.post(reverse('teacher_assignment_create'), {
            'title': 'Math HW 1',
            'description': 'Solve algebra',
            'class_subject': self.cs.id,
            'section': self.sec_b.id, # Teacher not assigned to section B
            'due_date': timezone.now() + timezone.timedelta(days=7),
            'max_score': 100
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Assignment.objects.count(), 0)

    def test_student_submit_and_teacher_grade(self):
        # 1. Teacher creates assignment
        assignment = Assignment.objects.create(
            academic_year=self.year,
            class_subject=self.cs,
            section=self.sec,
            teacher=self.teacher,
            title='Math HW 1',
            description='Solve',
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        # 2. Student views assignment
        self.client.login(username="student@test.com", password="pw")
        response = self.client.get(reverse('student_assignment_detail', args=[assignment.id]))
        self.assertEqual(response.status_code, 200)
        
        # 3. Student submits
        response = self.client.post(reverse('student_assignment_detail', args=[assignment.id]), {
            'submitted_text': 'Here is my answer'
        })
        self.assertEqual(response.status_code, 302)
        
        submission = AssignmentSubmission.objects.get(assignment=assignment, student=self.student)
        self.assertEqual(submission.status, 'SUBMITTED')
        self.assertEqual(submission.submitted_text, 'Here is my answer')
        
        # 4. Teacher grades
        self.client.login(username="teacher@test.com", password="pw")
        response = self.client.post(reverse('teacher_submission_grade', args=[assignment.id, self.student.id]), {
            'grade': 95.0,
            'feedback': 'Good job'
        })
        self.assertEqual(response.status_code, 302)
        
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'GRADED')
        self.assertEqual(submission.grade, Decimal('95.00'))
        
        # 5. Student cannot edit graded submission
        self.client.login(username="student@test.com", password="pw")
        response = self.client.post(reverse('student_assignment_detail', args=[assignment.id]), {
            'submitted_text': 'Trying to cheat'
        })
        self.assertEqual(response.status_code, 403)
        
        # 6. Parent views grade
        self.client.login(username="parent@test.com", password="pw")
        response = self.client.get(reverse('parent_assignments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Math HW 1')
        self.assertContains(response, '95.00')

    def test_student_cannot_access_other_section_assignment(self):
        assignment = Assignment.objects.create(
            academic_year=self.year,
            class_subject=self.cs,
            section=self.sec_b, # sec_b
            teacher=self.teacher2,
            title='Math HW B',
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        self.client.login(username="student@test.com", password="pw") # student is in sec A
        response = self.client.get(reverse('student_assignment_detail', args=[assignment.id]))
        self.assertEqual(response.status_code, 403)
