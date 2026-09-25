from django.db import models
from django.conf import settings

class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    hire_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Teacher"
