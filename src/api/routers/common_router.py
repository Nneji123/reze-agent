"""Common router with general endpoints."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str | str]:
    """Health check endpoint.

    Returns:
        Dictionary with service status information
    """
    return {
        "status": "healthy",
        "service": "reze-ai-agent",
        "version": "0.1.0",
    }


@router.get("/", response_model=None)
async def serve_chat_interface() -> FileResponse | dict[str, str]:
    """Serve chat interface HTML page.

    Returns:
        FileResponse if index.html exists, otherwise error message
    """
    index_file = Path(__file__).parent.parent.parent.parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Chat interface not found. Please ensure static/index.html exists."
    }


@router.get("/favicon.ico", response_model=None)
async def serve_favicon() -> FileResponse | dict[str, str]:
    """Serve favicon.ico file.

    Returns:
        FileResponse if favicon.ico exists, otherwise error message
    """
    favicon_file = Path(__file__).parent.parent.parent.parent / "static" / "favicon.ico"
    if favicon_file.exists():
        return FileResponse(favicon_file)
    return {"message": "Favicon not found. Please ensure static/favicon.ico exists."}
