.PHONY: venv install test run lint clean

# Path to virtual environment directory
VENV ?= .venv

activate = . $(VENV)/bin/activate

venv:
	python3 -m venv --prompt edgar $(VENV)

install: venv
	$(activate) && pip install --upgrade pip && pip install -e ".[test]"

test:
	$(activate) && pytest -q

# Usage: make run file=demo.html
run:
	@if [ -z "$(file)" ]; then echo "Usage: make run file=<HTML_PATH|->"; exit 1; fi
	$(activate) && python -m edgar_ai.cli run $(file)

lint:
	$(activate) && echo "(no linters configured yet)"

clean:
	rm -rf $(VENV)

# ---------------------------------------------------------------------------
# Convenience targets for the LLM Gateway & demo extraction pipeline
# ---------------------------------------------------------------------------

.PHONY: gateway-up gateway-down gateway-logs extract-sample


# Bring up the gateway container (rebuild to ensure latest code)
gateway-up:
	docker compose up -d --build llm-gateway

# Stop the gateway container
gateway-down:
	docker compose stop llm-gateway || true

# Tail gateway logs (Ctrl-C to detach)
gateway-logs:
	docker compose logs -f llm-gateway

# ---------------------------------------------------------------------------
# Smoke-test target: verifies .env URL and OpenAI key by calling the gateway.
# ---------------------------------------------------------------------------

.PHONY: smoke

smoke:  ## Ping the LLM gateway and print short response
	$(activate) && python - <<'PY'
	import sys, json, os
	from edgar_ai.config import settings
	from edgar_ai.llm import chat_completions
	
	print('Gateway URL:', settings.llm_gateway_url or '(not set)')
	
	try:
	    rsp = chat_completions(
	        model="o4-mini",
	        messages=[{"role": "system", "content": "You are a ping bot."}, {"role": "user", "content": "ping"}],
	        temperature=0.0,
	    )
	except Exception as exc:
	    print('Smoke-test FAILED:', exc)
	    sys.exit(1)
	
# Print first part of the reply to confirm success
	print('Gateway responded:', rsp["choices"][0]["message"]["content"][:80])
	PY

# ---------------------------------------------------------------------------
# Sample extraction convenience target
# ---------------------------------------------------------------------------
# Requires:
#   * gateway to be up ("make gateway-up")
#   * EDGAR_AI_OPENAI_API_KEY exported in the shell
# Sets EDGAR_AI_LLM_GATEWAY_URL for this invocation only.
extract-sample: gateway-up
	$(activate) && \
	  EDGAR_AI_LLM_GATEWAY_URL=http://localhost:9000 \
	  python -m edgar_ai.cli extract tests/fixtures/credit_agreement.txt --verbose --record-llm
