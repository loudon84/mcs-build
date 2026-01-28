"""Data redaction for sensitive information."""

import re
from typing import Any
from urllib.parse import urlparse


def mask_email(email: str) -> str:
    """Mask email: a***@domain.com format."""
    if "@" not in email:
        return "***REDACTED***"
    local, domain = email.split("@", 1)
    if len(local) > 1:
        masked_local = local[0] + "***"
    else:
        masked_local = "***"
    return f"{masked_local}@{domain}"


def mask_telephone(telephone: str) -> str:
    """Mask telephone: mask middle 4 digits."""
    if not telephone or len(telephone) < 4:
        return "***REDACTED***"
    # Keep first and last 2 digits, mask middle
    if len(telephone) <= 6:
        return telephone[0] + "****" + telephone[-1] if len(telephone) > 1 else "***REDACTED***"
    return telephone[:2] + "****" + telephone[-2:]


def mask_file_url(url: str) -> str:
    """Mask file URL: keep only domain + file_id, truncate path."""
    try:
        parsed = urlparse(url)
        # Extract file_id from path (assume last segment or query param)
        file_id = ""
        if parsed.path:
            segments = parsed.path.strip("/").split("/")
            if segments:
                file_id = segments[-1]
        elif parsed.query:
            # Try to extract file_id from query
            for param in parsed.query.split("&"):
                if "file_id" in param or "id" in param:
                    file_id = param.split("=", 1)[1] if "=" in param else ""
                    break

        if file_id:
            return f"{parsed.scheme}://{parsed.netloc}/.../{file_id}"
        else:
            return f"{parsed.scheme}://{parsed.netloc}/***"
    except Exception:
        return "***REDACTED***"


def redact_dict(obj: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive fields in dictionary."""
    sensitive_keys_simple = {
        "unit_price",
        "amount",
        "address",
        "token",
        "api_key",
        "password",
        "smtp_pass",
    }

    redacted = {}
    for key, value in obj.items():
        key_lower = key.lower()

        # Email masking
        if key_lower == "email" and isinstance(value, str):
            redacted[key] = mask_email(value)
        # Telephone masking
        elif key_lower == "telephone" and isinstance(value, str):
            redacted[key] = mask_telephone(value)
        # File URL masking
        elif (key_lower in ("file_url", "url", "order_url") and isinstance(value, str) and value.startswith(("http://", "https://"))):
            redacted[key] = mask_file_url(value)
        # Simple redaction
        elif key_lower in sensitive_keys_simple:
            redacted[key] = "***REDACTED***"
        # Recursive for dicts
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        # Recursive for lists
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item) if isinstance(item, dict) else (
                    mask_email(item) if isinstance(item, str) and "@" in item and key_lower == "email"
                    else mask_telephone(item) if isinstance(item, str) and key_lower == "telephone"
                    else item
                )
                for item in value
            ]
        else:
            redacted[key] = value

    return redacted

