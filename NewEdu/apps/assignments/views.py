from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import os
from .models import Assignment, AssignmentSubmission
from apps.academics.models import Enrollment, TeacherAssignment

class SecureFileDownloadView(LoginRequiredMixin, View):
    def get(self, request, file_path, *args, **kwargs):
        # file_path is something like 'assignments/2026-2027/MATH101/file.pdf'
        # To verify access, we should really look up the object that owns this file.
        # This is a basic implementation. For absolute security, we should query the DB.
        
        user = request.user
        has_access = False
        
        if user.role == 'ADMIN':
            has_access = True
            
        elif file_path.startswith('assignments/'):
            # It's an assignment attachment. We need to find the Assignment.
            assignment = Assignment.objects.filter(attachment=file_path).first()
            if assignment:
                if user.role == 'TEACHER':
                    if assignment.teacher == user.teacher_profile:
                        has_access = True
                elif user.role == 'STUDENT':
                    enrollment = Enrollment.objects.filter(student=user.student_profile, academic_year=assignment.academic_year, section=assignment.section).first()
                    if enrollment:
                        has_access = True
                elif user.role == 'PARENT':
                    for child in user.parent_profile.children.all():
                        enrollment = Enrollment.objects.filter(student=child, academic_year=assignment.academic_year, section=assignment.section).first()
                        if enrollment:
                            has_access = True
                            break
                            
        elif file_path.startswith('submissions/'):
            # It's a submission file. We need to find the Submission.
            submission = AssignmentSubmission.objects.filter(submitted_file=file_path).first()
            if submission:
                if user.role == 'TEACHER':
                    if submission.assignment.teacher == user.teacher_profile:
                        has_access = True
                elif user.role == 'STUDENT':
                    if submission.student == user.student_profile:
                        has_access = True
                elif user.role == 'PARENT':
                    if submission.student in user.parent_profile.children.all():
                        has_access = True

        if not has_access:
            return HttpResponseForbidden("You are not authorized to access this file.")

        from pathlib import Path
        media_root = Path(settings.MEDIA_ROOT).resolve()
        full_path = (media_root / file_path).resolve()
        
        # Verify the resolved path is inside MEDIA_ROOT to prevent directory traversal
        try:
            full_path.relative_to(media_root)
        except ValueError:
            raise Http404("Invalid file path")
            
        if full_path.exists() and full_path.is_file():
            # Use 'as_attachment=True' to avoid inline rendering of potentially malicious files
            return FileResponse(open(full_path, 'rb'), as_attachment=True)
        raise Http404("File does not exist")
