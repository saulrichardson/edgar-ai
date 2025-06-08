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
