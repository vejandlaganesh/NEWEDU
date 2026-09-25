from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import QuizAttempt, QuizResult, QuizAnswer

@transaction.atomic
def evaluate_quiz_attempt(attempt):
    """
    Evaluates a QuizAttempt server-side and creates a QuizResult.
    Ensures that this happens atomically and only if the attempt is IN_PROGRESS.
    """
    # Lock the attempt row to prevent race conditions (double submission)
    attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk)
    
    if attempt.status != 'IN_PROGRESS':
        raise ValidationError("This attempt has already been completed.")
        
    # Mark as completed
    attempt.status = 'COMPLETED'
    end_time = timezone.now()
    attempt.end_time = end_time
    attempt.save(update_fields=['status', 'end_time'])
    
    # Calculate score
    answers = attempt.answers.select_related('question').all()
    
    correct_answers = 0
    incorrect_answers = 0
    attempted_questions = len(answers)
    score = 0
    
    for answer in answers:
        if answer.selected_option == answer.question.correct_option:
            correct_answers += 1
            score += answer.question.marks
        else:
            incorrect_answers += 1
            
    # Calculate metrics
    total_possible_score = sum(q.marks for q in attempt.quiz.questions.all())
    
    if total_possible_score > 0:
        percentage = (score / total_possible_score) * 100
    else:
        percentage = 0
        
    passed = percentage >= attempt.quiz.passing_score
    completion_time = end_time - attempt.start_time
    
    # Create the result
    result = QuizResult.objects.create(
        attempt=attempt,
        score=score,
        percentage=percentage,
        passed=passed,
        correct_answers=correct_answers,
        incorrect_answers=incorrect_answers,
        attempted_questions=attempted_questions,
        completion_time=completion_time
    )
    
    return result
