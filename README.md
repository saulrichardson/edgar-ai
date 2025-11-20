```text
                Raw HTML Filing
                         |
                         v
                    Intake
                         |
                         v
                 Goal-Setter 
                         | 
                         v
              +-- Memory: schema? --+
              |                      |
            yes                     no
              |                      |
              v                      v
  Prompt-Builder (warm)      Schema Evolution Engine
              |                      |
              +------ selected schema ------+
                                             v
                                      Prompt-Builder
                                             |
                                             v
                                         Extractor
                                             | 
                                             v
                                         Critic (LLM)
                                             | 
                                             v
                                           Tutor
                                             | 
                                             v
                                           Governor
                                             | 
                                             +--> Memory (learning loop)

    Breaker (adversarial docs) feeds synthetic edge cases into Intake ->
```

# Edgar-AI

**Automated, self-improving data extraction for SEC exhibits.**

Edgar-AI ingests raw filings, routes them through a set of specialized LLM personas, and returns structured, auditable data. Each persona owns a single contract—goal setting, schema design, extraction, critique, remediation, or adversarial testing—so the pipeline can keep improving without retraining foundation models.

## Workflow

1. **Goal-Setter** reads the filing, chooses the most valuable analytical objective, and emits a compact goal blueprint.
2. **Memory lookup** checks for an existing schema keyed by the goal. If found, the pipeline jumps straight to extraction.
3. **Schema Evolution Engine** generates or revises schemas when no champion exists for the goal.
4. **Prompt-Builder** converts the active schema into a deterministic extraction prompt, including JSON schema fragments when needed.
5. **Extractor** runs the prompt against the exhibits and produces rows with cell-level provenance.
6. **Critic** rereads the document, scores each cell, and attaches structured feedback.
7. **Tutor** converts critic findings into challenger prompts or schema updates.
8. **Governor** decides whether challenger artifacts replace the current champion.
9. **Breaker** introduces adversarial documents that harden the pipeline before production filings shift.

## Design Principles

- **Observability-first schemas** ensure every field can be justified from the source document, reducing hallucinations.
- **Normal-form modelling** keeps schemas composable and scalable as new concepts appear.
- **Critic–Tutor feedback** provides objective scores that drive prompt and schema evolution.
- **Champion–Challenger governance** prevents regressions by requiring challengers to beat the current champion.

## Personas At A Glance

| Persona | Contract | Status |
|---------|----------|--------|
| Goal-Setter | `List[Document]` -> goal blueprint | ✅ production |
| Discoverer | Documents -> field candidates | 🏗️ experimental |
| Schema-Synth | Candidates -> JSON Schema | 🏗️ experimental |
| Prompt-Builder | Goal + Schema -> prompt payload | ✅ production |
| Extractor | Prompt + Docs -> rows | ✅ production |
| Schema-Critic | Schema + excerpts -> critiques | ✅ production |
| Critic (row-level) | Rows -> graded notes | 🏗️ proof-of-concept |
| Tutor | Critic notes -> challenger plan | 💤 stub |
| Governor | Rows + notes -> decision | 💤 stub |
| Breaker | Champion prompt -> adversarial cases | 💤 stub |

## Next Steps

- Start with the `src/edgar_ai/services/` modules to see how personas integrate with the orchestration code.
- Use the CLI entry points under `src/edgar_ai/cli/` for local runs; set `EDGAR_AI_SIMULATE=1` for deterministic stubs.
- Record LLM traffic with `--record-llm` to capture request/response payloads for debugging.

