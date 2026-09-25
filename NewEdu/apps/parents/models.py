from django.db import models
from apps.accounts.models import User
from apps.students.models import StudentProfile

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(StudentProfile, related_name='parents', blank=True)
    
    def __str__(self):
        return f"Parent Profile: {self.user.email}"
