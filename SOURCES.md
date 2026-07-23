# Sources — HarnessLab

HarnessLab is a **Hermes-facing agent harness** for multi-AI discussion on GitHub.
It does not vendor large upstream monorepos; it links patterns and recipes.

## Agent harness engineering

| Source | Why |
|--------|-----|
| [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Curated harness primitives: loop, context, tools, verify, multi-agent |
| [OpenAI — Harness Engineering](https://openai.com/index/harness-engineering/) | Discipline: scaffolding around the model |
| [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) | Workflows vs agents; compose primitives |
| [LangChain — Anatomy of an Agent Harness](https://blog.langchain.com/the-anatomy-of-an-agent-harness/) | Filesystem state, sandbox, memory, context |
| [GitHub Blog — Multi-agent workflows](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/) | Multi-agent ≈ distributed systems; typed handoffs |

## Multi-agent debate / council

| Source | Why |
|--------|-----|
| [Skytliang/Multi-Agents-Debate (MAD)](https://github.com/Skytliang/Multi-Agents-Debate) | Affirmative / negative / judge debate (DoT mitigation) |
| [kyegomez/swarms](https://github.com/kyegomez/swarms) | Multi-agent harness engineering notes |
| [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk) | End-to-end agent harness SDK |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | Long-horizon SuperAgent harness (also via CrewLab subrepo) |

## GitHub as collaboration surface

| Source | Why |
|--------|-----|
| GitHub Issues / PRs / Discussions | Durable multi-party conversation |
| [`gh` CLI](https://cli.github.com/) | Pull issue/PR JSON without embedding tokens |
| VS Code / Copilot multi-agent sessions | Parallel agents on same workspace (product pattern) |

## Secondary: Harness Open Source (CI product)

| Source | Why |
|--------|-----|
| [harness/harness](https://github.com/harness/harness) | Optional self-hosted SCM/CI Docker stack (`recipe docker-run`) |

## Local labs

| Lab | Role |
|-----|------|
| LoopLab | Loop contract / OPAV |
| CrewLab | One-agent-one-task meetings |
| HarnessLab | Multi-AI council on GitHub artifacts |
