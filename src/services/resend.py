"""Resend.com API client service.

This module provides an async interface to Resend.com's email API,
handling email sending, status checking, and attachment retrieval.
"""

from typing import Dict, List, Optional

import httpx
from loguru import logger

from src.config import settings


class ResendService:
    """Async Resend.com API client."""

    def __init__(self):
        """Initialize Resend service with configuration."""
        self.api_key = settings.resend_api_key
        self.base_url = settings.resend_base_url
        self.default_from = settings.resend_from_email

        # Create async HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        logger.info(f"Resend service initialized: {self.base_url}")

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> Dict:
        """Send an email via Resend.com API.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: Email body content (HTML format)
            from_email: Optional sender email (uses default if not provided)
            attachments: Optional list of attachment dictionaries

        Returns:
            Response dictionary with email_id and status

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            # Prepare request payload
            payload = {
                "from": from_email or self.default_from,
                "to": to,
                "subject": subject,
                "html": html_content,
            }

            # Add attachments if provided
            if attachments:
                payload["attachments"] = attachments

            logger.info(f"Sending email to {to} with subject: {subject}")

            # Make API request
            response = await self.client.post(
                f"{self.base_url}/emails",
                json=payload,
            )

            response.raise_for_status()

            result = response.json()
            logger.success(f"Email sent successfully: {result.get('id')}")

            return {
                "id": result.get("id"),
                "status": result.get("status", "queued"),
                "created_at": result.get("created_at"),
                "from": payload["from"],
                "to": to,
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response else str(e)
            logger.error(f"HTTP error sending email: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def get_email_status(self, email_id: str) -> Dict:
        """Get delivery status of a sent email.

        Args:
            email_id: The unique email ID from Resend

        Returns:
            Dictionary with status information

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            logger.info(f"Fetching status for email: {email_id}")

            response = await self.client.get(f"{self.base_url}/emails/{email_id}")

            response.raise_for_status()

            result = response.json()
            logger.info(f"Email status retrieved: {result.get('status')}")

            return {
                "id": result.get("id"),
                "status": result.get("status"),
                "created_at": result.get("created_at"),
                "updated_at": result.get("updated_at"),
                "last_event": result.get("last_event"),
                "from": result.get("from"),
                "to": result.get("to"),
                "subject": result.get("subject"),
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Email not found: {email_id}")
                return {"id": email_id, "status": "not_found"}
            error_detail = e.response.json() if e.response else str(e)
            logger.error(f"HTTP error fetching status: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to get email status: {e}")
            raise

    async def get_email_attachments(self, email_id: str) -> List[Dict]:
        """Retrieve attachments from a sent email.

        Args:
            email_id: The unique email ID

        Returns:
            List of attachment dictionaries

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            logger.info(f"Fetching attachments for email: {email_id}")

            # Get email details
            response = await self.client.get(f"{self.base_url}/emails/{email_id}")

            response.raise_for_status()

            email_data = response.json()

            # Extract attachments from email data
            attachments = email_data.get("attachments", [])

            logger.info(f"Found {len(attachments)} attachments")

            return [
                {
                    "filename": att.get("filename", "unknown"),
                    "size": att.get("size", 0),
                    "url": att.get("url"),
                    "content_type": att.get("content_type", "application/octet-stream"),
                }
                for att in attachments
            ]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Email not found: {email_id}")
                return []
            error_detail = e.response.json() if e.response else str(e)
            logger.error(f"HTTP error fetching attachments: {error_detail}")
            raise
        except Exception as e:
            logger.error(f"Failed to get attachments: {e}")
            raise

    async def list_emails(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict:
        """List sent emails.

        Args:
            limit: Number of emails to return (max 100)
            offset: Number of emails to skip
            status: Optional filter by status

        Returns:
            Dictionary with data and pagination info

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            logger.info(f"Listing emails (limit={limit}, offset={offset})")

            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status

            response = await self.client.get(
                f"{self.base_url}/emails",
                params=params,
            )

            response.raise_for_status()

            result = response.json()
            logger.info(f"Retrieved {len(result.get('data', []))} emails")

            return {
                "data": result.get("data", []),
                "total": result.get("total", 0),
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to list emails: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Resend service HTTP client closed")


# Global singleton instance
resend_service = ResendService()
