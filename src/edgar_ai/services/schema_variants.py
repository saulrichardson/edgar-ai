"""Create several schema proposals and pick the best one via LLM.

Public helpers
==============
generate_variants(doc)   -> list[dict]   # 2–3 candidate schemas
referee(candidates, doc) -> (int, str)   # winning index and rationale

All helpers raise *RuntimeError* when the LLM gateway is not configured so
mis-configurations fail fast.
"""

from __future__ import annotations

import json
import re
import sys
from typing import List, Tuple
import os

# Direct client to the LLM gateway – raises if the URL is missing.
from ..clients import llm_gateway

def _vlog(msg: str) -> None:  # noqa: D401
    """Debug log controlled by `EDGAR_AI_VERBOSE=1`."""

    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        print(f"[schema_variants] {msg}", file=sys.stderr)


def _pretty_json(raw: str) -> tuple[str, bool]:  # noqa: D401
    """Return pretty-printed JSON if *raw* parses, else raw. Bool indicates changed."""

    try:
        parsed = json.loads(raw)
        pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
        return pretty, pretty != raw
    except Exception:
        return raw, False
from ..config import settings
from ..interfaces import Document

# ---------------------------------------------------------------------------
# Variant generation
# ---------------------------------------------------------------------------


# Historical note – these principles were once included in the prompt but are
# now kept only for reference:
#   • Information-Completeness
#   • Observability
#   • Normal-form
#   • Stability
#   • Granularity

_VARIANT_SYSTEM_TEMPLATE = """You are a research strategist charged with creating a **comprehensive extraction schema** that converts an SEC exhibit into a standardized tabular format.

Think first (internally) about:
  * Which thematic topics recur across similar exhibits.
  * Which distinct, observable facts analysts will query later.
  * Why each field is valuable downstream.

Do NOT include your reasoning in the response; return only the final JSON.

Return ONLY valid JSON with these keys:
  1. overview – Up to 10 sentences describing the purpose and coverage of the schema.
  2. topics   – Array of short phrases representing thematic areas.
  3. fields   – **Object** mapping each snake_case field name → object with:
        • description – one-sentence business meaning.
        • rationale   – why the field matters.

Do **NOT** wrap the JSON in triple back-ticks.

⚠️  Exclude generic EDGAR filing metadata (e.g., CIK, file number, exhibit number) or any information that can be reliably obtained from the filing header outside the exhibit text. Focus on facts that are observable **within the exhibit itself**.

Normal-form modelling:
If any concept in the exhibit can appear more than once, represent it as a repeating structure.
  • Define the field as an *array of objects*.
  • Attach a *json_schema* that describes the object’s keys and primitive types.
This rule applies universally; do not enumerate concrete instances.

Additional guiding principles:
• Observability – every field must be able to capture a value that is **verbatim** present in the exhibit text.  Omit fields that rely on external filing metadata or speculative information.
• Granularity – prefer the smallest unit of information that is still meaningful; for example, separate interest margin for different benchmarks instead of merging them into one generic field.
• Value–density – prioritise fields that deliver high analytical value per token.  Avoid very large arrays whose elements differ only in label (e.g., boiler-plate “Form of …” exhibit lists); use a concise summary field instead unless each element affects economics or legal obligations.
• Analytical variation – prioritise fields whose values can vary materially across documents and therefore inform downstream quantitative or logical reasoning.
• Static layout – omit fields whose primary purpose is to mirror the document’s physical structure (tables of contents, attachment labels, page numbers); if such data is still useful, summarise it in a single concise field.
"""

# Mode-specific instructions appended to the system prompt.
_MODE_INSTRUCTIONS = {
    "maximalist": "Return the **most exhaustive** list of fields you reasonably expect to find across any similar exhibit (err on the side of too many).",
    "minimalist": "Return **only the absolute essentials** – the smallest set without which the exhibit is meaningless.",
    "balanced": "Return a **balanced** schema – comprehensive but without speculative edge-case fields.",
}


def _call_llm(system_prompt: str, exhibit: str, *, attempt: int = 1) -> dict:  # noqa: D401 – helper
    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        _vlog("LLM call attempt %d – system prompt:\n%s\n[EXHIBIT TEXT OMITTED]" % (attempt, system_prompt))

    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": exhibit},
        ],
        temperature=settings.goal_setter_temperature,
    )
    raw = rsp["choices"][0]["message"].get("content", "").strip()
    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        pretty, changed = _pretty_json(raw)
        _vlog(
            f"LLM response (attempt {attempt}):\n{pretty}\n"
            + ("(pretty-printed)" if changed else "(verbatim)")
        )

    def _clean(txt: str) -> str:  # noqa: D401 – local helper
        """Strip surrounding ```json fences if the model adds them."""

        m = re.match(r"```(?:json)?\s*(.*)\s*```", txt, flags=re.S | re.I)
        return m.group(1) if m else txt

    clean = _clean(raw)

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Variant LLM returned non-JSON: {raw!r}") from exc


