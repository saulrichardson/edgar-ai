from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from clients.gateway import send_chat
from pipeline import models
from pipeline.artifacts import PipelineState
from pipeline.config import load_gateway_config
from pipeline.context import ContextSpec, make_bundle
from pipeline.memory import MemoryStore
import personas as registry


def _save(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_json_strict(text: str) -> Any:
    s = (text or "").strip()
    if not s:
        raise ValueError("Expected JSON but got empty output")
    return json.loads(s)


def _load_existing_candidates(
    base_dir: Path,
    *,
    state: PipelineState,
    candidates: Dict[str, Any],
    candidate_meta: Dict[str, Dict[str, str]],
) -> None:
    if not base_dir.exists() or not base_dir.is_dir():
        return

    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir():
            continue
        candidate_id = entry.name
        schema_path = entry / "schema.json"
        if schema_path.exists():
            try:
                candidates[candidate_id] = json.loads(_load_text(schema_path))
            except Exception:
                continue
        else:
            continue

        if candidate_id not in candidate_meta:
            proposer = "unknown"
            if candidate_id.startswith("proposer_"):
                proposer = candidate_id.removeprefix("proposer_")
            elif candidate_id.startswith("memory_"):
                proposer = "memory"
            elif candidate_id.startswith("tutor_"):
                proposer = "tutor"
            candidate_meta[candidate_id] = {"proposer": proposer}

        prompt_path = entry / "prompt.txt"
        if prompt_path.exists():
            state.prompts[candidate_id] = _load_text(prompt_path)

        extraction_path = entry / "extraction.json"
        if extraction_path.exists():
            extraction_text = _load_text(extraction_path)
            try:
                _parse_json_strict(extraction_text)
            except Exception:
                # Ignore invalid JSON so resume logic re-runs extraction for this candidate.
                extraction_text = ""
            if extraction_text:
                state.extractions[candidate_id] = extraction_text

        state.critiques.setdefault(candidate_id, {})
        for critic_file in entry.glob("critic_*.json"):
            critic_style = critic_file.stem.removeprefix("critic_")
            crit_text = _load_text(critic_file)
            try:
                _parse_json_strict(crit_text)
            except Exception:
                continue
            state.critiques[candidate_id][critic_style] = crit_text

def _parse_json_loose(text: str) -> Any:
    s = (text or "").strip()
    if not s:
        raise ValueError("Expected JSON but got empty output")
    # Fast path: strict JSON only.
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # Robust path: decode the first JSON value from the first opening brace/bracket.
    first_obj = s.find("{")
    first_arr = s.find("[")
    starts = [idx for idx in (first_obj, first_arr) if idx != -1]
    if not starts:
        raise ValueError("Could not find JSON object/array in model output")
    start = min(starts)

    decoder = json.JSONDecoder()
    try:
        value, _end = decoder.raw_decode(s[start:])
        return value
    except json.JSONDecodeError:
        # Last resort: attempt to isolate a full object/array by the final matching close.
        if start == first_obj:
            end = s.rfind("}")
        else:
            end = s.rfind("]")
        if end == -1 or end <= start:
            raise ValueError("Could not isolate JSON from model output")
        return json.loads(s[start : end + 1])


def _safe_parse_json(text: str) -> Any:
    try:
        return _parse_json_loose(text)
    except Exception:
        return {"raw": (text or "").strip()}


def _goal_public_dict(goal) -> Dict[str, Any]:
    return {"goal_id": goal.goal_id, "title": goal.title, "blueprint": goal.blueprint}


def _choose_goal(
    *,
    memory: MemoryStore,
    gw_config,
    bundle,
    state: PipelineState,
    goal_text: str | None,
) -> Dict[str, Any]:
    if goal_text is not None:
        try:
            goal_obj = _parse_json_loose(goal_text)
            title = str(goal_obj.get("title") or "").strip()
            blueprint = str(goal_obj.get("blueprint") or "").strip()
            if not title:
                raise ValueError("goal_json missing title")
            return _goal_public_dict(memory.upsert_goal(title=title, blueprint=blueprint))
        except Exception:
            title = goal_text.strip()
            return _goal_public_dict(memory.upsert_goal(title=title, blueprint=title))

    existing = memory.list_goals()
    matched_goal = None
    if existing:
        goals_payload = [_goal_public_dict(g) for g in existing]
        router_raw = send_chat(
            registry.render_messages(registry.goal_router_spec(goals_payload), bundle, state),
            gw_config,
        )
        router = _safe_parse_json(router_raw)
        decision = str(router.get("decision") or "").lower()
        matched_id = router.get("goal_id")
        if decision == "match" and matched_id:
            matched_goal = memory.get_goal(str(matched_id))

    if matched_goal is not None:
        return _goal_public_dict(matched_goal)

    goal_raw = send_chat(
        registry.render_messages(registry.goal_setter_spec, bundle, state),
        gw_config,
    )
    goal_obj = _parse_json_loose(goal_raw)
    title = str(goal_obj.get("title") or "").strip()
    blueprint = str(goal_obj.get("blueprint") or "").strip()
    if not title:
        raise ValueError("Goal-Setter did not return JSON with a non-empty 'title'")

    return _goal_public_dict(memory.upsert_goal(title=title, blueprint=blueprint))


def _run_candidate(
    *,
    candidate_id: str,
    schema_obj: Any,
    goal: Dict[str, Any],
    include_provenance: bool,
    gw_config,
    bundle_schema,
    bundle_extractor,
    bundle_critic,
    state: PipelineState,
    critic_styles: List[str],
    artifacts_dir: str | None,
) -> None:
    prompt_text = send_chat(
        registry.render_messages(registry.prompt_builder_spec(goal, schema_obj, include_provenance), bundle_schema, state),
        gw_config,
    )
    state.prompts[candidate_id] = prompt_text

    extraction = send_chat(
        registry.render_messages(registry.extractor_spec(prompt_text), bundle_extractor, state),
        gw_config,
    )
    try:
        _parse_json_strict(extraction)
    except Exception as exc:
        extraction_retry = send_chat(
            registry.render_messages(registry.extractor_spec(prompt_text), bundle_extractor, state),
            gw_config,
        )
        try:
            _parse_json_strict(extraction_retry)
        except Exception:
            raise ValueError(f"{candidate_id}: extractor did not return valid JSON") from exc
        extraction = extraction_retry
    state.extractions[candidate_id] = extraction

    state.critiques.setdefault(candidate_id, {})
    for cstyle in critic_styles:
        crit_raw = send_chat(
            registry.render_messages(
                registry.schema_critic_spec(cstyle, goal, schema_obj, extraction),
                bundle_critic,
                state,
            ),
            gw_config,
        )
        try:
            _parse_json_strict(crit_raw)
        except Exception as exc:
            crit_raw_retry = send_chat(
                registry.render_messages(
                    registry.schema_critic_spec(cstyle, goal, schema_obj, extraction),
                    bundle_critic,
                    state,
                ),
                gw_config,
            )
            try:
                _parse_json_strict(crit_raw_retry)
            except Exception:
                if artifacts_dir:
                    base = Path(artifacts_dir) / state.exhibit_id / candidate_id
                    _save(base / f"critic_{cstyle}_error.txt", str(exc))
                continue
            crit_raw = crit_raw_retry
        state.critiques[candidate_id][cstyle] = crit_raw

    if artifacts_dir:
        base = Path(artifacts_dir) / state.exhibit_id / candidate_id
        _save(base / "schema.json", json.dumps(schema_obj, ensure_ascii=False, indent=2))
        _save(base / "prompt.txt", prompt_text)
        _save(base / "extraction.json", extraction)
        for cstyle, crit_raw in state.critiques[candidate_id].items():
            _save(base / f"critic_{cstyle}.json", crit_raw)


def _build_governor_payload(
    *,
    candidates: Dict[str, Any],
    candidate_meta: Dict[str, Dict[str, str]],
    critiques: Dict[str, Dict[str, str]],
) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for candidate_id, schema_obj in candidates.items():
        council = {k: _safe_parse_json(v) for k, v in (critiques.get(candidate_id) or {}).items()}
        payload.append(
            {
                "candidate_id": candidate_id,
                "proposer": candidate_meta.get(candidate_id, {}).get("proposer", "unknown"),
                "schema": schema_obj,
                "council": council,
            }
        )
    return payload


def _choose_champion(
    *,
    goal: Dict[str, Any],
    governor_payload: List[Dict[str, Any]],
    gw_config,
    bundle_schema,
    state: PipelineState,
    candidates: Dict[str, Any],
) -> Tuple[str, Any, str]:
    governor_raw = send_chat(
        registry.render_messages(registry.governor_spec(goal, governor_payload), bundle_schema, state),
        gw_config,
    )
    governor_decision = _safe_parse_json(governor_raw)
    champion_candidate_id = str(governor_decision.get("champion_candidate_id") or "").strip()
    if not champion_candidate_id:
        raise ValueError("Governor did not return a 'champion_candidate_id'")
    if champion_candidate_id not in candidates:
        raise ValueError(f"Governor selected unknown candidate_id: {champion_candidate_id!r}")
    return champion_candidate_id, governor_decision, governor_raw


def run_pipeline(
    exhibit_text: str,
    exhibit_id: str,
    goal_text: str | None = None,
    artifacts_dir: str | None = None,
    include_provenance: bool = False,
    memory_dir: str | None = None,
    proposer_styles: Optional[List[str]] = None,
    critic_styles: Optional[List[str]] = None,
    enable_schema_tutor: bool = False,
    resume_from_artifacts: bool = True,
    context_spec_goal: ContextSpec | None = None,
    context_spec_schema: ContextSpec | None = None,
    context_spec_extractor: ContextSpec | None = None,
    context_spec_critic: ContextSpec | None = None,
) -> Tuple[models.RunResult, PipelineState]:
    gw = load_gateway_config()
    memory = MemoryStore(memory_dir)

    context_spec_goal = context_spec_goal or ContextSpec(mode="full")
    context_spec_schema = context_spec_schema or ContextSpec(mode="full")
    context_spec_extractor = context_spec_extractor or ContextSpec(mode="full")
    context_spec_critic = context_spec_critic or ContextSpec(mode="full")

    bundle_goal = make_bundle(exhibit_id, exhibit_text, context_spec_goal)
    bundle_schema = make_bundle(exhibit_id, exhibit_text, context_spec_schema)
    bundle_extractor = make_bundle(exhibit_id, exhibit_text, context_spec_extractor)
    bundle_critic = make_bundle(exhibit_id, exhibit_text, context_spec_critic)

    state = PipelineState(exhibit_id=exhibit_id)

    proposer_styles = proposer_styles or registry.schema_proposer_styles()
    critic_styles = critic_styles or registry.schema_critic_styles()

    goal = _choose_goal(memory=memory, gw_config=gw, bundle=bundle_goal, state=state, goal_text=goal_text)
    state.goal = goal
    if artifacts_dir:
        base = Path(artifacts_dir) / exhibit_id
        _save(base / "goal.json", json.dumps(goal, ensure_ascii=False, indent=2))

    candidates: Dict[str, Any] = {}
    candidate_meta: Dict[str, Dict[str, str]] = {}

    if artifacts_dir and resume_from_artifacts:
        _load_existing_candidates(
            Path(artifacts_dir) / exhibit_id,
            state=state,
            candidates=candidates,
            candidate_meta=candidate_meta,
        )

    prior = memory.get_champion(goal["goal_id"])
    if prior is not None and prior.schema is not None:
        candidates.setdefault("memory_champion", prior.schema)
        candidate_meta.setdefault("memory_champion", {"proposer": "memory"})

    for style in proposer_styles:
        candidate_id = f"proposer_{style}"
        if candidate_id in candidates:
            continue
        schema_raw = send_chat(
            registry.render_messages(registry.schema_proposer_spec(style, goal), bundle_schema, state),
            gw,
        )
        try:
            schema_obj = _parse_json_loose(schema_raw)
        except Exception as exc:
            # Retry once. Schemas are large and models occasionally emit invalid JSON (missing commas, truncation).
            schema_raw_retry = send_chat(
                registry.render_messages(registry.schema_proposer_spec(style, goal), bundle_schema, state),
                gw,
            )
            try:
                schema_obj = _parse_json_loose(schema_raw_retry)
            except Exception:
                if artifacts_dir:
                    base = Path(artifacts_dir) / exhibit_id / candidate_id
                    _save(base / "schema_raw.txt", schema_raw)
                    _save(base / "schema_raw_retry.txt", schema_raw_retry)
                    _save(base / "schema_error.txt", str(exc))
                continue

        candidates[candidate_id] = schema_obj
        candidate_meta[candidate_id] = {"proposer": style}

    state.candidates = candidates

    failed_candidates: List[str] = []
    for candidate_id, schema_obj in list(candidates.items()):
        existing_prompt = candidate_id in state.prompts
        existing_extraction = candidate_id in state.extractions
        existing_critiques = all(
            style in (state.critiques.get(candidate_id) or {}) for style in critic_styles
        )
        if artifacts_dir and resume_from_artifacts and existing_prompt and existing_extraction and existing_critiques:
            continue
        try:
            _run_candidate(
                candidate_id=candidate_id,
                schema_obj=schema_obj,
                goal=goal,
                include_provenance=include_provenance,
                gw_config=gw,
                bundle_schema=bundle_schema,
                bundle_extractor=bundle_extractor,
                bundle_critic=bundle_critic,
                state=state,
                critic_styles=critic_styles,
                artifacts_dir=artifacts_dir,
            )
        except Exception as exc:
            failed_candidates.append(candidate_id)
            if artifacts_dir:
                base = Path(artifacts_dir) / exhibit_id / candidate_id
                _save(base / "candidate_error.txt", str(exc))
            continue

    for candidate_id in failed_candidates:
        candidates.pop(candidate_id, None)
        candidate_meta.pop(candidate_id, None)
        state.prompts.pop(candidate_id, None)
        state.extractions.pop(candidate_id, None)
        state.critiques.pop(candidate_id, None)

    if not candidates:
        raise ValueError("No viable schema candidates remained after extraction/critique. See artifacts for details.")

    governor_payload = _build_governor_payload(
        candidates=candidates,
        candidate_meta=candidate_meta,
        critiques=state.critiques,
    )
    champion_candidate_id, governor_decision, governor_raw = _choose_champion(
        goal=goal,
        governor_payload=governor_payload,
        gw_config=gw,
        bundle_schema=bundle_schema,
        state=state,
        candidates=candidates,
    )
    state.champion_candidate_id = champion_candidate_id
    state.governor_decision = governor_raw

    if artifacts_dir:
        base = Path(artifacts_dir) / exhibit_id
        _save(base / "goal.json", json.dumps(goal, ensure_ascii=False, indent=2))
        _save(base / "governor.json", json.dumps(governor_decision, ensure_ascii=False, indent=2))

    if enable_schema_tutor:
        champ_schema = candidates[champion_candidate_id]
        champ_extraction = state.extractions[champion_candidate_id]
        champ_council = state.critiques.get(champion_candidate_id, {})
        tutor_raw = send_chat(
            registry.render_messages(
                registry.tutor_spec(
                    json.dumps(goal, ensure_ascii=False, indent=2),
                    json.dumps(champ_schema, ensure_ascii=False, indent=2),
                    champ_extraction,
                    json.dumps({k: _safe_parse_json(v) for k, v in champ_council.items()}, ensure_ascii=False, indent=2),
                ),
                bundle_schema,
                state,
            ),
            gw,
        )
        if "NO-CHANGE" not in (tutor_raw or "").upper():
            challenger_schema = _parse_json_loose(tutor_raw)
            challenger_id = "tutor_challenger"
            candidates[challenger_id] = challenger_schema
            candidate_meta[challenger_id] = {"proposer": "tutor"}
            _run_candidate(
                candidate_id=challenger_id,
                schema_obj=challenger_schema,
                goal=goal,
                include_provenance=include_provenance,
                gw_config=gw,
                bundle_schema=bundle_schema,
                bundle_extractor=bundle_extractor,
                bundle_critic=bundle_critic,
                state=state,
                critic_styles=critic_styles,
                artifacts_dir=artifacts_dir,
            )
            governor_payload_2 = _build_governor_payload(
                candidates={champion_candidate_id: candidates[champion_candidate_id], challenger_id: candidates[challenger_id]},
                candidate_meta=candidate_meta,
                critiques=state.critiques,
            )
            champion_candidate_id, governor_decision, governor_raw = _choose_champion(
                goal=goal,
                governor_payload=governor_payload_2,
                gw_config=gw,
                bundle_schema=bundle_schema,
                state=state,
                candidates=candidates,
            )
            state.champion_candidate_id = champion_candidate_id
            state.governor_decision = governor_raw

            if artifacts_dir:
                base = Path(artifacts_dir) / exhibit_id
                _save(base / "governor_2.json", json.dumps(governor_decision, ensure_ascii=False, indent=2))

    memory.set_champion(
        goal_id=goal["goal_id"],
        candidate_id=state.champion_candidate_id,
        schema=candidates[state.champion_candidate_id],
        prompt=state.prompts.get(state.champion_candidate_id),
        governor_decision=governor_decision,
    )

    return (
        models.RunResult(
            exhibit_id=exhibit_id,
            goal_id=goal["goal_id"],
            goal_title=goal["title"],
            candidates=list(candidates.keys()),
            champion_candidate_id=state.champion_candidate_id,
            artifacts_dir=artifacts_dir,
            governor_decision=state.governor_decision,
        ),
        state,
    )
