# NexusLab

**Gộp 3 repo** thành lab Hermes-native cho multi-AI / agent harness / GitHub:

| Pillar | Upstream (vendored under `labs/`) | CLI |
|--------|-----------------------------------|-----|
| **Agent harness engineering** | [`labs/awesome-harness-engineering`](https://github.com/ai-boost/awesome-harness-engineering) | `ahe templates`, `loop`, `scaffold`, `score` |
| **Multi-agent debate (MAD)** | [`labs/Multi-Agents-Debate`](https://github.com/Skytliang/Multi-Agents-Debate) | `mad status/init`, `council --profile mad` |
| **GitHub multi-agent loops** | [`labs/loop-engineering`](https://github.com/cobusgreyling/loop-engineering) | `loop-eng list/copy/run`, `github pull`, `handoff`, `council --profile github` |

```text
git clone https://github.com/quangminh1212/NexusLab
cd NexusLab
python -m pip install -e ".[dev]"
python -m nexuslab smoke
python -m nexuslab vendors
```

## Quick flows

### 1) MAD debate (upstream code + durable council)

```powershell
python -m nexuslab mad status          # lists labs/Multi-Agents-Debate/code/*.py
python -m nexuslab mad init qa1 --topic "Alice uphill 1m/s downhill 3m/s average?"
python -m nexuslab council next qa1
# Optional live OpenAI engine: python labs/Multi-Agents-Debate/interactive.py
```

### 2) Agent harness scaffold (AHE templates)

```powershell
python -m nexuslab ahe templates templates/ahe
python -m nexuslab scaffold my-proj
python -m nexuslab loop init work1 --goal "Ship feature X" --root my-proj
python -m nexuslab score my-proj
```

### 3) GitHub multi-agent (loop-engineering patterns + handoffs)

```powershell
python -m nexuslab loop-eng list
python -m nexuslab loop-eng copy pr-babysitter
python -m nexuslab github pull --repo cli/cli --number 1
python -m nexuslab council init rev --profile github --repo cli/cli --number 1 --kind pr
python -m nexuslab handoff example --out handoffs/review.yaml
python -m nexuslab handoff validate handoffs/review.yaml
```

## Hermes

```powershell
python -m nexuslab attach
# chat: /nexuslab
```

## Layout

```text
NexusLab/
  nexuslab/            # unified CLI package
  labs/                # 3 vendored upstream trees (not git submodules)
    Multi-Agents-Debate/
    awesome-harness-engineering/
    loop-engineering/
  skills/              # Hermes junctions
  schemas/             # handoff JSON Schema
  templates/ tests/ scripts/
```

See [labs/README.md](labs/README.md) and [SOURCES.md](SOURCES.md).

## License

- **NexusLab** original code: MIT
- **Multi-Agents-Debate**: GPL-3.0 (vendored — keep separate license)
- **awesome-harness-engineering**: CC0
- **loop-engineering**: MIT
