# HarnessLab context (external module)

SoT: `C:\Dev\HarnessLab`  
Skills attached as junctions under Hermes home `skills/harnesslab` and `skills/harness-integration`.

## When to use

- Local **Harness Open Source** (Docker UI on :3000)
- CI/CD recipes for XLab / agent repos
- Gitspaces / artifact registry exploration (after local stack is up)

## Commands

```text
python -m harnesslab doctor
python -m harnesslab recipe docker-run
python -m harnesslab attach|detach
```

Do **not** vendor Harness monorepo into hermes-agent. Keep clone at `C:\Dev\harness` if needed.
