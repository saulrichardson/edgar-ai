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


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:  # noqa: D401
    parser = argparse.ArgumentParser(prog="edgar-ai")

    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Execute the **full** pipeline on pre-processed text input")
    run_cmd.add_argument(
        "source",
        help="Path to text file or '-' to read from stdin.",
    )


    # Goal-Setter only ----------------------------------------------------
    goal_cmd = sub.add_parser("goal", help="Run only the Goal-Setter persona")
    goal_cmd.add_argument("source", help="Text file or '-' for stdin")

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
        # Import orchestrator **after** potentially setting simulation env var
        from .orchestrator import run_once  # noqa: WPS433 (runtime import)

        text_batch = _read_html_source(args.source)
        rows = run_once(text_batch)
        console.print_json(json.dumps([row.data for row in rows]))

    elif args.command == "goal":
        from edgar_ai.interfaces import Document  # noqa: WPS433 (runtime import)
        from edgar_ai.services import goal_setter  # noqa: WPS433

        text = _read_html_source(args.source)[0]
        doc = Document(doc_id="cli", text=text, metadata={})
        goal = goal_setter.run([doc])
        if isinstance(goal, dict):
            import json as _json

            console.print_json(_json.dumps(goal))
        else:
            console.print(goal)


if __name__ == "__main__":  # pragma: no cover
    main()
