from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, TeacherAssignment, Enrollment
from apps.teachers.models import TeacherProfile
from apps.students.models import StudentProfile
from apps.parents.models import ParentProfile
from .models import Quiz, Question, QuizAttempt, QuizAnswer, QuizResult
from .services import evaluate_quiz_attempt
from django.core.exceptions import ValidationError

class QuizEngineTestCase(TestCase):
    def setUp(self):
        # Academic Structure
        self.year = AcademicYear.objects.create(name="2026-2027", start_date="2026-08-01", end_date="2027-05-31", is_active=True)
        self.old_year = AcademicYear.objects.create(name="2025-2026", start_date="2025-08-01", end_date="2026-05-31", is_active=False)
        self.class_10 = Class.objects.create(name="Class 10", level=10)
        self.section_a = Section.objects.create(name="A", class_level=self.class_10)
        self.section_b = Section.objects.create(name="B", class_level=self.class_10)
        self.subject_math = Subject.objects.create(name="Mathematics", code="MATH101")
        self.cs_math = ClassSubject.objects.create(class_level=self.class_10, subject=self.subject_math)
        
        # Teacher 1 (Math 10A)
        self.t1_user = User.objects.create_user(email="teacher1@example.com", password="password123", role="TEACHER")
        self.t1_profile = TeacherProfile.objects.create(user=self.t1_user)
        TeacherAssignment.objects.create(academic_year=self.year, teacher=self.t1_profile, class_subject=self.cs_math, section=self.section_a)
        
        # Teacher 2 (Math 10B)
        self.t2_user = User.objects.create_user(email="teacher2@example.com", password="password123", role="TEACHER")
        self.t2_profile = TeacherProfile.objects.create(user=self.t2_user)
        TeacherAssignment.objects.create(academic_year=self.year, teacher=self.t2_profile, class_subject=self.cs_math, section=self.section_b)
        
        # Student 1 (10A)
        self.s1_user = User.objects.create_user(email="student1@example.com", password="password123", role="STUDENT")
        self.s1_profile = StudentProfile.objects.create(user=self.s1_user)
        Enrollment.objects.create(student=self.s1_profile, academic_year=self.year, class_level=self.class_10, section=self.section_a)
        
        # Parent 1 (Parent of Student 1)
        self.p1_user = User.objects.create_user(email="parent1@example.com", password="password123", role="PARENT")
        self.p1_profile = ParentProfile.objects.create(user=self.p1_user)
        self.p1_profile.children.add(self.s1_profile)
        
    def test_teacher_quiz_creation_authorization(self):
        """Teacher can only create quiz for assigned section."""
        self.client.login(email="teacher1@example.com", password="password123")
        
        # T1 tries to create quiz for 10B (Unauthorized)
        response = self.client.post(reverse('teacher_quiz_add'), {
            'academic_year': self.year.id,
            'class_subject': self.cs_math.id,
            'section': self.section_b.id, # 10B
            'title': 'Test Quiz',
            'description': 'Desc',
            'duration': 30,
            'passing_score': 50,
            'max_attempts': 1,
            'is_published': False
        })
        self.assertEqual(response.status_code, 403)
        
        # T1 creates for 10A (Authorized)
        response = self.client.post(reverse('teacher_quiz_add'), {
            'academic_year': self.year.id,
            'class_subject': self.cs_math.id,
            'section': self.section_a.id, # 10A
            'title': 'Test Quiz 10A',
            'description': 'Desc',
            'duration': 30,
            'passing_score': 50,
            'max_attempts': 1,
            'is_published': False
        })
        self.assertEqual(response.status_code, 302) # Success, redirect
        self.assertEqual(Quiz.objects.count(), 1)
        
    def test_quiz_publishing_validation(self):
        """Quiz cannot be published if it has no questions."""
        quiz = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Q1", description="D", duration=10, passing_score=50, max_attempts=1)
        quiz.is_published = True
        with self.assertRaisesMessage(ValidationError, "Cannot publish a quiz with no questions."):
            quiz.clean()
            
    def test_student_quiz_isolation(self):
        """Student can only access published quizzes for their section."""
        # Quiz for 10A (Published) - S1 can access
        q_10a = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="10A Quiz", description="D", duration=10, passing_score=50, is_published=True)
        # Quiz for 10B (Published) - S1 CANNOT access
        q_10b = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_b, teacher=self.t2_profile, title="10B Quiz", description="D", duration=10, passing_score=50, is_published=True)
        # Quiz for All Sections (Published) - S1 can access
        q_all = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=None, teacher=self.t1_profile, title="All Quiz", description="D", duration=10, passing_score=50, is_published=True)
        # Quiz for 10A (Unpublished) - S1 CANNOT access
        q_unpub = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Unpub Quiz", description="D", duration=10, passing_score=50, is_published=False)
        
        self.client.login(email="student1@example.com", password="password123")
        
        self.assertEqual(self.client.get(reverse('student_quiz_detail', args=[q_10a.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_quiz_detail', args=[q_all.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_quiz_detail', args=[q_10b.id])).status_code, 403)
        self.assertEqual(self.client.get(reverse('student_quiz_detail', args=[q_unpub.id])).status_code, 403)
        
    def test_quiz_attempt_expiration_and_scoring(self):
        """Test server-side expiration calculation and atomic evaluation logic."""
        quiz = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Scoring Test", description="D", duration=10, passing_score=60, is_published=True)
        q1 = Question.objects.create(quiz=quiz, text="2+2", option_a="3", option_b="4", option_c="5", option_d="6", correct_option="B", marks=10)
        q2 = Question.objects.create(quiz=quiz, text="5+5", option_a="9", option_b="10", option_c="11", option_d="12", correct_option="B", marks=10)
        
        self.client.login(email="student1@example.com", password="password123")
        
        # Start Attempt
        response = self.client.post(reverse('student_quiz_start', args=[quiz.id]))
        self.assertEqual(response.status_code, 302)
        attempt = QuizAttempt.objects.get(quiz=quiz, student=self.s1_profile)
        
        # Assert duration sets expires_at
        self.assertAlmostEqual((attempt.expires_at - attempt.start_time).total_seconds(), 10 * 60 + 5, delta=1) # 10 mins + 5 sec grace
        
        # Submit answers via form
        response = self.client.post(reverse('student_quiz_take', args=[attempt.id]), {
            f'question_{q1.id}': 'B', # Correct (10 marks)
            f'question_{q2.id}': 'C', # Incorrect (0 marks)
        })
        self.assertEqual(response.status_code, 302)
        
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'COMPLETED')
        self.assertTrue(hasattr(attempt, 'result'))
        
        result = attempt.result
        self.assertEqual(result.score, 10)
        self.assertEqual(result.percentage, 50) # 10/20
        self.assertFalse(result.passed) # passing is 60%
        self.assertEqual(result.correct_answers, 1)
        self.assertEqual(result.incorrect_answers, 1)
        
    def test_max_attempts_enforcement(self):
        """Test max attempts logic server-side."""
        quiz = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Max attempts", description="D", duration=10, passing_score=50, is_published=True, max_attempts=1)
        
        self.client.login(email="student1@example.com", password="password123")
        
        # Attempt 1
        self.client.post(reverse('student_quiz_start', args=[quiz.id]))
        attempt = QuizAttempt.objects.first()
        evaluate_quiz_attempt(attempt) # force complete
        
        # Attempt 2 (should be blocked)
        response = self.client.post(reverse('student_quiz_start', args=[quiz.id]))
        self.assertEqual(response.status_code, 403)
        
    def test_post_attempt_question_locking(self):
        """Questions cannot be added, edited, or deleted once an attempt exists."""
        quiz = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Lock Test", description="D", duration=10, passing_score=50, is_published=True)
        q1 = Question.objects.create(quiz=quiz, text="2+2", option_a="3", option_b="4", option_c="5", option_d="6", correct_option="B", marks=10)
        
        # Create an attempt
        QuizAttempt.objects.create(quiz=quiz, student=self.s1_profile)
        
        # Try to modify q1
        q1.marks = 20
        with self.assertRaisesMessage(ValidationError, "Cannot modify questions for a quiz that has already been attempted."):
            q1.save()
            
        # Try to delete q1
        with self.assertRaisesMessage(ValidationError, "Cannot delete questions from a quiz that has already been attempted."):
            q1.delete()
            
    def test_cross_quiz_answer_injection(self):
        """Test that QuizAnswer model rejects questions belonging to other quizzes."""
        quiz1 = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Q1", description="D", duration=10, passing_score=50, is_published=True)
        q1 = Question.objects.create(quiz=quiz1, text="2+2", option_a="3", option_b="4", option_c="5", option_d="6", correct_option="B", marks=10)
        
        quiz2 = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Q2", description="D", duration=10, passing_score=50, is_published=True)
        q2 = Question.objects.create(quiz=quiz2, text="3+3", option_a="5", option_b="6", option_c="7", option_d="8", correct_option="B", marks=10)
        
        attempt = QuizAttempt.objects.create(quiz=quiz1, student=self.s1_profile)
        
        # Try to answer Q2 (which belongs to Quiz 2) in an attempt for Quiz 1
        answer = QuizAnswer(attempt=attempt, question=q2, selected_option='B')
        with self.assertRaisesMessage(ValidationError, "Question does not belong to the quiz being attempted."):
            answer.clean()
            
    def test_parent_read_only_access(self):
        """Test that parents can view results but not take quizzes."""
        quiz = Quiz.objects.create(academic_year=self.year, class_subject=self.cs_math, section=self.section_a, teacher=self.t1_profile, title="Parent Test", description="D", duration=10, passing_score=50, is_published=True)
        attempt = QuizAttempt.objects.create(quiz=quiz, student=self.s1_profile, status='COMPLETED')
        QuizResult.objects.create(attempt=attempt, score=10, percentage=100, passed=True, correct_answers=1, incorrect_answers=0, attempted_questions=1, completion_time=timezone.timedelta(minutes=5))
        
        self.client.login(email="parent1@example.com", password="password123")
        
        # Parent can see child's result
        response = self.client.get(reverse('parent_quiz_result', args=[attempt.id]))
        self.assertEqual(response.status_code, 200)
        
        # But parent cannot take quiz
        response = self.client.post(reverse('student_quiz_start', args=[quiz.id]))
        self.assertEqual(response.status_code, 403) # Fails StudentAccessMixin
