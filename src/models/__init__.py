"""Shared Pydantic models for Resend.com API operations.

These models are used by both the services and tools for validation.
"""

from .resend import Attachment, EmailResponse, GetEmailStatusRequest, SendEmailRequest

__all__ = [
    "SendEmailRequest",
    "GetEmailStatusRequest",
    "EmailResponse",
    "Attachment",
]
