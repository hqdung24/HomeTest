"""Main job orchestrator for daily article scraping and vector store updates."""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.scrape_articles import ArticleScraper
from scraper.article_store import ArticleStore
from openai_service.upload_markdown import OptiBot as OptiBotAssistant
from utils.logger import setup_logger
from utils.spaces_logger import setup_spaces_logging

logger = setup_logger("OptiBot-Job")


class OptiBotJob:
    """Main orchestrator for OptiBot article scraping and indexing."""
    
    def __init__(self):
        """Initialize OptiBot."""
        self.start_time = datetime.now()
        self.article_store = ArticleStore()  # Initialize article store
        self.scraper = ArticleScraper(store=self.article_store)
        
        # Setup Spaces logging (writes to local log AND S3)
        self.spaces_log_handler = setup_spaces_logging()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.spaces_log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.spaces_log_handler)
        
        logger.info("="*60)
        logger.info("OptiBot - Article Scraping and Indexing Job")
        logger.info(f"Started at {self.start_time.isoformat()}")
        logger.info("="*60)
    
    def scrape_articles(self, per_page: int = 30) -> Dict[str, Any]:
        """
        Scrape articles from Zendesk using pagination.
        Automatically continues from saved next_page_url.
        
        Args:
            per_page: Number of articles to fetch per batch (default 30)
            
        Returns:
            Scraping summary with changed_files list
        """
        logger.info("\nPHASE 1: SCRAPING ARTICLES")
        logger.info("-" * 60)
        
        try:
            summary = self.scraper.scrape_articles(per_page=per_page)
            
            processed = summary["added"] + summary["updated"]
            logger.info("\nScraping Phase Complete")
            logger.info(f"   • Total Fetched: {summary['total_fetched']}")
            logger.info(f"   • New Articles: {summary['added']}")
            logger.info(f"   • Updated Articles: {summary['updated']}")
            logger.info(f"   • Unchanged (Skipped): {summary['skipped']}")
            logger.info(f"   • Errors: {summary['errors']}")
            logger.info(f"   • Articles to Upload: {processed}")
            
            return summary
        
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
    
    def upload_to_vector_store(self, changed_files: List[str] = None,  # pyright: ignore[reportArgumentType]
                              articles_dir: str = "data/articles") -> Dict[str, Any]:
        """
        Upload markdown articles to OpenAI Vector Store and create Assistant.
        Only uploads changed files if provided, otherwise uploads all.
        
        Args:
            changed_files: List of changed file slugs to upload
            articles_dir: Directory containing markdown files
            
        Returns:
            Setup result
        """
        logger.info("\nPHASE 2: VECTOR STORE & ASSISTANT SETUP")
        logger.info("-" * 60)
        
        try:
            # Initialize OptiBot Assistant with article store
            logger.info("Setting up OptiBot Assistant...")
            bot = OptiBotAssistant(article_store=self.article_store)
            
            # Create/reuse vector store and upload files
            if changed_files:
                logger.info(f"\nUploading {len(changed_files)} changed files to vector store...")
            else:
                logger.info(f"\nSetting up vector store (first run or full sync)...")
            
            setup_result = bot.run_full_setup(articles_dir, changed_files=changed_files)
            
            logger.info("\nVector Store & Assistant Setup Complete")
            logger.info(f"   Vector Store ID: {setup_result['vector_store_id']}")
            logger.info(f"   Assistant ID: {setup_result['assistant_id']}")
            logger.info(f"   Files Uploaded: {setup_result['upload_summary']['successful']}")
            
            if setup_result['file_counts']:
                completed = setup_result['file_counts'].get('completed', 0)
                logger.info(f"   Files Processed: {completed}")
    
            return setup_result
        
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    def run(self, skip_upload: bool = False, per_page: int = 30) -> bool:
        """
        Run complete OptiBot job.
        Uses pagination automatically - continues from saved next_page_url.
        
        Args:
            skip_upload: Skip vector store upload phase
            per_page: Number of articles to fetch per batch (default 30)
            
        Returns:
            True if successful
        """
        try:
            # Step 1: Scrape articles
            scrape_summary = self.scrape_articles(per_page=per_page)
            
            # Step 2: Upload to vector store
            if not skip_upload:
                changed_files = scrape_summary.get("changed_files", [])
                if changed_files:
                    upload_summary = self.upload_to_vector_store(changed_files=changed_files)
                else:
                    upload_summary = {"skipped": True}
            else:
                upload_summary = {"skipped": True}

            # Log summary
            elapsed = datetime.now() - self.start_time
            summary_line = (
                f"[{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Scraped: {scrape_summary.get('total_fetched', 0)}, "
                f"Added: {scrape_summary.get('added', 0)}, "
                f"Updated: {scrape_summary.get('updated', 0)}, "
                f"Skipped: {scrape_summary.get('skipped', 0)}, "
                f"Uploaded: {len(scrape_summary.get('changed_files', []))} files, "
                f"Elapsed: {elapsed.total_seconds():.0f}s"
            )
            
            logger.info(summary_line)
            
            return True
        
        except Exception as e:
            elapsed = datetime.now() - self.start_time
            summary_line = (
                f"[{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"JOB FAILED: {str(e)[:80]} (Elapsed: {elapsed.total_seconds():.0f}s)"
            )
            
            logger.error(summary_line)
            
            return False


def main():
    """Main entry point for OptiBot job."""
    
    # Run job with defaults (no CLI args)
    bot = OptiBotJob()
    success = bot.run()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
