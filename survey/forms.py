from django import forms
from .models import Answer, Question
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = [] # no defaults needed

    def __init__(self, *args, **kwargs):
        questionnaire = kwargs.pop('questionnaire', None)  # get the questionnaire passed in
        super().__init__(*args, **kwargs)

        if questionnaire:

            for index, question in enumerate(questionnaire.questions.all(), start=1):
                if question.question_type == 'boolean':
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        label=f"{index}. {question.question_text}",
                        choices=[('agree', 'I agree'), ('disagree', 'I disagree')],
                        widget=forms.RadioSelect,
                        required=True
                    )

                elif question.question_type == 'rating':

                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        label=question.question_text,
                        choices=[(i, str(i)) for i in range(1, 6)],  # assuming a 1-5 rating
                        required=True
                    )


                else:

                    pass

                    # self.fields[f'question_{question.id}'] = forms.CharField(
                    #     label=question.question_text,
                    #     required=True,
                    #     widget=forms.Textarea(attrs={'rows': 4, 'style': 'width: 80%;'}),
                    # )
