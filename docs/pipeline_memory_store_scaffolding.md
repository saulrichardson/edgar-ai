### 2. Pipeline & Memory‑Store scaffolding (LLM‑only orchestration)

Earlier we sketched out how to:

* Define a `MemoryStore` interface (in‑memory implementation + swap‑out hook).
* Wire up a top‑level `Pipeline` (orchestrating Goal‑Setter → Memory → Extractor).
* Hook the LLM‑only “choose_schema” step into that pipeline.
* Stub out `extractor` so you can smoke‑test the flow before filling in that piece.
