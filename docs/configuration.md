# Configuration reference

Edgar-AI reads settings from **environment variables** via
pydantic-settings.  Each variable is prefixed `EDGAR_AI_`.  You may also place
them in a local `.env` file.

| Name | Default | Description |
|------|---------|-------------|
| `OPENAI_API_KEY` | – | Forwarded to the Gateway when `LLM_PROVIDER=openai`. |
| `LLM_GATEWAY_URL` | `None` | Override the default `https://api.openai.com/v1/chat/completions` target with a self-hosted gateway. |
| `BATCH_SIZE` | `8` | How many documents the Extractor feeds into the LLM in one call. |
| `MODEL_GOAL_SETTER` | `o4-mini` | Small, cheap model good enough for setting objectives. |
| `MODEL_EXTRACTOR` | `gpt-4.1` | Heavy hitter – change if you want cheaper bills. |
| `GOAL_SETTER_TEMPERATURE` | `0.8` | | 
| `EXTRACTOR_MAX_RETRIES` | `3` | Automatic retries for transient gateway errors. |
| `SIMULATE` | `false` | If `true` the `edgar_ai.llm` layer returns canned answers – perfect for unit tests. |

To discover *all* settings open `src/edgar_ai/config.py` – the list is
self-documenting and guaranteed to be current.

