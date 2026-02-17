"""File server client."""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
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

    async def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        base_dir: str,
        sub_dir: str,
    ) -> str:
        """Save file to local filesystem.
        
        Args:
            file_bytes: File content as bytes.
            filename: Name of the file.
            base_dir: Base directory path (e.g., 'public/files').
            sub_dir: Subdirectory name (e.g., message_id).
            
        Returns:
            Relative file path string (format: {sub_dir}/{filename}).
            
        Raises:
            OSError: If file system operations fail.
        """
        # Build full directory path
        base_path = Path(base_dir)
        target_dir = base_path / sub_dir
        
        # Create directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle filename conflicts by adding timestamp suffix
        file_path = target_dir / filename
        if file_path.exists():
            # Add timestamp suffix before file extension
            stem = file_path.stem
            suffix = file_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{stem}_{timestamp}{suffix}"
            file_path = target_dir / filename
        
        # Write file to disk (use asyncio to run in thread pool)
        await asyncio.to_thread(file_path.write_bytes, file_bytes)
        
        # Return relative path
        return f"{sub_dir}/{filename}"

    async def read_file(self, base_dir: str, file_path: str) -> bytes:
        """Read file from local filesystem.

        Args:
            base_dir: Base directory path (e.g., 'public/files').
            file_path: Relative file path (format: {message_id}/{filename}).

        Returns:
            File content as bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        full_path = Path(base_dir) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return await asyncio.to_thread(full_path.read_bytes)

