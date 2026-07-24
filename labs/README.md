# Vendored labs (git submodules)

NexusLab **gộp 3 repo upstream** dưới `labs/`:

| Key | Path | Upstream | Pillar | License |
|-----|------|----------|--------|---------|
| **mad** | `labs/Multi-Agents-Debate` | [Skytliang/Multi-Agents-Debate](https://github.com/Skytliang/Multi-Agents-Debate) | Multi-agent debate (devil/angel/judge) | **GPL-3.0** |
| **ahe** | `labs/awesome-harness-engineering` | [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Agent harness engineering templates/list | **CC0** |
| **loop** | `labs/loop-engineering` | [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | GitHub multi-agent loops, patterns, tools | **MIT** |

## Init after clone

```powershell
cd C:\Dev\NexusLab
git submodule update --init --recursive
python -m nexuslab vendors
python -m nexuslab smoke
```

## CLI bridges

```powershell
# MAD
python -m nexuslab mad status
python -m nexuslab mad init demo --topic "Is average speed 1.5 m/s?"

# awesome-harness-engineering
python -m nexuslab ahe templates templates/ahe

# loop-engineering (GitHub multi-agent patterns)
python -m nexuslab loop-eng list
python -m nexuslab loop-eng copy pr-babysitter --dest patterns/pr-babysitter.md
# optional node tools (after npm run build:tools in labs/loop-engineering):
# python -m nexuslab loop-eng run loop-init -- --help
```

## License note

- MAD is **GPL-3.0** — kept as submodule; do not relicense MAD code as MIT.
- AHE is CC0; loop-engineering is MIT.
- NexusLab original code remains MIT; combining distributions must respect GPL for MAD component.
