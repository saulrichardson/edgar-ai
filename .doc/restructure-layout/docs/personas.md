# Personas

Every logical “step” in the pipeline is modelled as a **persona** – an LLM
prompt with a clearly defined *contract* (inputs, outputs, and deterministic
behaviour expected from the surrounding code).  A persona is *not* a
monolithic prompt: teams are encouraged to experiment, multi-step reason, or
chain-of-thought internally as long as the I/O contract remains stable.

| Name | Input | Output | Implementation status |
|------|-------|--------|------------------------|
| Goal-Setter | `List[Document]` | GPT-generated objective string | ✅ production |
| Discoverer | `List[Document]` | List of field candidates (`name`, `description`, `rationale`) | 🏗️ experimental |
| Schema-Synth | Field candidates | JSON Schema object | 🏗️ experimental |
| Prompt-Builder | Goal + Schema | Extraction prompt | ✅ production |
| Extractor | Prompt + Docs | `List[Row]` | ✅ production |
| Schema-Critic | Schema + Exhibit excerpt | `List[SchemaCritique]` | ✅ production |
| Critic (row-level) | `List[Row]` | Graded notes | 🏗️ PoC |
| Tutor | Critic notes | Challenger prompt | 💤 stub |
| Governor | Rows + Notes | Decision enum | 💤 stub |
| Breaker | Champion prompt | Boolean pass/fail | 💤 stub |

Extending or replacing a persona
--------------------------------

1. Open the module under `src/edgar_ai/services/<persona>.py`.
2. Modify the call to `edgar_ai.llm.chat()` – that is *the* integration point.
3. Ensure the function signature and return type (usually a `pydantic`
   model) stays the same.

Debugging tips
--------------

* Use `EDGAR_AI_SIMULATE=1` to bypass real LLM calls and return deterministic
  canned answers.
* Pass `--record-llm` to the CLI to write request/response JSON under
  `~/.cache/edgar-ai/llm-traffic/` for inspection.
