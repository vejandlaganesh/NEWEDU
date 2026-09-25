from django.db import transaction
from django.urls import reverse
from apps.notifications.models import Notification
from apps.academics.models import Enrollment

class NotificationService:
    @staticmethod
    def _create_notification(recipient, title, message, notification_type, link_url):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url
        )

    @classmethod
    def notify_assignment_created(cls, assignment):
        # Notify eligible students based on Section, ClassSubject, AcademicYear, Enrollment
        enrollments = Enrollment.objects.filter(
            academic_year=assignment.academic_year,
            section=assignment.section,
        ).select_related('student__user')

        notifications = []
        for enrollment in enrollments:
            # Need to create URL. The student assignment detail URL is 'student_assignment_detail'
            link = reverse('student_assignment_detail', kwargs={'pk': assignment.pk})
            notif = Notification(
                recipient=enrollment.student.user,
                title=f"New Assignment: {assignment.title}",
                message=f"A new assignment has been posted in {assignment.class_subject.subject.name}.",
                notification_type='ASSIGNMENT',
                link_url=link
            )
            notifications.append(notif)
        
        Notification.objects.bulk_create(notifications)

    @classmethod
    def notify_quiz_published(cls, quiz):
        # Notify eligible students
        enrollments = Enrollment.objects.filter(
            academic_year=quiz.academic_year,
        ).select_related('student__user')

        if quiz.section:
            enrollments = enrollments.filter(section=quiz.section)
        else:
            # If quiz has no section, it applies to all sections for that ClassSubject taught by the teacher? 
            # In Phase 9, Quiz applies to class_subject. Let's just find students taking this class_subject.
            # But Enrollment is linked to class_level & section. 
            # So students enrolled in quiz's class_subject's class_level.
            enrollments = enrollments.filter(class_level=quiz.class_subject.class_level)

        notifications = []
        for enrollment in enrollments:
            link = reverse('student_quiz_detail', kwargs={'pk': quiz.pk})
            notif = Notification(
                recipient=enrollment.student.user,
                title=f"New Quiz: {quiz.title}",
                message=f"A new quiz has been published in {quiz.class_subject.subject.name}.",
                notification_type='QUIZ',
                link_url=link
            )
            notifications.append(notif)
        
        Notification.objects.bulk_create(notifications)

    @classmethod
    def notify_assignment_graded(cls, submission):
        student_user = submission.student.user
        link = reverse('student_assignment_detail', kwargs={'pk': submission.assignment.pk})
        cls._create_notification(
            recipient=student_user,
            title=f"Assignment Graded: {submission.assignment.title}",
            message=f"Your assignment has been graded. Score: {submission.grade}/{submission.assignment.max_score}",
            notification_type='RESULT',
            link_url=link
        )

    @classmethod
    def notify_lesson_created(cls, lesson):
        # Lesson belongs to chapter -> class_subject -> class_level
        # Get active academic year students in this class level
        from apps.academics.models import AcademicYear
        try:
            active_year = AcademicYear.objects.get(is_active=True)
            enrollments = Enrollment.objects.filter(
                academic_year=active_year,
                class_level=lesson.chapter.class_subject.class_level
            ).select_related('student__user')
            
            notifications = []
            for enrollment in enrollments:
                link = reverse('student_lesson_detail', kwargs={'pk': lesson.pk})
                notif = Notification(
                    recipient=enrollment.student.user,
                    title=f"New Lesson: {lesson.title}",
                    message=f"A new lesson has been added to {lesson.chapter.class_subject.subject.name}.",
                    notification_type='MATERIAL',
                    link_url=link
                )
                notifications.append(notif)
            
            Notification.objects.bulk_create(notifications)
        except AcademicYear.DoesNotExist:
            pass

    @classmethod
    def notify_ai_recommendation_ready(cls, recommendation):
        student_user = recommendation.student.user
        link = reverse('student_ai_assistant')
        cls._create_notification(
            recipient=student_user,
            title="New AI Learning Plan Available",
            message="Your personalized learning plan based on recent performance is ready.",
            notification_type='AI_RECOMMENDATION',
            link_url=link
        )
