"""Multi-agent council harness for GitHub issues/PRs.

Inspired by MAD (Multi-Agent Debate) + agent harness engineering:
  proposers / critics / verifier debate a GitHub artifact, then synthesize a decision.
State is durable on disk so Hermes (or humans) can fill turns without losing context.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

DEFAULT_ROLES: list[dict[str, str]] = [
    {
        "id": "proposer",
        "title": "Proposer",
        "stance": "affirmative",
        "brief": "Argue for a concrete solution; cite evidence from the GitHub context.",
    },
    {
        "id": "critic",
        "title": "Critic",
        "stance": "negative",
        "brief": "Challenge flaws, risks, missing tests, security, and scope creep.",
    },
    {
        "id": "verifier",
        "title": "Verifier",
        "stance": "judge",
        "brief": "Score both sides; require evidence; block weak claims; drive consensus.",
    },
    {
        "id": "synthesizer",
        "title": "Synthesizer",
        "stance": "closeout",
        "brief": "Produce DECISION.md: recommendation, risks, next actions, optional PR comment.",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class Turn:
    round: int
    role_id: str
    content: str
    at: str = field(default_factory=_utc_now)


@dataclass
class CouncilState:
    name: str
    topic: str
    profile: str = "github"
    github: dict[str, Any] = field(default_factory=dict)
    max_rounds: int = 2
    current_round: int = 1
    next_role_index: int = 0
    roles: list[dict[str, str]] = field(default_factory=lambda: list(DEFAULT_ROLES))
    turns: list[dict[str, Any]] = field(default_factory=list)
    status: str = "open"  # open | debating | decided | closed
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def next_role(self) -> dict[str, str]:
        return self.roles[self.next_role_index % len(self.roles)]

    def record_turn(self, content: str, role_id: str | None = None) -> dict[str, Any]:
        role = None
        if role_id:
            for r in self.roles:
                if r["id"] == role_id:
                    role = r
                    break
        if role is None:
            role = self.next_role()
        turn = asdict(
            Turn(round=self.current_round, role_id=role["id"], content=content.strip())
        )
        self.turns.append(turn)
        self.status = "debating"
        # advance role pointer
        idx = next((i for i, r in enumerate(self.roles) if r["id"] == role["id"]), 0)
        self.next_role_index = (idx + 1) % len(self.roles)
        if self.next_role_index == 0:
            self.current_round += 1
            if self.current_round > self.max_rounds:
                self.status = "decided"
        self.updated_at = _utc_now()
        return turn

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "topic": self.topic,
            "profile": self.profile,
            "github": self.github,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round,
            "next_role_index": self.next_role_index,
            "roles": self.roles,
            "turns": self.turns,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CouncilState:
        return cls(
            name=str(data.get("name") or "council"),
            topic=str(data.get("topic") or ""),
            profile=str(data.get("profile") or "github"),
            github=dict(data.get("github") or {}),
            max_rounds=int(data.get("max_rounds") or 2),
            current_round=int(data.get("current_round") or 1),
            next_role_index=int(data.get("next_role_index") or 0),
            roles=list(data.get("roles") or DEFAULT_ROLES),
            turns=list(data.get("turns") or []),
            status=str(data.get("status") or "open"),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or _utc_now()),
        )


def council_dir(root: Path, name: str) -> Path:
    return Path(root) / "councils" / name


def state_path(root: Path, name: str) -> Path:
    return council_dir(root, name) / "council.yaml"


def load_state(path: Path) -> CouncilState:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise RuntimeError("PyYAML required to load council.yaml")
        data = yaml.safe_load(text) or {}
    return CouncilState.from_dict(data)


def save_state(state: CouncilState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = state.to_dict()
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    if yaml is None:
        # fallback json sibling
        j = path.with_suffix(".json")
        j.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def init_council(
    root: Path,
    name: str,
    topic: str,
    *,
    max_rounds: int = 2,
    github: dict[str, Any] | None = None,
    profile: str = "github",
    mad_prompts: dict[str, str] | None = None,
) -> tuple[CouncilState, list[Path]]:
    from harnesslab.profiles import get_profile, roles_for

    prof = get_profile(profile)
    roles = roles_for(profile)
    if max_rounds is None or max_rounds <= 0:
        max_rounds = int(prof.get("max_rounds_default") or 2)

    d = council_dir(root, name)
    d.mkdir(parents=True, exist_ok=True)
    state = CouncilState(
        name=name,
        topic=topic,
        profile=profile,
        max_rounds=max_rounds,
        github=github or {},
        roles=roles,
    )
    sp = state_path(root, name)
    save_state(state, sp)
    written = [sp]

    ctx = d / "CONTEXT.md"
    gh = state.github
    mad_block = ""
    if mad_prompts:
        mad_block = (
            "\n## MAD prompts (from Multi-Agents-Debate config4all.json)\n"
            f"- player_meta: {mad_prompts.get('player_meta_prompt', '')[:300]}\n"
            f"- affirmative: {mad_prompts.get('affirmative_prompt', '')[:200]}\n"
            f"- negative: {mad_prompts.get('negative_prompt', '')[:200]}\n"
        )
    ctx.write_text(
        f"""# Council context — {name}

