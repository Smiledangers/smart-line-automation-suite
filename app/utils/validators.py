"""Validation utilities."""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_line_user_id(line_user_id: str) -> bool:
    """Validate LINE user ID format."""
    # LINE user IDs typically start with U followed by 32 hex characters
    pattern = r'^U[0-9a-fA-F]{32}$'
    return bool(re.match(pattern, line_user_id))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://'
    return bool(re.match(pattern, url))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input."""
    # Remove null bytes
    text = text.replace('\x00', '')
    # Strip whitespace
    text = text.strip()
    # Optionally truncate
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text


def validate_priority(priority: int) -> bool:
    """Validate job priority (1-5)."""
    return 1 <= priority <= 5


def validate_scraping_website_type(website_type: str) -> bool:
    """Validate scraping website type."""
    valid_types = ['generic', 'ecommerce', 'news', 'social', 'forum', 'blog']
    return website_type.lower() in valid_types