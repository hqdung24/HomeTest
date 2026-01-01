"""Store and manage articles locally as Markdown files."""

import os
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from slugify import slugify

logger = logging.getLogger(__name__)


class ArticleStore:
    """Manage local article storage and state tracking."""
    
    def __init__(self, articles_dir: str = "data/articles", state_file: str = "data/state.json"):
        """
        Initialize article store.
        
        Args:
            articles_dir: Directory to store markdown files
            state_file: JSON file to track article state (hash, updated_at)
        """
        self.articles_dir = Path(articles_dir)
        self.state_file = Path(state_file)
        
        # Create directories if they don't exist
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load article state from JSON file."""
        default_state = {
            "last_run": None,
            "total_articles": 0,
            "vector_store_id": None,
            "assistant_id": None,
            "next_page_url": None,
            "articles": {}
        }

        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    loaded = json.load(f)
                    # Backfill any missing keys (for older state files)
                    for key, value in default_state.items():
                        loaded.setdefault(key, value)
                    return loaded
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")

        return default_state
    
    def _save_state(self):
        """Save article state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def save_article(self, article: Dict[str, Any], markdown_content: str) -> bool:
        """
        Save article as Markdown file and update state.
        
        Args:
            article: Article dict with id, title, updated_at, etc.
            markdown_content: Markdown formatted content
            
        Returns:
            True if saved, False if error
        """
        try:
            # Generate slug from title
            slug = slugify(article['title'], max_length=100)
            if not slug:
                slug = f"article-{article['id']}"
            
            # Save markdown file
            file_path = self.articles_dir / f"{slug}.md"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # Add metadata header
                f.write(f"# {article['title']}\n\n")
                f.write(f"**Source:** [{article['html_url']}]({article['html_url']})\n")
                f.write(f"**Last Updated:** {article['updated_at']}\n\n")
                f.write("---\n\n")
                f.write(markdown_content)
            
            # Update state
            content_hash = hashlib.md5(markdown_content.encode()).hexdigest()
            
            self.state["articles"][str(article['id'])] = {
                "title": article['title'],
                "slug": slug,
                "hash": content_hash,
                "updated_at": article['updated_at'],
                "html_url": article['html_url'],
                "saved_at": datetime.now().isoformat()
            }
            
            logger.info(f"✓ Saved: {slug}.md")
            return True
        
        except Exception as e:
            logger.error(f"Error saving article {article['id']}: {e}")
            return False
    
    def has_changed(self, article_id: int, content_hash: str) -> bool:
        """
        Check if article content has changed since last save.
        
        Args:
            article_id: Article ID
            content_hash: MD5 hash of new content
            
        Returns:
            True if article is new or has changed
        """
        article_key = str(article_id)
        
        if article_key not in self.state["articles"]:
            return True  # New article
        
        old_hash = self.state["articles"][article_key].get("hash")
        return old_hash != content_hash
    
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get stored article state."""
        return self.state["articles"].get(str(article_id))
    
    def get_vector_store_id(self) -> Optional[str]:
        """Get stored vector store ID."""
        return self.state.get("vector_store_id")
    
    def set_vector_store_id(self, vector_store_id: str):
        """Set vector store ID."""
        self.state["vector_store_id"] = vector_store_id
        self._save_state()
    
    def get_assistant_id(self) -> Optional[str]:
        """Get stored assistant ID."""
        return self.state.get("assistant_id")
    
    def set_assistant_id(self, assistant_id: str):
        """Set assistant ID."""
        self.state["assistant_id"] = assistant_id
        self._save_state()
    
    def get_next_page_url(self) -> Optional[str]:
        """Get stored next_page_url for pagination."""
        return self.state.get("next_page_url")
    
    def set_next_page_url(self, next_page_url: Optional[str]):
        """Set next_page_url for pagination."""
        self.state["next_page_url"] = next_page_url
        self._save_state()
    
    def finalize(self):
        """Finalize storage - update metadata and save state."""
        self.state["last_run"] = datetime.now().isoformat()
        self.state["total_articles"] = len(self.state["articles"])
        self._save_state()
        
        logger.info(f"Finalized: {self.state['total_articles']} articles")
        logger.info(f"Saved to: {self.articles_dir}")

