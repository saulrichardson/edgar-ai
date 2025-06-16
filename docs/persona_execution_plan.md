# Roadmap: Implementing the Remaining Personas

The pipeline’s first five personas (Goal‑Setter → Field‑Discoverer → Schema‑Synthesizer → Prompt‑Writer → Extractor) are live and fully automated.  The final four personas (Critic, Tutor, Governor, Breaker) complete the *feedback* and *adversarial* loops that drive continuous improvement.

Below is a prioritized plan for designing, building, and rolling out each persona.

---

## 1. Critic – Automated Quality Scoring

**Objective:** Grade each extracted row (cell‑level and row‑level) and flag failures.

**Steps (AI‑forward):**
1. **Autogenerate evaluation rubric via LLM.** Prompt the LLM to produce JSON error codes, severities, and scoring guidelines based on the schema and sample exhibits.
2. **Generate synthetic test cases.** Ask the LLM to craft representative row examples paired with expected scores (CriticNotes) as golden tests.
3. **Implement Critic service.** Build `edgar_ai.services.critic` to submit extracted rows + rubric to the gateway and parse structured `CriticNote` responses.
4. **Integrate into pipeline.** Invoke Critic post‑extraction; record failures with `memory.save_error_record()` and log summary metrics.

---

## 2. Tutor – Challenger Prompt Generation

**Objective:** Rewrite or refine the schema/prompt when Critic notes accumulate.

**Steps:**
1. **Aggregate failures.** Group CriticNotes by schema + document subset needing improvement.
2. **Draft tutor prompt.** Guide the LLM to suggest challenger prompts or schema tweaks that address failures.
3. **Implement Tutor service.** Develop `edgar_ai.services.tutor` that returns candidate prompt patches.
4. **Version challenger prompts.** Snapshot new prompts alongside existing ones for A/B comparison.
5. **Golden‑file tests.** Validate that Tutor output matches expected rewrite guidelines.

---

## 3. Governor – Champion‑Challenger Promotion

**Objective:** Automatically decide when a challenger prompt/schema should supplant the champion.

**Steps:**
1. **Define promotion logic.** Formalize criteria (Δ critic score threshold, field overlap).
2. **Draft governor prompt (optional).** Or implement rule‑based checks in code.
3. **Implement Governor service.** Build `edgar_ai.services.governor` to compare scores and emit `GovernorDecision`.
4. **Integrate promotion.** If governor approves, mark schema/prompt as new champion and trigger back‑fill.
5. **Tests & metrics.** Write unit tests for decision logic; capture metrics on promotions.

---

## 4. Breaker – Adversarial Test Generation

**Objective:** Generate synthetic filings that surface edge‑case prompt/schema failures.

**Steps:**
1. **Identify target failure modes.** List Critic error categories to adversarially target.
2. **Draft breaker prompt.** Instruct LLM to generate minimal filings likely to cause failures.
3. **Implement Breaker service.** Create `edgar_ai.services.breaker` yielding synthetic exhibits.
4. **Feed into pipeline.** Route breaker outputs back to Goal‑Setter for schema isolation and hardening.
5. **Evaluation tests.** Verify synthetic docs trigger expected CriticNotes and schema branches.

---

Updating this roadmap as each persona moves from STUB/NOP to fully LLM‑driven ensures we achieve a self‑evolving pipeline with zero manual interventions beyond the two human touch‑points.