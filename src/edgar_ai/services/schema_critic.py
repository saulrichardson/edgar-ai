"""Schema-Critic persona: evaluates a JSON schema against high-level design principles."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List

from ..interfaces import SchemaCritique, Document
from ..config import settings
from ..clients import llm_gateway
from ..utils.paths import get_data_dir


_SCHEMA_CRITIC_PROMPT = (
    "You are the Edgar-AI Schema Critic. Evaluate the provided JSON schema against the following high-level design principles:\n\n"
    "{principles}\n\n"
    "Respond with only valid JSON matching the provided function signature.\n\n"
    "Use the sample exhibit text below to ground your assessment:\n\n"
    '"""\n'
    "{exhibit_excerpt}\n"
    '"""\n'
)

_SCHEMA_CRITIC_FUNCTION = {
    "name": "schema_critic",
    "description": "Evaluate JSON schema against high-level principles",
    "parameters": {
        "type": "object",
        "properties": {
            "critiques": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "principle": {"type": "string"},
                        "score": {"type": "number", "description": "0.0 (fails)–1.0 (perfect)"},
                        "message": {"type": "string"},
                    },
                    "required": ["principle", "score", "message"],
                },
            }
        },
        "required": ["critiques"],
    },
}


def run(schema_id: str, schema: dict, doc: Document) -> List[SchemaCritique]:
    """LLM-driven schema evaluation against configured principles."""
    principles = settings.schema_critic_principles
    text_principles = "\n".join(f"- {p}" for p in principles)

    excerpt = doc.text[:2000]

    system_msg = _SCHEMA_CRITIC_PROMPT.format(
        principles=text_principles,
        exhibit_excerpt=excerpt,
    )

    resp = llm_gateway.chat_completions(
        model=settings.model_schema_critic,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(schema, ensure_ascii=False)},
        ],
        functions=[_SCHEMA_CRITIC_FUNCTION],
        function_call={"name": "schema_critic"},
    )

    arg_str = resp["choices"][0]["message"]["function_call"]["arguments"]
    payload = json.loads(arg_str)

    now = datetime.now(timezone.utc)
    critiques: List[SchemaCritique] = []
    for item in payload.get("critiques", []):
        critiques.append(
            SchemaCritique(
                principle=item["principle"],
                score=item["score"],
                message=item["message"],
                schema_id=schema_id,
                created_at=now,
            )
        )

    base = get_data_dir() / "schema-critiques"
    base.mkdir(parents=True, exist_ok=True)
    for idx, critique in enumerate(critiques):
        path = base / f"{schema_id}-{critique.principle}-{now.isoformat()}-{idx}.json"
        path.write_text(json.dumps(critique.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    return critiques