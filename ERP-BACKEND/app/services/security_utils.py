"""
Security Utilities for Input Validation and Safe Operations
"""
import re
import hmac
import hashlib
from typing import Optional
from fastapi import UploadFile, HTTPException, status

def validate_password_strength(password: str) -> bool:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False
    
    patterns = [
        r'[A-Z]',  # Uppercase
        r'[a-z]',  # Lowercase
        r'\d',     # Digit
        r'[!@#$%^&*(),.?":{}|<>]'  # Special character
    ]
    
    return all(re.search(pattern, password) for pattern in patterns)

def constant_time_compare(val1: str, val2: str) -> bool:
    """Perform constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(val1.encode('utf-8'), val2.encode('utf-8'))

async def validate_file_upload(file: UploadFile, 
                               max_size_mb: int = 10,
                               allowed_mime_types: Optional[list] = None) -> str:
    """
    Validate file upload for security:
    - Check MIME type
    - Check file size
    - Sanitize filename
    """
    if allowed_mime_types is None:
        allowed_mime_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]
    
    # Validate MIME type
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {allowed_mime_types}"
        )
    
    # Validate file size (read first chunk to check)
    contents = await file.read()
    file_size = len(contents)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({max_size_mb}MB)"
        )
    
    # Reset file pointer for later reading
    await file.seek(0)
    
    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename or "unnamed")
    
    return safe_filename

def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove null bytes
    sanitized = input_string.replace('\x00', '')
    
    # Trim to max length
    sanitized = sanitized[:max_length]
    
    # Escape potential SQL injection characters (additional layer of protection)
    # Note: SQLAlchemy parameterization is the primary defense
    dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'EXEC']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()
