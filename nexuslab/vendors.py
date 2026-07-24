"""Bridges to the three vendored upstream labs (git submodules under labs/).

| Lab | Upstream | Pillar |
|-----|----------|--------|
| Multi-Agents-Debate | Skytliang/Multi-Agents-Debate | MAD multi-agent debate (GPL-3.0) |
| awesome-harness-engineering | ai-boost/awesome-harness-engineering | Agent harness engineering (CC0) |
| loop-engineering | cobusgreyling/loop-engineering | GitHub/agent loop multi-agent (MIT) |
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def labs_root() -> Path:
    return repo_root() / "labs"


VENDORS: dict[str, dict[str, str]] = {
    "mad": {
        "dir": "Multi-Agents-Debate",
        "url": "https://github.com/Skytliang/Multi-Agents-Debate",
        "license": "GPL-3.0",
        "pillar": "Multi-agent debate (MAD)",
        "marker": "code/utils/agent.py",
    },
    "ahe": {
        "dir": "awesome-harness-engineering",
        "url": "https://github.com/ai-boost/awesome-harness-engineering",
        "license": "CC0-1.0",
        "pillar": "Agent harness engineering",
        "marker": "templates/PLAN.md",
    },
    "loop": {
        "dir": "loop-engineering",
        "url": "https://github.com/cobusgreyling/loop-engineering",
        "license": "MIT",
        "pillar": "GitHub multi-agent / loop engineering",
        "marker": "patterns/pr-babysitter.md",
    },
}


@dataclass
class VendorStatus:
    key: str
    present: bool
    path: Path
    url: str
    license: str
    pillar: str


def vendor_path(key: str) -> Path:
    meta = VENDORS[key]
    return labs_root() / meta["dir"]


def status_all() -> list[VendorStatus]:
    out: list[VendorStatus] = []
    for key, meta in VENDORS.items():
        p = vendor_path(key)
        marker = p / meta["marker"]
        out.append(
            VendorStatus(
                key=key,
                present=marker.is_file(),
                path=p,
                url=meta["url"],
                license=meta["license"],
                pillar=meta["pillar"],
            )
        )
    return out


def format_status() -> str:
    lines = ["vendored labs (submodules under labs/):"]
    for s in status_all():
        mark = "OK" if s.present else "MISSING"
        lines.append(f"  [{mark}] {s.key:5} {s.pillar}")
        lines.append(f"         {s.path}")
        lines.append(f"         {s.url} ({s.license})")
    missing = [s for s in status_all() if not s.present]
    if missing:
        lines.append("")
        lines.append("Fix: git submodule update --init --recursive")
    return "\n".join(lines)


# ── MAD ──────────────────────────────────────────────────────────────────────


def mad_root() -> Path:
    return vendor_path("mad")


def load_mad_config() -> dict[str, Any]:
    cfg = mad_root() / "code" / "utils" / "config4all.json"
    if not cfg.is_file():
        raise FileNotFoundError(f"MAD config missing: {cfg} — init submodule")
    return json.loads(cfg.read_text(encoding="utf-8"))


def mad_prompts_for_topic(topic: str) -> dict[str, str]:
    cfg = load_mad_config()
    out: dict[str, str] = {}
    for k, v in cfg.items():
        if isinstance(v, str):
            out[k] = v.replace("##debate_topic##", topic)
        else:
            out[k] = v  # type: ignore[assignment]
    out["debate_topic"] = topic
    return out


def mad_code_files() -> list[Path]:
    root = mad_root() / "code"
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def run_mad_interactive_hint() -> str:
    root = mad_root()
    return f"""# Run upstream MAD interactive (needs OpenAI key; GPL-3.0 component)

cd "{root}"
# set OPENAI_API_KEY / edit interactive.py key as upstream docs
python interactive.py

# Or batch:
# sh debate4tran.sh

# Prefer offline durable council (no OpenAI dependency):
NexusLab council init my-mad --profile mad --topic "Your question"
"""


# ── awesome-harness-engineering ──────────────────────────────────────────────


def ahe_templates_dir() -> Path:
    return vendor_path("ahe") / "templates"


def copy_ahe_templates(dest: Path) -> list[Path]:
    src = ahe_templates_dir()
    if not src.is_dir():
        raise FileNotFoundError(f"AHE templates missing: {src}")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for f in sorted(src.iterdir()):
        if f.is_file():
            target = dest / f.name
            shutil.copy2(f, target)
            written.append(target)
    # also AGENTS.md / CLAUDE.md from root if present
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        p = vendor_path("ahe") / name
        if p.is_file() and name != "README.md":
            t = dest / f"AHE_{name}"
            shutil.copy2(p, t)
            written.append(t)
    return written


# ── loop-engineering ─────────────────────────────────────────────────────────


def loop_eng_root() -> Path:
    return vendor_path("loop")


def list_loop_patterns() -> list[Path]:
    d = loop_eng_root() / "patterns"
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.name != "README.md")


def list_loop_tools() -> list[str]:
    d = loop_eng_root() / "tools"
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir())


def copy_loop_pattern(name: str, dest: Path) -> Path:
    src = loop_eng_root() / "patterns" / name
    if not src.suffix:
        src = src.with_suffix(".md")
    if not src.is_file():
        # try with .md
        cand = loop_eng_root() / "patterns" / f"{name}.md"
        if cand.is_file():
            src = cand
        else:
            raise FileNotFoundError(f"pattern not found: {name}")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def run_loop_node_tool(tool: str, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run a loop-engineering tool CLI if node + dist exists."""
    tool_dir = loop_eng_root() / "tools" / tool
    cli_js = tool_dir / "dist" / "cli.js"
    if not cli_js.is_file():
        raise FileNotFoundError(
            f"{cli_js} missing — build with: cd labs/loop-engineering && npm run build:tools"
        )
    cmd = ["node", str(cli_js), *(args or [])]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(tool_dir))
