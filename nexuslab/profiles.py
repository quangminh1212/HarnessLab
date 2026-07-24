"""Council/session profiles merging the three pillars.

1. harness  — agent harness engineering (awesome-harness-engineering style)
2. mad      — Multi-Agent Debate (devil / angel / judge)
3. github   — GitHub multi-agent review with typed handoffs
"""

from __future__ import annotations

from typing import Any

PROFILES: dict[str, dict[str, Any]] = {
    "mad": {
        "title": "Multi-Agent Debate (MAD)",
        "source": "https://github.com/Skytliang/Multi-Agents-Debate",
        "description": "Devil vs angel with judge — reduce single-agent degeneration of thoughts.",
        "max_rounds_default": 3,
        "turn_format": "CLAIM: … | EVIDENCE: … | COUNTER: … | ASK: …",
        "roles": [
            {
                "id": "devil",
                "title": "Devil (Affirmative)",
                "stance": "affirmative",
                "brief": (
                    "Argue FOR a concrete answer/solution. Be bold but evidence-based. "
                    "Tit-for-tat with the angel; correct their mistakes when found."
                ),
            },
            {
                "id": "angel",
                "title": "Angel (Negative)",
                "stance": "negative",
                "brief": (
                    "Challenge the devil: bias, missing constraints, wrong assumptions. "
                    "Provide external feedback the devil cannot self-generate."
                ),
            },
            {
                "id": "judge",
                "title": "Judge",
                "stance": "judge",
                "brief": (
                    "Score both sides on evidence quality. Prefer the side that corrects "
                    "errors. End rounds with WINNER: devil|angel|tie and REASON: …"
                ),
            },
        ],
    },
    "github": {
        "title": "GitHub multi-agent review",
        "source": "https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/",
        "description": "Typed multi-agent discussion on issue/PR — handoffs like distributed systems.",
        "max_rounds_default": 2,
        "turn_format": "CLAIM: … | EVIDENCE: … | HANDOFF: role_id|none | ASK: …",
        "roles": [
            {
                "id": "proposer",
                "title": "Proposer",
                "stance": "affirmative",
                "brief": "Propose merge/ship decision or design with file-level evidence from PR/issue.",
            },
            {
                "id": "critic",
                "title": "Critic",
                "stance": "negative",
                "brief": "Security, tests, scope, breaking changes, missing CI — typed objections only.",
            },
            {
                "id": "verifier",
                "title": "Verifier",
                "stance": "judge",
                "brief": "Validate handoffs and claims against CONTEXT.md; block weak evidence.",
            },
            {
                "id": "synthesizer",
                "title": "Synthesizer",
                "stance": "closeout",
                "brief": "Write DECISION.md + optional gh comment body; list residual risks.",
            },
        ],
    },
    "harness": {
        "title": "Agent harness engineering loop",
        "source": "https://github.com/ai-boost/awesome-harness-engineering",
        "description": "Scaffold around the model: observe→plan→act→verify→closeout with durable artifacts.",
        "max_rounds_default": 1,
        "turn_format": "PHASE_NOTE: … | ARTIFACT: path | VERIFY: pass|fail|n/a | ASK: …",
        "roles": [
            {
                "id": "observer",
                "title": "Observer",
                "stance": "observe",
                "brief": "Read CONTEXT, repo signals, prior receipts. No mutations. Write OBSERVE notes.",
            },
            {
                "id": "planner",
                "title": "Planner",
                "stance": "plan",
                "brief": "Produce PLAN.md steps, risk class, stop conditions, verification plan.",
            },
            {
                "id": "actor",
                "title": "Actor",
                "stance": "act",
                "brief": "Smallest safe action only; respect forbidden_actions; prefer worktree for risky changes.",
            },
            {
                "id": "verifier",
                "title": "Verifier",
                "stance": "verify",
                "brief": "Run deterministic checks; refuse success without evidence; update VERIFY section.",
            },
            {
                "id": "closeout",
                "title": "Closeout",
                "stance": "closeout",
                "brief": "Update STATE.md + DECISION/receipt; list side effects and next harness work.",
            },
        ],
    },
    "chateval": {
        "title": "ChatEval multi-agent evaluation",
        "source": "https://github.com/thunlp/ChatEval",
        "description": (
            "Diverse evaluator personas debate quality of an answer/artifact "
            "(ChatEval: multi-agent debate for better LLM evaluators)."
        ),
        "max_rounds_default": 2,
        "turn_format": "SCORE: 1-10 | CLAIM: … | EVIDENCE: … | ASK: …",
        "roles": [
            {
                "id": "generalist",
                "title": "Generalist",
                "stance": "affirmative",
                "brief": "Holistic evaluation: correctness, completeness, clarity.",
            },
            {
                "id": "critic",
                "title": "Critic",
                "stance": "negative",
                "brief": "Stress flaws, hallucinations, missing edge cases, weak evidence.",
            },
            {
                "id": "domain",
                "title": "Domain Specialist",
                "stance": "specialist",
                "brief": "Judge domain-specific accuracy and terminology.",
            },
            {
                "id": "moderator",
                "title": "Moderator",
                "stance": "judge",
                "brief": "Synthesize scores; WINNER or FINAL_SCORE; residual risks.",
            },
        ],
    },
    "swe": {
        "title": "SWE-Debate issue resolution",
        "source": "https://github.com/YerbaPage/SWE-Debate",
        "description": (
            "Competitive multi-agent debate for software issue resolution "
            "(locate → propose → challenge → moderate)."
        ),
        "max_rounds_default": 3,
        "turn_format": "LOC: path:line | CLAIM: … | PATCH_IDEA: … | RISK: … | ASK: …",
        "roles": [
            {
                "id": "locator",
                "title": "Locator",
                "stance": "locate",
                "brief": "Pinpoint files/lines and root-cause hypotheses from issue context.",
            },
            {
                "id": "proposer",
                "title": "Proposer",
                "stance": "affirmative",
                "brief": "Propose concrete fix strategy with tests; cite LOC evidence.",
            },
            {
                "id": "challenger",
                "title": "Challenger",
                "stance": "negative",
                "brief": "Attack weak patches: regressions, missing tests, wrong root cause.",
            },
            {
                "id": "moderator",
                "title": "Moderator",
                "stance": "judge",
                "brief": "Pick best path; write DECISION with acceptance tests and residual risk.",
            },
        ],
    },
}


def list_profiles() -> list[str]:
    return sorted(PROFILES.keys())


def get_profile(name: str) -> dict[str, Any]:
    key = (name or "github").strip().lower()
    if key not in PROFILES:
        raise KeyError(f"unknown profile {name!r}; choose from {', '.join(list_profiles())}")
    return PROFILES[key]


def roles_for(profile: str) -> list[dict[str, str]]:
    p = get_profile(profile)
    return [dict(r) for r in p["roles"]]
