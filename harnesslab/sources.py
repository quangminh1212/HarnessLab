"""GitHub equivalent-source catalog for HarnessLab."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from harnesslab.profiles import list_profiles


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def catalog_path() -> Path:
    return repo_root() / "sources" / "catalog.yaml"


@dataclass
class SourceEntry:
    id: str
    url: str
    license: str
    status: str
    role: str
    evidence: list[str]


def load_catalog() -> list[SourceEntry]:
    data = yaml.safe_load(catalog_path().read_text(encoding="utf-8")) or {}
    out: list[SourceEntry] = []
    for e in data.get("entries") or []:
        if not isinstance(e, dict):
            continue
        out.append(
            SourceEntry(
                id=str(e.get("id") or ""),
                url=str(e.get("url") or ""),
                license=str(e.get("license") or ""),
                status=str(e.get("status") or "referenced"),
                role=str(e.get("role") or ""),
                evidence=[str(x) for x in (e.get("evidence") or [])],
            )
        )
    return out


def check_catalog(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    problems: list[str] = []
    for e in load_catalog():
        if e.status != "integrated":
            continue
        if not e.evidence:
            problems.append(f"{e.id}: integrated but no evidence")
        for rel in e.evidence:
            if not (root / rel).exists():
                problems.append(f"{e.id}: missing {rel}")
    # required council profiles from debate literature
    for need in ("mad", "chateval", "swe", "harness", "github"):
        if need not in list_profiles():
            problems.append(f"missing council profile: {need}")
    return problems


def format_catalog() -> str:
    lines = ["HarnessLab GitHub equivalent sources:", ""]
    for e in load_catalog():
        lines.append(f"  [{e.status:10}] {e.id:32} {e.url}")
        lines.append(f"               {e.role}")
    lines.append("")
    lines.append("council profiles: " + ", ".join(list_profiles()))
    problems = check_catalog()
    lines.append("check: PASS" if not problems else f"check: FAIL ({len(problems)})")
    for p in problems:
        lines.append(f"  - {p}")
    return "\n".join(lines)