def generate_variants(doc: Document, *, minimal_only: bool = False) -> List[dict]:  # noqa: D401
    """Return 2–3 schema variants for *doc* via separate LLM calls.

    If *minimal_only* is true we generate just the **balanced** proposal so the
    referee has a fresh challenger when there are already stored schemas.
    """

    modes = ["balanced"] if minimal_only else ["maximalist", "minimalist", "balanced"]
    variants: List[dict] = []
    for mode in modes:
        base_prompt = _VARIANT_SYSTEM_TEMPLATE + "\n\n" + _MODE_INSTRUCTIONS[mode]

        schema_obj = None
        for attempt in range(1, settings.goal_setter_max_retries + 1):
            system_prompt = base_prompt
            if attempt > 1:
                system_prompt += (
                    "\n\n⚠️ Your last response was not valid JSON. "
                    "Return ONLY the JSON object in the format requested."
                )

            try:
                schema_obj = _call_llm(system_prompt, doc.text, attempt=attempt)
                break
            except RuntimeError as exc:
                # Propagate if we've exhausted retries
                if attempt == settings.goal_setter_max_retries:
                    raise

        assert schema_obj is not None  # for mypy

        # Basic sanity checks – ensure mandatory keys are present
        for key in ("overview", "topics", "fields"):
            if key not in schema_obj:
                raise RuntimeError(f"Schema variant missing required key '{key}' for mode {mode}")

        # Validate that fields is a mapping with description & rationale, then
        # convert to the canonical list[dict] shape for storage.
        fields_obj = schema_obj["fields"]
        if not isinstance(fields_obj, dict) or not fields_obj:
            raise RuntimeError(f"'fields' must be a non-empty object (mode={mode})")

        new_fields: list[dict] = []
        for fname, meta in fields_obj.items():
            if not isinstance(meta, dict) or {"description", "rationale"} - meta.keys():
                raise RuntimeError(
                    f"Field '{fname}' in mode {mode} lacks description or rationale"
                )

            field_dict = {
                "name": fname,
                "description": meta["description"],
                "rationale": meta["rationale"],
                "required": True,
            }

            # Preserve nested schema details if provided.
            if "structure" in meta and isinstance(meta["structure"], dict):
                field_dict["json_schema"] = meta["structure"]
            elif "json_schema" in meta and isinstance(meta["json_schema"], dict):
                field_dict["json_schema"] = meta["json_schema"]

            new_fields.append(field_dict)

    # end for fname loop

        schema_obj["fields"] = new_fields
        variants.append(schema_obj)

    # end for mode loop

    return variants


# --- Merge referee: combine multiple candidate schemas into one ---


def merge_referee(candidates: List[dict], doc: Document) -> dict:  # noqa: D401
    """Return a **merged** schema created by the LLM from *candidates*."""

    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run merge referee")


    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        for i, c in enumerate(candidates):
            _vlog(f"Merge candidate {i}:\n{json.dumps(c, ensure_ascii=False, indent=2)}")

    numbered = [
        f"Schema {i}:\n```json\n{json.dumps(c, ensure_ascii=False, indent=2)}\n```" for i, c in enumerate(candidates)
    ]

    user_msg = (
        "Here are multiple candidate schemas. Merge them into a single BEST schema following the rules.\n\n"
        + "\n\n".join(numbered)
        + "\n\nEXHIBIT (full text):\n```text\n"
        + doc.text
        + "\n```"
    )

    system_msg = (
        "You are a senior data-architect. Merge the candidate schemas. Rules:\n"
        "• Keep every distinct field that is observable in the exhibit.\n"
        "• If two fields are duplicates, keep the clearer name.\n"
        "• Preserve descriptions and rationales; you may edit wording for clarity.\n"
        "• If fields naturally repeat, group them using an array/object and set json_schema accordingly.\n"
        "Return ONLY valid JSON with keys overview, topics and fields (list of objects). Do NOT wrap the JSON in triple back-ticks."
    )

    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=settings.goal_setter_temperature,
    )

    raw = rsp["choices"][0]["message"].get("content", "").strip()
    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        pretty, changed = _pretty_json(raw)
        _vlog("Referee response:\n" + pretty + ("\n(pretty-printed)" if changed else " (verbatim)"))
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S | re.I)

    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        pretty, changed = _pretty_json(clean)
        _vlog("Merge referee response:\n" + pretty + ("\n(pretty-printed)" if changed else " (verbatim)"))

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise RuntimeError("Merge-Referee returned invalid JSON") from exc


