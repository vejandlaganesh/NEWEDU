from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Enrollment, TeacherAssignment
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.quizzes.models import Quiz, Question, QuizAttempt, QuizResult
from apps.reports.services import (
    get_student_performance, get_missing_submissions, get_teacher_assignment_stats, get_weak_topics
)
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class ReportsAnalyticsTestCase(TestCase):
    def setUp(self):
        # Users
        self.s1_user = User.objects.create_user(email="student1@example.com", password="password123", role="STUDENT")
        self.s2_user = User.objects.create_user(email="student2@example.com", password="password123", role="STUDENT")
        self.t1_user = User.objects.create_user(email="teacher1@example.com", password="password123", role="TEACHER")
        self.t2_user = User.objects.create_user(email="teacher2@example.com", password="password123", role="TEACHER")
        self.p1_user = User.objects.create_user(email="parent1@example.com", password="password123", role="PARENT")
        self.p2_user = User.objects.create_user(email="parent2@example.com", password="password123", role="PARENT")
        
        # Profiles
        self.s1_profile = StudentProfile.objects.create(user=self.s1_user)
        self.s2_profile = StudentProfile.objects.create(user=self.s2_user)
        self.t1_profile = TeacherProfile.objects.create(user=self.t1_user)
        self.t2_profile = TeacherProfile.objects.create(user=self.t2_user)
        self.p1_profile = ParentProfile.objects.create(user=self.p1_user)
        self.p2_profile = ParentProfile.objects.create(user=self.p2_user)
        
        # Parent-Child Links
        self.p1_profile.children.add(self.s1_profile)
        self.p2_profile.children.add(self.s2_profile)
        
        # Academics
        self.year1 = AcademicYear.objects.create(name="2025-2026", start_date="2025-08-01", end_date="2026-06-01", is_active=True)
        self.year2 = AcademicYear.objects.create(name="2024-2025", start_date="2024-08-01", end_date="2025-06-01", is_active=False)
        
        self.class_10 = Class.objects.create(name="Grade 10", level=10)
        self.section_a = Section.objects.create(name="Section A", class_level=self.class_10)
        self.section_b = Section.objects.create(name="Section B", class_level=self.class_10)
        
        self.sub_math = Subject.objects.create(name="Math", code="MTH")
        self.cs_math = ClassSubject.objects.create(class_level=self.class_10, subject=self.sub_math)
        self.ch_math_1 = Chapter.objects.create(class_subject=self.cs_math, title="Algebra", order=1)
        self.ch_math_2 = Chapter.objects.create(class_subject=self.cs_math, title="Geometry", order=2)
        
        # Enrollments
        Enrollment.objects.create(student=self.s1_profile, academic_year=self.year1, class_level=self.class_10, section=self.section_a)
        Enrollment.objects.create(student=self.s2_profile, academic_year=self.year1, class_level=self.class_10, section=self.section_b)
        # Historical enrollment
        Enrollment.objects.create(student=self.s1_profile, academic_year=self.year2, class_level=self.class_10, section=self.section_a)
        
        # Teacher Assignments
        TeacherAssignment.objects.create(academic_year=self.year1, teacher=self.t1_profile, class_subject=self.cs_math, section=self.section_a)
        TeacherAssignment.objects.create(academic_year=self.year1, teacher=self.t2_profile, class_subject=self.cs_math, section=self.section_b)

    def test_student_report_calculation_accuracy_and_normalization(self):
        # 1. Zero Score
        a1 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Zero Test", max_score=Decimal('50.00'), due_date=timezone.now() + timedelta(days=1))
        AssignmentSubmission.objects.create(assignment=a1, student=self.s1_profile, status='GRADED', grade=Decimal('0.00'))
        
        # 2. Max Score
        a2 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Max Test", max_score=Decimal('20.00'), due_date=timezone.now() + timedelta(days=1))
        AssignmentSubmission.objects.create(assignment=a2, student=self.s1_profile, status='GRADED', grade=Decimal('20.00'))
        
        # 3. Partial Score (70%)
        a3 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Partial Test", max_score=Decimal('200.00'), due_date=timezone.now() + timedelta(days=1))
        AssignmentSubmission.objects.create(assignment=a3, student=self.s1_profile, status='GRADED', grade=Decimal('140.00'))
        
        # 4. NULL Grade (Pending/Submitted)
        a4 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Ungraded Test", max_score=Decimal('10.00'), due_date=timezone.now() + timedelta(days=1))
        AssignmentSubmission.objects.create(assignment=a4, student=self.s1_profile, status='SUBMITTED', grade=None)
        
        perf = get_student_performance(self.s1_profile, self.year1)
        
        # Percentages: a1=0%, a2=100%, a3=70%. Average should be 170 / 3 = 56.67
        self.assertAlmostEqual(perf['avg_assignment_score'], 56.67, places=1)
        self.assertEqual(perf['assignments_completed'], 3)
        self.assertEqual(perf['avg_quiz_score'], None) # No quizzes
        self.assertAlmostEqual(perf['overall_assessment_avg'], 56.67, places=1)

    def test_current_academic_year_isolation(self):
        # Create an assignment in year 2 (historical) and grade it 100%
        a_hist = Assignment.objects.create(academic_year=self.year2, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Hist Test", max_score=Decimal('100.00'), due_date=timezone.now() - timedelta(days=300))
        AssignmentSubmission.objects.create(assignment=a_hist, student=self.s1_profile, status='GRADED', grade=Decimal('100.00'))
        
        # Year 1 perf should be None/empty since no year 1 data
        perf = get_student_performance(self.s1_profile, self.year1)
        self.assertEqual(perf['assignments_completed'], 0)
        self.assertEqual(perf['avg_assignment_score'], None)

    def test_missing_submission_logic(self):
        now = timezone.now()
        # Due in future (NOT missing)
        a_future = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Future", max_score=Decimal('10.00'), due_date=now + timedelta(days=1))
        # Due in past, NO submission (MISSING)
        a_past = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Past Missing", max_score=Decimal('10.00'), due_date=now - timedelta(days=1))
        # Due in past, HAS submission (NOT missing)
        a_past_done = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Past Done", max_score=Decimal('10.00'), due_date=now - timedelta(days=1))
        AssignmentSubmission.objects.create(assignment=a_past_done, student=self.s1_profile, status='SUBMITTED', grade=None)
        
        missing = get_missing_submissions(self.s1_profile, self.year1)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].id, a_past.id)

    def test_teacher_weak_topics_min_data_behavior(self):
        # Create 2 submissions for ch_math_1 scoring 40%
        a1 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, chapter=self.ch_math_1, teacher=self.t1_profile, title="Ch1 A1", max_score=10, due_date=timezone.now())
        a2 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, chapter=self.ch_math_1, teacher=self.t1_profile, title="Ch1 A2", max_score=10, due_date=timezone.now())
        
        AssignmentSubmission.objects.create(assignment=a1, student=self.s1_profile, status='GRADED', grade=4)
        AssignmentSubmission.objects.create(assignment=a2, student=self.s1_profile, status='GRADED', grade=4)
        
        # 2 data points is below the default threshold of 3, so it should NOT be flagged as a weak topic yet
        weak = get_weak_topics(self.t1_profile, self.year1, min_data_threshold=3, weak_threshold_percentage=60.0)
        self.assertEqual(len(weak), 0)
        
        # Add a 3rd data point scoring 40%
        a3 = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, chapter=self.ch_math_1, teacher=self.t1_profile, title="Ch1 A3", max_score=10, due_date=timezone.now())
        AssignmentSubmission.objects.create(assignment=a3, student=self.s1_profile, status='GRADED', grade=4)
        
        weak2 = get_weak_topics(self.t1_profile, self.year1, min_data_threshold=3, weak_threshold_percentage=60.0)
        self.assertEqual(len(weak2), 1)
        self.assertEqual(weak2[0]['chapter_name'], "Algebra")
        self.assertEqual(weak2[0]['overall_avg'], 40.0)

    def test_teacher_assignment_isolation(self):
        # T1 has Section A, T2 has Section B.
        a_sec_a = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="A", max_score=10, due_date=timezone.now())
        AssignmentSubmission.objects.create(assignment=a_sec_a, student=self.s1_profile, status='GRADED', grade=10)
        
        a_sec_b = Assignment.objects.create(academic_year=self.year1, class_subject=self.cs_math, section=self.section_b, teacher=self.t2_profile, title="B", max_score=10, due_date=timezone.now())
        AssignmentSubmission.objects.create(assignment=a_sec_b, student=self.s2_profile, status='GRADED', grade=5)
        
        # T1 stats should only include a_sec_a
        t1_stats = get_teacher_assignment_stats(self.t1_profile, self.year1)
        self.assertEqual(len(t1_stats), 1)
        self.assertEqual(t1_stats[0]['title'], "A")
        
        # T2 stats should only include a_sec_b
        t2_stats = get_teacher_assignment_stats(self.t2_profile, self.year1)
        self.assertEqual(len(t2_stats), 1)
        self.assertEqual(t2_stats[0]['title'], "B")

    def test_role_and_child_isolation_in_views(self):
        self.client.login(email="parent1@example.com", password="password123")
        
        # Parent 1 tries to view Parent 2's child by passing child_id (prevented by get_selected_child in ParentAccessMixin)
        response = self.client.get(reverse('parent_reports') + f"?child_id={self.s2_profile.id}")
        self.assertEqual(response.status_code, 403) # PermissionDenied

        # Parent 1 views their own child
        response = self.client.get(reverse('parent_reports') + f"?child_id={self.s1_profile.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_child'], self.s1_profile)

        self.client.logout()
        
        # Student self-access
        self.client.login(email="student1@example.com", password="password123")
        response = self.client.get(reverse('student_reports'))
        self.assertEqual(response.status_code, 200)
        # Student cannot view another student's report because the view implicitly uses self.request.user.student_profile
        
        # Try parent url as student
        response = self.client.get(reverse('parent_reports'))
        self.assertEqual(response.status_code, 403)
        
        self.client.logout()

    def test_student_no_data_empty_state(self):
        self.client.login(email="student1@example.com", password="password123")
        response = self.client.get(reverse('student_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not enough assessment data")
