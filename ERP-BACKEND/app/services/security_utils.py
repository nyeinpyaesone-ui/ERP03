"""
Security utilities for password validation, file handling, and constant-time comparisons.
"""
import os
import mimetypes
import secrets
from typing import List, Optional, Tuple
from pathlib import Path

# Allowed MIME types for document uploads
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/plain": ".txt",
    "application/zip": ".zip",
}

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate a password against the required length and character composition rules.
    
    Parameters:
        password (str): Password to validate.
    
    Returns:
        tuple[bool, str]: A validity flag and an error message. The message is
            empty when the password satisfies all requirements.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, f"Password must contain at least one special character ({special_chars})."
    
    return True, ""


def validate_file_upload(file_content: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate an uploaded file's size, type, and extension, and generate a safe filename for valid files.
    
    Parameters:
        file_content (bytes): The uploaded file contents.
        filename (str): The original filename used to determine its extension and type.
    
    Returns:
        Tuple[bool, str, Optional[str]]: A validity flag, an error message, and a randomized filename with the validated extension when valid; otherwise, no filename.
    """
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB.", None
    
    # Check extension
    file_ext = Path(filename).suffix.lower()
    if not file_ext:
        return False, "File must have a valid extension.", None
    
    # Get MIME type from magic bytes
    mime_type, _ = mimetypes.guess_type(filename)
    
    # If mimetypes fails, try to detect from content (basic check)
    if not mime_type:
        # Basic magic byte checking for common types
        if file_content.startswith(b'%PDF'):
            mime_type = "application/pdf"
        elif file_content.startswith(b'\xff\xd8\xff'):
            mime_type = "image/jpeg"
        elif file_content.startswith(b'\x89PNG'):
            mime_type = "image/png"
        elif file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
            mime_type = "image/gif"
        else:
            return False, "Unable to determine file type. Unsupported format.", None
    
    # Validate MIME type against allowlist
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"File type '{mime_type}' is not allowed.", None
    
    # Verify extension matches MIME type
    expected_ext = ALLOWED_MIME_TYPES[mime_type]
    if file_ext != expected_ext:
        return False, f"File extension mismatch. Expected {expected_ext} for {mime_type}.", None
    
    # Generate safe filename to prevent directory traversal
    safe_filename = f"{secrets.token_hex(16)}{file_ext}"
    
    return True, "", safe_filename


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Performs a constant-time comparison of two strings to prevent timing attacks.
    Uses hmac.compare_digest which is designed for this purpose.
    """
    import hmac
    return hmac.compare_digest(val1.encode('utf-8'), val2.encode('utf-8'))
