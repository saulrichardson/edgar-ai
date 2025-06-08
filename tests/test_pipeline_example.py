"""End-to-end pipeline test using the sample credit agreement text file.

The test runs in *simulation* mode so that no internet / OpenAI access is
required.  It ensures the orchestrator processes a real-looking document and
returns at least one Row with non-empty data.
"""

import os
from pathlib import Path

# Add src to import path when running without installation
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from edgar_ai.config import settings  # noqa: E402
from edgar_ai.orchestrator import run_once  # noqa: E402


def test_pipeline_on_credit_agreement():
    # Enable simulation mode for deterministic offline behaviour.
    from edgar_ai.clients import llm_gateway

def _fake_chat(**kwargs):
    return {
        "choices": [
            {
                "message": {
                    "content": "{\"overview\":\"demo\",\"topics\":[],\"fields\":[]}",
                    "tool_calls": [
                        {"function": {"arguments": "{\"company_name\": \"ACME\"}"}}
                    ],
                }
            }
        ]
    }

    llm_gateway.chat_completions = _fake_chat  # type: ignore
    settings.llm_gateway_url = "http://dummy"  # type: ignore

    sample = project_root / "tests" / "fixtures" / "credit_agreement.txt"
    assert sample.exists(), "Sample credit agreement file missing"

    rows = run_once([sample.read_text()])

    assert rows, "Expected at least one row from pipeline"
    # The stub extractor returns company_name in simulation
    assert rows[0].data, "Row data should not be empty"
