from django.urls import reverse
from django.db.models import Q
from apps.academics.models import AcademicYear, ClassSubject, Section, Subject, Chapter, Lesson, Enrollment, TeacherAssignment
from apps.assignments.models import Assignment
from apps.quizzes.models import Quiz
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile
from apps.content.models import LearningMaterial

class GlobalSearchService:
    @staticmethod
    def _get_active_year():
        return AcademicYear.objects.filter(is_active=True).first()
        
    @staticmethod
    def _get_authorized_scopes(user, year):
        """Returns (class_subjects_qs, sections_qs) authorized for the user."""
        if not year:
            return ClassSubject.objects.none(), Section.objects.none()
            
        if user.role == 'STUDENT':
            enrollments = Enrollment.objects.filter(student__user=user, academic_year=year)
            class_subjects = ClassSubject.objects.filter(class_level__in=enrollments.values('class_level'))
            sections = Section.objects.filter(id__in=enrollments.values('section'))
            return class_subjects, sections
            
        elif user.role == 'TEACHER':
            assignments = TeacherAssignment.objects.filter(teacher__user=user, academic_year=year)
            class_subjects = ClassSubject.objects.filter(id__in=assignments.values('class_subject'))
            sections = Section.objects.filter(id__in=assignments.values('section'))
            return class_subjects, sections
            
        elif user.role == 'PARENT':
            try:
                parent = ParentProfile.objects.get(user=user)
                children = parent.children.all()
                enrollments = Enrollment.objects.filter(student__in=children, academic_year=year)
                class_subjects = ClassSubject.objects.filter(class_level__in=enrollments.values('class_level'))
                sections = Section.objects.filter(id__in=enrollments.values('section'))
                return class_subjects, sections
            except ParentProfile.DoesNotExist:
                return ClassSubject.objects.none(), Section.objects.none()
                
        return ClassSubject.objects.none(), Section.objects.none()

    @staticmethod
    def search(user, query, limit_per_category=10):
        if not query or not query.strip():
            return {}
            
        query = query.strip()
        year = GlobalSearchService._get_active_year()
        if not year:
            return {}
            
        auth_class_subjects, auth_sections = GlobalSearchService._get_authorized_scopes(user, year)
        
        if not auth_class_subjects.exists():
            return {}

        results = {
            'subjects': [],
            'chapters': [],
            'lessons': [],
            'assignments': [],
            'quizzes': []
        }
        
        # 1. Subjects
        subjects = Subject.objects.filter(class_subjects__in=auth_class_subjects).filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        ).distinct()[:limit_per_category]
        
        for s in subjects:
            cs = auth_class_subjects.filter(subject=s).first()
            url = reverse('student_subject_detail', args=[cs.id]) if cs and user.role == 'STUDENT' else reverse('teacher_subjects') if user.role == 'TEACHER' else reverse('parent_reports')
            results['subjects'].append({
                'id': s.id,
                'title': f"{s.name} ({s.code})",
                'type': 'Subject',
                'url': url,
            })
            
        # 2. Chapters
        chapters = Chapter.objects.filter(class_subject__in=auth_class_subjects).filter(
            title__icontains=query
        ).distinct()[:limit_per_category]
        
        for c in chapters:
            if user.role == 'STUDENT':
                url = reverse('student_chapter_detail', args=[c.id])
            elif user.role == 'TEACHER':
                url = reverse('teacher_chapter_edit', args=[c.id])
            else:
                url = reverse('parent_reports')
            results['chapters'].append({
                'id': c.id,
                'title': c.title,
                'type': 'Chapter',
                'context': str(c.class_subject),
                'url': url,
            })
            
        # 3. Lessons
        lessons = Lesson.objects.filter(chapter__class_subject__in=auth_class_subjects).filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).distinct()[:limit_per_category]
        
        for l in lessons:
            if user.role == 'STUDENT':
                url = reverse('student_lesson_detail', args=[l.id])
            elif user.role == 'TEACHER':
                url = reverse('teacher_lesson_edit', args=[l.id])
            else:
                url = reverse('parent_reports')
            results['lessons'].append({
                'id': l.id,
                'title': l.title,
                'type': 'Lesson',
                'context': f"{l.chapter.class_subject} - {l.chapter.title}",
                'url': url,
            })
            
        # 4. Assignments
        if user.role == 'TEACHER':
            assignments = Assignment.objects.filter(
                academic_year=year,
                teacher__user=user,
                class_subject__in=auth_class_subjects,
                section__in=auth_sections
            )
        else:
            assignments = Assignment.objects.filter(
                academic_year=year,
                class_subject__in=auth_class_subjects,
                section__in=auth_sections
            )
            
        assignments = assignments.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()[:limit_per_category]
        
        for a in assignments:
            if user.role == 'STUDENT':
                url = reverse('student_assignment_detail', args=[a.id])
            elif user.role == 'TEACHER':
                url = reverse('teacher_assignment_detail', args=[a.id])
            elif user.role == 'PARENT':
                url = reverse('parent_assignments')
            else:
                url = reverse('admin_assignments')
            results['assignments'].append({
                'id': a.id,
                'title': a.title,
                'type': 'Assignment',
                'context': str(a.class_subject),
                'url': url,
            })
            
        # 5. Quizzes
        if user.role == 'TEACHER':
            quizzes = Quiz.objects.filter(
                academic_year=year,
                teacher__user=user
            )
        else:
            quizzes = Quiz.objects.filter(
                academic_year=year,
                class_subject__in=auth_class_subjects,
                is_published=True
            ).filter(
                Q(section__in=auth_sections) | Q(section__isnull=True)
            )
            
        quizzes = quizzes.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()[:limit_per_category]
        
        for q in quizzes:
            if user.role == 'STUDENT':
                url = reverse('student_quiz_detail', args=[q.id])
            elif user.role == 'TEACHER':
                url = reverse('teacher_quiz_detail', args=[q.id])
            elif user.role == 'PARENT':
                url = reverse('parent_quizzes')
            else:
                url = reverse('admin_quizzes')
            results['quizzes'].append({
                'id': q.id,
                'title': q.title,
                'type': 'Quiz',
                'context': str(q.class_subject),
                'url': url,
            })
            
        # 6. Learning materials
        materials = LearningMaterial.objects.filter(class_subject__in=auth_class_subjects, is_published=True).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('lesson','chapter','class_subject').distinct()[:limit_per_category]
        results['materials'] = []
        for m in materials:
            url = reverse('student_lesson_detail', args=[m.lesson_id]) if user.role == 'STUDENT' and m.lesson_id else (reverse('teacher_materials') if user.role == 'TEACHER' else reverse('parent_reports'))
            results['materials'].append({'id': m.id, 'title': m.title, 'type': 'Learning Material', 'context': str(m.class_subject), 'url': url})

        return results
