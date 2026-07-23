---
name: harness-integration
description: >
  Alias of HarnessLab: multi-AI GitHub council + optional Harness OSS Docker.
  Prefer /harnesslab.
compatibility: terminal; gh recommended
metadata:
  author: HarnessLab
  version: "0.2.0"
  hermes:
    tags: [multi-agent, debate, github, harness, ci-cd]
    category: development
    requires_toolsets: [terminal]
---

# harness-integration (alias → HarnessLab)

Primary skill: **`/harnesslab`**.

Multi-AI debate on GitHub:

```powershell
cd C:\Dev\HarnessLab
python -m harnesslab council init my-debate --ref owner/repo#12 --topic "Review approach"
python -m harnesslab council next my-debate
```

Optional Harness OSS local UI: `python -m harnesslab recipe docker-run` → http://localhost:3000

Follow full rules in the **harnesslab** skill.
