# LLM Gateway

The **Gateway** is a tiny FastAPI service that presents the exact same surface
as OpenAI’s `/v1/chat/completions` endpoint but lets Edgar-AI (or any other
client) inject provider-specific tweaks, capture traffic, or stub out calls in
development.

Run it locally
--------------

```bash
docker compose up -d llm-gateway   # port 9000
```

Environment variables honoured inside the container

| Variable | Meaning | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | Forwarded to the openai-python SDK | – |
| `LLM_PROVIDER`   | `openai` (only supported value today) | `openai` |

Request recording
-----------------

If the client sends header `X-EdgarAI-Record-Session: 1` the middleware will:

* write the raw JSON request under `~/.cache/edgar-ai/llm-traffic/requests/`
* write the JSON response under `~/.cache/edgar-ai/llm-traffic/responses/`

This is invaluable for prompt debugging and unit tests that snapshot the exact
model output.

Switching providers
-------------------

The Gateway was designed to support *any* chat-completion compliant backend
(Azure OpenAI, Fireworks, local models, …).  Wire-in another SDK, set
`LLM_PROVIDER`, and keep Edgar-AI completely oblivious.

