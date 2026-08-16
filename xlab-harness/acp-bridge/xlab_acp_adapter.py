#!/usr/bin/env python3
"""
XLabHarness ACP Adapter — Multi-Provider Agent Bridge cho Hermes
Triển khai Agent Client Protocol cho phép delegate tasks đến bất kỳ LLM provider.

Providers: OpenAI, Anthropic, Google, Kimi-k33, Kimi-k3-k3, OKimi-k3, vLLM, OKimi-k3, OpenRouter...
"""
import json, os, subprocess, sys, time
from typing import Dict, Any, Optional, List

# Import registry
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "providers"))
try:
    from model_registry import registry
except ImportError:
    registry = None


class XLabACPAdapter:
    def __init__(self, workspace=None, model="auto", provider=None, timeout=600):
        self.ws = workspace or os.getcwd()
        self.model = model
        self.provider = provider
        self.timeout = timeout

    def submit(self, task: str, model: str = None) -> Dict[str, Any]:
        t0 = time.time()
        use_model = model or self.model

        if not registry:
            return {"success": False, "output": "", "error": "Registry not loaded", "elapsed_ms": 0}

        # Auto-detect
        if use_model == "auto":
            available = registry.detect_available()
            if not available:
                return {"success": False, "output": "", "error": "No models available. Set API keys.", "elapsed_ms": 0}
            use_model = available[0]

        cfg = registry.get(use_model)
        if not cfg:
            return {"success": False, "output": "", "error": f"Unknown: {use_model}", "elapsed_ms": 0}

        try:
            import urllib.request
            base = cfg.openai_base_url()
            key = cfg.resolved_api_key
            headers = {"Content-Type": "application/json"}
            if key:
                if cfg.provider == "anthropic":
                    headers["x-api-key"] = key
                    headers["anthropic-version"] = "2023-06-01"
                else:
                    headers["Authorization"] = f"Bearer {key}"
            headers.update(cfg.headers)

            body = json.dumps({
                "model": cfg.model,
                "messages": [{"role": "user", "content": task}],
                "max_tokens": cfg.max_tokens,
                "temperature": cfg.temperature,
                "stream": False,
            }).encode()

            url = f"{base}/messages" if cfg.provider == "anthropic" else f"{base}/chat/completions"
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())

            if cfg.provider == "anthropic":
                text = "".join(b.get("text","") for b in data.get("content",[]))
            else:
                text = data.get("choices",[{}])[0].get("message",{}).get("content","")

            elapsed = int((time.time()-t0)*1000)
            return {"success": True, "output": text, "model": cfg.model,
                    "provider": cfg.provider, "elapsed_ms": elapsed,
                    "usage": data.get("usage", {})}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e),
                    "model": cfg.model, "provider": cfg.provider,
                    "elapsed_ms": int((time.time()-t0)*1000)}


def hermes_delegate(goal: str, model="auto", provider=None, timeout=300) -> str:
    a = XLabACPAdapter(model=model, provider=provider, timeout=timeout)
    r = a.submit(goal)
    return r["output"] if r["success"] else f"Error [{r.get('provider','?')}]: {r['error']}"


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="XLabHarness ACP Adapter")
    p.add_argument("task", nargs="?")
    p.add_argument("--model", "-m", default="auto")
    p.add_argument("--provider", "-p", default=None)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--list", action="store_true")
    args = p.parse_args()

    if args.list:
        if registry:
            print("Auto-detected:")
            for m in registry.detect_available(): print(f"  {m}")
            print(f"\nAll {len(registry.models)} models:")
            for n,c in sorted(registry.models.items()): print(f"  {n:30} [{c.provider}]")
        sys.exit(0)

    if not args.task: p.print_help(); sys.exit(1)
    a = XLabACPAdapter(model=args.model, provider=args.provider, timeout=args.timeout)
    print(json.dumps(a.submit(args.task), ensure_ascii=False, indent=2))
