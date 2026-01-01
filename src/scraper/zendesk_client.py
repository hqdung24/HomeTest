"""Zendesk API client for fetching public Help Center articles (no auth required)."""

import requests
import logging
from typing import List, Dict, Any, Optional
from config import ZENDESK_SUBDOMAIN

logger = logging.getLogger(__name__)


class ZendeskClient:
    """
    Client for fetching Zendesk Help Center articles via public API.
    No authentication required for public Help Centers.
    """
    
    def __init__(self, subdomain: str = "", api_key: str = ''):
        """
        Initialize Zendesk client for public Help Center API.
        
        Args:
            subdomain: Zendesk subdomain (e.g., "support.optisigns" for support.optisigns.com)
            api_key: Not required for public Help Centers 
        """
        # Load from config if not provided
        if subdomain == '':
            subdomain = ZENDESK_SUBDOMAIN
        self.api_key = api_key
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })
    
    def get_articles(self, next_page_url: Optional[str] = None, per_page: int = 30) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch articles from Zendesk Help Center API using pagination.
        
        Args:
            next_page_url: Full next_page URL from previous response (if continuing pagination)
            per_page: Number of articles per page (default 30)
            
        Returns:
            Tuple of (articles list, next_page_url for continuation)
        """
        try:
            if next_page_url:
                # Use existing next_page URL (already has all params)
                url = next_page_url
                logger.info(f"Fetching articles from next_page URL...")
                logger.debug(f"   URL: {next_page_url}")
                response = self.session.get(url, timeout=10)
            else:
                # First request - build URL with defaults
                url = f"{self.base_url}/help_center/en-us/articles"
                params = {
                    "per_page": per_page,
                    "sort_by": "updated_at",
                    "sort_order": "desc"
                }
                logger.info(f"Fetching articles (first page, per_page={per_page})...")
                logger.debug(f"   URL: {url}")
                logger.debug(f"   Params: {params}")
                response = self.session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            next_page = data.get("next_page")  # This is the full URL or None
            
            logger.info(f"Fetched {len(articles)} articles")
            if next_page:
                logger.info(f"Next page available: {next_page[:80]}...")
            else:
                logger.info("No more pages (pagination complete)")
            
            return articles, next_page
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching articles: {e}")
            raise
    
    def get_article_content(self, article_id: int) -> Dict[str, Any]:
        """
        Fetch detailed content for a single article (including body_html).
        
        Args:
            article_id: Zendesk article ID
            
        Returns:
            Article object with full content
        """
        try:
            url = f"{self.base_url}/help_center/en-us/articles/{article_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json().get("article", {})
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching article {article_id}: {e}")
            raise
    
    def get_articles_with_content(self, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch first page of articles with full HTML content.
        Uses per_page to match pagination defaults.
        
        Args:
            per_page: Number of articles to fetch in the first page (default 30)
            
        Returns:
            List of complete article objects with body_html
        """
        articles, _ = self.get_articles(per_page=per_page)
        logger.info(f"Fetching full content for {len(articles)} articles...")
        
        articles_with_content = []
        for i, article in enumerate(articles, 1):
            try:
                full_article = self.get_article_content(article["id"])
                articles_with_content.append(full_article)
                logger.info(f"  [{i}/{len(articles)}] {full_article['title']}")
            except Exception as e:
                logger.warning(f"  [{i}/{len(articles)}] Failed: {e}")
                continue
        
        logger.info(f"Fetched content for {len(articles_with_content)} articles")
        return articles_with_content
