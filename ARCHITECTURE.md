# OptiBot Architecture

## Overview

OptiBot is an intelligent customer support assistant that scrapes articles from Zendesk, converts them to Markdown, and indexes them in OpenAI Vector Store for semantic search.

## Key Features

### 1. Single Vector Store & Assistant

- **One vector store** for the entire application (reused across all runs)
- **One assistant** configured with system prompt (reused across all runs)
- IDs stored in `data/state.json` for persistence

### 2. Incremental Updates

- **MD5-based change detection**: Only uploads new or modified articles
- **Delta sync**: On subsequent runs, only changed files are uploaded
- **Efficient**: Skips unchanged articles entirely

### 3. State Tracking

The `data/state.json` file tracks:

- `vector_store_id`: Persistent OpenAI vector store ID
- `assistant_id`: Persistent OpenAI assistant ID
- `articles`: Per-article metadata with MD5 hashes
- `last_run`: Timestamp of last successful run

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         Daily Job                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Scrape Articles from Zendesk                      │
│ • Fetch articles via API                                    │
│ • Convert HTML → Markdown                                   │
│ • Calculate MD5 hash                                        │
│ • Compare with stored hash                                  │
│ • Save if changed                                           │
│ • Track changed_files list                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Update Vector Store (only if changes)             │
│ • Load stored vector_store_id and assistant_id              │
│ • If exists, verify and reuse                               │
│ • If not exists, create new and save IDs                    │
│ • Upload only changed files to vector store                 │
│ • Wait for processing (chunking & embedding)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              OptiBot Ready in Playground                    │
│ https://platform.openai.com/playground                      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Article Store (`src/scraper/article_store.py`)

- Manages article state and file storage
- Methods:
  - `save_article()`: Save markdown file
  - `has_changed()`: Check if article changed via MD5
  - `get_vector_store_id()` / `set_vector_store_id()`: Persist vector store ID
  - `get_assistant_id()` / `set_assistant_id()`: Persist assistant ID

### 2. OpenAI Client (`src/openai_service/client.py`)

Uses REST API directly (not SDK) for:

- `list_vector_stores()`: List all vector stores
- `get_vector_store()`: Get specific vector store by ID
- `create_vector_store()`: Create new vector store
- `upload_files_to_vector_store()`: Upload files and add to vector store
- `wait_for_vector_store_processing()`: Poll until processing complete
- `list_assistants()`: List all assistants
- `get_assistant()`: Get specific assistant by ID
- `create_assistant()`: Create new assistant with vector store

### 3. OptiBot Orchestrator (`src/openai_service/upload_markdown.py`)

- `get_or_create_vector_store()`: Reuse if exists in state, create if not
- `get_or_create_assistant()`: Reuse if exists in state, create if not
- `upload_files()`: Upload specific files to vector store
- `run_full_setup()`: Complete setup with reuse logic

### 4. Main Job (`src/jobs/main.py`)

- Orchestrates complete pipeline
- Tracks changed files from scraper
- Only uploads changed files to vector store
- Skips upload if no changes detected

## Model & Performance

### Current Configuration

- **Model**: `gpt-4o-mini` (cost optimized)
- **Context Window**: 128K tokens
- **Pricing**: $0.15 (input) / $0.60 (output) per 1M tokens
- **Speed**: ~0.5-1s per response
- **Cost per query**: ~$0.004 (0.4¢)

### Model Comparison

| Model       | Input  | Output | Use Case                       |
| ----------- | ------ | ------ | ------------------------------ |
| gpt-4o-mini | $0.15  | $0.60  | **Current - best for budget**  |
| gpt-4o      | $2.50  | $10.00 | Higher quality, more expensive |
| gpt-4-turbo | $10.00 | $30.00 | Legacy (deprecated)            |

## Chunking Strategy

OpenAI automatically chunks files using the following strategy:

- **Chunk size**: ~800 tokens per chunk (default, ~3000 chars)
- **Chunk overlap**: ~400 tokens (for context continuity)
- **Structure preservation**: Markdown headers (H1, H2, H3), lists, and links preserved
- **Metadata**: Each file includes title, URL, and timestamp in header
- **Process**:
  1. Parse markdown structure
  2. Split by headers and paragraphs
  3. Combine into ~800 token chunks
  4. Create embeddings for each chunk
  5. Index in vector store

## System Prompt

```
You are OptiBot, the customer-support bot for OptiSigns.com.

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
• Always maintain a professional, helpful tone
```

## API Endpoints Used

### OpenAI REST API (v1)

All requests include headers:

- `Authorization: Bearer {api_key}`
- `OpenAI-Beta: assistants=v2`

Endpoints:

