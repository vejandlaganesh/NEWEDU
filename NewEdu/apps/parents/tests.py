from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.students.models import StudentProfile
from apps.parents.models import ParentProfile
from apps.academics.models import AcademicYear, Class, Section, Enrollment

class ParentModuleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Setup Academic Data
        self.year = AcademicYear.objects.create(name="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31), is_active=True)
        self.class_10 = Class.objects.create(level=10, name="Class 10")
        self.section_a = Section.objects.create(class_level=self.class_10, name="A")
        
        # Setup Students
        self.student1_user = User.objects.create_user(email="child1@test.com", password="pw", role="STUDENT", first_name="Child", last_name="One")
        self.student1_profile = StudentProfile.objects.create(user=self.student1_user)
        self.enrollment1 = Enrollment.objects.create(student=self.student1_profile, academic_year=self.year, class_level=self.class_10, section=self.section_a)

        self.student2_user = User.objects.create_user(email="child2@test.com", password="pw", role="STUDENT", first_name="Child", last_name="Two")
        self.student2_profile = StudentProfile.objects.create(user=self.student2_user)
        self.enrollment2 = Enrollment.objects.create(student=self.student2_profile, academic_year=self.year, class_level=self.class_10, section=self.section_a)
        
        self.student3_user = User.objects.create_user(email="otherchild@test.com", password="pw", role="STUDENT", first_name="Other", last_name="Child")
        self.student3_profile = StudentProfile.objects.create(user=self.student3_user)

        # Setup Parent
        self.parent_user = User.objects.create_user(email="parent@test.com", password="pw", role="PARENT", first_name="Parent", last_name="User")
        self.parent_profile = ParentProfile.objects.create(user=self.parent_user)
        
        # Link Parent to Child 1 and Child 2
        self.parent_profile.children.add(self.student1_profile, self.student2_profile)

    def test_parent_dashboard_default_child(self):
        self.client.login(username='parent@test.com', password='pw')
        response = self.client.get(reverse('parent_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Should default to first child (Child One)
        self.assertContains(response, "Child's Academic Status")
        # Session should have child id
        self.assertIn('selected_child_id', self.client.session)

    def test_parent_dashboard_switch_child(self):
        self.client.login(username='parent@test.com', password='pw')
        response = self.client.get(reverse('parent_dashboard') + f'?child_id={self.student2_profile.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Child's Academic Status") # It will say "Child's Academic Status" (first name is Child for both, but it works)
        self.assertEqual(self.client.session['selected_child_id'], self.student2_profile.id)

    def test_parent_unauthorized_child_access(self):
        self.client.login(username='parent@test.com', password='pw')
        # Try to access a child not linked to this parent
        response = self.client.get(reverse('parent_dashboard') + f'?child_id={self.student3_profile.id}')
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_parent_unlinked_state(self):
        parent2_user = User.objects.create_user(email="parent2@test.com", password="pw", role="PARENT")
        ParentProfile.objects.create(user=parent2_user)
        self.client.login(username='parent2@test.com', password='pw')
        
        response = self.client.get(reverse('parent_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You currently have no children linked")

    def test_role_isolation(self):
        # Teacher cannot access parent dashboard
        teacher_user = User.objects.create_user(email="t@test.com", password="pw", role="TEACHER")
        self.client.login(username='t@test.com', password='pw')
        response = self.client.get(reverse('parent_dashboard'))
        self.assertEqual(response.status_code, 403)
