"""
Input validation utilities for PromptSmith.
"""

from typing import Tuple


def validate_user_text(text: str, min_length: int = 3, max_length: int = 50000) -> Tuple[bool, str]:
    """
    Validate the user input text for basic sanity.

    Args:
        text: The input provided by the user.
        min_length: Minimum non-whitespace length required.
        max_length: Maximum length allowed to prevent DoS.

    Returns:
        (is_valid, error_message)
    """
    if text is None:
        return False, "Missing 'user_text'"
    
    # Check raw length first to prevent DoS with large inputs
    if len(text) > max_length:
        return False, f"'user_text' must not exceed {max_length} characters"

    stripped = text.strip()
    if len(stripped) < min_length:
        return False, f"'user_text' must be at least {min_length} characters"

    return True, ""
