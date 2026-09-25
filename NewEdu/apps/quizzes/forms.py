from django import forms
from .models import Quiz, Question, QuizAnswer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['academic_year', 'class_subject', 'section', 'chapter', 'title', 'description', 'duration', 'passing_score', 'max_attempts']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks', 'explanation']

class QuizSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.quiz_attempt = kwargs.pop('quiz_attempt')
        super().__init__(*args, **kwargs)
        
        # Add a field for each question in the quiz
        for question in self.quiz_attempt.quiz.questions.all():
            self.fields[f'question_{question.id}'] = forms.ChoiceField(
                choices=Question.OPTION_CHOICES,
                widget=forms.RadioSelect,
                required=True,
                label=question.text
            )
            
    def save(self):
        answers = []
        for question in self.quiz_attempt.quiz.questions.all():
            selected_option = self.cleaned_data[f'question_{question.id}']
            answers.append(QuizAnswer(
                attempt=self.quiz_attempt,
                question=question,
                selected_option=selected_option
            ))
            
        # Bulk create the answers
        QuizAnswer.objects.bulk_create(answers)
