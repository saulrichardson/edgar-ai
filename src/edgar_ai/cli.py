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

    # Extract pipeline -------------------------------------------------
    extract_cmd = sub.add_parser(
        "extract",
        help="Run pipeline up to extraction and persist snapshots",
    )
    extract_cmd.add_argument(
        "path",
        help="HTML/HTM or plain-text file containing an exhibit.",
    )
    extract_cmd.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose progress information to stderr.",
    )
    extract_cmd.add_argument(
        "--reset-memory",
        action="store_true",
        help="Flush the persisted schema memory before running (starts fresh).",
    )

    # Schema management
    schemas_cmd = sub.add_parser("schemas", help="List, show, or delete stored schemas")
    schemas_cmd.add_argument("action", choices=["list", "show", "delete"], help="Management action")
    schemas_cmd.add_argument("schema_id", nargs="?", help="ID of schema for show/delete")
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

    elif args.command == "extract":
        # --------------------------------------------------------------
        # Lazy imports to avoid heavy deps when not needed
        # --------------------------------------------------------------
        import uuid
        from datetime import datetime, timezone
        from pathlib import Path
        import hashlib
        import json as _json

        from edgar_ai.interfaces import Document, Prompt, Row, Schema  # noqa: WPS433
        from edgar_ai.memory import FileMemoryStore  # noqa: WPS433
        from edgar_ai.pipeline import choose_schema as _choose_schema  # noqa: WPS433
        from edgar_ai.services import extractor as _svc_extractor  # noqa: WPS433
        from edgar_ai.storage.snapshots import save_prompt, save_rows  # noqa: WPS433
        from edgar_ai.services import document_provider  # noqa: WPS433

        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"

        verbose: bool = getattr(args, "verbose", False)

        def _log(msg: str):  # noqa: D401
            if verbose:
                print(f"[extract][{run_id}] {msg}", file=sys.stderr)

        memory = FileMemoryStore()

        if getattr(args, "reset_memory", False):
            _log("⚠️  --reset-memory flag detected – clearing memory.json")
            memory._path.write_text("[]", encoding="utf-8")  # type: ignore[attr-defined]

        path = Path(args.path).expanduser().resolve()

        if path.is_dir():
            _log(f"Scanning directory {path} for exhibits…")
            documents = document_provider.run(str(path))
        else:
            _log(f"Reading single file {path.name}")
            if path.suffix.lower() not in {".html", ".htm"}:
                _log("⚠️  File extension is not .html/.htm – treating content as plain text.")
            text = path.read_text(encoding="utf-8", errors="ignore")
            documents = [Document(doc_id=path.name, text=text, metadata={})]

        _log(f"{len(documents)} document(s) queued")

        all_rows: list[Row] = []

        for idx, doc in enumerate(documents, start=1):
            _log(f"[{idx}/{len(documents)}] Processing {doc.doc_id}")

            schema_dict = _choose_schema(doc, memory, verbose=verbose)

            # Create stable hash for snapshot naming
            schema_hash = hashlib.sha256(_json.dumps(schema_dict, sort_keys=True).encode()).hexdigest()[:12]

            from edgar_ai.interfaces import FieldMeta  # local import to avoid circular

            raw_fields = schema_dict["fields"]

            # Convert various legacy shapes into List[FieldMeta]
            if isinstance(raw_fields, list):
                if raw_fields and isinstance(raw_fields[0], dict):
                    field_meta = [FieldMeta(**f) for f in raw_fields]  # type: ignore[arg-type]
                else:
                    field_meta = [FieldMeta(name=str(f)) for f in raw_fields]
            elif isinstance(raw_fields, dict):
                field_meta = [FieldMeta(name=k, **v) for k, v in raw_fields.items()]
            else:
                raise RuntimeError("Unsupported 'fields' format in schema JSON")

            # Render extraction prompt
            from jinja2 import Environment, FileSystemLoader

            env = Environment(loader=FileSystemLoader("src/edgar_ai/prompts"))
            prompt_text = env.get_template("extractor.jinja").render(fields=field_meta)

            if verbose:
                _log("  → Extractor system prompt ⬇")
                _log(prompt_text.replace("\n", "\n      "))

            prompt_obj = Prompt(text=prompt_text, schema_def=Schema(name=f"schema_{schema_hash}", fields=field_meta))

            _log("  → Extracting rows via LLM…")
            rows_objs = _svc_extractor.run([doc], prompt_obj)
            _log(f"    Extractor returned {len(rows_objs)} row(s)")

            # Snapshot prompt & rows
            try:
                save_prompt(prompt_obj, schema_hash)
            except Exception:
                pass
            try:
                save_rows(doc.doc_id, rows_objs)
            except Exception:
                pass

            all_rows.extend(rows_objs)

        for row in all_rows:
            console.print_json(_json.dumps(row.data))


if __name__ == "__main__":  # pragma: no cover
    main()