- `POST /vector_stores` - Create vector store
- `GET /vector_stores` - List vector stores
- `GET /vector_stores/{id}` - Get vector store details
- `POST /files` - Upload file
- `POST /vector_stores/{id}/files` - Add file to vector store
- `POST /assistants` - Create assistant
- `GET /assistants` - List assistants
- `GET /assistants/{id}` - Get assistant details

### Zendesk API (v2)

- `GET /api/v2/help_center/en-us/articles` - List articles
- `GET /api/v2/help_center/en-us/articles/{id}` - Get article content

## Running the Job

### Basic Usage

```bash
# Default: 50 articles, sequential (same articles each run)
python -m src.jobs.main --limit 50

# With randomization: fetches 100, selects random 50
python -m src.jobs.main --limit 50 --randomize

# Paginate: skip to page 2 (articles 51-100)
python -m src.jobs.main --limit 50 --start-page 2

# Sort by creation date
python -m src.jobs.main --limit 50 --sort-by created_at

# Combine: random 50 from page 2, sorted by title
python -m src.jobs.main --limit 50 --randomize --start-page 2 --sort-by title
```

### Available Options

```
--limit N              Number of articles (default: 50)
--randomize           Fetch 2x articles and select random subset
--start-page N        Start from page N (default: 1, each page = ~100 articles)
--sort-by FIELD       Sort by: updated_at, created_at, title, position
--skip-upload         Skip vector store upload phase (scraping only)
```

### First Run (Creates vector store & assistant)

```bash
python -m src.jobs.main --limit 50 --randomize
```

**What happens:**

1. Scrapes random 50 from ~100 Zendesk articles
2. Converts all to Markdown
3. Creates NEW vector store
4. Uploads all 50 files (chunking & embedding)
5. Creates NEW assistant (gpt-4o-mini)
6. Saves vector_store_id and assistant_id to state.json
7. **Time**: ~60 seconds

### Second Run (No changes)

```bash
python -m src.jobs.main --limit 50
```

**What happens:**

1. Scrapes articles from Zendesk
2. Compares MD5 hashes with stored state
3. Detects 0 changed files
4. **Skips upload entirely** (no API calls)
5. **Time**: ~2 seconds ⚡

### Run with Updates

```bash
# 2 articles updated on Zendesk
python -m src.jobs.main --limit 50
```

**What happens:**

1. Scrapes articles from Zendesk
2. Compares MD5 hashes
3. Detects 2 changed files
4. **Reuses existing vector_store_id**
5. **Uploads only 2 changed files** (delta sync)
6. **Reuses existing assistant_id**
7. **No duplicate resources created**
8. **Time**: ~35 seconds

## Benefits

✅ **Cost Efficient**: Only uploads changed files, avoids duplicate vector stores  
✅ **Fast**: Incremental updates instead of full re-index  
✅ **Stateless-Friendly**: All state in state.json, safe for Docker restarts  
✅ **Idempotent**: Can run multiple times safely, no duplicates  
✅ **Scalable**: Works with 50, 500, or 5000 articles

## Testing

### Test Reuse

```bash
python scripts/test_reuse.py
```

Verifies that vector_store_id and assistant_id are reused correctly.

### Test Full Pipeline

```bash
python -m src.jobs.main --limit 3
```

Quick test with 3 articles.

## Current Status

✅ **Production Ready**

- Vector Store: `vs_69553329d2fc81918ac8d1ea7aec5c20`
- Assistant: `asst_jutFwOrVvAVSwCjypbn1tTBc`
- Model: gpt-4o-mini
- Articles Indexed: 38 (26 chunks processed)
- Cost per query: $0.004 (0.4¢)

## Deployment

### Docker (Daily Job)

```bash
# Build image
docker build -t optibot .

# Run daily with randomization
docker run -e OPENAI_API_KEY=xxx \
  -v ./data:/app/data \
  optibot python -m src.jobs.main --limit 50 --randomize
```

### DigitalOcean App Platform

```yaml
# app.yaml
name: optibot
services:
  - name: optibot
    github:
      repo: your-repo/optibot
      branch: main
    build_command: pip install -r requirements.txt
    run_command: python -m src.jobs.main --limit 50 --randomize
    env:
      - key: OPENAI_API_KEY
        scope: RUN_AND_BUILD_TIME
        value: ${OPENAI_API_KEY}
    envs:
      - key: ZENDESK_SUBDOMAIN
        value: support.optisigns
crons:
  - name: daily-optibot
    command: python -m src.jobs.main --limit 50 --randomize
    schedule: '0 2 * * *' # 2 AM UTC daily
```

### State Persistence

State stored in `data/state.json`:

- Vector store ID (persists across runs)
- Assistant ID (persists across runs)
- Article MD5 hashes (enables delta sync)
- Last run timestamp

Mount as Docker volume:

```bash
docker run -v ./data:/app/data optibot
```
