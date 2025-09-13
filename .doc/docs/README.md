Edgar-AI Documentation
======================

Welcome to the **Edgar-AI** knowledge base.  This folder is intentionally
light-weight: every page should be directly actionable for somebody who wants
to *run, modify, or extend* the latest “AI-forward” version of the pipeline.

If you remember one rule, remember this one:

> 📌  **The code is always the source-of-truth.**  Docs exist only to explain
>     *why* the code is the way it is, or *how* to interact with it at the
>     highest level.  Whenever the code and the docs diverge, fix the docs (or
>     delete them) – never add work-arounds in code to keep an outdated doc
>     alive.

Table of Contents
-----------------

Core concepts & architecture

| Document | Purpose |
|----------|---------|
| [`overview.md`](overview.md) | Two-minute tour of what Edgar-AI does and the core ideas that drive it. |
| [`architecture.md`](architecture.md) | Deep dive into the self-evolving, LLM-first design – component graph, data flow, autonomy loop. |
| [`personas.md`](personas.md) | Behavioural contract of every *persona* (Goal-Setter, Extractor, Critic, …). |

Day-to-day usage

| Document | Purpose |
|----------|---------|
| [`quickstart.md`](quickstart.md) | Install, configure an API key, run your first extraction. |
| [`gateway.md`](gateway.md) | How the FastAPI Gateway works, environment variables, request recording. |
| [`configuration.md`](configuration.md) | All `EDGAR_AI_*` knobs in one place with sane defaults. |

Contributor guides

| Document | Purpose |
|----------|---------|
| [`development.md`](development.md) | Local dev loop, tests, pre-commit, debugging tips. |

Historical / research notes
---------------------------

Papers, design experiments, or one-off strategy docs live under
[`archive/`](archive/).  They are **not** guaranteed to be up-to-date but are
preserved for posterity.


Versioning policy
-----------------

The documentation follows **rolling release** semantics: pages are updated as
soon as a feature lands on `main`.  There are no versioned snapshots.  If you
are running an older tag, pin the commit hash and read the docs from that
point in history via GitHub’s UI.


Contributing to the docs
------------------------

1. Keep prose concise; link to code for implementation details.
2. Prefer deleting outdated content over tweaking it – dead text costs real
   attention.
3. Open a normal pull request.  The CI job will spell-check Markdown and build
   the table of contents.

