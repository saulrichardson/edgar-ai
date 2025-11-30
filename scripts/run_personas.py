#!/usr/bin/env python3
"""Run persona pipeline sequentially on a prompt_view file."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from pipeline.runner import run_pipeline


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_view", help="Path to prompt_view.txt")
    ap.add_argument("--goal", help="Optional goal text (skip Goal-Setter)")
    ap.add_argument("--artifacts", default="artifacts", help="Where to store outputs")
    args = ap.parse_args()

    text = Path(args.prompt_view).read_text()
    exhibit_id = Path(args.prompt_view).parent.name

    result = run_pipeline(
        exhibit_text=text,
        exhibit_id=exhibit_id,
        goal_text=args.goal,
        artifacts_dir=args.artifacts,
    )

    print("Champion variant:", result.champion)
    print("Goal:", result.goal)
    print("Variants:", ", ".join(result.variants))
    print(f"Artifacts written under {args.artifacts}/{exhibit_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
