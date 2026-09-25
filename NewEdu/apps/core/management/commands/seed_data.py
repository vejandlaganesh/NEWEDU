from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.academics.models import AcademicYear, Class, Section, Subject, ClassSubject, Chapter, Lesson, Enrollment, TeacherAssignment

User=get_user_model()

class Command(BaseCommand):
    help='Create safe development/demo data for NEWEDU.'
    def handle(self,*args,**options):
        year,_=AcademicYear.objects.get_or_create(name='2026-2027', defaults={'start_date':date(2026,6,1),'end_date':date(2027,5,31),'is_active':True})
        if not year.is_active:
            AcademicYear.objects.update(is_active=False); year.is_active=True; year.save(update_fields=['is_active'])
        for level in range(6,13): Class.objects.get_or_create(level=level, defaults={'name':f'Class {level}'})
        subjects=[('Mathematics','MATH'),('Science','SCI'),('English','ENG')]
        teacher_user,_=User.objects.get_or_create(email='teacher@newedu.local', defaults={'first_name':'Demo','last_name':'Teacher','role':'TEACHER'})
        teacher_user.role='TEACHER'; teacher_user.set_password('DemoTeacher123!'); teacher_user.save()
        teacher,_=TeacherProfile.objects.get_or_create(user=teacher_user)
        student_user,_=User.objects.get_or_create(email='student@newedu.local', defaults={'first_name':'Demo','last_name':'Student','role':'STUDENT'})
        student_user.role='STUDENT'; student_user.set_password('DemoStudent123!'); student_user.save()
        student,_=StudentProfile.objects.get_or_create(user=student_user)
        parent_user,_=User.objects.get_or_create(email='parent@newedu.local', defaults={'first_name':'Demo','last_name':'Parent','role':'PARENT'})
        parent_user.role='PARENT'; parent_user.set_password('DemoParent123!'); parent_user.save()
        parent,_=ParentProfile.objects.get_or_create(user=parent_user); parent.children.add(student)
        cls=Class.objects.get(level=10); section,_=Section.objects.get_or_create(class_level=cls,name='A')
        Enrollment.objects.update_or_create(student=student,academic_year=year,defaults={'class_level':cls,'section':section})
        for name,code in subjects:
            sub,_=Subject.objects.get_or_create(code=code,defaults={'name':name})
            cs,_=ClassSubject.objects.get_or_create(class_level=cls,subject=sub)
            TeacherAssignment.objects.get_or_create(teacher=teacher,academic_year=year,section=section,class_subject=cs)
            chapter,_=Chapter.objects.get_or_create(class_subject=cs,title='Introduction',defaults={'order':1})
            Lesson.objects.get_or_create(chapter=chapter,title='Getting Started',defaults={'order':1,'content':f'Introduction to {name} for Class 10.'})
        self.stdout.write(self.style.SUCCESS('NEWEDU demo data created/updated.'))
        self.stdout.write('Demo accounts: student@newedu.local / DemoStudent123!, teacher@newedu.local / DemoTeacher123!, parent@newedu.local / DemoParent123!')
