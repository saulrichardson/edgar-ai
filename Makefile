PYTHON ?= python3

.PHONY: help setup install install-dev lock lint format typecheck test run-gateway cli pre-commit

help:
	@echo "Common tasks:"
	@echo "  make setup         # Install dev deps (uv if available, else pip)"
	@echo "  make lint          # Ruff lint"
	@echo "  make format        # Ruff format"
	@echo "  make typecheck     # Mypy type checking"
	@echo "  make test          # Run pytest"
	@echo "  make run-gateway   # Start FastAPI gateway (dev)"
	@echo "  make cli           # Show CLI help"
	@echo "  make pre-commit    # Install pre-commit hooks"

setup: install-dev pre-commit

install:
	@if command -v uv >/dev/null 2>&1; then \
	  echo "Using uv"; \
	  uv sync; \
	else \
	  echo "Using pip"; \
	  $(PYTHON) -m pip install -U pip; \
	  $(PYTHON) -m pip install -e .; \
	fi

install-dev:
	@if command -v uv >/dev/null 2>&1; then \
	  echo "Using uv (with dev + gateway extras)"; \
	  uv sync --all-extras --group dev; \
	else \
	  echo "Using pip"; \
	  $(PYTHON) -m pip install -U pip; \
	  $(PYTHON) -m pip install -e .[gateway,dev]; \
	fi

lint:
	ruff check

format:
	ruff format

typecheck:
	@if [ -d src ]; then \
	  mypy src; \
	else \
	  echo "No src/ directory to typecheck (docs-only)"; \
	fi

test:
	pytest

run-gateway:
	@if [ -f src/gateway/app/main.py ]; then \
	  uvicorn gateway.app.main:app --reload; \
	else \
	  echo "Gateway app not present (docs-only)"; \
	fi

cli:
	@if [ -f src/cli/commands.py ]; then \
	  $(PYTHON) -m cli --help || true; \
	else \
	  echo "CLI not present (docs-only)"; \
	fi

pre-commit:
	@if command -v pre-commit >/dev/null 2>&1; then \
	  pre-commit install; \
	else \
	  echo "Install pre-commit: pip install pre-commit"; \
	fi
