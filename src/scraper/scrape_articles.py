"""Main scraping orchestration logic."""

import logging
import hashlib
from typing import List, Dict, Any, Optional

from .zendesk_client import ZendeskClient
from .html_to_md import html_to_markdown, clean_markdown
from .article_store import ArticleStore

logger = logging.getLogger(__name__)




class ArticleScraper:
    """Orchestrate article scraping, conversion, and storage."""
    
    def __init__(self, articles_dir: str = "data/articles", 
                 state_file: str = "data/state.json",
                 store: Optional[ArticleStore] = None):
        """
        Initialize scraper.
        
        Args:
            subdomain: Zendesk subdomain (reads from ZENDESK_SUBDOMAIN env var if not provided)
            articles_dir: Directory for markdown files
            state_file: State tracking JSON file
        """

        
        self.client = ZendeskClient()
        # Allow sharing a single store instance to avoid state overwrite in multi-phase jobs
        self.store = store or ArticleStore(articles_dir=articles_dir, state_file=state_file)
        self.subdomain = self.client.subdomain
        logger.info(f"Initialized scraper with subdomain: {self.subdomain}")
    
    def scrape_articles(self, per_page: int = 30) -> Dict[str, Any]:
        """
        Scrape, convert, and store articles using pagination.
        Automatically loads next_page_url from state and continues from there.
        
        Args:
            per_page: Number of articles to fetch per batch (default 30)
            
        Returns:
            Summary dict with counts (added, updated, skipped) and changed_files list
        """
        # Load pagination state
        next_page_url = self.store.get_next_page_url()
        
        if next_page_url:
            logger.info(f"Continuing pagination from saved position...")
        else:
            logger.info(f"Starting fresh pagination (fetching {per_page} articles)...")
        
        summary = {
            "total_fetched": 0,
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "changed_files": [],  # Track slugs of new/updated files
            "pagination_complete": False
        }
        
        try:
            # Fetch articles from Zendesk with pagination
            articles, new_next_page_url = self.client.get_articles(
                next_page_url=next_page_url,
                per_page=per_page
            )
            
            summary["total_fetched"] = len(articles)
            
            # Save new pagination state
            self.store.set_next_page_url(new_next_page_url)
            
            if new_next_page_url is None:
                summary["pagination_complete"] = True
                logger.info("Pagination cycle complete - will restart from beginning next run")

            # Fetch full content and convert each
            logger.info("Processing articles...\n")
            for i, article in enumerate(articles, 1):
                try:
                    full_article = self.client.get_article_content(article["id"])
                    
                    # Extract HTML body
                    html_body = full_article.get("body", "")
                    if not html_body:
                        logger.warning(f"  [{i}/{len(articles)}] No body content")
                        summary["skipped"] += 1
                        continue
                    
                    # Convert HTML to Markdown
                    markdown = html_to_markdown(
                        html_body,
                        base_url=full_article.get("html_url", "")
                    )
                    markdown = clean_markdown(markdown)
                    
                    # Check if changed
                    content_hash = hashlib.md5(markdown.encode()).hexdigest()
                    
                    if self.store.has_changed(article["id"], content_hash):
                        # Check before saving so we can distinguish added vs updated
                        old_record = self.store.get_article(article["id"])
                        self.store.save_article(full_article, markdown)
                        
                        # Get slug for changed file tracking
                        new_record = self.store.get_article(article["id"])
                        if new_record and new_record.get("slug"):
                            summary["changed_files"].append(new_record["slug"])
                        
                        if old_record:
                            summary["updated"] += 1
                        else:
                            summary["added"] += 1
                    else:
                        logger.info(f"  [{i}/{len(articles)}] No changes (skipped)")
                        summary["skipped"] += 1
                
                except Exception as e:
                    logger.error(f"  [{i}/{len(articles)}] Error: {e}")
                    summary["errors"] += 1
                    continue
            
            # Finalize storage
            self.store.finalize()
            
            # Print summary
            logger.info("\n" + "="*50)
            logger.info("Scrape summary:")
            logger.info(f"Total fetched: {summary['total_fetched']}")
            logger.info(f"Added: {summary['added']}")
            logger.info(f"Updated: {summary['updated']}")
            logger.info(f"Skipped: {summary['skipped']}")
            logger.info(f"Errors: {summary['errors']}")
            logger.info("="*50 + "\n")
            
            return summary
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise


def scrape_all_articles(per_page: int = 30) -> Dict[str, Any]:
    """
    Function to scrape articles using pagination.
    
    Args:
        per_page: Number of articles to fetch per batch (default 30)
        
    Returns:
        Summary dict
    """
    scraper = ArticleScraper()
    return scraper.scrape_articles(per_page=per_page)

