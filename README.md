# Home Test Readme

> Zendesk Help Center scraper → OpenAI vector store uploader. Runs once, exits 0.

## Run Locally

### Option 1: Python (requires setup)

1. Setup:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure env:

   ```bash
   cp .env.sample .env
   # Set OPENAI_API_KEY=... (required)
   # Optional: add SPACES_* keys for remote state/logs
   ```

3. Run:
   ```bash
   python -m src.jobs.main
   ```
   Reads `.env` file; writes state/logs to `data/`.

### Option 2: Docker (no setup or .env file needed)

```bash
docker build -t optibot:latest .
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY optibot:latest
```

With local persistence (articles & state survive container):

```bash
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY -v $(pwd)/data:/app/data optibot:latest
```

## Deploy as Daily DigitalOcean Job

- Push image: `docker push registry.digitalocean.com/hometest/optibot:latest`.
- Job command: `python -m src.jobs.main`.
- Set envs in DO: at least `OPENAI_API_KEY`; add `SPACES_*` for remote state/logs.
- Daily log (Spaces CDN): https://hometest.sfo3.cdn.digitaloceanspaces.com/logs/run.log

## Repo Hygiene

- Keep secrets out of git; `.env.sample` lists required keys.
- Repo name is intentionally non-obvious; no hard-coded keys.

## Screenshot

![Playground answer](assets/hometest-result.jpeg)