# --- Referee: pick the single best schema ---

_REFEREE_PROMPT = (
    "You are a meticulous reviewer. Choose the BEST extraction schema for the exhibit.\n\n"
    "Judge each candidate using these criteria (in order of importance):\n"
    "• Observability – every field should have a value that can be found verbatim in the exhibit text. Penalise reliance on external metadata.\n"
    "• Normal-form – avoid redundant or duplicate fields; prefer proper use of repeating structures.\n"
    "• Information-Completeness – capture as many distinct observable facts as possible *after* satisfying the above two criteria.\n"
    "• Stability – field names remain valid if future exhibits add more items.\n"
    "• Granularity – represent each logically independent concept as its own field.\n\n"
    "Return ONLY valid JSON:\n"
    "{\n  \"winner_index\": <integer 0-based index of the best schema>,\n  \"reason\": \"single sentence rationale\"\n}\n"
    "If two schemas are equally strong on the above criteria, prefer the one with clearer naming.\n"
)


def referee(candidates: List[dict], doc: Document) -> Tuple[int, str]:  # noqa: D401
    """Return `(winner_index, reason)` using an LLM judge."""

    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot run schema referee")


    numbered = [f"Schema {i}:\n```json\n{json.dumps(c, ensure_ascii=False, indent=2)}\n```" for i, c in enumerate(candidates)]

    user_msg = (
        "Here are the candidate schemas. Read the full exhibit before choosing the best fit.\n\n"
        + "\n\n".join(numbered)
        + "\n\nEXHIBIT (full text):\n\n\"\"\"\n"
        + doc.text
        + "\n\"\"\""
    )

    if os.getenv("EDGAR_AI_VERBOSE") == "1":
        _vlog("Referee system prompt:\n" + _REFEREE_PROMPT)
        for i, c in enumerate(candidates):
            _vlog(f"Candidate schema {i}:\n{json.dumps(c, ensure_ascii=False, indent=2)}")

    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": _REFEREE_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,  # deterministic vote
    )
    raw = rsp["choices"][0]["message"]["content"].strip()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Referee returned invalid JSON: {raw!r}") from exc

    if "winner_index" not in payload:
        raise RuntimeError("Referee JSON missing 'winner_index'")

    return int(payload["winner_index"]), str(payload.get("reason", ""))

# --- Blend helper: merge three variants into an improved schema ---

_BLEND_SYSTEM_PROMPT = """You are a senior data architect. Given three candidate extraction schemas for the *same* SEC exhibit, design a **single best-of-all-worlds schema**.\n\nYour goal is to create the most analytically useful schema possible. You MAY:\n  • keep existing fields you deem valuable,\n  • merge or rename duplicates,\n  • remove low-value or redundant fields, **and**\n  • **add brand-new fields** if important information is not yet captured.\n\nAdditional requirements:\n  • Resolve naming conflicts (choose clear snake_case).\n  • Every field must include *description* and *rationale*.\n  • Preserve any provided json_schema definitions for repeating structures; feel free to create new ones if you invent a new array/object field.\n\nReturn ONLY valid JSON with the keys: overview, topics, fields (object mapping field_name → {description, rationale, json_schema?}). Do NOT wrap in triple back-ticks or add commentary.\n"""


def blend_schema(variants: List[dict], doc: Document) -> dict:  # noqa: D401
    """Blend *variants* into a consolidated schema via LLM."""

    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot blend schemas")


    import json as _json

    user_payload = {
        "candidate_schemas": variants,
        "exhibit_text": doc.text[:10000],  # clip for token safety
    }

    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": _BLEND_SYSTEM_PROMPT},
            {"role": "user", "content": _json.dumps(user_payload, ensure_ascii=False)},
        ],
        temperature=settings.goal_setter_temperature,
    )

    raw = rsp["choices"][0]["message"].get("content", "").strip()

    # Strip fences if model adds them
    import re

    m = re.match(r"```(?:json)?\s*(.*)\s*```", raw, flags=re.S | re.I)
    if m:
        raw = m.group(1)

    try:
        blended = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 – preserve context
        raise RuntimeError(f"Blender returned non-JSON: {raw!r}") from exc

    for key in ("overview", "topics", "fields"):
        if key not in blended:
            raise RuntimeError(f"Blended schema missing key '{key}'")

    return blended
