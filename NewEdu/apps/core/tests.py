from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject

class AdminModuleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup Admin
        self.admin_user = User.objects.create_superuser(email="admin@test.com", password="pw")
        
        # Setup Non-Admin
        self.student_user = User.objects.create_user(email="student@test.com", password="pw", role="STUDENT")

    def test_admin_dashboard_access(self):
        # Admin can access
        self.client.login(username='admin@test.com', password='pw')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Overview")
        
        # Student cannot access
        self.client.login(username='student@test.com', password='pw')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_user_creation_creates_profile(self):
        self.client.login(username='admin@test.com', password='pw')
        
        response = self.client.post(reverse('admin_user_create'), {
            'email': 'newstudent@test.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'STUDENT'
        })
        
        self.assertEqual(response.status_code, 302) # Redirect to user list
        
        # Verify user created
        user = User.objects.get(email='newstudent@test.com')
        self.assertEqual(user.role, 'STUDENT')
        
        # Verify profile created transactionally
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    def test_user_toggle_active(self):
        self.client.login(username='admin@test.com', password='pw')
        
        # Toggle student active status
        self.assertTrue(self.student_user.is_active)
        
        response = self.client.post(reverse('admin_user_toggle', args=[self.student_user.id]))
        self.assertEqual(response.status_code, 302)
        
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active)

    def test_academic_management(self):
        self.client.login(username='admin@test.com', password='pw')
        
        # Create class
        response = self.client.post(reverse('admin_class_create'), {
            'level': 10,
            'name': 'Class 10'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Class.objects.filter(level=10).exists())
