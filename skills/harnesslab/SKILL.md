---
name: harnesslab
description: >
  HarnessLab — Harness Open Source for Hermes/XLab: local Docker run, clone recipes,
  CI pipeline scaffolds, Gitspaces/artifact notes. Activate with /harnesslab.
compatibility: Docker Desktop recommended for local stack; git for optional clone
metadata:
  author: HarnessLab
  version: "0.1.0"
  hermes:
    tags: [ci-cd, harness, docker, devops, xlab]
    category: development
    requires_toolsets: [terminal]
---

# HarnessLab (Hermes)

You help integrate **[Harness Open Source](https://github.com/harness/harness)** with XLab / Hermes workflows.

SoT: `C:\Dev\HarnessLab` (external lab). Attach via junctions only — no hermes-agent patches.

```text
python -m harnesslab attach
python -m harnesslab doctor
python -m harnesslab recipe docker-run|clone|stop
python -m harnesslab init-pipeline <project-dir>
```

## Default workflow (YAGNI)

1. **Doctor** — `python -m harnesslab doctor` (Docker engine must be up for local UI).
2. **Run local** — print + run docker recipe (ports **3000** UI, **3022** git).
3. **Optional clone** — `C:\Dev\harness` only if you need source/docs offline.
4. **Pipeline scaffold** — `init-pipeline` writes `.harness/pipelines/xlab-smoke.yaml` (edit later).
5. **Do not** author full multi-stage production pipelines until local stack is verified.

## Local Docker (canonical)

```powershell
docker run -d -p 3000:3000 -p 3022:3022 `
  -v /var/run/docker.sock:/var/run/docker.sock `
  -v "$env:TEMP/harness:/data" `
  --name harness --restart always harness/harness
# http://localhost:3000
```

Stop:

```powershell
docker stop harness; docker rm harness
```

## XLab integration notes

| Use | How |
|-----|-----|
| Repo / SCM | Point Harness at XLab Git remotes after UI is up |
| CI | Prefer Harness pipelines over GH Actions when self-hosted CI is the goal |
| Gitspaces | Hosted/dev containers for long agent sessions |
| Artifacts | Store builds, model weights, export bundles |

## Relation to other labs

| Lab | Focus |
|-----|--------|
| **HarnessLab** | Harness OSS local + CI recipes |
| **LoopLab** | Loop contract / OPAV / triage |
| **CrewLab** | Multi-agent crew meetings |
| **RouterLab** | Model/provider routing |

## Rules

- Prefer **print recipe → user/agent runs** over silent long clones.
- Never store secrets in skill files; use Hermes `config.yaml` / `.env`.
- If Docker is unavailable, report clearly and stop at recipe stage.
