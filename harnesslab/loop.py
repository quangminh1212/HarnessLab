"""OPAV agent loop — core of agent harness engineering.

observe → plan → act → verify → closeout
Durable files: OBSERVE.md, PLAN.md, ACT.md, VERIFY.md, STATE.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class Phase(str, Enum):
    OBSERVE = "observe"
    PLAN = "plan"
    ACT = "act"
    VERIFY = "verify"
    CLOSEOUT = "closeout"


ORDER = [Phase.OBSERVE, Phase.PLAN, Phase.ACT, Phase.VERIFY, Phase.CLOSEOUT]

PHASE_FILES = {
    Phase.OBSERVE: "OBSERVE.md",
    Phase.PLAN: "PLAN.md",
    Phase.ACT: "ACT.md",
    Phase.VERIFY: "VERIFY.md",
    Phase.CLOSEOUT: "STATE.md",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class LoopState:
    name: str
    goal: str
    phase: str = Phase.OBSERVE.value
    pending_verification: bool = False
    mutations: int = 0
    verifications: list[dict[str, Any]] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def advance(self) -> Phase:
        cur = Phase(self.phase)
        idx = ORDER.index(cur)
        if idx >= len(ORDER) - 1:
            return cur
        nxt = ORDER[idx + 1]
        self.phase = nxt.value
        self.history.append(f"{_utc_now()} advance→{nxt.value}")
        self.updated_at = _utc_now()
        return nxt

    def record_mutation(self) -> None:
        if self.phase != Phase.ACT.value:
            raise ValueError("mutations only in act phase")
        self.mutations += 1
        self.pending_verification = True
        self.history.append(f"{_utc_now()} mutation#{self.mutations}")
        self.updated_at = _utc_now()

    def record_verification(self, passed: bool, note: str = "") -> None:
        if self.phase != Phase.VERIFY.value:
            raise ValueError("verification only in verify phase")
        self.verifications.append(
            {"passed": passed, "note": note, "at": _utc_now(), "after_mutations": self.mutations}
        )
        self.pending_verification = False
        self.history.append(f"{_utc_now()} verify={'PASS' if passed else 'FAIL'}")
        self.updated_at = _utc_now()

    def panel(self) -> str:
        lines = [
            f"loop: {self.name}",
            f"  goal: {self.goal}",
            f"  phase: **{self.phase}**",
            f"  pending_verification: {self.pending_verification}",
            f"  mutations: {self.mutations}",
            f"  verifications: {len(self.verifications)}",
            "",
            "## Cycle",
        ]
        for p in ORDER:
            mark = "→" if p.value == self.phase else " "
            lines.append(f"{mark} {p.value}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LoopState:
        return cls(
            name=str(data.get("name") or "loop"),
            goal=str(data.get("goal") or ""),
            phase=str(data.get("phase") or Phase.OBSERVE.value),
            pending_verification=bool(data.get("pending_verification")),
            mutations=int(data.get("mutations") or 0),
            verifications=list(data.get("verifications") or []),
            history=list(data.get("history") or []),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or _utc_now()),
        )


def loop_dir(root: Path, name: str) -> Path:
    return Path(root) / "loops" / name


def save_loop(state: LoopState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = state.to_dict()
    if yaml is None:
        import json

        path.with_suffix(".json").write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )
        return
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_loop(path: Path) -> LoopState:
    import json

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return LoopState.from_dict(json.loads(text))
    if yaml is None:
        raise RuntimeError("PyYAML required")
    return LoopState.from_dict(yaml.safe_load(text) or {})


def init_loop(root: Path, name: str, goal: str) -> tuple[LoopState, list[Path]]:
    d = loop_dir(root, name)
    d.mkdir(parents=True, exist_ok=True)
    state = LoopState(name=name, goal=goal)
    sp = d / "loop.yaml"
    save_loop(state, sp)
    written = [sp]
    templates = {
        "OBSERVE.md": f"# Observe — {name}\n\n## Goal\n{goal}\n\n## Signals\n- \n\n## No mutations this phase\n",
        "PLAN.md": f"# Plan — {name}\n\n## Steps\n1. \n\n## Risk\nL0–L5: \n\n## Stop when\n- \n\n## Verify with\n- \n",
        "ACT.md": f"# Act — {name}\n\n## Actions taken\n- \n\n## Side effects\n- \n",
        "VERIFY.md": f"# Verify — {name}\n\n## Checks\n- [ ] \n\n## Result\npending\n",
        "STATE.md": f"# State — {name}\n\n- phase: observe\n- last_run: never\n- status: open\n",
        "HARNESS.md": f"""# HARNESS.md — {name}

Agent harness contract (awesome-harness-engineering primitives):

| Primitive | File |
|-----------|------|
| Loop | loop.yaml (observe→plan→act→verify→closeout) |
| Context | OBSERVE.md + goal |
| Plan | PLAN.md |
| Act log | ACT.md |
| Verify | VERIFY.md |
| Memory | STATE.md |

Goal: {goal}
""",
    }
    for fname, body in templates.items():
        p = d / fname
        if not p.exists():
            p.write_text(body, encoding="utf-8")
            written.append(p)
    return state, written
