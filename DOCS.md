Edgar‑AI Documentation Index (Archived Snapshot)

These are the “old docs that spelled everything out,” preserved under `./.docs/`. Use this index to browse them quickly or copy them into a new repository when starting fresh.

Sections

- Specs (vision and core design)
  - North‑Star: `./.docs/specs/north-star.md`
  - Architecture: `./.docs/specs/architecture.md`
  - Personas: `./.docs/specs/personas.md`
  - Persona execution plan: `./.docs/specs/persona_execution_plan.md`
  - Goal alignment: `./.docs/specs/goal_alignment.md`
  - Hebbia method: `./.docs/specs/hebbia_method.md`

- Guides (how‑tos and setup)
  - Overview: `./.docs/guides/overview.md`
  - Quickstart: `./.docs/guides/quickstart.md`
  - Development: `./.docs/guides/development.md`
  - Configuration: `./.docs/guides/configuration.md`
  - Gateway: `./.docs/guides/gateway.md`
  - Goal‑Setter best practices: `./.docs/guides/goal_setter_best_practices.md`
  - Goal‑Setter LLM memory: `./.docs/guides/goal_setter_llm_memory.md`

- Pipeline (mechanics and evolution)
  - Schema evolution: `./.docs/pipeline/schema_evolution.md`
  - Critic → schema refinement: `./.docs/pipeline/critic_schema_refinement.md`
  - Pipeline fork & merge: `./.docs/pipeline/pipeline_fork_merge.md`
  - Referee merge strategy: `./.docs/pipeline/referee_merge_strategy.md`
  - EX‑10 routing & learning: `./.docs/pipeline/ex10_routing_and_learning.md`
  - Exhibit type vs goal: `./.docs/pipeline/exhibit_type_vs_goal.md`

- ADRs (former tickets)
  - `./.docs/adr/` (DISC‑01_..., TST‑01_..., etc.)

Also present (local, visible):

- v2 architecture notes: `./docs/architecture_v2.md`
- v2 migration guide: `./docs/migration_to_v2.md`

Copying these into a new repo

1) Export a bundle of the canonical doc set:
   - `zip -r edgar_docs_export.zip .docs/specs .docs/guides .docs/pipeline .docs/adr .docs/README.md .docs/README.txt docs/architecture_v2.md docs/migration_to_v2.md`

2) In your fresh repo:
   - Create a `docs/` directory and unzip: `unzip ../edgar_docs_export.zip -d docs_archive/`
   - Optionally promote key files (North‑Star, Overview, Architecture, Quickstart) into top‑level `docs/` and add a root `NORTH_STAR.md` that links to them.
