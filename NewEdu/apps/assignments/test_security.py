from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from decimal import Decimal
import os
from pathlib import Path

from apps.accounts.models import User
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, TeacherAssignment, Enrollment
from apps.teachers.models import TeacherProfile
from apps.students.models import StudentProfile
from apps.assignments.models import Assignment, AssignmentSubmission

class AssignmentSecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup basic data
        self.year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-06-30", is_active=True)
        self.cls = Class.objects.create(level=10, name="10th Grade")
        self.sec_a = Section.objects.create(name="A", class_level=self.cls)
        self.sec_b = Section.objects.create(name="B", class_level=self.cls)
        self.sub = Subject.objects.create(name="Math", code="MATH101")
        self.cs = ClassSubject.objects.create(class_level=self.cls, subject=self.sub)
        
        # Teacher
        self.teacher_user = User.objects.create_user(email="teacher@test.com", password="pwd", role="TEACHER")
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        TeacherAssignment.objects.create(teacher=self.teacher, academic_year=self.year, class_subject=self.cs, section=self.sec_a)
        
        # Student A (Section A)
        self.student_a_user = User.objects.create_user(email="studenta@test.com", password="pwd", role="STUDENT")
        self.student_a = StudentProfile.objects.create(user=self.student_a_user)
        Enrollment.objects.create(student=self.student_a, academic_year=self.year, class_level=self.cls, section=self.sec_a)
        
        # Student B (Section B) - Cross-section
        self.student_b_user = User.objects.create_user(email="studentb@test.com", password="pwd", role="STUDENT")
        self.student_b = StudentProfile.objects.create(user=self.student_b_user)
        Enrollment.objects.create(student=self.student_b, academic_year=self.year, class_level=self.cls, section=self.sec_b)
        
        # Assignment in Section A
        self.assignment = Assignment.objects.create(
            academic_year=self.year,
            class_subject=self.cs,
            section=self.sec_a,
            teacher=self.teacher,
            title="Secured Assignment",
            description="Test",
            due_date=timezone.now() + timezone.timedelta(days=7),
            attachment="assignments/2026-2027/MATH101/test.pdf"
        )
        
        # Dummy file for tests
        self.media_root = Path(settings.MEDIA_ROOT)
        self.media_root.mkdir(parents=True, exist_ok=True)
        self.test_file_path = self.media_root / "assignments" / "2026-2027" / "MATH101"
        self.test_file_path.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_file_path / "test.pdf"
        self.test_file.write_text("dummy pdf content")

    def tearDown(self):
        try:
            if self.test_file.exists():
                self.test_file.unlink()
        except OSError:
            pass

    def test_directory_traversal_blocked(self):
        self.client.login(email="teacher@test.com", password="pwd")
        # Attempt traversal outside MEDIA_ROOT
        response = self.client.get(reverse('secure_download', kwargs={'file_path': '../config/settings.py'}))
        self.assertEqual(response.status_code, 403) # 403 because it's rejected by logic or 404 because not found
        
        # Another traversal attempt bypassing the string check
        response = self.client.get(reverse('secure_download', kwargs={'file_path': 'assignments/../../config/settings.py'}))
        self.assertEqual(response.status_code, 403) # 403 because it's rejected by logic or ValueError block depending on string start

    def test_student_b_cannot_access_student_a_assignment(self):
        # Student B is in Section B, assignment is in Section A
        self.client.login(email="studentb@test.com", password="pwd")
        
        # 1. Download attachment
        response = self.client.get(reverse('secure_download', kwargs={'file_path': 'assignments/2026-2027/MATH101/test.pdf'}))
        self.assertEqual(response.status_code, 403)
        
        # 2. View assignment detail (IDOR check)
        response = self.client.get(reverse('student_assignment_detail', kwargs={'pk': self.assignment.pk}))
        self.assertEqual(response.status_code, 403)
        
    def test_student_a_can_access_assignment(self):
        self.client.login(email="studenta@test.com", password="pwd")
        response = self.client.get(reverse('secure_download', kwargs={'file_path': 'assignments/2026-2027/MATH101/test.pdf'}))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('student_assignment_detail', kwargs={'pk': self.assignment.pk}))
        self.assertEqual(response.status_code, 200)

    def test_invalid_file_extension_rejected(self):
        # We test model validation
        self.client.login(email="studenta@test.com", password="pwd")
        bad_file = SimpleUploadedFile("malicious.exe", b"fake exe content")
        
        response = self.client.post(
            reverse('student_assignment_detail', kwargs={'pk': self.assignment.pk}),
            {'submitted_file': bad_file}
        )
        # Should rerender form with errors
        self.assertEqual(response.status_code, 200)
        self.assertIn("not allowed. Allowed extensions are", response.content.decode())
        
    def test_oversized_file_rejected(self):
        self.client.login(email="studenta@test.com", password="pwd")
        # 11MB dummy file
        large_file = SimpleUploadedFile("large.pdf", b"0" * (11 * 1024 * 1024))
        
        response = self.client.post(
            reverse('student_assignment_detail', kwargs={'pk': self.assignment.pk}),
            {'submitted_file': large_file}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('File too large', response.content.decode())
