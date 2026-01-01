"""Reset local data and OpenAI resources for OptiBot."""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
# Load environment from project .env before importing config
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

# Make src importable and pull shared config (paths, env)
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from config import STATE_FILE, ARTICLES_DIR, OPENAI_API_KEY  # type: ignore

OPENAI_BASE_URL = "https://api.openai.com/v1"
STATE_PATH = Path(STATE_FILE)


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read state file: {e}")
    return {
        "last_run": None,
        "total_articles": 0,
        "vector_store_id": None,
        "assistant_id": None,
        "articles": {}
    }


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def delete_openai_resource(headers: dict, resource: str, resource_id: str):
    url = f"{OPENAI_BASE_URL}/{resource}/{resource_id}"
    try:
        resp = requests.delete(url, headers=headers, timeout=15)
        if resp.status_code in (200, 204):
            logger.info(f"Deleted {resource} {resource_id}")
        elif resp.status_code == 404:
            logger.info(f"{resource} {resource_id} not found (already deleted)")
        else:
            logger.warning(f"Failed to delete {resource} {resource_id}: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"Error deleting {resource} {resource_id}: {e}")


def delete_all_files(headers: dict):
    """Delete all files in the OpenAI workspace via Files API."""
    total_deleted = 0
    
    try:
        # Get all files (simple approach - just fetch once)
        resp = requests.get(f"{OPENAI_BASE_URL}/files", headers=headers, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        files = payload.get("data", [])
        
        if not files:
            logger.info("No files found in OpenAI workspace")
            return
        
        logger.info(f"Found {len(files)} files to delete")
        
        for file_obj in files:
            file_id = file_obj.get("id")
            try:
                del_resp = requests.delete(f"{OPENAI_BASE_URL}/files/{file_id}", headers=headers, timeout=15)
                if del_resp.status_code in (200, 204):
                    total_deleted += 1
                elif del_resp.status_code == 404:
                    logger.info(f"File {file_id} not found (already deleted)")
                else:
                    logger.warning(f"Failed to delete file {file_id}: {del_resp.status_code}")
            except Exception as e:
                logger.warning(f"Error deleting file {file_id}: {e}")
        
        logger.info(f"Deleted {total_deleted} files from OpenAI workspace")
        
    except Exception as e:
        logger.warning(f"Error listing/deleting files: {e}")


def delete_articles_dir():
    if ARTICLES_DIR.exists():
        for md_file in ARTICLES_DIR.glob("*.md"):
            try:
                md_file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete {md_file}: {e}")
        logger.info(f"Cleared markdown files in {ARTICLES_DIR}")
    else:
        logger.info(f"Articles directory not found: {ARTICLES_DIR}")


def reset_state_file():
    new_state = {
        "last_run": None,
        "total_articles": 0,
        "vector_store_id": None,
        "assistant_id": None,
        "next_page_url": None,
        "articles": {}
    }
    save_state(new_state)
    logger.info("State file reset")


def reset_all():
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "assistants=v2"
    }

    state = load_state()
    vs_id = state.get("vector_store_id")
    asst_id = state.get("assistant_id")

    if vs_id:
        delete_openai_resource(headers, "vector_stores", vs_id)
    else:
        logger.info("No vector store ID in state")

    if asst_id:
        delete_openai_resource(headers, "assistants", asst_id)
    else:
        logger.info("No assistant ID in state")

    # Delete all files from OpenAI workspace
    delete_all_files(headers)

    delete_articles_dir()
    reset_state_file()
    logger.info("Reset complete")
    return True


if __name__ == "__main__":
    reset_all()
