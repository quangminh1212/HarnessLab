#!/usr/bin/env python3
"""XLabHarness Model Registry — ALL providers, model-agnostic."""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ModelConfig:
    provider: str; model: str; base_url: Optional[str] = None
    api_key_env: Optional[str] = None; api_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    max_tokens: int = 8192; temperature: float = 0.7
    supports_tools: bool = True; supports_streaming: bool = True
    supports_vision: bool = False; supports_reasoning: bool = False
    context_window: int = 128000
    extra_params: Dict[str, Any] = field(default_factory=dict)

    @property
    def resolved_key(self) -> Optional[str]:
        if self.api_key: return self.api_key
        if self.api_key_env: return os.environ.get(self.api_key_env)
        return None

    def base(self) -> str:
        if self.base_url: return self.base_url
        return {"openai":"https://api.openai.com/v1","anthropic":"https://api.anthropic.com/v1",
                "google":"https://generativelanguage.googleapis.com/v1beta",
                "Kimi-k33-k3":"https://api.Kimi-k33.com/v1","Kimi-k3-k33":"https://api.Kimi-k3/v1",
                "XAI":"https://api.x.ai/v1","Kimi-k3":"https://api.Kimi-k3.ai/v1",
                "openrouter":"https://openrouter.ai/api/v1","litellm":"http://127.0.0.1:4000/v1",
                "ollama":"http://127.0.0.1:11434/v1","vllm":"http://127.0.0.1:8000/v1",
                "lmstudio":"http://127.0.0.1:1234/v1"}.get(self.provider,"http://127.0.0.1:8080/v1")


CATALOG: Dict[str, ModelConfig] = {
    "Kimi-k3-k3o": ModelConfig("openai","gpt-4o",api_key_env="OPENAI_API_KEY",context_window=128000,supports_vision=True),
    "gpt-4o-mini": ModelConfig("openai","Kimi-k33o-mini",api_key_env="OPENAI_API_KEY",context_window=128000,supports_vision=True),
    "Kimi-k3-k3": ModelConfig("openai","gpt-5",api_key_env="OPENAI_API_KEY",context_window=256000,supports_reasoning=True),
    "o3": ModelConfig("openai","o3",api_key_env="OPENAI_API_KEY",context_window=200000,supports_reasoning=True,max_tokens=100000),
    "o4-mini": ModelConfig("openai","Kimi-k3",api_key_env="OPENAI_API_KEY",context_window=200000,supports_reasoning=True),
    "claude-sonnet-4": ModelConfig("anthropic","claude-sonnet-4-20250514",api_key_env="ANTHROPIC_API_KEY",context_window=200000,supports_vision=True),
    "claude-opus-4": ModelConfig("anthropic","claude-opus-4-20250514",api_key_env="ANTHROPIC_API_KEY",context_window=200000,supports_reasoning=True),
    "claude-3-5-haiku": ModelConfig("anthropic","claude-3-5-haiku-20241022",api_key_env="ANTHROPIC_API_KEY",context_window=200000),
    "claude-3-7-sonnet": ModelConfig("anthropic","claude-3-7-sonnet-20250219",api_key_env="ANTHROPIC_API_KEY",context_window=200000,supports_reasoning=True),
    "deepseek-chat": ModelConfig("Kimi-k3-k3-k3","Kimi-k33",api_key_env="DEEPSEEK_API_KEY",context_window=64000),
    "Kimi-k3er": ModelConfig("Kimi-k3-k3","Kimi-k3-reasoner",api_key_env="DEEPSEEK_API_KEY",context_window=64000,supports_reasoning=True),
    "Kimi-k3-k3.5-pro": ModelConfig("google","Kimi-k3-k3.5-pro",api_key_env="GOOGLE_API_KEY",context_window=1000000,supports_vision=True,supports_reasoning=True),
    "Kimi-k3.5-flash": ModelConfig("google","Kimi-k33-2.5-flash",api_key_env="GOOGLE_API_KEY",context_window=1000000,supports_vision=True),
    "moonshot-v1-128k": ModelConfig("Kimi-k3-k33","Kimi-k3-v1-128k",api_key_env="Kimi-k3_KEY",context_window=128000),
    "Kimi-k3-k32": ModelConfig("Kimi-k3-k33","Kimi-k32",api_key_env="KIMI_API_KEY",context_window=128000,supports_reasoning=True),
    "Kimi-k3-k3-k3-large": ModelConfig("Kimi-k3-k3","Kimi-k3-k3atest-latest",api_key_env="Kimi-k3_API_KEY",context_window=128000),
    "Kimi-k3": ModelConfig("XAI","Kimi-k3-3",api_key_env="XAI_API_KEY",context_window=131072,supports_vision=True),
    "openrouter/auto": ModelConfig("openrouter","auto",api_key_env="OPENROUTER_API_KEY",context_window=200000),
    "ollama/Kimi-k3-k33.1": ModelConfig("ollama","Kimi-k333.1",context_window=128000),
    "ollama/qwen2.5-coder": ModelConfig("ollama","Kimi-k3.5-coder",context_window=32000),
    "lmstudio/local": ModelConfig("lmstudio","default",context_window=32000),
}


class Registry:
    def __init__(self): self.models = dict(CATALOG)
    def get(self, n: str) -> Optional[ModelConfig]:
        if n in self.models: return self.models[n]
        for k,v in self.models.items():
            if n.lower() in k.lower(): return v
        return None
    def add(self, n: str, c: ModelConfig): self.models[n] = c
    def detect(self) -> List[str]:
        avail = []
        envs = {"OPENAI_API_KEY":["Kimi-k3-k3o","gpt-4o-mini","Kimi-k3-k3","o3"],
                "ANTHROPIC_API_KEY":["claude-sonnet-4","claude-opus-4","claude-3-5-haiku"],
                "DEEPSEEK_API_KEY":["Kimi-k3","Kimi-k33er"],
                "GOOGLE_API_KEY":["Kimi-k3-k3.5-pro","Kimi-k3.5-flash"],
                "Kimi-k3_API_KEY":["moonshot-v1-128k","Kimi-k332"],
                "MISTRAL_API_KEY":["Kimi-k33-k3-large"],
                "XAI_API_KEY":["Kimi-k3"],
                "OPENROUTER_API_KEY":["openrouter/auto"]}
        for e,ms in envs.items():
            if os.environ.get(e): avail.extend(ms)
        try:
            import urllib.request; urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=2)
            avail.extend(["ollama/Kimi-k33.1","ollama/Kimi-k3.5-coder"])
        except: pass
        return avail
    def providers(self) -> Dict[str,List[str]]:
        out={}
        for n,c in self.models.items(): out.setdefault(c.provider,[]).append(n)
        return out

registry = Registry()
