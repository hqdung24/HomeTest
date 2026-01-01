"""Configuration and constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (only OPENAI_API_KEY)
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Directories
DATA_DIR = PROJECT_ROOT / "data"
ARTICLES_DIR = DATA_DIR / "articles"
STATE_FILE = DATA_DIR / "state.json"

# Zendesk 
ZENDESK_SUBDOMAIN = "support.optisigns"
ZENDESK_API_KEY = None  # Not required for public Help Center

# OpenAI 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

# DigitalOcean Spaces (S3-compatible)
SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT")
SPACES_REGION = os.getenv("SPACES_REGION")
SPACES_BUCKET = os.getenv("SPACES_BUCKET")
SPACES_KEY = os.getenv("SPACES_KEY")
SPACES_SECRET = os.getenv("SPACES_SECRET")
SPACES_STATE_KEY = os.getenv("SPACES_STATE_KEY", "state/state.json")
SPACES_LOG_PREFIX = os.getenv("SPACES_LOG_PREFIX", "logs/")
SPACES_ARTIFACT_PREFIX = os.getenv("SPACES_ARTIFACT_PREFIX", "artifacts/")

SPACES_ENABLED = all([
	SPACES_ENDPOINT,
	SPACES_REGION,
	SPACES_BUCKET,
	SPACES_KEY,
	SPACES_SECRET,
])

# System Prompt for OptiBot
SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply."""

# Scraper settings
MIN_ARTICLES = 30
CHUNK_SIZE = 1024  # tokens
