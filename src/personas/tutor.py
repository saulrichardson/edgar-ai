from __future__ import annotations

SYSTEM_PROMPT = (
    "You are Tutor. Given the current champion schema and critic council feedback, propose a challenger schema update.\n\n"
    "Rules:\n"
    "- Keep improvements minimal and targeted to concrete weaknesses.\n"
    "- Preserve goal alignment; do not change the goal.\n"
    "- Output either 'NO-CHANGE' if the schema is sufficient, or output the revised schema as JSON only.\n"
)


def build_user_message(goal_json: str, schema_json: str, extraction_json: str, council_json: str) -> str:
    return (
        "GOAL:\n" + goal_json + "\n\n"
        "CHAMPION SCHEMA (JSON):\n" + schema_json + "\n\n"
        "EXTRACTION OUTPUT (JSON text):\n" + extraction_json + "\n\n"
        "CRITIC COUNCIL OUTPUTS:\n" + council_json + "\n\n"
        "Return revised schema JSON or NO-CHANGE."
    )
