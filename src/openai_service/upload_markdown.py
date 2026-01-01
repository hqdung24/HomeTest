"""Upload Markdown files to OpenAI Vector Store and create Assistant."""

import logging
from pathlib import Path
from typing import List, Optional, Dict
from .client import OpenAIVectorStoreClient

logger = logging.getLogger(__name__)


class OptiBot:
    """Setup and manage OptiBot Assistant with Vector Store."""
    
    def __init__(self, api_key: Optional[str] = None, article_store = None):
        """
        Initialize OptiBot.
        
        Args:
            api_key: OpenAI API key
            article_store: ArticleStore instance for state tracking
        """
        self.client = OpenAIVectorStoreClient(api_key=api_key)
        self.article_store = article_store
        self.vector_store_id = None
        self.assistant_id = None
        logger.info("Initialized OptiBot setup")
    
    SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.

Your responsibilities:
• Answer questions about OptiSigns digital signage products, features, and setup
• Tone: helpful, factual, concise
• Only answer using the uploaded documentation
• Keep responses to max 5 bullet points; link to full articles for more details
• Always cite the Article URL for your sources (up to 3 URLs per reply)
• If unsure, admit it and suggest contacting support

Guidelines:
• Be specific about product names (Pro Player, ProMax Player, etc)
• Provide step-by-step instructions when relevant
• Link to related articles when applicable
• Always maintain a professional, helpful tone"""
    
    def get_or_create_vector_store(self) -> str:
        """
        Get existing vector store or create new one.
        
        Returns:
            Vector store ID
        """
        # Check if we have a stored vector store ID
        if self.article_store:
            stored_id = self.article_store.get_vector_store_id()
            if stored_id:
                # Verify it still exists
                vs = self.client.get_vector_store(stored_id)
                if vs:
                    logger.info(f"Reusing existing vector store: {stored_id}")
                    self.vector_store_id = stored_id
                    return stored_id
                else:
                    logger.warning(f"Stored vector store {stored_id} not found, creating new one")
        
        # Create new vector store
        logger.info("Creating new vector store...")
        self.vector_store_id = self.client.create_vector_store("OptiBot-Articles")
        
        # Save to state
        if self.article_store:
            self.article_store.set_vector_store_id(self.vector_store_id)
        
        return self.vector_store_id
    
    def get_or_create_assistant(self) -> str:
        """
        Get existing assistant or create new one.
        
        Returns:
            Assistant ID
        """
        if not self.vector_store_id:
            raise ValueError("Vector store not initialized")
        
        # Check if we have a stored assistant ID
        if self.article_store:
            assistant_id = self.article_store.get_assistant_id()
            if assistant_id:
                # Verify it still exists
                assistant = self.client.get_assistant(assistant_id)
                if assistant:
                    logger.info(f"Reusing existing assistant: {assistant_id}")
                    self.assistant_id = assistant_id
                    return assistant_id
                else:
                    logger.warning(f"Stored assistant {assistant_id} not found, creating new one")
        
        # Create new assistant
        logger.info("Creating new assistant...")
        self.assistant_id = self.client.create_assistant(
            name="OptiBot",
            instructions=self.SYSTEM_PROMPT,
            vector_store_id=self.vector_store_id,
            model="gpt-4o-mini"  # Cheapest option: $0.15/$0.60 per 1M tokens, supports Assistants API
        )
        
        # Save to state
        if self.article_store:
            self.article_store.set_assistant_id(self.assistant_id)
        
        return self.assistant_id
    
    def upload_files(self, file_paths: List[str]) -> dict:
        """
        Upload files to existing vector store.
        
        Args:
            file_paths: List of markdown file paths to upload
            
        Returns:
            Upload summary
        """
        if not self.vector_store_id:
            raise ValueError("Vector store not initialized")
        
        if not file_paths:
            logger.info("No files to upload")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "file_ids": [],
                "errors": []
            }
        
        logger.info(f"Uploading {len(file_paths)} files to vector store...")
        upload_summary = self.client.upload_files_to_vector_store(
            file_paths,
            self.vector_store_id
        )

        logger.info("Processing files (chunking & embedding)...")
        file_counts = self.client.wait_for_vector_store_processing(self.vector_store_id)
        
        return {
            "upload_summary": upload_summary,
            "file_counts": file_counts
        }
    
    def create_vector_store_and_upload(self, markdown_dir: str = "data/articles", 
                                      changed_files: Optional[List[str]] = None) -> dict:
        """
        Setup vector store and upload files (reuses existing if available).
        
        Chunking Strategy:
        - OpenAI automatically chunks at ~800 token boundaries
        - Markdown structure (headers, lists) is preserved
        - Each markdown file includes metadata (title, URL, update date)
        
        Args:
            markdown_dir: Directory containing markdown files
            changed_files: List of changed file slugs to upload (if None, uploads all)
            
        Returns:
            Summary with vector store ID and upload results
        """
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: VECTOR STORE SETUP & FILE UPLOAD")
        logger.info("="*60)
        
        try:
            # Get or create vector store
            self.vector_store_id = self.get_or_create_vector_store()
            
            # Determine which files to upload
            dir_path = Path(markdown_dir)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {markdown_dir}")
            
            if changed_files:
                # Upload only changed files
                files = [dir_path / f"{slug}.md" for slug in changed_files]
                files = [f for f in files if f.exists()]
                logger.info(f"\nFound {len(files)} changed files to upload")
            else:
                # Upload all files (first run or full sync)
                files = sorted(dir_path.glob("*.md"))
                logger.info(f"\nFound {len(files)} markdown files")
            
            if not files:
                logger.info("No files to upload")
                return {
                    "vector_store_id": self.vector_store_id,
                    "upload_summary": {"total": 0, "successful": 0, "failed": 0},
                    "file_counts": None
                }
            
            # Upload files
            file_paths = [str(f) for f in files]
            result = self.upload_files(file_paths)
            
            return {
                "vector_store_id": self.vector_store_id,
                "upload_summary": result["upload_summary"],
                "file_counts": result["file_counts"]
            }
        
        except Exception as e:
            logger.error(f"Vector store setup failed: {e}")
            raise
    
    def create_assistant(self) -> str:
        """
        Get or create OptiBot Assistant with Vector Store.
        
        Returns:
            Assistant ID
        """
        if not self.vector_store_id:
            raise ValueError("Vector store not initialized. Call create_vector_store_and_upload first.")
        
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: ASSISTANT SETUP")
        logger.info("="*60)
        
        try:
            self.assistant_id = self.get_or_create_assistant()
            
            logger.info(f"\nAssistant ready")
            logger.info(f"Assistant ID: {self.assistant_id}")
            logger.info(f"Vector Store ID: {self.vector_store_id}")
            
            return self.assistant_id
        
        except Exception as e:
            logger.error(f"Assistant setup failed: {e}")
            raise
    
    def run_full_setup(self, markdown_dir: str = "data/articles", 
                      changed_files: Optional[List[str]] = None) -> dict:
        """
        Run complete setup: get/create vector store, upload files, get/create assistant.
        
        Args:
            markdown_dir: Directory with markdown files
            changed_files: List of changed file slugs to upload (if None, uploads all)
            
        Returns:
            Summary with all IDs and stats
        """
        try:
            # Phase 1: Vector store
            vs_result = self.create_vector_store_and_upload(markdown_dir, changed_files)
            
            # Phase 2: Assistant
            assistant_id = self.create_assistant()
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("OPTIBOT SETUP COMPLETE")
            logger.info("="*60)
            logger.info(f"\nOptiBot is ready to answer customer questions!")
            logger.info(f"\n   Vector Store ID: {self.vector_store_id}")
            logger.info(f"   Assistant ID: {assistant_id}")
            logger.info(f"   Articles uploaded: {vs_result['upload_summary']['successful']}")
            
            if vs_result['file_counts']:
                completed = vs_result['file_counts'].get('completed', 0)
                logger.info(f"   Files processed: {completed}")
            else:
                logger.info(f"   Files processed: pending")
            logger.info(f"\n   Next: Test in OpenAI Playground")
            logger.info(f"   https://platform.openai.com/playground")
            logger.info("="*60 + "\n")
            
            return {
                "vector_store_id": self.vector_store_id,
                "assistant_id": assistant_id,
                "upload_summary": vs_result["upload_summary"],
                "file_counts": vs_result["file_counts"]
            }
        
        except Exception as e:
            logger.error(f"Full setup failed: {e}")
            raise


def setup_optibot(markdown_dir: str = "data/articles", api_key: str = '', 
                 article_store = None, changed_files: Optional[List[str]] = None) -> dict:
    """
    Convenience function to setup OptiBot completely.
    
    Args:
        markdown_dir: Directory with markdown files
        api_key: OpenAI API key (optional)
        article_store: ArticleStore instance for state tracking
        changed_files: List of changed file slugs to upload (if None, uploads all)
        
    Returns:
        Setup result dict
    """
    bot = OptiBot(api_key=api_key, article_store=article_store)
    return bot.run_full_setup(markdown_dir, changed_files)
