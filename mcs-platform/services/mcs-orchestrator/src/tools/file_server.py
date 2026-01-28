"""File server client."""

import hashlib
from typing import Optional

import httpx

from mcs_contracts import ErrorInfo, FileUploadResult
from errors import FILE_UPLOAD_FAILED, OrchestratorError
from settings import Settings


class FileServerClient:
    """Client for file server."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize file server client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[dict] = None,
        sha256: Optional[str] = None,
    ) -> FileUploadResult:
        """Upload file to file server."""
        # Calculate SHA256 if not provided
        if not sha256:
            sha256 = hashlib.sha256(file_bytes).hexdigest()

        try:
            with httpx.Client() as client:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                files = {"file": (filename, file_bytes, content_type)}
                data = {"metadata": metadata} if metadata else {}

                response = client.post(
                    f"{self.base_url}/v1/files/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                return FileUploadResult(
                    ok=True,
                    file_url=result.get("file_url"),
                    file_id=result.get("file_id"),
                    sha256=sha256,
                )
        except httpx.HTTPError as e:
            return FileUploadResult(
                ok=False,
                errors=[
                    ErrorInfo(
                        code=FILE_UPLOAD_FAILED,
                        reason=f"File upload failed: {str(e)}",
                        details={"filename": filename},
                    )
                ],
            )

