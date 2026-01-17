"""Resend.com API client service."""

from typing import List

import httpx
from loguru import logger

from src.config import settings
from src.models.resend import (
    Attachment,
    EmailListResponse,
    EmailResponse,
    SendEmailRequest,
)


class ResendService:
    """Async Resend.com API client."""

    def __init__(self):
        self.api_key: str = settings.resend_api_key
        self.base_url: str = settings.resend_base_url
        self.default_from: str = settings.resend_from_email

        self.client: httpx.AsyncClient = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        logger.info(f"Resend service initialized: {self.base_url}")

    async def send_email(self, request: SendEmailRequest) -> EmailResponse:
        payload = {
            "from": request.from_email or self.default_from,
            "to": request.to,
            "subject": request.subject,
            "html": request.html_content,
        }

        if request.attachments:
            payload["attachments"] = request.attachments

        logger.info(f"Sending email to {request.to} with subject: {request.subject}")

        response = await self.client.post(f"{self.base_url}/emails", json=payload)
        response.raise_for_status()

        result = response.json()
        logger.success(f"Email sent successfully: {result.get('id', '')}")

        return EmailResponse(
            id=result.get("id"),
            status=result.get("status", "queued"),
            created_at=result.get("created_at"),
            from_email=payload["from"],
            to=(
                [result.get("to")]
                if isinstance(result.get("to"), str)
                else result.get("to", [])
            ),
            subject=request.subject,
        )

    async def get_email_status(self, email_id: str) -> EmailResponse:
        logger.info(f"Fetching status for email: {email_id}")

        response = await self.client.get(f"{self.base_url}/emails/{email_id}")
        response.raise_for_status()

        result = response.json()
        status = result.get("status") or result.get("last_event", "unknown")
        logger.info(f"Email status retrieved: {status}")

        return EmailResponse(
            id=result.get("id") or email_id,
            status=status,
            created_at=result.get("created_at") or None,
            updated_at=result.get("updated_at") or None,
            last_event=result.get("last_event") or None,
            from_email=result.get("from") or None,
            to=result.get("to") or [],
            subject=result.get("subject") or None,
        )

    async def get_email_attachments(self, email_id: str) -> List[Attachment]:
        logger.info(f"Fetching attachments for email: {email_id}")

        response = await self.client.get(f"{self.base_url}/emails/{email_id}")
        response.raise_for_status()

        email_data = response.json()
        attachments = email_data.get("attachments", [])

        logger.info(f"Found {len(attachments)} attachments")

        return [
            Attachment(
                filename=att.get("filename", "unknown") or "unknown",
                size=att.get("size", 0) or 0,
                url=att.get("url") or None,
                content_type=att.get("content_type", "application/octet-stream")
                or "application/octet-stream",
            )
            for att in attachments
        ]

    async def list_emails(
        self,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> EmailListResponse:
        logger.info(f"Listing emails (limit={limit}, offset={offset})")

        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = await self.client.get(f"{self.base_url}/emails", params=params)
        response.raise_for_status()

        result = response.json()
        data = result.get("data", [])

        logger.info(f"Retrieved {len(data)} emails")

        return EmailListResponse(
            data=[
                EmailResponse(
                    id=email.get("id") or "",
                    status=email.get("status") or "unknown",
                    created_at=email.get("created_at") or None,
                    last_event=email.get("last_event") or None,
                    from_email=email.get("from") or None,
                    to=email.get("to") or [],
                    subject=email.get("subject") or None,
                )
                for email in data
            ],
            total=result.get("total", 0),
            limit=limit,
            offset=offset,
        )

    async def close(self):
        await self.client.aclose()
        logger.info("Resend service HTTP client closed")


resend_service = ResendService()
