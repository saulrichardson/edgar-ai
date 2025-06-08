from pathlib import Path

import pytest

# ensure src path available without install
import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "src"))


from edgar_ai.services import document_provider  # noqa: E402, pylint: disable=wrong-import-position


@pytest.fixture()
def tmp_filing(tmp_path: Path) -> Path:
    # Create sample exhibit files
    (tmp_path / "ex10-1.htm").write_text("<html>contract</html>")
    (tmp_path / "ex99-1.htm").write_text("<html>press</html>")
    return tmp_path


def test_document_provider_reads_html(tmp_filing: Path):
    docs = document_provider.run(tmp_filing)
    assert len(docs) == 2
    types = {d.metadata.get("exhibit_type") for d in docs}
    assert "EX-10" in types and "EX-99" in types
