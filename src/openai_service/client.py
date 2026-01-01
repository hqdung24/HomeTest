"""OpenAI API client for Vector Stores and Assistants using REST API."""

import logging
import time
import json
import requests
from typing import Optional, List
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class OpenAIVectorStoreClient:
    """Client for managing OpenAI Vector Stores and Assistants via REST API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (reads from config if not provided)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "assistants=v2"
        }
        logger.info("Initialized OpenAI REST API client")
    
    def list_vector_stores(self) -> List[dict]:
        """
        List all vector stores.
        
        Returns:
            List of vector store objects
        """
        try:
            response = requests.get(
                f"{self.base_url}/vector_stores",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Error listing vector stores: {e}")
            raise
    
    def get_vector_store(self, vector_store_id: str) -> Optional[dict]:
        """
        Get a specific vector store by ID.
        
        Args:
            vector_store_id: Vector store ID
            
        Returns:
            Vector store object or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/vector_stores/{vector_store_id}",
                headers=self.headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting vector store: {e}")
            return None
    
    def create_vector_store(self, name: str = "OptiBot-Articles") -> str:
        """
        Create a new vector store.
        
        Args:
            name: Name of the vector store
            
        Returns:
            Vector store ID
        """
        try:
            logger.info(f"Creating vector store: {name}")
            response = requests.post(
                f"{self.base_url}/vector_stores",
                headers=self.headers,
                json={"name": name}
            )
            response.raise_for_status()
            vs = response.json()
            logger.info(f"Created vector store: {vs['id']}")
            return vs["id"]
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise
    
    def upload_files_to_vector_store(self, file_paths: List[str], vector_store_id: str) -> dict:
        """
        Upload files to vector store.
        
        Args:
            file_paths: List of markdown file paths
            vector_store_id: Target vector store ID
            
        Returns:
            Summary with file IDs and status
        """
        summary = {
            "total": len(file_paths),
            "successful": 0,
            "failed": 0,
            "file_ids": [],
            "errors": []
        }
        
        logger.info(f"Uploading {len(file_paths)} files to vector store...")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                # Upload file
                with open(file_path, 'rb') as f:
                    files = {"file": f}
                    upload_response = requests.post(
                        f"{self.base_url}/files",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files,
                        data={"purpose": "assistants"}
                    )
                upload_response.raise_for_status()
                file_obj = upload_response.json()
                file_id = file_obj["id"]
                
                # Add file to vector store
                vs_response = requests.post(
                    f"{self.base_url}/vector_stores/{vector_store_id}/files",
                    headers=self.headers,
                    json={"file_id": file_id}
                )
                vs_response.raise_for_status()
                
                summary["successful"] += 1
                summary["file_ids"].append(file_id)
                logger.info(f"  [{i}/{len(file_paths)}] {file_path}")
                
            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append(f"{file_path}: {str(e)}")
                logger.warning(f"  [{i}/{len(file_paths)}] {file_path}: {e}")
                continue
        
        logger.info(f"\nUpload complete: {summary['successful']}/{summary['total']} successful")
        return summary
    
    def wait_for_vector_store_processing(self, vector_store_id: str, max_wait: int = 300):
        """
        Wait for vector store to finish processing files.
        
        Args:
            vector_store_id: Vector store ID
            max_wait: Maximum seconds to wait
        """
        logger.info("Waiting for vector store to process files...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{self.base_url}/vector_stores/{vector_store_id}",
                headers=self.headers
            )
            response.raise_for_status()
            vs = response.json()
            
            file_counts = vs.get("file_counts", {})
            if file_counts.get("completed", 0) > 0:
                logger.info(f"Processing complete!")
                logger.info(f"   • Files processed: {file_counts.get('completed', 0)}")
                logger.info(f"   • Files failed: {file_counts.get('failed', 0)}")
                logger.info(f"   • Files cancelled: {file_counts.get('cancelled', 0)}")
                return file_counts
            
            elapsed = int(time.time() - start_time)
            logger.info(f"   Status: {file_counts.get('in_progress', 0)} in progress, {file_counts.get('completed', 0)} completed... ({elapsed}s)")
            time.sleep(5)
        
            logger.warning(f"Vector store processing timeout after {max_wait}s")
        return None
    
    def list_assistants(self) -> List[dict]:
        """
        List all assistants.
        
        Returns:
            List of assistant objects
        """
        try:
            response = requests.get(
                f"{self.base_url}/assistants",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Error listing assistants: {e}")
            raise
    
    def get_assistant(self, assistant_id: str) -> Optional[dict]:
        """
        Get a specific assistant by ID.
        
        Args:
            assistant_id: Assistant ID
            
        Returns:
            Assistant object or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/assistants/{assistant_id}",
                headers=self.headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting assistant: {e}")
            return None
    
    def create_assistant(self, name: str = "OptiBot", instructions: str = "", 
                        vector_store_id: str = "", model: str = "gpt-4o-mini") -> str:
        """
        Create an Assistant with Vector Store.
        
        Args:
            name: Assistant name
            instructions: System prompt/instructions
            vector_store_id: Vector store to attach
            model: Model to use
            
        Returns:
            Assistant ID
        """
        try:
            logger.info(f"Creating assistant: {name}")
            
            payload = {
                "name": name,
                "instructions": instructions,
                "model": model,
                "tools": [{"type": "file_search"}],
                "tool_resources": {
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/assistants",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            assistant = response.json()
            logger.info(f"Created assistant: {assistant['id']}")
            return assistant["id"]
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise
