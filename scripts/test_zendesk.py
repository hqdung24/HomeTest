"""Quick test script to verify Zendesk API connection (no auth required)."""

import sys
import os
from pathlib import Path

# Add src to path (go up one level to project root, then into src)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import ZENDESK_SUBDOMAIN
from scraper.zendesk_client import ZendeskClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_zendesk():
    """Test Zendesk public API and fetch a sample page of articles."""

    try:
        client = ZendeskClient(subdomain=ZENDESK_SUBDOMAIN)
        articles, next_page = client.get_articles(per_page=5)

        if not articles:
            logger.warning("No articles found")
            return False

        logger.info(f"Fetched {len(articles)} articles from {ZENDESK_SUBDOMAIN}")
        logger.info(f"Next page present: {'yes' if next_page else 'no'}")
        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_zendesk()
    exit(0 if success else 1)
