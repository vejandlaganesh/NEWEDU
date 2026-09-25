from django.db import models
from django.conf import settings

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    # Add any phase 1 appropriate fields here, e.g., enrollment_date, etc.
    enrollment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Student"
