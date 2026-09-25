from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.get_success_url())
        
    def get_success_url(self):
        role = self.request.user.role
        if role == 'STUDENT':
            return reverse('student_dashboard')
        elif role == 'TEACHER':
            return reverse('teacher_dashboard')
        elif role == 'PARENT':
            return reverse('parent_dashboard')
        elif role == 'ADMIN':
            return reverse('admin_dashboard')
        return reverse('home')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        role = self.request.user.role
        if role == 'STUDENT':
            return reverse('student_dashboard')
        elif role == 'TEACHER':
            return reverse('teacher_dashboard')
        elif role == 'PARENT':
            return reverse('parent_dashboard')
        elif role == 'ADMIN':
            return reverse('admin_dashboard')
        return reverse('home')
