---
name: harness-integration
description: >
  Alias of HarnessLab (Harness Open Source: clone, Docker local, CI recipes).
  Prefer /harnesslab. Kept for back-compat with older Hermes skill name.
compatibility: Docker Desktop recommended; git optional
metadata:
  author: HarnessLab
  version: "0.1.0"
  hermes:
    tags: [ci-cd, harness, docker, devops]
    category: development
    requires_toolsets: [terminal]
---

# Harness Integration (alias → HarnessLab)

This skill is the **back-compat name** for **HarnessLab**.

SoT: `C:\Dev\HarnessLab`  
Primary skill: `/harnesslab` (`skills/harnesslab`).

## Quick actions

```powershell
cd C:\Dev\HarnessLab
python -m harnesslab doctor
python -m harnesslab recipe docker-run
```

Local UI after docker-run: **http://localhost:3000**

Follow the full workflow and rules in the **harnesslab** skill content when both are loaded.
