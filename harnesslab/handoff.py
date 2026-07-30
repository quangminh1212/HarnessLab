"""Typed multi-agent handoffs (GitHub multi-agent engineering pattern).

Multi-agent systems fail like distributed systems without schemas.
Every handoff must declare from_role, to_role, payload, and acceptance criteria.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

REQUIRED_KEYS = ("from_role", "to_role", "intent", "payload", "acceptance")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Handoff:
    from_role: str
    to_role: str
    intent: str
    payload: dict[str, Any] = field(default_factory=dict)
    acceptance: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | accepted | rejected
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Handoff:
        return cls(
            from_role=str(data.get("from_role") or ""),
            to_role=str(data.get("to_role") or ""),
            intent=str(data.get("intent") or ""),
            payload=dict(data.get("payload") or {}),
            acceptance=list(data.get("acceptance") or []),
            evidence=list(data.get("evidence") or []),
            status=str(data.get("status") or "pending"),
            created_at=str(data.get("created_at") or _utc_now()),
        )


def validate_handoff(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for k in REQUIRED_KEYS:
        if k not in data or data[k] in (None, "", [], {}):
            errors.append(f"missing or empty: {k}")
    if data.get("from_role") and data.get("to_role") and data["from_role"] == data["to_role"]:
        errors.append("from_role must differ from to_role")
    if data.get("acceptance") is not None and not isinstance(data.get("acceptance"), list):
        errors.append("acceptance must be a list of strings")
    if data.get("payload") is not None and not isinstance(data.get("payload"), dict):
        errors.append("payload must be an object")
    return errors


def parse_handoff_line(text: str) -> dict[str, str] | None:
    """Parse optional HANDOFF: to_role from a turn line."""
    m = re.search(r"HANDOFF:\s*([a-zA-Z0-9_-]+|none)", text, re.I)
    if not m:
        return None
    target = m.group(1).lower()
    if target == "none":
        return {"to_role": "none"}
    return {"to_role": target}


def write_handoff(path: Path, handoff: Handoff) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = handoff.to_dict()
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    elif yaml is not None:
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    else:
        path = path.with_suffix(".json")
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_handoff(path: Path) -> Handoff:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise RuntimeError("PyYAML required")
        data = yaml.safe_load(text) or {}
    return Handoff.from_dict(data)


def example_handoff() -> dict[str, Any]:
    return {
        "from_role": "proposer",
        "to_role": "critic",
        "intent": "review_pr_diff",
        "payload": {
            "repo": "owner/repo",
            "number": 12,
            "focus": ["security", "tests"],
        },
        "acceptance": [
            "all security claims cite file:line",
            "list blocking vs non-blocking nits",
        ],
        "evidence": [],
        "status": "pending",
    }
