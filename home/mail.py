"""
Shared helpers for sending email.

SORT can send email through either Django's SMTP backend or the Gmail API
backend (``gmailapi_backend.mail.GmailBackend``), chosen by the
DJANGO_EMAIL_BACKEND environment variable. See docs/deployment.md.
"""

import smtplib

import google.auth.exceptions
import googleapiclient.errors
import httplib2

# Exceptions that mean "the email could not be sent", whichever backend is in
# use. Catch these rather than a bare Exception so that programming errors
# (e.g. a broken template) still surface.
EMAIL_SEND_ERRORS = (
    # SMTP backend
    smtplib.SMTPException,
    # Network failures (socket errors, timeouts) from either backend
    OSError,
    # Gmail API backend: the API rejected the request (e.g. HttpError 403)
    googleapiclient.errors.Error,
    # Gmail API backend: the OAuth2 token could not be refreshed
    # (e.g. RefreshError "invalid_grant" when the refresh token was revoked)
    google.auth.exceptions.GoogleAuthError,
    # Gmail API backend: HTTP transport failures
    httplib2.HttpLib2Error,
)
