"""PydanticAI tools for Resend.com API operations.

These tools are automatically available to the Reze AI agent and can be called
when the user wants to send emails, check delivery status, or retrieve attachments.
"""

from pydantic import BaseModel, EmailStr, Field
from pydantic_ai import RunContext


class SendEmailInput(BaseModel):
    """Input for sending an email."""

    to: EmailStr = Field(
        ...,
        description="REQUIRED: The recipient's email address (e.g., john@example.com). Must be a valid email format.",
    )
    subject: str = Field(
        ...,
        description="REQUIRED: The subject line for the email. A clear, descriptive subject.",
    )
    content: str = Field(
        ...,
        description="REQUIRED: The email body content. Can be plain text or HTML format.",
    )
    from_email: EmailStr = Field(
        None,
        description="OPTIONAL: The sender's email address. If not provided, uses default sender.",
    )


class EmailStatusInput(BaseModel):
    """Input for checking email status."""

    email_id: str = Field(
        ...,
        description="REQUIRED: The unique email ID from Resend (e.g., 'abc123-xyz789'). This can be provided by the user or obtained from a previous send_email operation.",
    )


async def send_email(ctx: RunContext, data: SendEmailInput) -> str:
    """Send an email via Resend.com API.

    CALL THIS TOOL ONLY WHEN:
    - User wants to send an email
    - You have collected ALL required parameters (to, subject, content)
    - User has confirmed the details are correct

    REQUIRED PARAMETERS (all must be present):
    - to: Valid email address of recipient
    - subject: Email subject line
    - content: Email body text or HTML

    OPTIONAL PARAMETERS:
    - from_email: Sender email (skip if not provided)

    DO NOT CALL THIS TOOL if any required parameter is missing. Ask the user for missing information first.
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

    CALL THIS TOOL ONLY WHEN:
    - User asks about email delivery status
    - User asks if an email was sent/delivered/bounced
    - User provides a valid email_id

    REQUIRED PARAMETERS:
    - email_id: The unique email ID from a previous send_email operation

    DO NOT CALL THIS TOOL without a valid email_id. If user doesn't have it, ask them to provide it.
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

    CALL THIS TOOL ONLY WHEN:
    - User asks about attachments in an email
    - User wants to list or download attachments
    - User provides a valid email_id

    REQUIRED PARAMETERS:
    - email_id: The unique email ID from a previous send_email operation

    DO NOT CALL THIS TOOL without a valid email_id. If user doesn't have it, ask them to provide it.
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
