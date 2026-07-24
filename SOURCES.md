# Sources — equivalent GitHub projects

Machine-readable: [`sources/catalog.yaml`](sources/catalog.yaml) · CLI: `nexuslab sources`

## Vendored trees (`labs/`)

| Path | Repo | Role |
|------|------|------|
| `labs/Multi-Agents-Debate` | https://github.com/Skytliang/Multi-Agents-Debate | MAD engine + prompts (GPL-3.0) |
| `labs/awesome-harness-engineering` | https://github.com/ai-boost/awesome-harness-engineering | Harness templates (CC0) |
| `labs/loop-engineering` | https://github.com/cobusgreyling/loop-engineering | GitHub multi-agent patterns (MIT) |

## Integrated profiles (literature → council)

| Profile | Upstream |
|---------|----------|
| `mad` | Skytliang/Multi-Agents-Debate |
| `chateval` | thunlp/ChatEval |
| `swe` | YerbaPage/SWE-Debate |
| `harness` | ai-boost/awesome-harness-engineering |
| `github` | loop-engineering + typed handoffs |

## Referenced catalogs

- Picrew/awesome-agent-harness
- RUCAIBox/awesome-agent-harness
- albinjal/multi-agent-debate-mcp

CLI: `mad`, `ahe`, `loop-eng`, `council --profile mad|github|harness|chateval|swe`

See [labs/README.md](labs/README.md).
