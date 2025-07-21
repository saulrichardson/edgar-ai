.PHONY: venv install test run lint clean

# Path to virtual environment directory
VENV ?= .venv

activate = . $(VENV)/bin/activate

# Create the virtual-env *only if it doesn't already exist*.
$(VENV)/bin/activate:
	python3 -m venv --prompt edgar $(VENV)

venv: $(VENV)/bin/activate

install: venv ## Install project & deps into the existing venv
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

smoke: | venv ## Ping the LLM gateway and print short response
	PYTHONPATH=src $(activate) && python -m edgar_ai.smoke

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
