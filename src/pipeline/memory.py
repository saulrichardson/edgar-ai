from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _slugify(value: str, *, max_len: int = 48) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if not s:
        return "goal"
    return s[:max_len].rstrip("-")


def stable_goal_id(goal_title: str) -> str:
    slug = _slugify(goal_title)
    digest = hashlib.sha1(goal_title.encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}"


@dataclass(frozen=True)
class GoalRecord:
    goal_id: str
    title: str
    blueprint: str
    created_at: str
    updated_at: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "GoalRecord":
        return cls(
            goal_id=str(data["goal_id"]),
            title=str(data["title"]),
            blueprint=str(data.get("blueprint") or ""),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "blueprint": self.blueprint,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ChampionRecord:
    goal_id: str
    candidate_id: str
    schema: Any
    prompt: Optional[str]
    governor_decision: Optional[Any]
    updated_at: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ChampionRecord":
        return cls(
            goal_id=str(data["goal_id"]),
            candidate_id=str(data["candidate_id"]),
            schema=data.get("schema"),
            prompt=data.get("prompt"),
            governor_decision=data.get("governor_decision"),
            updated_at=str(data["updated_at"]),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "candidate_id": self.candidate_id,
            "schema": self.schema,
            "prompt": self.prompt,
            "governor_decision": self.governor_decision,
            "updated_at": self.updated_at,
        }


class MemoryStore:
    def __init__(self, root_dir: str | Path | None = None) -> None:
        root = root_dir or os.getenv("EDGAR_AI_MEMORY_DIR", "memory")
        self.root_dir = Path(root)

    def _goal_dir(self, goal_id: str) -> Path:
        return self.root_dir / "goals" / goal_id

    def list_goals(self) -> List[GoalRecord]:
        base = self.root_dir / "goals"
        if not base.exists():
            return []
        goals: List[GoalRecord] = []
        for goal_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            goal_file = goal_dir / "goal.json"
            if not goal_file.exists():
                continue
            try:
                data = json.loads(goal_file.read_text(encoding="utf-8"))
                goals.append(GoalRecord.from_json(data))
            except Exception:
                continue
        return goals

    def get_goal(self, goal_id: str) -> Optional[GoalRecord]:
        goal_file = self._goal_dir(goal_id) / "goal.json"
        if not goal_file.exists():
            return None
        data = json.loads(goal_file.read_text(encoding="utf-8"))
        return GoalRecord.from_json(data)

    def upsert_goal(self, *, title: str, blueprint: str, goal_id: str | None = None) -> GoalRecord:
        gid = goal_id or stable_goal_id(title)
        existing = self.get_goal(gid)
        created_at = existing.created_at if existing else _now_iso()
        record = GoalRecord(
            goal_id=gid,
            title=title,
            blueprint=blueprint,
            created_at=created_at,
            updated_at=_now_iso(),
        )
        goal_file = self._goal_dir(gid) / "goal.json"
        _atomic_write_text(goal_file, json.dumps(record.to_json(), ensure_ascii=False, indent=2))
        return record

    def get_champion(self, goal_id: str) -> Optional[ChampionRecord]:
        champ_file = self._goal_dir(goal_id) / "champion.json"
        if not champ_file.exists():
            return None
        data = json.loads(champ_file.read_text(encoding="utf-8"))
        return ChampionRecord.from_json(data)

    def set_champion(
        self,
        *,
        goal_id: str,
        candidate_id: str,
        schema: Any,
        prompt: Optional[str],
        governor_decision: Optional[Any],
    ) -> ChampionRecord:
        record = ChampionRecord(
            goal_id=goal_id,
            candidate_id=candidate_id,
            schema=schema,
            prompt=prompt,
            governor_decision=governor_decision,
            updated_at=_now_iso(),
        )
        champ_file = self._goal_dir(goal_id) / "champion.json"
        _atomic_write_text(champ_file, json.dumps(record.to_json(), ensure_ascii=False, indent=2))
        return record

