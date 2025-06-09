# Same import-path shim as in *test_orchestrator* so that running tests without
# prior installation works.
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))


from edgar_ai.interfaces import Document  # noqa: E402  pylint: disable=wrong-import-position


from edgar_ai.services import (  # noqa: E402  pylint: disable=wrong-import-position
    discoverer,
    extractor,
    intake,
    prompt_builder,
    schema_synth,
)


def test_service_chain():
    # Mock LLM gateway call for both prompt_builder and extractor
    from edgar_ai.clients import llm_gateway
    from edgar_ai.config import settings as config_settings

    def _fake_chat(**kwargs):
        return {
            "choices": [
                {
                    "message": {
                        "content": "{\"overview\":\"demo\",\"topics\":[],\"fields\":[]}",
                        "tool_calls": [
                            {
                                "function": {
                                    "arguments": "{\"company_name\": \"ACME\"}"
                                }
                            }
                        ],
                    }
                }
            ]
        }

    llm_gateway.chat_completions = _fake_chat  # type: ignore
    config_settings.llm_gateway_url = "http://dummy"

    docs = intake.run(["demo exhibit text"])
    candidates = discoverer.run(docs)
    schema = schema_synth.run(candidates)
    # Use a dummy goal matching the stubbed content
    goal = {"overview": "demo", "topics": [], "fields": []}
    prompt = prompt_builder.run(schema, goal)

    rows = extractor.run(docs, prompt)
    assert rows and rows[0].data["company_name"] == "ACME"