## Profile
- id: {profile}
- title: {prof.get('title')}
- source: {prof.get('source')}
- turn_format: {prof.get('turn_format')}

## Topic
{topic}

## GitHub
- kind: {gh.get("kind", "(none)")}
- repo: {gh.get("repo", "(none)")}
- number: {gh.get("number", "(none)")}
- url: {gh.get("url", "(none)")}
- title: {gh.get("title", "(none)")}

## Body
{gh.get("body") or "(no body pulled — run HarnessLab github pull)"}
{mad_block}
## Roles
"""
        + "\n".join(f"- **{r['id']}** ({r['stance']}): {r['brief']}" for r in state.roles)
        + "\n",
        encoding="utf-8",
    )
    written.append(ctx)

    transcript = d / "TRANSCRIPT.md"
    if not transcript.exists():
        transcript.write_text(
            f"# Transcript — {name}\n\n_Topic:_ {topic}\n\n",
            encoding="utf-8",
        )
        written.append(transcript)

    decision = d / "DECISION.md"
    if not decision.exists():
        decision.write_text(
            f"""# Decision — {name}

status: pending

## Recommendation
(none yet)

## Risks
- (none)

## Next actions
- [ ] complete debate rounds
- [ ] optional: post summary to GitHub
""",
            encoding="utf-8",
        )
        written.append(decision)

    return state, written


def append_transcript(root: Path, name: str, turn: dict[str, Any], role_title: str) -> Path:
    path = council_dir(root, name) / "TRANSCRIPT.md"
    block = (
        f"\n## Round {turn['round']} — {role_title} (`{turn['role_id']}`)\n"
        f"_at {turn['at']}_\n\n{turn['content']}\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    return path


def prompt_for_next(state: CouncilState) -> str:
    role = state.next_role()
    prior = state.turns[-3:] if state.turns else []
    prior_txt = "\n\n".join(
        f"[{t['role_id']} r{t['round']}]: {t['content'][:800]}" for t in prior
    ) or "(no prior turns)"
    gh = state.github
    return f"""# Council turn prompt

You are **{role['title']}** (`{role['id']}`, stance={role['stance']}).
{role['brief']}

## Topic
{state.topic}

## GitHub
{gh.get('kind', 'n/a')} {gh.get('repo', '')}#{gh.get('number', '')} — {gh.get('title', '')}
URL: {gh.get('url', '')}

## Prior turns (recent)
{prior_txt}

## Rules
- Stay in role; do not impersonate other roles.
- Cite concrete evidence from CONTEXT.md / GitHub body / MAD prompts.
- End with structured tags for this profile (see CONTEXT.md turn_format).

When done, record via:
  HarnessLab council turn {state.name} --role {role['id']} --file turn.md
"""


def status_text(state: CouncilState) -> str:
    role = state.next_role()
    lines = [
        f"council: {state.name}",
        f"  profile: {getattr(state, 'profile', 'github')}",
        f"  status: {state.status}",
        f"  topic: {state.topic}",
        f"  round: {state.current_round}/{state.max_rounds}",
        f"  turns: {len(state.turns)}",
        f"  next: {role['id']} ({role['title']})",
    ]
    if state.github:
        lines.append(
            f"  github: {state.github.get('kind')} "
            f"{state.github.get('repo')}#{state.github.get('number')}"
        )
    return "\n".join(lines)


def write_decision_scaffold(root: Path, name: str, state: CouncilState) -> Path:
    path = council_dir(root, name) / "DECISION.md"
    claims = []
    for t in state.turns:
        if "CLAIM:" in t["content"]:
            claims.append(f"- ({t['role_id']}) {t['content'].split('CLAIM:')[-1].strip()[:200]}")
    path.write_text(
        f"""# Decision — {name}

status: {state.status}
updated: {state.updated_at}

## Topic
{state.topic}

## GitHub
{state.github.get('url') or '(none)'}

## Claims heard
{chr(10).join(claims) if claims else '- (none tagged CLAIM:)'}

## Recommendation
(synthesizer: fill after final round)

## Risks
- 

## Next actions
- [ ] 
- [ ] optional: `gh pr comment` / `gh issue comment` with summary

## Transcript
See TRANSCRIPT.md ({len(state.turns)} turns)
""",
        encoding="utf-8",
    )
    return path
