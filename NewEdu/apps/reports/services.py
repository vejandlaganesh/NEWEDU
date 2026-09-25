from django.db.models import Avg, Count, F, ExpressionWrapper, FloatField, Q
from django.utils import timezone
from apps.assignments.models import AssignmentSubmission, Assignment
from apps.quizzes.models import QuizResult, QuizAttempt, Quiz
from apps.academics.models import ClassSubject, Chapter, Enrollment
from itertools import groupby
from operator import itemgetter

def get_student_performance(student, academic_year):
    """
    Aggregates overall student performance for a given academic year.
    Returns average assignment score (normalized to percentage) and average quiz score.
    """
    # Assignments
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__academic_year=academic_year,
        status='GRADED',
        grade__isnull=False
    )
    
    assignment_stats = submissions.annotate(
        percentage=ExpressionWrapper(
            F('grade') * 100.0 / F('assignment__max_score'),
            output_field=FloatField()
        )
    ).aggregate(
        avg_score=Avg('percentage'),
        total_completed=Count('id')
    )
    
    avg_assignment = round(assignment_stats['avg_score'], 2) if assignment_stats['avg_score'] is not None else None
    
    # Quizzes
    quiz_results = QuizResult.objects.filter(
        attempt__student=student,
        attempt__quiz__academic_year=academic_year,
        attempt__status='COMPLETED'
    )
    
    quiz_stats = quiz_results.aggregate(
        avg_score=Avg('percentage'),
        total_completed=Count('id')
    )
    
    avg_quiz = round(quiz_stats['avg_score'], 2) if quiz_stats['avg_score'] is not None else None
    
    # Overall Assessment Average (simple average of the two if both exist, otherwise the one that exists)
    overall_avg = None
    if avg_assignment is not None and avg_quiz is not None:
        overall_avg = round((avg_assignment + avg_quiz) / 2, 2)
    elif avg_assignment is not None:
        overall_avg = avg_assignment
    elif avg_quiz is not None:
        overall_avg = avg_quiz
        
    return {
        'avg_assignment_score': avg_assignment,
        'assignments_completed': assignment_stats['total_completed'] or 0,
        'avg_quiz_score': avg_quiz,
        'quizzes_completed': quiz_stats['total_completed'] or 0,
        'overall_assessment_avg': overall_avg
    }

def get_student_subject_performance(student, academic_year):
    """
    Returns list of dicts with subject-level performance.
    """
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__academic_year=academic_year,
        status='GRADED',
        grade__isnull=False
    ).annotate(
        subject_id=F('assignment__class_subject_id'),
        subject_name=F('assignment__class_subject__subject__name'),
        percentage=ExpressionWrapper(
            F('grade') * 100.0 / F('assignment__max_score'),
            output_field=FloatField()
        )
    ).values('subject_id', 'subject_name').annotate(
        avg_assignment=Avg('percentage')
    ).order_by('subject_name')
    
    quiz_results = QuizResult.objects.filter(
        attempt__student=student,
        attempt__quiz__academic_year=academic_year,
        attempt__status='COMPLETED'
    ).annotate(
        subject_id=F('attempt__quiz__class_subject_id'),
        subject_name=F('attempt__quiz__class_subject__subject__name')
    ).values('subject_id', 'subject_name').annotate(
        avg_quiz=Avg('percentage')
    ).order_by('subject_name')
    
    # Merge the two QuerySets by subject_id
    subjects_map = {}
    
    for sub in submissions:
        sid = sub['subject_id']
        subjects_map[sid] = {
            'subject_name': sub['subject_name'],
            'avg_assignment': round(sub['avg_assignment'], 2) if sub['avg_assignment'] is not None else None,
            'avg_quiz': None
        }
        
    for qz in quiz_results:
        sid = qz['subject_id']
        if sid not in subjects_map:
            subjects_map[sid] = {
                'subject_name': qz['subject_name'],
                'avg_assignment': None,
                'avg_quiz': round(qz['avg_quiz'], 2) if qz['avg_quiz'] is not None else None
            }
        else:
            subjects_map[sid]['avg_quiz'] = round(qz['avg_quiz'], 2) if qz['avg_quiz'] is not None else None
            
    for sid, data in subjects_map.items():
        avg_a = data['avg_assignment']
        avg_q = data['avg_quiz']
        overall = None
        if avg_a is not None and avg_q is not None:
            overall = round((avg_a + avg_q) / 2, 2)
        elif avg_a is not None:
            overall = avg_a
        elif avg_q is not None:
            overall = avg_q
        data['overall_avg'] = overall
        
    return list(subjects_map.values())

