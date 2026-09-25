from django.db import models
from apps.accounts.models import User

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=255, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} for {self.user.email}"

class AIMessage(models.Model):
    ROLE_CHOICES = (
        ('USER', 'User'),
        ('MODEL', 'Model'),
        ('SYSTEM', 'System'),
    )
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()} in {self.conversation.id}"

class AIInteraction(models.Model):
    """Tracks one-off AI operations like quiz generation, learning recommendations, etc."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_interactions')
    operation = models.CharField(max_length=100)  # e.g., 'generate_quiz', 'generate_explanation'
    model_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50)      # e.g., 'SUCCESS', 'FAILED', 'TIMEOUT'
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True) # Safe non-sensitive metadata (e.g. topic, params)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operation} by {self.user.email} - {self.status}"

from apps.students.models import StudentProfile
from apps.academics.models import AcademicYear, Subject, Chapter

class AIRecommendation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='ai_recommendations')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='ai_recommendations')
    related_subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_recommendations')
    related_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_recommendations')
    
    # Structured JSON data representing the recommendation (strengths, weaknesses, advice)
    recommendation = models.JSONField(null=True, blank=True)
    
    # Snapshot of the performance facts supplied to Gemini (for auditing and verification)
    source_data = models.JSONField(null=True, blank=True)
    
    # Summary or reason for this recommendation
    reason = models.TextField(blank=True)
    
    status = models.CharField(max_length=50, default='GENERATED') # GENERATED, DISCARDED, COMPLETED
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Recommendation for {self.student.user.email} at {self.created_at}"
