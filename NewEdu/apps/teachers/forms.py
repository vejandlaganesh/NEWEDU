from django import forms
from apps.assignments.models import Assignment, AssignmentSubmission
import os

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['class_subject', 'section', 'chapter', 'title', 'description', 'due_date', 'max_score', 'attachment']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.teacher_profile = kwargs.pop('teacher_profile', None)
        super().__init__(*args, **kwargs)
        if self.teacher_profile:
            # We must filter class_subject and section based on TeacherAssignments
            from apps.academics.models import TeacherAssignment, AcademicYear
            try:
                active_year = AcademicYear.objects.get(is_active=True)
                assignments = TeacherAssignment.objects.filter(teacher=self.teacher_profile, academic_year=active_year)
                cs_ids = assignments.values_list('class_subject_id', flat=True).distinct()
                section_ids = assignments.values_list('section_id', flat=True).distinct()
                
                self.fields['class_subject'].queryset = self.fields['class_subject'].queryset.filter(id__in=cs_ids)
                self.fields['section'].queryset = self.fields['section'].queryset.filter(id__in=section_ids)
            except AcademicYear.DoesNotExist:
                self.fields['class_subject'].queryset = self.fields['class_subject'].queryset.none()
                self.fields['section'].queryset = self.fields['section'].queryset.none()
                
    def clean(self):
        cleaned_data = super().clean()
        class_subject = cleaned_data.get('class_subject')
        section = cleaned_data.get('section')
        attachment = cleaned_data.get('attachment')
        
        if class_subject and section:
            if class_subject.class_level != section.class_level:
                raise forms.ValidationError("The selected Section must belong to the same Class as the ClassSubject.")
                
        if attachment:
            ext = os.path.splitext(attachment.name)[1].lower()
            valid_extensions = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg', '.txt']
            if ext not in valid_extensions:
                raise forms.ValidationError(f"Unsupported file extension {ext}. Allowed: {', '.join(valid_extensions)}")
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 5MB.")
                
        return cleaned_data

class AssignmentGradingForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback']