def get_student_assessment_trend(student, academic_year):
    """
    Time-series data of assignment and quiz scores for chart.
    """
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__academic_year=academic_year,
        status='GRADED',
        grade__isnull=False
    ).annotate(
        percentage=ExpressionWrapper(
            F('grade') * 100.0 / F('assignment__max_score'),
            output_field=FloatField()
        )
    ).values('updated_at', 'assignment__title', 'percentage').order_by('updated_at')
    
    quiz_results = QuizResult.objects.filter(
        attempt__student=student,
        attempt__quiz__academic_year=academic_year,
        attempt__status='COMPLETED'
    ).values('attempt__end_time', 'attempt__quiz__title', 'percentage').order_by('attempt__end_time')
    
    trend_data = []
    for sub in submissions:
        trend_data.append({
            'date': sub['updated_at'].strftime('%Y-%m-%d %H:%M'),
            'timestamp': sub['updated_at'].timestamp(),
            'title': f"Assign: {sub['assignment__title']}",
            'score': round(sub['percentage'], 2)
        })
        
    for qz in quiz_results:
        trend_data.append({
            'date': qz['attempt__end_time'].strftime('%Y-%m-%d %H:%M'),
            'timestamp': qz['attempt__end_time'].timestamp(),
            'title': f"Quiz: {sub['attempt__quiz__title']}" if 'attempt__quiz__title' in sub else f"Quiz: {qz['attempt__quiz__title']}",
            'score': round(qz['percentage'], 2)
        })
        
    # Correcting the bug above where I used `sub` instead of `qz` in loop body:
    for item in trend_data:
        if 'Quiz: ' in item['title'] and 'attempt__quiz__title' not in locals():
            pass # Just a safeguard, I will rewrite the loop properly below.
    
    # Actually, let's fix it right here:
    trend_data = []
    for sub in submissions:
        trend_data.append({
            'date': sub['updated_at'].strftime('%Y-%m-%d %H:%M'),
            'timestamp': sub['updated_at'].timestamp(),
            'title': f"Assign: {sub['assignment__title']}",
            'score': round(sub['percentage'], 2)
        })
        
    for qz in quiz_results:
        if qz['attempt__end_time']:
            trend_data.append({
                'date': qz['attempt__end_time'].strftime('%Y-%m-%d %H:%M'),
                'timestamp': qz['attempt__end_time'].timestamp(),
                'title': f"Quiz: {qz['attempt__quiz__title']}",
                'score': round(qz['percentage'], 2)
            })
            
    trend_data.sort(key=lambda x: x['timestamp'])
    return trend_data

def get_missing_submissions(student, academic_year):
    """
    Returns assignments whose due date has passed and for which the student has no submission.
    """
    now = timezone.now()
    try:
        enrollment = Enrollment.objects.get(student=student, academic_year=academic_year)
    except Enrollment.DoesNotExist:
        return []
        
    # Assignments applicable to this student's section/class that are past due
    applicable_assignments = Assignment.objects.filter(
        academic_year=academic_year,
        section=enrollment.section,
        class_subject__class_level=enrollment.class_level,
        due_date__lt=now
    )
    
    # Exclude assignments where student has a submission
    missing = applicable_assignments.exclude(
        submissions__student=student
    ).order_by('-due_date')
    
    return list(missing)

