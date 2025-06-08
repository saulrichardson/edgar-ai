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
    docs = intake.run(["demo exhibit text"])
    candidates = discoverer.run(docs)
    schema = schema_synth.run(candidates)
    prompt = prompt_builder.run(schema)
    rows = extractor.run(docs, prompt)

    assert docs and candidates and rows
    assert rows[0].data["company_name"] == "Example Corp"
