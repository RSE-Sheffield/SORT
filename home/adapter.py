import logging
import smtplib

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        try:
            super().send_mail(template_prefix, email, context)
        except (smtplib.SMTPException, OSError):
            logger.exception(
                "Failed to send email (template=%s, to=%s)", template_prefix, email
            )
            raise
