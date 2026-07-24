---
name: harness-integration
description: >
  Alias of NexusLab: multi-AI GitHub council + optional Harness OSS Docker.
  Prefer /nexuslab.
compatibility: terminal; gh recommended
metadata:
  author: NexusLab
  version: "0.3.0"
  hermes:
    tags: [multi-agent, debate, github, harness, ci-cd]
    category: development
    requires_toolsets: [terminal]
---

# harness-integration (alias → NexusLab)

Primary skill: **`/nexuslab`**.

Multi-AI debate on GitHub:

```powershell
cd C:\Dev\NexusLab
python -m nexuslab council init my-debate --ref owner/repo#12 --topic "Review approach"
python -m nexuslab council next my-debate
```

Optional Harness OSS local UI: `python -m nexuslab recipe docker-run` → http://localhost:3000

Follow full rules in the **nexuslab** skill.
