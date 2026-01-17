"""Pydantic models for Resend.com API operations."""

from pydantic import BaseModel, EmailStr, Field


class SendEmailRequest(BaseModel):
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    html_content: str = Field(
        ..., alias="html", description="Email body content (HTML)"
    )
    from_email: EmailStr | None = Field(
        None, alias="from", description="Sender email address"
    )
    attachments: list[dict[str, object]] | None = Field(
        None, description="List of attachment dictionaries"
    )

    class Config:
        populate_by_name: bool = True


class GetEmailStatusRequest(BaseModel):
    email_id: str = Field(..., description="The unique email ID from Resend")


class Attachment(BaseModel):
    filename: str = Field(default="unknown", description="Attachment filename")
    size: int = Field(default=0, description="Attachment size in bytes")
    url: str | None = Field(None, description="Attachment download URL")
    content_type: str = Field(
        default="application/octet-stream", description="Attachment MIME type"
    )


class EmailResponse(BaseModel):
    id: str = Field(..., description="Email ID")
    status: str = Field(default="unknown", description="Email status")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    last_event: str | None = Field(None, description="Last delivery event")
    from_email: str | None = Field(None, alias="from", description="Sender email")
    to: list[str] | None = Field(None, description="Recipient emails")
    subject: str | None = Field(None, description="Email subject")

    class Config:
        populate_by_name: bool = True


class EmailListResponse(BaseModel):
    data: list[EmailResponse] = Field(
        default_factory=list, description="List of emails"
    )
    total: int = Field(default=0, description="Total number of emails")
    limit: int = Field(default=100, description="Page limit")
    offset: int = Field(default=0, description="Page offset")
