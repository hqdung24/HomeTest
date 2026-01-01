"""Test script for article scraping pipeline."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from scraper.scrape_articles import scrape_all_articles
from utils.logger import setup_logger

# Load environment
load_dotenv()

logger = setup_logger(__name__)


def test_scraper():
    """Test the complete scraping pipeline."""
    
    try:
        summary = scrape_all_articles(limit=50)
        
        if summary["added"] + summary["updated"] > 0:
            logger.info(f"Success: {summary['added']} added, {summary['updated']} updated")
            return True
        else:
            logger.warning("No articles processed")
            return False
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scraper()
    exit(0 if success else 1)
