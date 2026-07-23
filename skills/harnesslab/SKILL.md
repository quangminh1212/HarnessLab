---
name: harnesslab
description: >
  HarnessLab multi-AI council on GitHub: many agents debate one issue/PR
  (proposer/critic/verifier/synthesizer), durable TRANSCRIPT + DECISION.
  Activate with /harnesslab. Use when user wants multiple AIs to discuss,
  review, or argue about a GitHub issue, PR, or design decision.
compatibility: Requires terminal; gh CLI recommended for GitHub pull
metadata:
  author: HarnessLab
  version: "0.2.0"
  hermes:
    tags: [multi-agent, debate, council, github, harness, review]
    category: development
    requires_toolsets: [terminal]
---

# HarnessLab — multi-AI GitHub council

You run an **agent harness**: roles + durable state + GitHub context + verify/closeout.
Goal: **nhiều AI bàn luận** trên một issue/PR rồi chốt quyết định có bằng chứng.

SoT: `C:\Dev\HarnessLab` (junction only — no hermes-agent patches).

```powershell
python -m harnesslab attach
python -m harnesslab council init <name> --ref owner/repo#n --topic "..."
python -m harnesslab council next <name>
python -m harnesslab council turn <name> --role <id> --file turn.md
python -m harnesslab council decide <name>
```

## Roles (default)

| id | Job |
|----|-----|
| `proposer` | Affirmative: propose solution with evidence |
| `critic` | Negative: attack gaps, security, tests, scope |
| `verifier` | Judge: score evidence; block weak claims |
| `synthesizer` | Closeout: write DECISION.md + optional `gh` comment recipe |

Inspired by **MAD** (Multi-Agent Debate): truth from clash of ideas; avoid single-agent “degeneration of thoughts”.

## Workflow (autonomous after user gives topic/ref)

1. **Init** council under project (or `C:\Dev\HarnessLab\runs\...`).
2. **Pull** GitHub context if `--ref` given (`gh issue/pr view`).
3. For each round × role (except skip synthesizer until end of last round):
   - `council next` → fill turn as that role only
   - End every turn with: `CLAIM: … | EVIDENCE: … | ASK: …`
   - `council turn --role … --content/file …`
4. **Decide** → refresh DECISION.md; offer `gh issue comment` / `gh pr comment`.
5. Do **not** merge/close GitHub items unless user explicitly asks.

## Hard rules

- One turn = one role. Never write as two roles in one message.
- Cite GitHub body / files / comments; no invented CI results.
- Prefer durable files (`CONTEXT.md`, `TRANSCRIPT.md`, `DECISION.md`) over chat-only memory.
- If blocked >1 step, re-read CONTEXT + last 3 turns, then continue.
- Relation: **CrewLab** = ship with one-task-per-agent meetings; **LoopLab** = single OPAV loop; **HarnessLab** = multi-voice debate on a GitHub artifact.

## Secondary (optional)

Harness Open Source Docker CI (`python -m harnesslab recipe docker-run`) — only if user asks for self-hosted Harness UI, not the default path.
