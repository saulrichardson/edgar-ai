import sys
from pathlib import Path

# Ensure the src directory is on the import path when the project is executed
# without installation (e.g., during local development).
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))


from edgar_ai.orchestrator import run_once  # noqa: E402  pylint: disable=wrong-import-position


def test_run_once_returns_rows():
    html_batch = ["demo exhibit text"]
    rows = run_once(html_batch)
    assert rows, "Expected at least one row"
    for row in rows:
        assert "company_name" in row.data