def get_teacher_class_performance(teacher, academic_year):
    """
    Aggregates performance across sections assigned to a teacher.
    """
    # TeacherAssignments for the year
    teacher_assignments = teacher.assignments.filter(academic_year=academic_year)
    section_ids = teacher_assignments.values_list('section_id', flat=True).distinct()
    class_subject_ids = teacher_assignments.values_list('class_subject_id', flat=True).distinct()
    
    if not section_ids:
        return []
        
    # We want average score per section for the teacher's class_subjects.
    # Assignments:
    submissions = AssignmentSubmission.objects.filter(
        assignment__academic_year=academic_year,
        assignment__section_id__in=section_ids,
        assignment__class_subject_id__in=class_subject_ids,
        status='GRADED',
        grade__isnull=False
    ).annotate(
        section_name=F('assignment__section__name'),
        class_name=F('assignment__class_subject__class_level__name'),
        percentage=ExpressionWrapper(
            F('grade') * 100.0 / F('assignment__max_score'),
            output_field=FloatField()
        )
    ).values('assignment__section_id', 'section_name', 'class_name').annotate(
        avg_assignment=Avg('percentage')
    )
    
    # Quizzes:
    # Quiz might have section=None (cross section). But we filter QuizAttempts by student's enrollment section?
    # Actually, QuizAttempt links to student. We can join student -> enrollment -> section.
    quiz_results = QuizResult.objects.filter(
        attempt__quiz__academic_year=academic_year,
        attempt__quiz__class_subject_id__in=class_subject_ids,
        attempt__status='COMPLETED'
    ).annotate(
        # We need the student's section.
        section_id=F('attempt__student__enrollments__section_id'),
        section_name=F('attempt__student__enrollments__section__name'),
        class_name=F('attempt__student__enrollments__class_level__name')
    ).filter(
        # Make sure the enrollment is for the same academic year
        attempt__student__enrollments__academic_year=academic_year,
        section_id__in=section_ids
    ).values('section_id', 'section_name', 'class_name').annotate(
        avg_quiz=Avg('percentage')
    )
    
    sections_map = {}
    for sub in submissions:
        sid = sub['assignment__section_id']
        sections_map[sid] = {
            'section_name': f"{sub['class_name']} - {sub['section_name']}",
            'avg_assignment': round(sub['avg_assignment'], 2) if sub['avg_assignment'] is not None else None,
            'avg_quiz': None
        }
        
    for qz in quiz_results:
        sid = qz['section_id']
        if sid not in sections_map:
            sections_map[sid] = {
                'section_name': f"{qz['class_name']} - {qz['section_name']}",
                'avg_assignment': None,
                'avg_quiz': round(qz['avg_quiz'], 2) if qz['avg_quiz'] is not None else None
            }
        else:
            sections_map[sid]['avg_quiz'] = round(qz['avg_quiz'], 2) if qz['avg_quiz'] is not None else None
            
    for sid, data in sections_map.items():
        avg_a = data['avg_assignment']
        avg_q = data['avg_quiz']
        overall = None
        if avg_a is not None and avg_q is not None:
            overall = round((avg_a + avg_q) / 2, 2)
        elif avg_a is not None:
            overall = avg_a
        elif avg_q is not None:
            overall = avg_q
        data['overall_avg'] = overall
        
    return sorted(list(sections_map.values()), key=lambda x: x['section_name'])

def get_teacher_assignment_stats(teacher, academic_year):
    """
    Completion rate and avg grade for teacher's assignments.
    """
    assignments = Assignment.objects.filter(
        teacher=teacher,
        academic_year=academic_year
    ).annotate(
        total_students=Count('section__enrollment', filter=Q(section__enrollment__academic_year=academic_year), distinct=True),
        submitted_count=Count('submissions', distinct=True)
    ).values('id', 'title', 'total_students', 'submitted_count', 'due_date').order_by('-due_date')
    
    # Calculate avg grade separately because of aggregation complexity with distincts
    for a in assignments:
        subs = AssignmentSubmission.objects.filter(
            assignment_id=a['id'],
            status='GRADED',
            grade__isnull=False
        ).annotate(
            percentage=ExpressionWrapper(
                F('grade') * 100.0 / F('assignment__max_score'),
                output_field=FloatField()
            )
        ).aggregate(avg_score=Avg('percentage'))
        
        a['avg_score'] = round(subs['avg_score'], 2) if subs['avg_score'] is not None else None
        
        if a['total_students'] > 0:
            a['completion_rate'] = round((a['submitted_count'] / a['total_students']) * 100, 2)
        else:
            a['completion_rate'] = 0.0
            
    return list(assignments)

