from django import forms
from .models import LearningMaterial
from apps.academics.models import Chapter, Lesson

class LearningMaterialForm(forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = ['class_subject','chapter','lesson','title','description','material_type','file','external_url','text_content','is_published']
        widgets = {'description': forms.Textarea(attrs={'rows':4}), 'text_content': forms.Textarea(attrs={'rows':8})}

    def __init__(self, *args, teacher_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher_profile = teacher_profile
        if teacher_profile:
            from apps.academics.models import AcademicYear, TeacherAssignment
            year = AcademicYear.objects.filter(is_active=True).first()
            assignments = TeacherAssignment.objects.filter(teacher=teacher_profile, academic_year=year) if year else TeacherAssignment.objects.none()
            self.fields['class_subject'].queryset = self.fields['class_subject'].queryset.filter(id__in=assignments.values_list('class_subject_id', flat=True))
            self.fields['chapter'].queryset = Chapter.objects.filter(class_subject__in=self.fields['class_subject'].queryset)
            self.fields['lesson'].queryset = Lesson.objects.filter(chapter__class_subject__in=self.fields['class_subject'].queryset)

    def clean(self):
        cleaned = super().clean()
        cs, chapter, lesson = cleaned.get('class_subject'), cleaned.get('chapter'), cleaned.get('lesson')
        if chapter and cs and chapter.class_subject_id != cs.id: self.add_error('chapter','Chapter does not belong to the selected subject.')
        if lesson and cs and lesson.chapter.class_subject_id != cs.id: self.add_error('lesson','Lesson does not belong to the selected subject.')
        return cleaned
