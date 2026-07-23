"""Environment checks for local Harness Open Source."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DoctorReport:
    ok: bool
    lines: list[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.ok else "WARN"
        body = "\n".join(self.lines)
        return f"doctor: {status}\n{body}"


def default_clone_path() -> Path:
    return Path(os.environ.get("HARNESS_CLONE", r"C:\Dev\harness"))


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _run_ok(args: list[str]) -> tuple[bool, str]:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
        out = (r.stdout or r.stderr or "").strip().splitlines()
        msg = out[0] if out else f"exit {r.returncode}"
        return r.returncode == 0, msg
    except Exception as e:
        return False, str(e)


def run_doctor() -> DoctorReport:
    lines: list[str] = []
    ok = True

    docker = _which("docker")
    if docker:
        lines.append(f"+ docker: {docker}")
        d_ok, d_msg = _run_ok(["docker", "version", "--format", "{{.Server.Version}}"])
        if d_ok:
            lines.append(f"+ docker engine: {d_msg}")
        else:
            lines.append(f"! docker engine not ready: {d_msg}")
            ok = False
    else:
        lines.append("! docker: not on PATH (install Docker Desktop for local Harness)")
        ok = False

    git = _which("git")
    lines.append(f"+ git: {git}" if git else "! git: not on PATH")
    if not git:
        ok = False

    clone = default_clone_path()
    if clone.is_dir() and (clone / ".git").exists():
        lines.append(f"+ clone: {clone}")
    else:
        lines.append(f"- clone missing (optional): {clone}")

    for port in (3000, 3022):
        lines.append(f"- UI/port note: Harness default binds {port} when using docker-run recipe")

    return DoctorReport(ok=ok, lines=lines)
