"""Test script for OptiBot setup - Vector Store + Assistant."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from openai_service.upload_markdown import OptiBot
from utils.logger import setup_logger

# Load environment
load_dotenv()

logger = setup_logger(__name__)


def test_optibot_setup():
    """Test complete OptiBot setup: Vector Store + Assistant."""
    
    try:
        articles_dir = "data/articles"
        if not Path(articles_dir).exists():
            logger.error(f"Directory not found: {articles_dir}")
            return False
        
        markdown_files = list(Path(articles_dir).glob("*.md"))
        if not markdown_files:
            logger.error(f"No markdown files in {articles_dir}")
            return False
        
        bot = OptiBot()
        result = bot.run_full_setup(articles_dir)
        
        logger.info(f"Vector Store: {result['vector_store_id']}")
        logger.info(f"Assistant: {result['assistant_id']}")
        logger.info(f"Files: {result['upload_summary']['successful']}/{len(markdown_files)} uploaded")
        
        return True
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_optibot_setup()
    exit(0 if success else 1)
