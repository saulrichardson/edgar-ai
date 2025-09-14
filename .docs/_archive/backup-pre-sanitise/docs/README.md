# Edgar-AI Documentation Index

This folder captures design notes, architectural sketches, and decision logs.
Each file is *immutable history*—we rarely delete content, but when a document
becomes obsolete its ideas are either folded into the codebase or replaced by
a newer note (the old file is then removed to avoid confusion).

| File | Purpose |
|------|---------|
| **architecture.md** | End-to-end overview of the self-evolving, LLM-first architecture. |
| **critic_schema_refinement.md** | Concept note on how the Critic/Tutor loop detects over- vs under-compression in schemas. |
| **ex10_routing_and_learning.md** | Explains how the pipeline learns to specialise for heterogeneous EX-10 contracts *without* hand-coded routers. |
| **exhibit_type_vs_goal.md** | Rationale for ignoring SEC exhibit type and letting the Goal-Setter decide objectives. |
| **goal_alignment.md** | Describes deduplication of goals via embedding similarity & ontology alignment. |
| **goal_setter_best_practices.md** | Practical tips for prompt iteration, golden-file tests, and CLI flags. |
| **goal_setter_llm_memory.md** | Design for storing/retrieving multiple schema records using only LLM reasoning (no embeddings). |
| **northstar_spec.md** | The original project “North-Star” manifesto—moved here from the repo root for archival. |
| **pipeline_fork_merge.md** | How the pipeline forks objectives when Critic detects a mismatch, and later re-merges. |
| **referee_merge_strategy.md** | Pros/cons of a “merge-then-referee” variant selection flow and a hybrid fallback strategy. |
| **schema_evolution.md** | Mechanism for automatically promoting new concepts into official schemas over time. |

---

### Removed / merged files

• `pipeline_memory_store_scaffolding.md` – scaffolding now fully implemented.<br>
• `schema_merge_referee.md` – superseded by `referee_merge_strategy.md`.

---

If you add a new design note, please:
1. Use a brief, lower-case, hyphenated filename.
2. Update the table above with a single-line purpose.
3. Keep the **docs** folder focused on high-level reasoning and decisions, not code-level HOW-TOs (those belong in inline comments or module docstrings).
