# Vendored labs (git submodules)

HarnessLab **gộp 3 repo upstream** dưới `labs/`:

| Key | Path | Upstream | Pillar | License |
|-----|------|----------|--------|---------|
| **mad** | `labs/Multi-Agents-Debate` | [Skytliang/Multi-Agents-Debate](https://github.com/Skytliang/Multi-Agents-Debate) | Multi-agent debate (devil/angel/judge) | **GPL-3.0** |
| **ahe** | `labs/awesome-harness-engineering` | [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Agent harness engineering templates/list | **CC0** |
| **loop** | `labs/loop-engineering` | [cobusgreyling/loop-engineering](https://github.com/cobusgreyling/loop-engineering) | GitHub multi-agent loops, patterns, tools | **MIT** |

## Init after clone

```powershell
cd C:\Dev\HarnessLab
git submodule update --init --recursive
python -m harnesslab vendors
python -m harnesslab smoke
```

## CLI bridges

```powershell
# MAD
python -m harnesslab mad status
python -m harnesslab mad init demo --topic "Is average speed 1.5 m/s?"

# awesome-harness-engineering
python -m harnesslab ahe templates templates/ahe

# loop-engineering (GitHub multi-agent patterns)
python -m harnesslab loop-eng list
python -m harnesslab loop-eng copy pr-babysitter --dest patterns/pr-babysitter.md
# optional node tools (after npm run build:tools in labs/loop-engineering):
# python -m harnesslab loop-eng run loop-init -- --help
```

## License note

- MAD is **GPL-3.0** — kept as submodule; do not relicense MAD code as MIT.
- AHE is CC0; loop-engineering is MIT.
- HarnessLab original code remains MIT; combining distributions must respect GPL for MAD component.
