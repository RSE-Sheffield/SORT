from django.core.validators import EmailValidator


class EmailListValidator(EmailValidator):
    """
    Validate a sequence of email addresses.
    """

    message = "Enter valid email addresses."

    @classmethod
    def clean(cls, value):
        """
        Separate strings by commas or whitespace.
        """
        # Replace commas with whitespace
        return [email.strip() for email in value.replace(",", " ").lower().split()]

    def __call__(self, value):
        for email in self.clean(value):
            super().__call__(email)
