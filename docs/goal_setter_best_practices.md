# Goal-Setter: Best Practices for Prompt Iteration & Pipeline Robustness

This document captures recommended steps to refine and maintain the Goal‑Setter component,
ensuring a repeatable prompt‑engineering workflow and robust JSON‑schema enforcement.

## 1. Prompt Playground (`--show-prompt` CLI flag)

Enable rapid experimentation by previewing the composed system + user messages without consuming retries.

- Add a `--show-prompt` flag to the `edgar_ai.cli goal` command.
- When passed, print the LLM payload (system and user messages) and exit.
- Example:
  ```bash
  edgar-ai goal path/to/exhibit.txt --show-prompt
  ```

## 2. Golden-File Tests for Prompt Stability

Guard against unintended prompt changes by locking down known-good outputs.

- Store representative exhibit inputs in `tests/fixtures/`.
- For each, add a corresponding expected JSON in `tests/fixtures/expected_goal_outputs/`.
- Write a parametrized pytest that reads each input, runs `goal_setter.run()`, and compares against the golden JSON.

## 3. Formalize the JSON Schema with Pydantic

Centralize key/type validation and generate self-documenting contracts.

```python
from pydantic import BaseModel, Field, conlist

class GoalSchema(BaseModel):
    overview: str = Field(..., description="Up to 10 sentences on extraction purpose")
    topics: conlist(str, min_items=1) = Field(..., description="Thematic areas to cover")
    fields: conlist(str, min_items=1) = Field(..., description="snake_case field names to extract")
```

Replace ad-hoc checks in `goal_setter.run()` with:
```python
goal_obj = GoalSchema(**goal)
return goal_obj.dict()
```

## 4. Surface Metrics and Telemetry

Measure model obedience, retry overhead, and overview length to inform prompt tweaks.

- Track counters for total calls and retries per attempt.
- Record timers or histograms for overview token/word counts.
- Use your existing metrics/logging stack (e.g. StatsD, Prometheus, or custom).

## 5. Update Documentation & README

Keep docs in sync with code changes and prompt guidelines:

- Document the `--show-prompt` flag in the CLI section.
- Update the JSON schema contract (keys/types and 10-sentence overview).
- Note any new environment variables (e.g. `EDGAR_AI_GOAL_SETTER_MAX_RETRIES`).

## 6. Iterate on Real-World Samples

Refine the prompt and schema by batch-running on representative exhibits:

1. Run the Goal‑Setter on a diverse sample set.
2. Inspect raw & parsed outputs via the playground or golden tests.
3. Adjust prompt phrasing to improve coverage, conciseness, and schema completeness.
4. Repeat until the outputs consistently meet quality criteria.