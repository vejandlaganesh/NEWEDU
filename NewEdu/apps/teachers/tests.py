from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, Enrollment, TeacherAssignment

class TeacherModuleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup Academic Data
        self.year = AcademicYear.objects.create(name="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31), is_active=True)
        self.class_10 = Class.objects.create(level=10, name="Class 10")
        self.section_a = Section.objects.create(class_level=self.class_10, name="A")
        self.section_b = Section.objects.create(class_level=self.class_10, name="B")
        
        self.subject_math = Subject.objects.create(name="Mathematics", code="MATH101")
        self.subject_science = Subject.objects.create(name="Science", code="SCI101")
        
        self.cs_math = ClassSubject.objects.create(class_level=self.class_10, subject=self.subject_math)
        self.cs_science = ClassSubject.objects.create(class_level=self.class_10, subject=self.subject_science)
        
        self.chapter_math = Chapter.objects.create(class_subject=self.cs_math, title="Algebra", order=1)
        self.lesson_math = Lesson.objects.create(chapter=self.chapter_math, title="Linear Equations", order=1)

        # Setup Teacher 1 (Math in 10A)
        self.teacher1_user = User.objects.create_user(email="teacher1@test.com", password="pw", role="TEACHER", first_name="T1", last_name="Teacher")
        self.teacher1_profile = TeacherProfile.objects.create(user=self.teacher1_user)
        self.assignment1 = TeacherAssignment.objects.create(teacher=self.teacher1_profile, academic_year=self.year, section=self.section_a, class_subject=self.cs_math)

        # Setup Teacher 2 (Science in 10B)
        self.teacher2_user = User.objects.create_user(email="teacher2@test.com", password="pw", role="TEACHER", first_name="T2", last_name="Teacher")
        self.teacher2_profile = TeacherProfile.objects.create(user=self.teacher2_user)
        self.assignment2 = TeacherAssignment.objects.create(teacher=self.teacher2_profile, academic_year=self.year, section=self.section_b, class_subject=self.cs_science)

        # Setup Student (In 10A)
        self.student_user = User.objects.create_user(email="student@test.com", password="pw", role="STUDENT", first_name="S1", last_name="Student")
        self.student_profile = StudentProfile.objects.create(user=self.student_user)
        self.enrollment = Enrollment.objects.create(student=self.student_profile, academic_year=self.year, class_level=self.class_10, section=self.section_a)

    def test_dashboard_kpis(self):
        self.client.login(username='teacher1@test.com', password='pw')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, T1 Teacher')
        # 1 section, 1 subject, 1 student
        self.assertEqual(response.context['classes_count'], 1)
        self.assertEqual(response.context['subjects_count'], 1)
        self.assertEqual(response.context['student_count'], 1)

    def test_student_isolation(self):
        # Teacher 1 should see student in 10A
        self.client.login(username='teacher1@test.com', password='pw')
        response = self.client.get(reverse('teacher_students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'S1 Student')
        
        # Teacher 2 should NOT see student in 10A (since they only teach 10B)
        self.client.login(username='teacher2@test.com', password='pw')
        response = self.client.get(reverse('teacher_students'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'S1 Student')

    def test_material_creation_authorization(self):
        # Teacher 1 can add chapter to Math
        self.client.login(username='teacher1@test.com', password='pw')
        response = self.client.get(reverse('teacher_chapter_create', kwargs={'class_subject_id': self.cs_math.id}))
        self.assertEqual(response.status_code, 200)
        
        # Teacher 2 CANNOT add chapter to Math
        self.client.login(username='teacher2@test.com', password='pw')
        response = self.client.get(reverse('teacher_chapter_create', kwargs={'class_subject_id': self.cs_math.id}))
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_material_edit_isolation(self):
        # Teacher 1 can edit Math chapter (but let's check view access)
        # Edit view filters queryset. So accessing an unauthorized chapter ID should 404
        self.client.login(username='teacher2@test.com', password='pw')
        response = self.client.get(reverse('teacher_chapter_edit', kwargs={'pk': self.chapter_math.id}))
        self.assertEqual(response.status_code, 404) # Due to queryset filtering

    def test_role_isolation(self):
        # Student cannot access teacher dashboard
        self.client.login(username='student@test.com', password='pw')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 403) # PermissionDenied

import json
from unittest.mock import patch, MagicMock
from apps.content.models import GeneratedContent
from apps.quizzes.models import Quiz, Question
from apps.ai_assistant.services.schemas import GeneratedContentSchema, GeneratedQuizSchema, QuizQuestionSchema

class TeacherAIToolsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.year = AcademicYear.objects.create(name="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31), is_active=True)
        self.class_10 = Class.objects.create(level=10, name="Class 10")
        self.section_a = Section.objects.create(class_level=self.class_10, name="A")
        self.subject_math = Subject.objects.create(name="Mathematics", code="MATH101")
        self.cs_math = ClassSubject.objects.create(class_level=self.class_10, subject=self.subject_math)
        
        self.teacher_user = User.objects.create_user(email="teacher@test.com", password="pw", role="TEACHER")
        self.teacher_profile = TeacherProfile.objects.create(user=self.teacher_user)
        self.assignment = TeacherAssignment.objects.create(teacher=self.teacher_profile, academic_year=self.year, section=self.section_a, class_subject=self.cs_math)
        
        self.other_teacher_user = User.objects.create_user(email="other@test.com", password="pw", role="TEACHER")
        self.other_teacher_profile = TeacherProfile.objects.create(user=self.other_teacher_user)

    @patch('apps.teachers.views.GeminiService.generate_teacher_content')
    def test_generate_content_api(self, mock_generate):
        # Mock the AI response
        mock_schema = GeneratedContentSchema(title="Test Title", content="Test Content")
        mock_generate.return_value = (mock_schema, None)
        
        self.client.login(username='teacher@test.com', password='pw')
        payload = {
            'class_subject_id': self.cs_math.id,
            'topic': 'Algebra',
            'difficulty': 'Medium',
            'content_type': 'Explanation'
        }
        response = self.client.post(reverse('teacher_ai_content'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], "Test Title")
        
    def test_generate_content_isolation(self):
        self.client.login(username='other@test.com', password='pw')
        payload = {
            'class_subject_id': self.cs_math.id,
            'topic': 'Algebra',
            'difficulty': 'Medium',
            'content_type': 'Explanation'
        }
        response = self.client.post(reverse('teacher_ai_content'), data=json.dumps(payload), content_type='application/json')
        # other_teacher is not assigned to cs_math
        self.assertEqual(response.status_code, 403)
        
    def test_save_generated_content(self):
        self.client.login(username='teacher@test.com', password='pw')
        payload = {
            'class_subject_id': self.cs_math.id,
            'topic': 'Algebra',
            'difficulty': 'Medium',
            'content_type': 'Explanation',
            'title': 'Test Save',
            'content': 'Saved content'
        }
        response = self.client.post(reverse('teacher_ai_content_save'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify it was saved as DRAFT
        gc = GeneratedContent.objects.first()
        self.assertIsNotNone(gc)
        self.assertEqual(gc.status, 'DRAFT')
        self.assertEqual(gc.title, 'Test Save')
        self.assertEqual(gc.teacher, self.teacher_profile)

    def test_save_generated_quiz(self):
        self.client.login(username='teacher@test.com', password='pw')
        payload = {
            'class_subject_id': self.cs_math.id,
            'quiz_data': {
                'title': 'AI Quiz',
                'description': 'AI Quiz Desc',
                'questions': [
                    {
                        'question_text': '1+1?',
                        'option_a': '1', 'option_b': '2', 'option_c': '3', 'option_d': '4',
                        'correct_option': 'B',
                        'explanation': 'Because math'
                    }
                ]
            }
        }
        response = self.client.post(reverse('teacher_ai_quiz_save'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify it was saved as Unpublished
        quiz = Quiz.objects.first()
        self.assertIsNotNone(quiz)
        self.assertFalse(quiz.is_published)
        self.assertEqual(quiz.title, 'AI Quiz')
        
        # Verify question was created
        q = Question.objects.first()
        self.assertIsNotNone(q)
        self.assertEqual(q.quiz, quiz)
        self.assertEqual(q.correct_option, 'B')
