from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Enrollment
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.quizzes.models import Quiz, QuizAttempt, QuizResult
from apps.ai_assistant.models import AIRecommendation
from apps.ai_assistant.services.schemas import LearningRecommendationSchema

class StudentAIPersonalizedLearningTests(TestCase):
    def setUp(self):
        # Setup basic academic structure
        self.year = AcademicYear.objects.create(name="2026-2027", start_date="2026-08-01", end_date="2027-06-01", is_active=True)
        self.old_year = AcademicYear.objects.create(name="2025-2026", start_date="2025-08-01", end_date="2026-06-01", is_active=False)
        
        self.cls = Class.objects.create(name="10th Grade", level=10)
        self.section = Section.objects.create(name="A", class_level=self.cls)
        
        self.subject = Subject.objects.create(name="Mathematics")
        self.class_subject = ClassSubject.objects.create(class_level=self.cls, subject=self.subject)
        
        self.chapter1 = Chapter.objects.create(class_subject=self.class_subject, title="Algebra", order=1)
        self.chapter2 = Chapter.objects.create(class_subject=self.class_subject, title="Geometry", order=2)
        
        # Setup users
        self.student_user = User.objects.create_user(email='student@test.com', password='password123', role='STUDENT')
        self.student = StudentProfile.objects.create(user=self.student_user)
        self.enrollment = Enrollment.objects.create(student=self.student, class_level=self.cls, section=self.section, academic_year=self.year)

        self.student2_user = User.objects.create_user(email='student2@test.com', password='password123', role='STUDENT')
        self.student2 = StudentProfile.objects.create(user=self.student2_user)
        self.enrollment2 = Enrollment.objects.create(student=self.student2, class_level=self.cls, section=self.section, academic_year=self.year)

        self.teacher_user = User.objects.create_user(email='teacher@test.com', password='password123', role='TEACHER')
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)

        self.url = reverse('student_ai_assistant')

    def setup_sufficient_data(self, student):
        # Create 3 assignments to pass the default 3 data point threshold
        for i in range(3):
            assign = Assignment.objects.create(
                academic_year=self.year, section=self.section, 
                class_subject=self.class_subject, chapter=self.chapter1, 
                title=f"A{i}", max_score=100, teacher=self.teacher, due_date=timezone.now()
            )
            # Create graded submission with 50%
            AssignmentSubmission.objects.create(
                assignment=assign, student=student, status='GRADED', grade=50.0
            )

    @override_settings(AI_RECOMMENDATION_MIN_DATA_POINTS=3)
    def test_zero_data(self):
        self.client.login(email='student@test.com', password='password123')
        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Not enough data yet', response.json()['error'])

    @override_settings(AI_RECOMMENDATION_MIN_DATA_POINTS=3)
    def test_insufficient_data(self):
        # 1 assignment graded
        assign = Assignment.objects.create(
            academic_year=self.year, section=self.section, 
            class_subject=self.class_subject, chapter=self.chapter1, 
            title="A1", max_score=100, teacher=self.teacher, due_date=timezone.now()
        )
        AssignmentSubmission.objects.create(
            assignment=assign, student=self.student, status='GRADED', grade=50.0
        )
        self.client.login(email='student@test.com', password='password123')
        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('apps.ai_assistant.services.ai_service.GeminiService.generate_student_recommendation')
    def test_successful_generation(self, mock_generate):
        self.setup_sufficient_data(self.student)
        
        # Mock valid AI output
        mock_schema = LearningRecommendationSchema(
            strengths=["Nothing"],
            weaknesses=["Algebra concepts"],
            recommended_topics=["Algebra"], # Valid topic
            actionable_advice=["Practice more"],
            encouragement_message="You can do it!"
        )
        mock_generate.return_value = (mock_schema, None)
        
        self.client.login(email='student@test.com', password='password123')
        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Verify recommendation created
        rec = AIRecommendation.objects.get(student=self.student, academic_year=self.year)
        self.assertIn('Algebra', rec.recommendation['recommended_topics'])
        # Source data must reflect the calculated 50%
        self.assertEqual(rec.source_data['weak_topics'][0]['score'], 50.0)

    @patch('apps.ai_assistant.services.ai_service.GeminiService.generate_student_recommendation')
    def test_invalid_topic_filtering(self, mock_generate):
        self.setup_sufficient_data(self.student)
        
        # AI returns a hallucinated topic
        mock_schema = LearningRecommendationSchema(
            strengths=[],
            weaknesses=[],
            recommended_topics=["Hallucinated Topic", "Algebra"], # "Algebra" is valid
            actionable_advice=[],
            encouragement_message="Keep trying!"
        )
        mock_generate.return_value = (mock_schema, None)
        
        self.client.login(email='student@test.com', password='password123')
        response = self.client.post(self.url, content_type='application/json')
        
        rec = AIRecommendation.objects.get(student=self.student)
        # Should filter out "Hallucinated Topic", keep "Algebra"
        topics = rec.recommendation['recommended_topics']
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0].lower(), "algebra")

    def test_rate_limiting(self):
        # Directly create a recent recommendation
        AIRecommendation.objects.create(
            student=self.student, academic_year=self.year,
            status='COMPLETED'
        )
        
        self.client.login(email='student@test.com', password='password123')
        response = self.client.post(self.url, content_type='application/json')
        self.assertEqual(response.status_code, 429)
        self.assertIn('once per hour', response.json()['error'])

    def test_student_isolation(self):
        # Create rec for student 1
        rec1 = AIRecommendation.objects.create(
            student=self.student, academic_year=self.year,
            recommendation={"msg": "Student 1"}, status='COMPLETED'
        )
        # Login as student 2
        self.client.login(email='student2@test.com', password='password123')
        response = self.client.get(reverse('student_dashboard'))
        # Should not see student 1's recommendation
        self.assertNotContains(response, "Student 1")

    @override_settings(AI_RECOMMENDATION_WEAK_THRESHOLD=80.0)
    def test_weak_topic_threshold(self):
        # 3 assignments with 75%. Threshold is 80, so should be marked weak.
        for i in range(3):
            assign = Assignment.objects.create(
                academic_year=self.year, section=self.section, 
                class_subject=self.class_subject, chapter=self.chapter1, 
                title=f"A{i}", max_score=100, teacher=self.teacher, due_date=timezone.now()
            )
            AssignmentSubmission.objects.create(
                assignment=assign, student=self.student, status='GRADED', grade=75.0
            )
        
        from apps.reports.services import get_student_weak_topics
        weak = get_student_weak_topics(self.student, self.year)
        self.assertEqual(len(weak), 1)
        self.assertEqual(weak[0]['overall_avg'], 75.0)
        self.assertEqual(weak[0]['threshold_used'], 80.0)

    def test_ungraded_and_null_ignored(self):
        # 1 Graded with 50%, 2 SUBMITTED (null grade)
        assign = Assignment.objects.create(
            academic_year=self.year, section=self.section, 
            class_subject=self.class_subject, chapter=self.chapter1, 
            title="A1", max_score=100, teacher=self.teacher, due_date=timezone.now()
        )
        AssignmentSubmission.objects.create(
            assignment=assign, student=self.student, status='GRADED', grade=50.0
        )
        assign2 = Assignment.objects.create(
            academic_year=self.year, section=self.section, 
            class_subject=self.class_subject, chapter=self.chapter1, 
            title="A2", max_score=100, teacher=self.teacher, due_date=timezone.now()
        )
        AssignmentSubmission.objects.create(
            assignment=assign2, student=self.student, status='SUBMITTED', grade=None
        )
        
        from apps.reports.services import get_student_weak_topics
        weak = get_student_weak_topics(self.student, self.year)
        # Only 1 data point, which is below min_data default (3)
        self.assertEqual(len(weak), 0)

    def test_academic_year_isolation(self):
        # Data points in old year
        for i in range(3):
            assign = Assignment.objects.create(
                academic_year=self.old_year, section=self.section, 
                class_subject=self.class_subject, chapter=self.chapter1, 
                title=f"A{i}", max_score=100, teacher=self.teacher, due_date=timezone.now()
            )
            AssignmentSubmission.objects.create(
                assignment=assign, student=self.student, status='GRADED', grade=50.0
            )
        
        from apps.reports.services import get_student_weak_topics
        # Current year has no data
        weak = get_student_weak_topics(self.student, self.year)
        self.assertEqual(len(weak), 0)
