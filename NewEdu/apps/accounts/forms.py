from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User
from apps.students.models import StudentProfile
from apps.teachers.models import TeacherProfile
from apps.parents.models import ParentProfile

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(choices=[('STUDENT', 'Student'), ('TEACHER', 'Teacher'), ('PARENT', 'Parent')])

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.role = self.cleaned_data.get('role')
        if commit:
            user.save()
            if user.role == 'STUDENT':
                StudentProfile.objects.create(user=user)
            elif user.role == 'TEACHER':
                TeacherProfile.objects.create(user=user)
            elif user.role == 'PARENT':
                ParentProfile.objects.create(user=user)
        return user
