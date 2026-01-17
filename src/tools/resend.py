"""PydanticAI tools for Resend.com API operations."""

from pydantic_ai import RunContext

from src.models.resend import GetEmailStatusRequest, SendEmailRequest
from src.services.resend import resend_service


async def send_email(ctx: RunContext, data: SendEmailRequest) -> str:
    """Send an email via Resend.com API.

    CALL THIS TOOL ONLY WHEN:
    - User wants to send an email
    - You have collected ALL required parameters (to, subject, content)
    - User has confirmed the details are correct

    REQUIRED PARAMETERS (all must be present):
    - to: Valid email address of recipient
    - subject: Email subject line
    - html: Email body text or HTML

    OPTIONAL PARAMETERS:
    - from: Sender email (skip if not provided)

    DO NOT CALL THIS TOOL if any required parameter is missing.
    Ask the user for missing information first.
    """
    try:
        result = await resend_service.send_email(data)

        return f"✓ Email sent successfully! Email ID: {result.id}. It should be delivered shortly. Would you like me to check its delivery status?"
    except Exception as e:
        return f"✗ Failed to send email: {str(e)}. Please check the email address and try again."


async def get_email_status(ctx: RunContext, data: GetEmailStatusRequest) -> str:
    """Get the delivery status of a sent email.

    ALWAYS CALL THIS TOOL when user asks about email status, even if they provide the email_id directly.

    The email_id can come from:
    - User provides it directly (most common)
    - From a previous send_email operation in this conversation
    - From conversation context/memory

    REQUIRED PARAMETERS:
    - email_id: The unique email ID from Resend
    """
    try:
        result = await resend_service.get_email_status(data.email_id)

        response = f"Email {data.email_id} status: {result.status.upper()}\n"
        response += f"- Created: {result.created_at}\n"

        if result.last_event:
            response += f"- Last event: {result.last_event}\n"

        if result.status == "queued":
            response += "The email is queued and will be sent shortly."
        elif result.status == "sent":
            response += "The email has been sent to the recipient's mail server."
        elif result.status == "delivered":
            response += "✓ The email has been successfully delivered to the recipient."
        elif result.status == "bounced":
            response += "✗ The email bounced. The recipient's mail server rejected it. Check the email address."
        elif result.status == "complained":
            response += "⚠ The recipient marked the email as spam."
        else:
            response += f"The email status is: {result.status}"

        return response
    except Exception as e:
        return (
            f"✗ Failed to retrieve email status: {str(e)}. Please verify the email ID."
        )


async def get_email_attachments(ctx: RunContext, data: GetEmailStatusRequest) -> str:
    """Get attachments from a sent email.

    ALWAYS CALL THIS TOOL when user asks about email attachments, even if they provide the email_id directly.

    The email_id can come from:
    - User provides it directly (most common)
    - From a previous send_email operation in this conversation
    - From conversation context/memory

    REQUIRED PARAMETERS:
    - email_id: The unique email ID from Resend
    """
    try:
        attachments = await resend_service.get_email_attachments(data.email_id)

        if not attachments or len(attachments) == 0:
            return f"Email {data.email_id} has no attachments."

        response = f"Found {len(attachments)} attachment(s):\n\n"

        for i, attachment in enumerate(attachments, 1):
            size_mb = (
                round(attachment.size / (1024 * 1024), 2) if attachment.size > 0 else 0
            )

            response += f"{i}. {attachment.filename}\n"
            response += f"   Size: {size_mb} MB\n"
            response += f"   Download: {attachment.url}\n\n"

        response += (
            "⚠️  Warning: Always scan attachments before opening them for security."
        )

        return response
    except Exception as e:
        return (
            f"✗ Failed to retrieve attachments: {str(e)}. Please verify the email ID."
        )


ALL_TOOLS = [send_email, get_email_status, get_email_attachments]
