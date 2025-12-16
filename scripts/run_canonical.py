#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pipeline.runner import run_pipeline


def main() -> int:
    ap = argparse.ArgumentParser(description="Run schema-discovery pipeline on a full document (canonical.txt).")
    ap.add_argument("--doc", default="canonical.txt", help="Path to canonical document text")
    ap.add_argument("--exhibit-id", default="canonical", help="Identifier used for artifacts directory naming")
    ap.add_argument("--goal", help="Optional goal text or goal JSON (skip routing/goal-setter)")
    ap.add_argument("--artifacts", default="artifacts", help="Where to store per-run outputs")
    ap.add_argument("--memory", default=None, help="Memory directory (defaults to EDGAR_AI_MEMORY_DIR or ./memory)")
    ap.add_argument(
        "--proposers",
        default=None,
        help="Comma-separated schema proposer styles (default: all built-ins)",
    )
    ap.add_argument(
        "--critics",
        default=None,
        help="Comma-separated schema critic styles (default: all built-ins)",
    )
    ap.add_argument("--provenance", action="store_true", help="Include provenance offsets/snippets in extraction output")
    ap.add_argument(
        "--schema-tutor",
        action="store_true",
        help="Enable an extra tutor round to propose a challenger schema",
    )
    args = ap.parse_args()

    text = Path(args.doc).read_text(encoding="utf-8")
    proposer_styles = [s.strip() for s in args.proposers.split(",") if s.strip()] if args.proposers else None
    critic_styles = [s.strip() for s in args.critics.split(",") if s.strip()] if args.critics else None

    result, _state = run_pipeline(
        exhibit_text=text,
        exhibit_id=args.exhibit_id,
        goal_text=args.goal,
        artifacts_dir=args.artifacts,
        memory_dir=args.memory,
        include_provenance=args.provenance,
        enable_schema_tutor=args.schema_tutor,
        proposer_styles=proposer_styles,
        critic_styles=critic_styles,
    )

    print("Goal:", result.goal_title, f"({result.goal_id})")
    print("Candidates:", ", ".join(result.candidates))
    print("Champion:", result.champion_candidate_id)
    if result.artifacts_dir:
        print(f"Artifacts: {result.artifacts_dir}/{args.exhibit_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
