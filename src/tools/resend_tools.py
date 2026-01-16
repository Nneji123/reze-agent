"""PydanticAI tools for Resend.com API operations.

These tools are automatically available to the Reze AI agent and can be called
when the user wants to send emails, check delivery status, or retrieve attachments.
"""

from pydantic import BaseModel, EmailStr, Field
from pydantic_ai import RunContext


class SendEmailInput(BaseModel):
    """Input for sending an email."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    content: str = Field(..., description="Email content (HTML or plain text)")
    from_email: EmailStr = Field(None, description="Optional sender email address")


class EmailStatusInput(BaseModel):
    """Input for checking email status."""

    email_id: str = Field(..., description="The unique email ID from Resend")


async def send_email(ctx: RunContext, data: SendEmailInput) -> str:
    """Send an email via Resend.com API.

    This tool is called when the user wants to send an email.
    You must have gathered the recipient email address, subject line, and
    email content before calling this tool.

    Args:
        to: Recipient's email address
        subject: Email subject line
        content: Email body content (HTML or plain text)
        from_email: Optional sender email (uses default if not provided)

    Returns:
        Confirmation message with email ID
    """
    from src.services.resend import resend_service

    try:
        result = await resend_service.send_email(
            to=data.to,
            subject=data.subject,
            html_content=data.content,
            from_email=data.from_email,
        )

        return f"✓ Email sent successfully! Email ID: {result.get('id', 'unknown')}. It should be delivered shortly. Would you like me to check its delivery status?"
    except Exception as e:
        return f"✗ Failed to send email: {str(e)}. Please check the email address and try again."


async def get_email_status(ctx: RunContext, data: EmailStatusInput) -> str:
    """Get the delivery status of a sent email.

    This tool is called when the user asks about a specific email's
    delivery status or tracking information.

    Args:
        email_id: The unique email ID returned when the email was sent

    Returns:
        Current delivery status and relevant information
    """
    from src.services.resend import resend_service

    try:
        status_info = await resend_service.get_email_status(data.email_id)

        status = status_info.get("status", "unknown")
        created_at = status_info.get("created_at", "unknown")
        last_event = status_info.get("last_event", "none")

        response = f"Email {data.email_id} status: {status.upper()}\n"
        response += f"- Created: {created_at}\n"

        if last_event:
            response += f"- Last event: {last_event}\n"

        # Provide context based on status
        if status == "queued":
            response += "The email is queued and will be sent shortly."
        elif status == "sent":
            response += "The email has been sent to the recipient's mail server."
        elif status == "delivered":
            response += "✓ The email has been successfully delivered to the recipient."
        elif status == "bounced":
            response += "✗ The email bounced. The recipient's mail server rejected it. Check the email address."
        elif status == "complained":
            response += "⚠ The recipient marked the email as spam."
        else:
            response += f"The email status is: {status}"

        return response
    except Exception as e:
        return (
            f"✗ Failed to retrieve email status: {str(e)}. Please verify the email ID."
        )


async def get_email_attachments(ctx: RunContext, data: EmailStatusInput) -> str:
    """Get attachments from a sent email.

    This tool is called when the user wants to retrieve or list attachments
    from a specific email that was sent.

    Args:
        email_id: The unique email ID of the sent email

    Returns:
        List of attachments with details
    """
    from src.services.resend import resend_service

    try:
        attachments = await resend_service.get_email_attachments(data.email_id)

        if not attachments or len(attachments) == 0:
            return f"Email {data.email_id} has no attachments."

        response = f"Found {len(attachments)} attachment(s):\n\n"

        for i, attachment in enumerate(attachments, 1):
            filename = attachment.get("filename", "unknown")
            size = attachment.get("size", 0)
            url = attachment.get("url", "not available")

            size_mb = round(size / (1024 * 1024), 2) if size > 0 else 0

            response += f"{i}. {filename}\n"
            response += f"   Size: {size_mb} MB\n"
            response += f"   Download: {url}\n\n"

        response += (
            "⚠️  Warning: Always scan attachments before opening them for security."
        )

        return response
    except Exception as e:
        return (
            f"✗ Failed to retrieve attachments: {str(e)}. Please verify the email ID."
        )


# Export all tools for PydanticAI agent
ALL_TOOLS = [send_email, get_email_status, get_email_attachments]
