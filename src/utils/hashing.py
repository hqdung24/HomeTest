"""Hashing utilities for content integrity."""

import hashlib


def hash_content(content: str, algorithm: str = "md5") -> str:
    """
    Generate hash of content for change detection.
    
    Args:
        content: Content to hash
        algorithm: Hash algorithm (md5, sha256, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    hasher.update(content.encode('utf-8'))
    return hasher.hexdigest()


def hash_content_md5(content: str) -> str:
    """Generate MD5 hash (commonly used for change detection)."""
    return hash_content(content, algorithm="md5")


def hash_content_sha256(content: str) -> str:
    """Generate SHA256 hash (more secure)."""
    return hash_content(content, algorithm="sha256")
