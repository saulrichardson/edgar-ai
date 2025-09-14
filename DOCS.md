Edgar‑AI Documentation Index (Archived Snapshot)

These are the “old docs that spelled everything out,” preserved in this repo under `./.doc/main/`. Use this index to browse them quickly or copy them into a new repository when starting fresh.

Core docs (./.docs):

- North‑Star: `./.docs/northstar_spec.md`
- Overview: `./.docs/overview.md`
- Architecture: `./.docs/architecture.md`
- Quickstart: `./.docs/quickstart.md`
- Development guide: `./.docs/development.md`
- Configuration: `./.docs/configuration.md`
- Gateway: `./.docs/gateway.md`
- Personas: `./.docs/personas.md`
- Persona execution plan: `./.docs/persona_execution_plan.md`
- Goal alignment: `./.docs/goal_alignment.md`
- Goal‑Setter best practices: `./.docs/goal_setter_best_practices.md`
- Goal‑Setter LLM memory: `./.docs/goal_setter_llm_memory.md`
- Schema evolution: `./.docs/schema_evolution.md`
- Critic → schema refinement: `./.docs/critic_schema_refinement.md`
- Referee merge strategy: `./.docs/referee_merge_strategy.md`
- Pipeline fork & merge: `./.docs/pipeline_fork_merge.md`
- EX‑10 routing & learning: `./.docs/ex10_routing_and_learning.md`
- Exhibit type vs goal: `./.docs/exhibit_type_vs_goal.md`
- Hebbia method: `./.docs/hebbia_method.md`

Tickets (./.docs/tickets):

- DISC‑01 FieldCandidate extension: `./.docs/tickets/DISC-01_FieldCandidate_extension.md`
- DISC‑02 GoalAware Discoverer: `./.docs/tickets/DISC-02_GoalAware_Discoverer.md`
- DOC‑01 Update Docs: `./.docs/tickets/DOC-01_Update_Docs.md`
- INT‑01 Orchestrator Wiring: `./.docs/tickets/INT-01_Orchestrator_Wiring.md`
- MEM‑01 GoalHash Lookup: `./.docs/tickets/MEM-01_GoalHash_Lookup.md`
- PRE‑01 PreCritic Pipeline Improvements: `./.docs/tickets/PRE-01_PreCritic_Pipeline_Improvements.md`
- SCH‑01 MultiVariant SchemaSynth: `./.docs/tickets/SCH-01_MultiVariant_SchemaSynth.md`
- SCH‑02 Update schema_variants glue: `./.docs/tickets/SCH-02_Update_schema_variants_glue.md`
- TST‑01 New Unit Tests: `./.docs/tickets/TST-01_New_Unit_Tests.md`
- TYP‑05 LLM Sample Values: `./.docs/tickets/TYP-05_LLMSampleValues.md`

Also present (local, visible):

- v2 architecture notes: `./docs/architecture_v2.md`
- v2 migration guide: `./docs/migration_to_v2.md`

Copying these into a new repo

1) Export a bundle of the canonical doc set:
   - `zip -r edgar_docs_export.zip .doc/main/docs .doc/main/tickets .doc/main/README.md .doc/README.txt docs/architecture_v2.md docs/migration_to_v2.md`

2) In your fresh repo:
   - Create a `docs/` directory and unzip: `unzip ../edgar_docs_export.zip -d docs_archive/`
   - Optionally promote key files (North‑Star, Overview, Architecture, Quickstart) into top‑level `docs/` and add a root `NORTH_STAR.md` that links to them.
