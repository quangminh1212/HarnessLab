"""Project-level harness scaffold (agent harness engineering)."""

from __future__ import annotations

from pathlib import Path

FILES: dict[str, str] = {
    "HARNESS.md": """# HARNESS.md

This repo is agent-ready. NexusLab unifies:

1. **Agent harness engineering** — loop, context, plan, verify, state
2. **MAD multi-agent debate** — devil / angel / judge
3. **GitHub multi-agent** — typed handoffs on issues/PRs

## Commands

```text
NexusLab score .
NexusLab loop init <name> --goal "..."
NexusLab council init <name> --profile mad|github|harness --ref owner/repo#n
NexusLab handoff validate path/to/handoff.yaml
NexusLab github pull --ref owner/repo#n
```

## Rules

- Prefer durable files over chat-only memory
- Every multi-agent handoff needs schema (from_role, to_role, intent, payload, acceptance)
- No success claim without VERIFY evidence
""",
    "AGENTS.md": """# AGENTS.md

## Roles available via NexusLab

### Profile `mad`
- devil (affirmative), angel (negative), judge

### Profile `github`
- proposer, critic, verifier, synthesizer

### Profile `harness`
- observer, planner, actor, verifier, closeout

## Conventions
- One agent turn = one role
- End turns with structured tags (CLAIM/EVIDENCE or PHASE_NOTE/VERIFY)
""",
    "PLAN.md": """# PLAN.md

## Goal
(fill)

## Milestones
1. [ ] 
2. [ ] 

## Risk
L0–L5:

## Stop conditions
- 

## Verification
- 
""",
    "STATE.md": """# STATE.md

- last_run: never
- last_status: never
- open_blockers: none
- harness_mode: idle
""",
}


def scaffold_project(root: Path) -> list[Path]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, body in FILES.items():
        path = root / name
        if not path.exists():
            path.write_text(body, encoding="utf-8")
            written.append(path)
    handoffs = root / "handoffs"
    handoffs.mkdir(exist_ok=True)
    ex = handoffs / "example.yaml"
    if not ex.exists():
        ex.write_text(
            """from_role: proposer
to_role: critic
intent: review_change
payload:
  focus: [tests, security]
acceptance:
  - cite file paths
  - separate blocking vs nit
evidence: []
status: pending
""",
            encoding="utf-8",
        )
        written.append(ex)
    return written
