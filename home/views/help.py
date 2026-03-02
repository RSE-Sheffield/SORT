from django.utils import timezone
from django.views.generic import TemplateView


class HelpView(TemplateView):
    """
    User guide
    """
    template_name = "help/index.html"


class VideoTutorialView(TemplateView):
    """
    Beginner's intro video.
    """
    template_name = "help/video-tutorial.html"


class TroubleshootingView(TemplateView):
    template_name = "help/troubleshooting.html"


class FAQView(TemplateView):
    """
    Frequently asked questions (FAQs)
    """
    template_name = "help/faq.html"


class LicenseAgreementView(TemplateView):
    """
    End user license agreement
    """

    template_name = "about/end_user_license_agreement.html"


class PrivacyPolicyView(TemplateView):
    """
    Privacy policy and data protection notice
    """

    template_name = "about/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now().strftime("%d %B %Y")
        return context


class ParticipantInformationView(TemplateView):
    """
    Participant information sheet for research study
    """

    template_name = "about/participant_information.html"
