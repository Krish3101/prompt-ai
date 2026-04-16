import re


def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a string.
    A simple rule of thumb is that one token is approximately 4 characters.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        int: Estimated number of tokens
    """
    if not text:
        return 0
    return len(text) // 4


def count_words(text: str) -> int:
    """
    Counts the number of words in a string.
    
    Args:
        text: The text to count words in
        
    Returns:
        int: Number of words
    """
    if not text:
        return 0
    # Split on whitespace and filter out empty strings
    return len([word for word in text.split() if word.strip()])
