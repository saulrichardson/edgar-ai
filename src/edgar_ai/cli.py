"""Command-line interface for the edgar_ai scaffold.

Usage examples
--------------
Run on a local HTML file::

    python -m edgar_ai.cli run path/to/file.html

Pipe HTML via stdin::

    cat file.html | python -m edgar_ai.cli run -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from rich.console import Console

from .orchestrator import run_once


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:  # noqa: D401
    parser = argparse.ArgumentParser(prog="edgar-ai")

    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Execute the pipeline on HTML input")
    run_cmd.add_argument(
        "source",
        help="Path to HTML file or '-' to read from stdin.",
    )

    return parser.parse_args(argv)


def _read_html_source(source: str) -> List[str]:  # noqa: D401
    if source == "-":
        html = sys.stdin.read()
        return [html]

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(source)

    return [path.read_text()]


def main(argv: List[str] | None = None) -> None:  # noqa: D401
    args = _parse_args(argv)

    console = Console()

    if args.command == "run":
        html_batch = _read_html_source(args.source)
        rows = run_once(html_batch)
        console.print_json(json.dumps([row.data for row in rows]))


if __name__ == "__main__":  # pragma: no cover
    main()
