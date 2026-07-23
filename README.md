# HarnessLab

**Gộp 3 repo** thành lab Hermes-native cho multi-AI / agent harness / GitHub:

| Pillar | Upstream (submodule) | CLI |
|--------|----------------------|-----|
| **Agent harness engineering** | [`labs/awesome-harness-engineering`](https://github.com/ai-boost/awesome-harness-engineering) | `ahe templates`, `loop`, `scaffold`, `score` |
| **Multi-agent debate (MAD)** | [`labs/Multi-Agents-Debate`](https://github.com/Skytliang/Multi-Agents-Debate) | `mad status/init`, `council --profile mad` |
| **GitHub multi-agent loops** | [`labs/loop-engineering`](https://github.com/cobusgreyling/loop-engineering) | `loop-eng list/copy/run`, `github pull`, `handoff`, `council --profile github` |

```text
git clone --recurse-submodules https://github.com/quangminh1212/HarnessLab
cd HarnessLab
python -m pip install -e ".[dev]"
python -m harnesslab smoke
python -m harnesslab vendors
```

## Quick flows

### 1) MAD debate (upstream code + durable council)

```powershell
python -m harnesslab mad status          # lists labs/Multi-Agents-Debate/code/*.py
python -m harnesslab mad init qa1 --topic "Alice uphill 1m/s downhill 3m/s average?"
python -m harnesslab council next qa1
# Optional live OpenAI engine: python labs/Multi-Agents-Debate/interactive.py
```

### 2) Agent harness scaffold (AHE templates)

```powershell
python -m harnesslab ahe templates templates/ahe
python -m harnesslab scaffold my-proj
python -m harnesslab loop init work1 --goal "Ship feature X" --root my-proj
python -m harnesslab score my-proj
```

### 3) GitHub multi-agent (loop-engineering patterns + handoffs)

```powershell
python -m harnesslab loop-eng list
python -m harnesslab loop-eng copy pr-babysitter
python -m harnesslab github pull --repo cli/cli --number 1
python -m harnesslab council init rev --profile github --repo cli/cli --number 1 --kind pr
python -m harnesslab handoff example --out handoffs/review.yaml
python -m harnesslab handoff validate handoffs/review.yaml
```

## Hermes

```powershell
python -m harnesslab attach
# chat: /harnesslab
```

## Layout

```text
HarnessLab/
  harnesslab/          # unified CLI package
  labs/                # 3 git submodules (full upstream trees)
    Multi-Agents-Debate/
    awesome-harness-engineering/
    loop-engineering/
  skills/              # Hermes junctions
  schemas/             # handoff JSON Schema
  templates/ tests/ scripts/
```

See [labs/README.md](labs/README.md) and [SOURCES.md](SOURCES.md).

## License

- **HarnessLab** original code: MIT
- **Multi-Agents-Debate**: GPL-3.0 (submodule — keep separate license)
- **awesome-harness-engineering**: CC0
- **loop-engineering**: MIT
