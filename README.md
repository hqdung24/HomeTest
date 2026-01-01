# cryptic-repo-name

A Python-based system for scraping Zendesk articles and uploading them to OpenAI vector store.

## Project Structure

```
cryptic-repo-name/
├─ src/
│  ├─ scraper/          # Zendesk scraping logic
│  ├─ openai/           # OpenAI vector store integration
│  ├─ jobs/             # Main job entrypoint
│  └─ utils/            # Utility functions
├─ data/
│  ├─ articles/         # Generated markdown files
│  └─ state.json        # Hash tracking
├─ scripts/
│  └─ run_local.py      # Local development helper
└─ Configuration files
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.sample .env
# Zendesk: No auth needed! Using public Help Center API
# Only add OPENAI_API_KEY from https://platform.openai.com/api-keys
```

### 4. Test Zendesk Connection

```bash
source .venv/bin/activate
python scripts/test_zendesk.py
```

Expected output: 50 articles fetched from support.optisigns.com/hc/en-us

### 5. Run Locally

```bash
python scripts/run_local.py
```

## Docker Deployment

Build and run with Docker:

```bash
docker build -t cryptic-repo .
docker run cryptic-repo
```

## API Configuration

- **Zendesk**: Add your API key and subdomain to `.env`
- **OpenAI**: Add your OpenAI API key to `.env`

## Development

Each module is organized by functionality:

- `scraper/`: Handles Zendesk API calls and article storage
- `openai/`: Vector embeddings and storage
- `jobs/`: Orchestration and main execution
- `utils/`: Shared utilities (slugs, hashing, logging)
