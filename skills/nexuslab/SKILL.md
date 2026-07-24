---
name: nexuslab
description: >
  NexusLab unifies 3 upstream labs: Multi-Agents-Debate (MAD),
  awesome-harness-engineering (AHE templates/loop), loop-engineering
  (GitHub multi-agent patterns). Council profiles mad|github|harness.
  Activate with /nexuslab.
compatibility: terminal; gh recommended; submodules under labs/
metadata:
  author: NexusLab
  version: "0.3.0"
  hermes:
    tags: [multi-agent, debate, harness, github, mad, loop-engineering]
    category: development
    requires_toolsets: [terminal]
---

# NexusLab — 3 labs in one

SoT: `C:\Dev\NexusLab` with **git submodules**:

| Pillar | Path |
|--------|------|
| MAD debate | `labs/Multi-Agents-Debate` (GPL-3) |
| Harness engineering | `labs/awesome-harness-engineering` (CC0) |
| GitHub multi-agent loops | `labs/loop-engineering` (MIT) |

```powershell
git submodule update --init --recursive
python -m nexuslab vendors
python -m nexuslab smoke
```

## When user asks for multi-AI debate

```powershell
python -m nexuslab mad init <id> --topic "..."
# or: council init <id> --profile mad --topic "..."
python -m nexuslab council next <id>
python -m nexuslab council turn <id> --role devil --content "..."
```

Roles MAD: **devil → angel → judge** (upstream Affirmative/Negative/Moderator).

Optional live OpenAI: `python labs/Multi-Agents-Debate/interactive.py` (needs API key).

## When user asks for harness scaffold / long loop

```powershell
python -m nexuslab ahe templates templates/ahe
python -m nexuslab scaffold .
python -m nexuslab loop init <id> --goal "..."
python -m nexuslab score .
```

## When user asks for GitHub multi-agent review

```powershell
python -m nexuslab loop-eng list
python -m nexuslab loop-eng copy pr-babysitter
python -m nexuslab github pull --ref owner/repo#n
python -m nexuslab council init r1 --profile github --ref owner/repo#n
python -m nexuslab handoff validate handoffs/x.yaml
```

## Rules

- Prefer durable files under `councils/` `loops/` `handoffs/`
- One turn = one role
- Respect MAD GPL: do not relicense upstream MAD sources as MIT
- Do not merge/close GitHub items unless user asks
