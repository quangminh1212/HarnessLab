"""Harness readiness score (0–100) — agent harness engineering checklist."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScoreResult:
    score: int
    band: str
    checks: list[tuple[str, bool, int]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"score: {self.score}/100 ({self.band})"]
        for name, ok, pts in self.checks:
            mark = "+" if ok else "-"
            lines.append(f"  {mark} {name} ({pts})")
        return "\n".join(lines)


def _exists(root: Path, *parts: str) -> bool:
    return (root.joinpath(*parts)).exists()


def score_project(root: Path) -> ScoreResult:
    root = Path(root)
    checks: list[tuple[str, bool, int]] = []

    def add(name: str, ok: bool, pts: int) -> None:
        checks.append((name, ok, pts if ok else 0))

    # Agent harness engineering
    add("HARNESS.md or AGENTS.md", _exists(root, "HARNESS.md") or _exists(root, "AGENTS.md"), 15)
    add("PLAN.md", _exists(root, "PLAN.md"), 10)
    add("STATE.md", _exists(root, "STATE.md"), 10)
    add("loop workspace (loops/)", (root / "loops").is_dir(), 10)
    # MAD / council
    add("council workspace (councils/)", (root / "councils").is_dir(), 15)
    # GitHub multi-agent
    add("typed handoffs dir", (root / "handoffs").is_dir(), 15)
    has_handoff = False
    hd = root / "handoffs"
    if hd.is_dir():
        has_handoff = any(hd.glob("*.yaml")) or any(hd.glob("*.yml")) or any(hd.glob("*.json"))
    add("at least one handoff file", has_handoff, 10)
    # Tooling
    add("git repo", (root / ".git").exists(), 5)
    add("tests/ or pytest", (root / "tests").is_dir() or _exists(root, "pyproject.toml"), 10)

    total = sum(p for _, _, p in checks)
    if total >= 80:
        band = "ready"
    elif total >= 50:
        band = "partial"
    else:
        band = "thin"
    # recompute with actual points
    checks_out: list[tuple[str, bool, int]] = []
    for name, ok, _ in checks:
        # recover intended points from definition
        pts_map = {
            "HARNESS.md or AGENTS.md": 15,
            "PLAN.md": 10,
            "STATE.md": 10,
            "loop workspace (loops/)": 10,
            "council workspace (councils/)": 15,
            "typed handoffs dir": 15,
            "at least one handoff file": 10,
            "git repo": 5,
            "tests/ or pytest": 10,
        }
        max_p = pts_map.get(name, 0)
        checks_out.append((name, ok, max_p if ok else 0))
    total = sum(p for _, _, p in checks_out)
    return ScoreResult(score=total, band=band if total >= 50 else "thin", checks=checks_out)
