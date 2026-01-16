"""Tools registry for Reze AI Agent.

This module exports all PydanticAI tools that are automatically
available to the GLM 4.7 AI agent. The agent can call these tools
to perform actions like sending emails, checking status, and retrieving attachments.
"""

from .resend_tools import ALL_TOOLS, get_email_attachments, get_email_status, send_email

__all__ = [
    "ALL_TOOLS",
    "send_email",
    "get_email_status",
    "get_email_attachments",
]
