# Local development with Docker Compose Gateway

This guide shows how to run the Edgar‑AI LLM‑Gateway and CLI in Docker Compose for a consistent local dev loop that mirrors CI and production.

## Prerequisites

- Docker & Docker Compose (v1.27+ or Compose v2)
- Python 3.11 on your host
- A `.env` file at the repo root, with:

  ```dotenv
  # .env (gitignored)
  EDGAR_AI_OPENAI_API_KEY=sk-...
  EDGAR_AI_LLM_GATEWAY_URL=http://localhost:9000
  ```

- (Optional) Python virtualenv for the CLI:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```

---

## 1. Start the LLM‑Gateway container

```bash
# Build & launch only the Gateway service on port 9000
docker compose up -d llm-gateway

	# (Optional) Tail its logs in a separate terminal
	docker compose logs -f llm-gateway
	```

	```bash
	# Confirm gateway container is running
	docker compose ps llm-gateway

	# Quick smoke test (if exposed)
	curl http://localhost:9000/health || echo "(health endpoint not present)"
	```

The Gateway now proxies `/v1/chat/completions` calls to your LLM provider.

---

## 2. Run the Edgar‑AI extract CLI

```bash
# Extract single exhibit file with verbose logging
python -m edgar_ai.cli extract /path/to/file.txt --verbose --reset-memory

# Or extract all exhibits under a directory (HTML/HTM/TXT files)
python -m edgar_ai.cli extract /path/to/exhibits/ --verbose --reset-memory
```

To record raw LLM traffic, add `--record-llm`:

```bash
python -m edgar_ai.cli extract path/to/file.txt --verbose --reset-memory --record-llm
```

---

## 3. Hot‑reload the Gateway for edits

```bash
# Stop the container if running
docker compose stop llm-gateway

# Launch with reload for code changes
uvicorn edgar_ai.gateway.server:app --reload --port 9000

# Restore the container afterwards
docker compose up -d llm-gateway
```

---

## 4. Inspect audit artifacts

All files live under your Edgar‑AI data dir (`~/.edgar_ai`):

```bash
# Schema history
cat ~/.edgar_ai/memory.json

# Prompts & extracted rows
ls ~/.edgar_ai/prompts ~/.edgar_ai/rows

# Raw LLM traffic if recorded
ls ~/.edgar_ai/llm-traffic/requests ~/.edgar_ai/llm-traffic/responses
```

---

## 5. Manage stored schemas

```bash
python -m edgar_ai.cli schemas list
python -m edgar_ai.cli schemas show schema_1
python -m edgar_ai.cli schemas delete schema_1
```

---

## 6. Tear down

```bash
docker compose down
```