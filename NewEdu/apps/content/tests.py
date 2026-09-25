from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.content.models import LearningMaterial
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, TeacherAssignment, Enrollment
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from datetime import date

User=get_user_model()

class LearningMaterialTests(TestCase):
    def setUp(self):
        self.teacher_user=User.objects.create_user(email='teacher@newedu.test',password='pass12345',role='TEACHER')
        self.teacher=TeacherProfile.objects.create(user=self.teacher_user)
        year=AcademicYear.objects.create(name='2026-2027',start_date=date(2026,6,1),end_date=date(2027,5,31),is_active=True)
        cls=Class.objects.create(level=6,name='Class 6'); sec=Section.objects.create(class_level=cls,name='A')
        sub=Subject.objects.create(name='Mathematics',code='MATH6'); cs=ClassSubject.objects.create(class_level=cls,subject=sub)
        TeacherAssignment.objects.create(teacher=self.teacher,academic_year=year,section=sec,class_subject=cs)
        chapter=Chapter.objects.create(class_subject=cs,title='Numbers',order=1)
        lesson=Lesson.objects.create(chapter=chapter,title='Integers',order=1,content='Basics')
        self.material=LearningMaterial.objects.create(class_subject=cs,chapter=chapter,lesson=lesson,teacher=self.teacher,title='Integers Notes',material_type='TEXT',text_content='Notes')
    def test_material_is_linked(self):
        self.assertEqual(self.material.lesson.title,'Integers')
        self.assertEqual(self.material.class_subject.class_level.level,6)