def get_weak_topics(teacher, academic_year, min_data_threshold=3, weak_threshold_percentage=60.0):
    """
    Identify weak chapters based on assignment and quiz scores, with a configurable minimum data threshold.
    """
    class_subject_ids = teacher.assignments.filter(
        academic_year=academic_year
    ).values_list('class_subject_id', flat=True).distinct()
    
    if not class_subject_ids:
        return []
        
    # Aggregate Chapter scores
    chapters = Chapter.objects.filter(class_subject_id__in=class_subject_ids)
    
    weak_topics = []
    
    for chapter in chapters:
        # Assignments for chapter
        assign_subs = AssignmentSubmission.objects.filter(
            assignment__chapter=chapter,
            assignment__academic_year=academic_year,
            status='GRADED',
            grade__isnull=False
        ).annotate(
            percentage=ExpressionWrapper(
                F('grade') * 100.0 / F('assignment__max_score'),
                output_field=FloatField()
            )
        )
        
        assign_stats = assign_subs.aggregate(
            avg_score=Avg('percentage'),
            count=Count('id')
        )
        
        # Quizzes for chapter
        quiz_results = QuizResult.objects.filter(
            attempt__quiz__chapter=chapter,
            attempt__quiz__academic_year=academic_year,
            attempt__status='COMPLETED'
        )
        
        quiz_stats = quiz_results.aggregate(
            avg_score=Avg('percentage'),
            count=Count('id')
        )
        
        total_count = (assign_stats['count'] or 0) + (quiz_stats['count'] or 0)
        
        if total_count >= min_data_threshold:
            # Weighted average based on counts
            total_sum = 0
            if assign_stats['count']:
                total_sum += assign_stats['avg_score'] * assign_stats['count']
            if quiz_stats['count']:
                total_sum += float(quiz_stats['avg_score']) * quiz_stats['count']
                
            overall_avg = total_sum / total_count
            
            if overall_avg < weak_threshold_percentage:
                weak_topics.append({
                    'chapter_name': chapter.title,
                    'subject_name': chapter.class_subject.subject.name,
                    'overall_avg': round(overall_avg, 2),
                    'data_points': total_count
                })
                
    weak_topics.sort(key=lambda x: x['overall_avg'])
    return weak_topics

from django.conf import settings

def get_student_weak_topics(student, academic_year):
    """
    Identify weak chapters for a specific student based on assignment and quiz scores, 
    with configurable minimum data thresholds.
    """
    threshold = getattr(settings, 'AI_RECOMMENDATION_WEAK_THRESHOLD', 60.0)
    min_data = getattr(settings, 'AI_RECOMMENDATION_MIN_DATA_POINTS', 3)
    
    enrollment = Enrollment.objects.filter(student=student, academic_year=academic_year).first()
    if not enrollment:
        return []
        
    class_level = enrollment.class_level
    chapters = Chapter.objects.filter(class_subject__class_level=class_level)
    
    weak_topics = []
    
    for chapter in chapters:
        # Assignments
        assign_subs = AssignmentSubmission.objects.filter(
            student=student,
            assignment__chapter=chapter,
            assignment__academic_year=academic_year,
            status='GRADED',
            grade__isnull=False
        ).annotate(
            percentage=ExpressionWrapper(
                F('grade') * 100.0 / F('assignment__max_score'),
                output_field=FloatField()
            )
        )
        
        assign_stats = assign_subs.aggregate(
            avg_score=Avg('percentage'),
            count=Count('id')
        )
        
        # Quizzes
        quiz_results = QuizResult.objects.filter(
            attempt__student=student,
            attempt__quiz__chapter=chapter,
            attempt__quiz__academic_year=academic_year,
            attempt__status='COMPLETED'
        )
        
        quiz_stats = quiz_results.aggregate(
            avg_score=Avg('percentage'),
            count=Count('id')
        )
        
        total_count = (assign_stats['count'] or 0) + (quiz_stats['count'] or 0)
        
        if total_count >= min_data:
            total_sum = 0
            if assign_stats['count']:
                total_sum += assign_stats['avg_score'] * assign_stats['count']
            if quiz_stats['count']:
                total_sum += float(quiz_stats['avg_score']) * quiz_stats['count']
                
            overall_avg = total_sum / total_count
            
            if overall_avg < threshold:
                weak_topics.append({
                    'chapter_id': chapter.id,
                    'chapter_name': chapter.title,
                    'subject_id': chapter.class_subject.subject.id,
                    'subject_name': chapter.class_subject.subject.name,
                    'overall_avg': round(overall_avg, 2),
                    'data_points': total_count,
                    'threshold_used': threshold
                })
                
    weak_topics.sort(key=lambda x: x['overall_avg'])
    return weak_topics
