from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Questionnaire, Answer, Comment
from .forms import AnswerForm
from django.contrib import messages
from invites.models import Invitation
from .mixins import TokenAuthenticationMixin
import logging

logger = logging.getLogger(__name__)

class QuestionnaireView(TokenAuthenticationMixin, View):
    login_url = '/login/'  # redirect to login if not authenticated

    def get(self, request, pk, token):
        # Retrieve the questionnaire
        questionnaire = get_object_or_404(Questionnaire, pk=pk)

        if not self.validate_token(token):
            messages.error(request, "Invalid or expired invitation token.")
            logger.error(f"Token validation failed.")
            return redirect('completion_page')

        form = AnswerForm(questionnaire=questionnaire)
        question_numbers = list(enumerate(questionnaire.questions.all(), start=1))

        rating_questions = questionnaire.questions.filter(question_type='rating')
        legend_text = self.get_legend_text(rating_questions)

        return render(request, 'survey/questionnaire.html', {
            'form': form,
            'questionnaire': questionnaire,
            'question_numbers': question_numbers,
            'legend_text': legend_text,
            'token': token,
        })

    def post(self, request, pk, token):
        logger.info("Received POST request for questionnaire and token")
        questionnaire = get_object_or_404(Questionnaire, pk=pk)
        form = AnswerForm(request.POST, questionnaire=questionnaire)

        if form.is_valid():
            if self.all_agree(form, questionnaire):
                self.save_answers(form, questionnaire, token)
                next_questionnaire = self.get_next_questionnaire(questionnaire)

                if next_questionnaire:
                    logger.info(f"Redirecting to next questionnaire: {next_questionnaire.pk}")
                    return redirect('questionnaire', pk=next_questionnaire.pk, token=token)
                else:
                    logger.info("No more questionnaires. Redirecting to completion page.")
                    return redirect('completion_page')

            else:
                messages.error(request, "You must agree to all statements to proceed.")

        context = {
            'form': form,
            'questionnaire': questionnaire,
            'question_numbers': enumerate(questionnaire.questions.all(), start=1),
            'token': token,
        }
        return render(request, 'survey/questionnaire.html', context=context)

    def all_agree(self, form, questionnaire):
        if questionnaire.title == "Consent":
            for question in questionnaire.questions.all():
                answer_text = form.cleaned_data.get(f'question_{question.id}')
                if answer_text != "agree":
                    return False
        return True

    def save_answers(self, form, questionnaire, token):
        for question in questionnaire.questions.all():
            answer_text = form.cleaned_data.get(f'question_{question.id}')
            Answer.objects.create(
                question=question,
                answer_text=answer_text,
                token=token,
            )

        comment_text = form.cleaned_data.get('comments')
        if comment_text:
            Comment.objects.create(
                text=comment_text,
                questionnaire=questionnaire,
                token=token,
            )

    def get_legend_text(self, rating_questions):
        if rating_questions.exists():
            return "Our Organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3=Substantial Progress; 4=Established)"
        return ""

    def get_next_questionnaire(self, current_questionnaire):
        next_questionnaire = (
            Questionnaire.objects
            .exclude(title="Consent")
            .filter(pk__gt=current_questionnaire.pk)
            .order_by('pk')
            .first()
        )
        return next_questionnaire


    def validate_token(self, token):

        is_valid = Invitation.objects.filter(token=token).exists()

        if is_valid:
            logger.info(f"Token is valid.")
        else:
            logger.warning(f"Token is invalid or expired.")
        return is_valid

class CompletionView(View):
    def get(self, request):
        messages.info(request, "You have completed the survey.")
        return render(request, 'survey/completion.html')
