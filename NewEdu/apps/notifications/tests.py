from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Enrollment, TeacherAssignment, Chapter, Lesson
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.quizzes.models import Quiz
from apps.ai_assistant.models import AIRecommendation

User = get_user_model()

class NotificationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(email='student1@test.com', password='password', role='STUDENT', first_name='S1', last_name='L1')
        self.student1 = StudentProfile.objects.create(user=self.user1)
        
        self.user2 = User.objects.create_user(email='student2@test.com', password='password', role='STUDENT', first_name='S2', last_name='L2')
        self.student2 = StudentProfile.objects.create(user=self.user2)
        
        self.teacher_user = User.objects.create_user(email='teacher@test.com', password='password', role='TEACHER', first_name='T1', last_name='L1')
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user)
        
        from datetime import date
        self.year = AcademicYear.objects.create(name='2026-2027', is_active=True, start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
        self.cls = Class.objects.create(name='Class 10', level=10)
        self.sec = Section.objects.create(name='A', class_level=self.cls)
        self.sec_b = Section.objects.create(name='B', class_level=self.cls)
        
        self.subject = Subject.objects.create(name='Math', code='MTH')
        self.class_subject = ClassSubject.objects.create(class_level=self.cls, subject=self.subject)
        
        # Enroll students
        self.enr1 = Enrollment.objects.create(student=self.student1, academic_year=self.year, class_level=self.cls, section=self.sec)
        self.enr2 = Enrollment.objects.create(student=self.student2, academic_year=self.year, class_level=self.cls, section=self.sec_b)
        
        # Teacher assignment
        TeacherAssignment.objects.create(teacher=self.teacher, academic_year=self.year, section=self.sec, class_subject=self.class_subject)

    def test_notification_creation_and_list(self):
        # Create a notification for user1
        n = Notification.objects.create(recipient=self.user1, title='Test', message='Msg')
        self.assertEqual(Notification.objects.filter(recipient=self.user1).count(), 1)
        
        self.client.login(email='student1@test.com', password='password')
        response = self.client.get(reverse('notification_list'))
        self.assertContains(response, 'Test')
        
        # User 2 shouldn't see it
        self.client.login(email='student2@test.com', password='password')
        response = self.client.get(reverse('notification_list'))
        self.assertNotContains(response, 'Test')

    def test_mark_as_read(self):
        n = Notification.objects.create(recipient=self.user1, title='Test', message='Msg', link_url='/test/')
        self.client.login(email='student1@test.com', password='password')
        
        response = self.client.post(reverse('notification_mark_read', args=[n.pk]))
        self.assertEqual(response.status_code, 302)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertEqual(response.url, '/test/')

    def test_mark_all_as_read(self):
        Notification.objects.create(recipient=self.user1, title='Test1', message='Msg1')
        Notification.objects.create(recipient=self.user1, title='Test2', message='Msg2')
        self.client.login(email='student1@test.com', password='password')
        
        response = self.client.post(reverse('notification_mark_all_read'))
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=True).count(), 2)
        
    def test_cross_user_isolation(self):
        n = Notification.objects.create(recipient=self.user1, title='Test1', message='Msg1')
        self.client.login(email='student2@test.com', password='password')
        # Student 2 tries to mark Student 1's notification as read
        response = self.client.post(reverse('notification_mark_read', args=[n.pk]))
        self.assertEqual(response.status_code, 404)
        n.refresh_from_db()
        self.assertFalse(n.is_read)

    def test_notify_assignment_created(self):
        assignment = Assignment.objects.create(
            title="Assignment 1",
            description="Test",
            academic_year=self.year,
            class_subject=self.class_subject,
            section=self.sec,
            teacher=self.teacher,
            due_date="2026-12-31"
        )
        NotificationService.notify_assignment_created(assignment)
        
        # Student 1 is in sec A, Student 2 is in sec B
        self.assertEqual(Notification.objects.filter(recipient=self.user1, notification_type='ASSIGNMENT').count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user2, notification_type='ASSIGNMENT').count(), 0)

    def test_notify_quiz_published(self):
        quiz = Quiz.objects.create(
            title="Quiz 1",
            description="Test",
            academic_year=self.year,
            class_subject=self.class_subject,
            section=self.sec,
            teacher=self.teacher,
            duration=10,
            passing_score=50,
            is_published=True
        )
        NotificationService.notify_quiz_published(quiz)
        
        self.assertEqual(Notification.objects.filter(recipient=self.user1, notification_type='QUIZ').count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user2, notification_type='QUIZ').count(), 0)

    def test_notify_assignment_graded(self):
        assignment = Assignment.objects.create(
            title="Assignment 1", description="Test", academic_year=self.year,
            class_subject=self.class_subject, section=self.sec, teacher=self.teacher, due_date="2026-12-31"
        )
        sub = AssignmentSubmission.objects.create(
            assignment=assignment, student=self.student1, status='GRADED', grade=80
        )
        NotificationService.notify_assignment_graded(sub)
        
        self.assertEqual(Notification.objects.filter(recipient=self.user1, notification_type='RESULT').count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user2, notification_type='RESULT').count(), 0)

    def test_notify_lesson_created(self):
        chap = Chapter.objects.create(class_subject=self.class_subject, title="Ch1", order=1)
        lesson = Lesson.objects.create(chapter=chap, title="L1", content="Content")
        NotificationService.notify_lesson_created(lesson)
        
        # Both students are in the same class level, so both should get it (assuming it's class-wide)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, notification_type='MATERIAL').count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user2, notification_type='MATERIAL').count(), 1)

    def test_notify_ai_recommendation(self):
        rec = AIRecommendation.objects.create(
            student=self.student1,
            academic_year=self.year,
            recommendation={"plan": "test"},
            source_data={"score": 80},
            reason="test",
            status='COMPLETED'
        )
        NotificationService.notify_ai_recommendation_ready(rec)
        
        self.assertEqual(Notification.objects.filter(recipient=self.user1, notification_type='AI_RECOMMENDATION').count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user2, notification_type='AI_RECOMMENDATION').count(), 0)
