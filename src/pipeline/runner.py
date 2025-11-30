from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from clients.gateway import send_chat
from pipeline.config import load_gateway_config
from pipeline import models
from pipeline.context import ContextSpec, make_bundle
from pipeline.artifacts import PipelineState
from personas import registry


def _save(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_pipeline(
    exhibit_text: str,
    exhibit_id: str,
    goal_text: str | None = None,
    artifacts_dir: str | None = None,
    context_spec_goal: ContextSpec | None = None,
    context_spec_schema: ContextSpec | None = None,
    context_spec_extractor: ContextSpec | None = None,
    context_spec_critic: ContextSpec | None = None,
):
    gw = load_gateway_config()

    # Default: full context for all personas
    context_spec_goal = context_spec_goal or ContextSpec(mode="full")
    context_spec_schema = context_spec_schema or ContextSpec(mode="full")
    context_spec_extractor = context_spec_extractor or ContextSpec(mode="full")
    context_spec_critic = context_spec_critic or ContextSpec(mode="full")

    bundle_goal = make_bundle(exhibit_id, exhibit_text, context_spec_goal)
    bundle_schema = make_bundle(exhibit_id, exhibit_text, context_spec_schema)
    bundle_extractor = make_bundle(exhibit_id, exhibit_text, context_spec_extractor)
    bundle_critic = make_bundle(exhibit_id, exhibit_text, context_spec_critic)

    state = PipelineState(exhibit_id=exhibit_id)

    # Goal
    if goal_text is None:
        goal_out = send_chat(registry.render_messages(registry.goal_setter_spec, bundle_goal, state), gw)
        goal_text = goal_out.strip()
    state.goal_text = goal_text

    # Schema variants
    schema_raw = send_chat(registry.render_messages(registry.schema_synth_spec(goal_text), bundle_schema, state), gw)
    start = schema_raw.find("[")
    end = schema_raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Schema synth did not return JSON array")
    schemas = json.loads(schema_raw[start : end + 1])
    variants: List[models.SchemaVariant] = [models.SchemaVariant(**v) for v in schemas]
    state.schemas = variants

    variant_names: List[str] = []
    champion = None
    best_score = -1e9

    for variant in variants:
        vname = variant.variant
        variant_names.append(vname)

        prompt_text = send_chat(registry.render_messages(registry.prompt_builder_spec(variant), bundle_schema, state), gw)
        state.prompts[vname] = prompt_text

        extraction = send_chat(registry.render_messages(registry.extractor_spec(prompt_text), bundle_extractor, state), gw)
        state.extractions[vname] = extraction

        critique_raw = send_chat(registry.render_messages(registry.critic_spec(extraction), bundle_critic, state), gw)
        state.critiques[vname] = critique_raw

        try:
            c_start = critique_raw.find("[")
            c_end = critique_raw.rfind("]")
            c_data = json.loads(critique_raw[c_start : c_end + 1])
            crit_items = [models.CritiqueItem(**item) for item in c_data]
            crit = models.Critique(variant=vname, items=crit_items)
            score = crit.score
        except Exception:
            score = -999

        if artifacts_dir:
            base = Path(artifacts_dir) / exhibit_id / vname
            _save(base / "schema.json", json.dumps(variant.dict(), indent=2))
            _save(base / "prompt.txt", prompt_text)
            _save(base / "extraction.json", extraction)
            _save(base / "critique.json", critique_raw)

        if score > best_score:
            best_score = score
            champion = vname

    state.champion = champion or variant_names[0]

    return models.RunResult(
        exhibit_id=exhibit_id,
        goal=goal_text,
        variants=variant_names,
        champion=state.champion,
        artifacts_dir=artifacts_dir,
    ), state
