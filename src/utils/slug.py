"""Slug generation utilities."""

from slugify import slugify as _slugify


def generate_slug(text: str, max_length: int = 100) -> str:
    """
    Generate URL-friendly slug from text.
    
    Args:
        text: Text to slugify
        max_length: Maximum slug length
        
    Returns:
        URL-friendly slug
    """
    slug = _slugify(text, max_length=max_length)
    return slug if slug else "article"
