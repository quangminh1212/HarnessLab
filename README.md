# HarnessLab

**Hermes-native multi-AI council harness on GitHub** — many agents debate one issue/PR, leave a durable transcript + decision.

Agent **harness** = scaffolding around models (roles, state, context, verify, closeout), not just a single chat.  
Secondary: optional recipes for [Harness Open Source](https://github.com/harness/harness) Docker/CI.

```text
GitHub issue/PR  →  CONTEXT.md  →  multi-role debate turns  →  TRANSCRIPT.md  →  DECISION.md
                         ↑                    ↑
                    gh pull              Hermes /looplab-style
```

SoT: this repo. Hermes only gets **junctions** (same pattern as LoopLab / CrewLab).

## Quick start

```powershell
cd C:\Dev\HarnessLab
python -m pip install -e ".[dev]"
python -m harnesslab smoke
python -m harnesslab doctor

# Multi-AI council on a GitHub issue
python -m harnesslab council init demo `
  --ref quangminh1212/HarnessLab#1 `
  --topic "Should we ship council v0.2?"
python -m harnesslab council next demo
# …agent writes turn…
python -m harnesslab council turn demo --role proposer --content "CLAIM: yes | EVIDENCE: … | ASK: …"
python -m harnesslab council status demo
python -m harnesslab council decide demo
```

## Attach Hermes

```powershell
python -m harnesslab attach
# chat: /harnesslab
# detach: python -m harnesslab detach
```

## CLI

| Command | Purpose |
|---------|---------|
| `council init/status/next/turn/decide` | Multi-AI debate workspace |
| `github pull --ref owner/repo#n` | Pull issue/PR body via `gh` |
| `attach` / `detach` | Junction skills into Hermes |
| `doctor` | git / gh / optional docker |
| `recipe docker-run` | Secondary: Harness OSS local UI |
| `init-pipeline` | Scaffold sample pipeline YAML |
| `smoke` | Regression self-check |

### Default council roles (MAD-inspired)

| Role | Stance |
|------|--------|
| **proposer** | Affirmative solution |
| **critic** | Challenge risks / gaps |
| **verifier** | Judge evidence, block weak claims |
| **synthesizer** | Closeout → DECISION.md |

## Sources (harness engineering)

See [SOURCES.md](SOURCES.md) — [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering), MAD multi-agent debate, GitHub multi-agent workflow notes, strands harness-sdk, deer-flow, etc.

## Relation to other labs

| Lab | Focus |
|-----|--------|
| **HarnessLab** | Multi-AI debate + GitHub context harness |
| **LoopLab** | Single-loop contract / OPAV / triage cron |
| **CrewLab** | Multi-agent crew meetings, one task each |

## Layout

```text
HarnessLab/
  harnesslab/     # CLI: council, github, attach, doctor
  skills/         # /harnesslab + alias /harness-integration
  examples/       # sample council + pipeline
  templates/
  scripts/
  tests/
```

## License

MIT — see [LICENSE](LICENSE). Upstream projects keep their own licenses.
