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

logger = setup_logger("OptiBot-Job")


class OptiBotJob:
    """Main orchestrator for OptiBot article scraping and indexing."""
    
    def __init__(self):
        """Initialize OptiBot."""
        self.start_time = datetime.now()
        self.article_store = ArticleStore()  # Initialize article store
        self.scraper = ArticleScraper(store=self.article_store)
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
                # Only upload changed files (new + updated)
                changed_files = scrape_summary.get("changed_files", [])
                if changed_files:
                    logger.info(f"\n{len(changed_files)} files changed, uploading to vector store...")
                    upload_summary = self.upload_to_vector_store(changed_files=changed_files)
                else:
                    logger.info("\nNo files changed, skipping upload")
                    upload_summary = {"skipped": True, "reason": "no changes"}
            else:
                logger.info("\nSkipping upload phase (skip_upload=True)")

            
            # Summary
            elapsed = datetime.now() - self.start_time
            logger.info("\n" + "="*60)
            logger.info("JOB COMPLETED SUCCESSFULLY")

            
            return True
        
        except Exception as e:
            elapsed = datetime.now() - self.start_time
            logger.error("\n" + "="*60)
            logger.error("JOB FAILED")
            logger.error(f"Failed at {datetime.now().isoformat()}")
            logger.error(f"Elapsed Time: {elapsed.total_seconds():.1f} seconds")
            logger.error(f"Error: {e}")
            logger.error("="*60 + "\n")
            
            import traceback
            logger.debug(traceback.format_exc())
            
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
