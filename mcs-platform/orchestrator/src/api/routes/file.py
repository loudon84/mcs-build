"""File download API routes."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from api.deps import get_file_server, get_listener_repo
from listener.repo import ListenerRepo
from tools.file_server import FileServerClient

router = APIRouter(prefix="/v1/file", tags=["file"])

# Base directory for attachment files (consistent with alimail listener save path)
_FILES_BASE_DIR = "public/files"


@router.get("/{message_id}")
async def get_file(
    message_id: str,
    file_id: Annotated[UUID, Query(description="Attachment file UUID")],
    repo: Annotated[ListenerRepo, Depends(get_listener_repo)],
    file_server: Annotated[FileServerClient, Depends(get_file_server)],
) -> Response:
    """Get attachment file by file_id.

    Args:
        message_id: Email message ID (path parameter, used for access validation).
        file_id: UUID of the attachment file record (query parameter).

    Returns:
        File stream response with appropriate content headers.
    """
    # Look up attachment record
    record = repo.get_attachment_file(file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment file not found: {file_id}",
        )

    # Validate message_id matches to prevent cross-message access
    if record.message_id != message_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment file not found for message: {message_id}",
        )

    # Read file from disk
    try:
        file_bytes = await file_server.read_file(_FILES_BASE_DIR, record.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file not found on disk",
        )

    # Extract filename from file_path for Content-Disposition header
    filename = Path(record.file_path).name

    return Response(
        content=file_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
