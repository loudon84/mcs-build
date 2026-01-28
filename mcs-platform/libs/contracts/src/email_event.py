"""Email event models."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailAttachment(BaseModel):
    """Email attachment model."""

    attachment_id: str = Field(..., description="Attachment identifier")
    filename: str = Field(..., description="Attachment filename")
    content_type: str = Field(..., description="MIME content type")
    size: int = Field(..., description="File size in bytes", ge=0)
    sha256: Optional[str] = Field(None, description="SHA256 hash of file content")
    bytes_b64: Optional[str] = Field(None, description="Base64 encoded file content")
    url: Optional[str] = Field(None, description="URL to download attachment")

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, v: Optional[str]) -> Optional[str]:
        """Validate SHA256 format (64 hex characters)."""
        if v is not None and len(v) != 64:
            raise ValueError("SHA256 must be 64 hexadecimal characters")
        return v


class EmailEvent(BaseModel):
    """Email event model."""

    provider: str = Field(..., description="Email provider (imap/exchange/pop3)")
    account: str = Field(..., description="Email account")
    folder: str = Field(..., description="Email folder")
    uid: str = Field(..., description="Email UID")
    message_id: str = Field(..., description="Email message ID")
    from_email: EmailStr = Field(..., description="Sender email address")
    to: list[EmailStr] = Field(default_factory=list, description="Recipient email addresses")
    cc: list[EmailStr] = Field(default_factory=list, description="CC email addresses")
    subject: str = Field(..., description="Email subject")
    body_text: str = Field(..., description="Plain text body")
    body_html: Optional[str] = Field(None, description="HTML body")
    received_at: str = Field(..., description="Received timestamp (ISO format)")
    attachments: list[EmailAttachment] = Field(default_factory=list, description="Email attachments")

    @field_validator("from_email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email: lowercase and strip."""
        return v.lower().strip()

    @field_validator("attachments")
    @classmethod
    def validate_attachments(cls, v: list[EmailAttachment]) -> list[EmailAttachment]:
        """Validate attachment size limits."""
        max_size = 50 * 1024 * 1024  # 50MB
        for attachment in v:
            if attachment.size > max_size:
                raise ValueError(f"Attachment {attachment.filename} exceeds maximum size of {max_size} bytes")
        return v

