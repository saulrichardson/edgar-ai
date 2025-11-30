from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from clients.gateway import send_chat
from pipeline.config import load_gateway_config
from pipeline import models
from personas import goal_setter, schema_synth, prompt_builder, extractor, critic


def _save(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_pipeline(
    exhibit_text: str,
    exhibit_id: str,
    goal_text: str | None = None,
    artifacts_dir: str | None = None,
) -> models.RunResult:
    gw = load_gateway_config()

    # Goal
    if goal_text is None:
        goal_prompt = goal_setter.build_user_message(exhibit_text)
        goal_out = send_chat(goal_setter.messages(goal_prompt), gw)
        goal_text = goal_out.strip()

    # Schema variants
    schema_user = schema_synth.build_user_message(goal_text, exhibit_text)
    schema_raw = send_chat(schema_synth.messages(schema_user), gw)
    # parse first json array
    start = schema_raw.find("[")
    end = schema_raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Schema synth did not return JSON array")
    schemas = json.loads(schema_raw[start : end + 1])
    variants: List[models.SchemaVariant] = [models.SchemaVariant(**v) for v in schemas]

    variant_names: List[str] = []
    champion = None
    best_score = -1e9

    for variant in variants:
        vname = variant.variant
        variant_names.append(vname)

        prompt_text = send_chat(prompt_builder.messages(variant), gw)
        extraction = send_chat(extractor.messages(prompt_text, exhibit_text), gw)
        critique_raw = send_chat(critic.messages(exhibit_text, extraction), gw)

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

    return models.RunResult(
        exhibit_id=exhibit_id,
        goal=goal_text,
        variants=variant_names,
        champion=champion or variant_names[0],
    )
