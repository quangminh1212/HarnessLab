"""Scaffold minimal pipeline example under a project directory."""

from __future__ import annotations

from pathlib import Path

EXAMPLE = """# Example Harness-style pipeline (scaffold only — adapt to your runner)
# NexusLab YAGNI: author real pipelines after local Harness is running.

pipeline:
  name: xlab-smoke
  stages:
    - name: test
      steps:
        - name: unit
          type: run
          command: |
            python -m pytest -q
"""


def write_pipeline_scaffold(target: Path) -> list[Path]:
    target = Path(target)
    pipe_dir = target / ".harness" / "pipelines"
    pipe_dir.mkdir(parents=True, exist_ok=True)
    path = pipe_dir / "xlab-smoke.yaml"
    path.write_text(EXAMPLE, encoding="utf-8")
    return [path]
