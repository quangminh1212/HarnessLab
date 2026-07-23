# HarnessLab

**Hermes-native lab for [Harness Open Source](https://github.com/harness/harness)** — local Docker, CI/Gitspaces recipes, XLab workflow notes.

SoT lives in this repo. Hermes only gets **junctions** (same pattern as LoopLab / CrewLab / Hermes_Zalo).

## Quick start

```powershell
cd C:\Dev\HarnessLab
python -m pip install -e ".[dev]"
python -m harnesslab smoke
python -m harnesslab doctor
python -m harnesslab recipe docker-run
```

## Attach to Hermes (no hermes-agent code edits)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
# or:
python -m harnesslab attach

# chat: /harnesslab   or  /harness-integration
# detach:
python -m harnesslab detach
# or: scripts\uninstall.ps1
```

| Module | SoT | Hermes receives | Patch hermes-agent? |
|--------|-----|-----------------|---------------------|
| **HarnessLab** | `C:\Dev\HarnessLab` | `skills/harnesslab`, `skills/harness-integration` | **No** |

## CLI

| Command | Purpose |
|---------|---------|
| `harnesslab attach` / `detach` | Junction skills into Hermes home |
| `harnesslab doctor` | Docker / ports / clone path checks |
| `harnesslab recipe docker-run` | Print local Docker run recipe |
| `harnesslab recipe clone` | Print clone target (`C:\Dev\harness`) |
| `harnesslab init-pipeline <dir>` | Scaffold example pipeline YAML |
| `harnesslab smoke` | Self-check skills + recipes |

## Local Harness (YAGNI default)

```powershell
# requires Docker Desktop
docker run -d -p 3000:3000 -p 3022:3022 `
  -v /var/run/docker.sock:/var/run/docker.sock `
  -v ${env:TEMP}/harness:/data `
  --name harness --restart always harness/harness
# UI: http://localhost:3000
```

Clone source (optional):

```powershell
git clone https://github.com/harness/harness.git C:\Dev\harness
```

## Layout

```text
HarnessLab/
  harnesslab/           # CLI package
  skills/harnesslab/    # primary skill (/harnesslab)
  skills/harness-integration/  # alias skill (back-compat)
  scripts/              # install.ps1 / uninstall.ps1
  templates/            # HERMES.md context note
  examples/pipelines/   # sample pipeline YAML
  tests/
```

## License

MIT — see [LICENSE](LICENSE). Harness itself is separate OSS (see upstream license).
