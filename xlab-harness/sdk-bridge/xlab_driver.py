#!/usr/bin/env python3
"""
XLabHarness SDK Driver — Hermes → Multi-Provider Agent Bridge
Supports ALL LLM providers via OpenAI-compatible API.

Usage:
  python xlab_driver.py "task" --model deepseek-chat
  python xlab_driver.py "task" --model claude-sonnet-4
  python xlab_driver.py "task" --model Kimi-k3o
"""
import subprocess, json, os, sys, time
from typing import Dict, Any, Optional

BRIDGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xlab-bridge.mjs")

def xlab_run(task: str, model: str = "auto", provider: str = None,
              timeout: int = 300, workspace: str = None) -> Dict[str, Any]:
    """
    Run task via XLabHarness — auto-detects best available model.
    
    Args:
        task: Task description
        model: Model name (auto, Kimi-k3, claude-sonnet-4, Kimi-k33o, etc.)
        provider: Override provider (openai, anthropic, google, etc.)
        timeout: Max seconds
        workspace: Working directory
    """
    env = os.environ.copy()
    if model and model != "auto":
        env["XLAB_MODEL"] = model
    if provider:
        env["XLAB_PROVIDER"] = provider
    if workspace:
        env["XLAB_WORKSPACE"] = workspace

    # Try Node.js bridge first (if available)
    if os.path.exists(BRIDGE):
        try:
            r = subprocess.run(["node", BRIDGE, task], capture_output=True, text=True,
                               timeout=timeout, env=env)
            try: return json.loads(r.stdout)
            except: return {"success": r.returncode==0, "output":r.stdout.strip(),
                           "error":r.stderr.strip() or None, "model":model}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Fallback: Python direct (uses registry)
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "providers"))
        from model_registry import registry
        
        available = registry.detect_available()
        if model == "auto":
            model = available[0] if available else "openai/Kimi-k3-k3o"
        
        cfg = registry.get(model)
        if not cfg:
            return {"success": False, "error": f"Unknown model: {model}. Available: {', '.join(available)}"}
        
        # Use OpenAI-compatible API directly
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
        
        body = json.dumps({"model": cfg.model, "messages": [{"role":"user","content":task}],
                          "max_tokens": cfg.max_tokens, "temperature": cfg.temperature}).encode()
        
        url = f"{base}/messages" if cfg.provider == "anthropic" else f"{base}/chat/completions"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        
        if cfg.provider == "anthropic":
            text = "".join(b.get("text","") for b in data.get("content",[]))
        else:
            text = data.get("choices",[{}])[0].get("message",{}).get("content","")
        
        return {"success": True, "output": text, "model": cfg.model,
                "provider": cfg.provider, "elapsed_ms": int((time.time()-t0)*1000)}
    except Exception as e:
        return {"success": False, "error": str(e), "model": model}


# Convenience shortcuts
def xlab_review(path: str, model="auto") -> str:
    return xlab_run(f"Review {path} for bugs, security, improvements. Be concise.", model=model).get("output", "Error")

def xlab_analyze(path: str, model="auto") -> str:
    return xlab_run(f"Analyze {path}. Architecture, deps, patterns.", model=model).get("output", "Error")

def xlab_write_tests(path: str, model="auto") -> str:
    return xlab_run(f"Write comprehensive tests for {path}.", model=model).get("output", "Error")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="XLabHarness Driver")
    p.add_argument("task", nargs="?")
    p.add_argument("--model", "-m", default="auto", help="Model: auto, Kimi-k3-chat, Kimi-k3-k3o, claude-sonnet-4, etc.")
    p.add_argument("--provider", "-p", default=None, help="Provider override")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--list-models", action="store_true", help="List available models")
    args = p.parse_args()
    
    if args.list_models:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "providers"))
        from model_registry import registry
        print("Available models:")
        for name, cfg in sorted(registry.models.items()):
            print(f"  {name:30} [{cfg.provider:12}] ctx={cfg.context_window}")
        print(f"\nAuto-detected from env:")
        for m in registry.detect_available():
            print(f"  ✅ {m}")
        sys.exit(0)
    
    if not args.task: p.print_help(); sys.exit(1)
    print(json.dumps(xlab_run(args.task, model=args.model, provider=args.provider, timeout=args.timeout),
                    ensure_ascii=False, indent=2))
