"""Goal-Setter v2 – generate multiple schema variants and let an LLM referee.

The module exposes two public helpers used by the pipeline:

* generate_variants(doc: Document, minimal_only: bool = False) -> list[dict]
    – Calls the LLM 2–3 times with different prompts (maximalist, minimalist,
      balanced).
    – Returns a list of **schema objects** (`dict`) each containing:

        {
          "overview": str,
          "topics": [str],
          "fields": {
              field_name: {
                  "description": str,
                  "rationale": str
              }, ...
          }
        }

* referee(candidates: list[dict], doc: Document) -> tuple[int, str]
    – Calls the LLM once with all candidate schemas + exhibit text, asking for
      a JSON response `{ "winner_index": n, "reason": "..." }` (0-based).

Both helpers raise *RuntimeError* if the LLM gateway URL is missing so that
callers fail fast in misconfigured environments.
"""

from __future__ import annotations

import json
import re
from typing import List, Tuple

from ..clients import llm_gateway
from ..config import settings
from ..interfaces import Document

# ---------------------------------------------------------------------------
# Variant generation
# ---------------------------------------------------------------------------


_VARIANT_SYSTEM_TEMPLATE = """You are an expert legal data architect. Your task is to propose an **extraction schema** for a single SEC exhibit.

General principles to apply in EVERY schema you design
• Purpose-first – include only fields an analyst needs to answer the exhibit’s key question.
• Observability – prefer values stated verbatim; avoid speculative / inferred data.
• Normal-form – avoid compound blob fields; normalise repeating sub-structures.
• Stability – choose names that stay valid even if new, similar items appear.
• Compression – when multiple labelled items share identical attributes, group them in one object/array rather than one flat field per label-attribute.

IMPORTANT: Do **NOT** include your reasoning **or** wrap the JSON in triple back-ticks. Return ONLY valid JSON.

The JSON must have these keys:
  1. overview   – 1-10 sentence purpose of the extraction.
  2. topics     – array of short thematic strings.
  3. fields     – an *object* mapping each snake_case field name to another object with:
        • description – one sentence business meaning.
        • rationale   – why this field is valuable downstream.
"""

# Mode-specific instructions appended to the system prompt.
_MODE_INSTRUCTIONS = {
    "maximalist": "Return the **most exhaustive** list of fields you reasonably expect to find across any similar exhibit (err on the side of too many).",
    "minimalist": "Return **only the absolute essentials** – the smallest set without which the exhibit is meaningless.",
    "balanced": "Return a **balanced** schema – comprehensive but without speculative edge-case fields.",
}


def _call_llm(system_prompt: str, exhibit: str) -> dict:  # noqa: D401 – helper
    if not settings.llm_gateway_url:
        raise RuntimeError("LLM gateway URL not configured; cannot generate schema variants")

    rsp = llm_gateway.chat_completions(
        model=settings.model_goal_setter,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": exhibit},
        ],
        temperature=settings.goal_setter_temperature,
    )
    raw = rsp["choices"][0]["message"]["content"].strip()

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
                schema_obj = _call_llm(system_prompt, doc.text)
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
            if not isinstance(meta, dict) or {
                "description",
                "rationale",
            } - meta.keys():
                raise RuntimeError(
                    f"Field '{fname}' in mode {mode} lacks description or rationale"
                )

        field_dict = {
            "name": fname,
            "description": meta["description"],
            "rationale": meta["rationale"],
            "required": True,
        }

        # If LLM provided nested structure under a key 'structure' or
        # 'json_schema', capture it.
        if "structure" in meta and isinstance(meta["structure"], dict):
            field_dict["json_schema"] = meta["structure"]
        elif "json_schema" in meta and isinstance(meta["json_schema"], dict):
            field_dict["json_schema"] = meta["json_schema"]

        new_fields.append(field_dict)

        schema_obj["fields"] = new_fields
        variants.append(schema_obj)

    return variants


# ---------------------------------------------------------------------------
# Referee – pick the winning schema
# ---------------------------------------------------------------------------

_REFEREE_PROMPT = (
    "You are a meticulous reviewer. Choose the BEST extraction schema for the exhibit.\n\n"
    "Judge each candidate using these criteria (in order of importance):\n"
    "• Coverage – captures all *distinct* observable concepts present in the exhibit.\n"
    "• Purpose-first – every field supports key analytical questions.\n"
    "• Observability – values appear verbatim; avoid speculation.\n"
    "• Normal-form & Compression – compact, non-redundant structure.\n"
    "• Stability – field names remain valid if future exhibits add more items.\n\n"
    "Return ONLY valid JSON:\n"
    "{\n  \"winner_index\": <integer 0-based index of the best schema>,\n  \"reason\": \"single sentence rationale\"\n}\n"
    "If two schemas are equally valid, prefer the one with **fewer** fields.\n"
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
