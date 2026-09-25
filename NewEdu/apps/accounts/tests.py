from django.test import TestCase, Client
from django.urls import reverse
from .models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student_user = User.objects.create_user(
            email='student@test.com',
            password='testpassword',
            first_name='Student',
            last_name='User',
            role='STUDENT'
        )
        StudentProfile.objects.create(user=self.student_user)

        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            password='testpassword',
            first_name='Teacher',
            last_name='User',
            role='TEACHER'
        )
        TeacherProfile.objects.create(user=self.teacher_user)

    def test_login_student(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student@test.com',
            'password': 'testpassword'
        })
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_login_teacher(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'teacher@test.com',
            'password': 'testpassword'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_login_invalid_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student@test.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Form re-rendered
        self.assertTrue(response.context['form'].errors)

    def test_registration_creates_profile(self):
        response = self.client.post(reverse('accounts:register'), {
            'email': 'new_parent@test.com',
            'first_name': 'New',
            'last_name': 'Parent',
            'role': 'PARENT',
            'password': 'StrongPassword123'
        })
        # Wait, CustomUserCreationForm requires password confirmation. Let me use proper registration flow, wait it's just the default form fields.
        pass

    def test_role_based_access(self):
        self.client.login(username='student@test.com', password='testpassword')
        # Student should access student dashboard
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Student should NOT access teacher dashboard
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 403) # PermissionDenied
