# Development guide

This page explains the **inner loop**: edit → test → run.  It assumes you are
familiar with the code base (use [`overview.md`](overview.md) first).

Editable install
----------------

```bash
pip install -e ".[test]"
pre-commit install            # optional – runs lint & format automatically
```

Run the test suite
------------------

```bash
pytest -q
```

Right now the scaffold contains mostly integration tests driven by fixtures,
so the run is fast.

Simulate vs real LLM calls
--------------------------

* **Default** – hits the Gateway (or OpenAI) and costs money.
* **Simulate mode** – set `EDGAR_AI_SIMULATE=1` to stub out responses.  The
  canned answers live under `src/edgar_ai/llm/sim_stubs.py`.

Debugging
---------

* Add `--record-llm` to any CLI invocation to get full JSON transcripts.
* Use `rich.pretty` or `console.print_json` inside `ipython` to inspect
  `Row` / `Schema` objects.

Coding standards
---------------

* Black formatting + Ruff linting enforced by pre-commit.
* No mutable default args, no bare `except:`.
* Type check with `pyright` (optional but recommended).

Releasing
---------

* Bump `version` in `pyproject.toml`.
* `git tag vX.Y.Z && git push --tags` – CI will build and publish the wheel.  

