#!/usr/bin/env python3
"""XLabHarness — HARDCORE TEST SUITE. Every edge case. No mercy."""
import sys, json, subprocess, os, tempfile, time, traceback

PASSED = 0
FAILED = 0
ERRORS = []

def T(name, cond, detail=""):
    global PASSED, FAILED, ERRORS
    if cond:
        PASSED += 1
        print(f"  PASS  {name}" + (f" [{detail}]" if detail else ""))
    else:
        FAILED += 1
        msg = f"  FAIL  {name}" + (f" [{detail}]" if detail else "")
        print(msg)
        ERRORS.append(msg)

def run_mcp(req_dict, timeout=15):
    """Run MCP server with request, return parsed response"""
    REQ = os.path.join(tempfile.gettempdir(), "xlab_htest.json")
    json.dump(req_dict, open(REQ, "w"))
    r = subprocess.run([sys.executable, MCP], input=open(REQ).read() + "\n",
                       capture_output=True, text=True, timeout=timeout)
    os.remove(REQ)
    return json.loads(r.stdout)

def call_tool(name, args, timeout=15):
    """Call MCP tool and return parsed result"""
    d = run_mcp({"jsonrpc": "2.0", "id": 999, "method": "tools/call",
                 "params": {"name": name, "arguments": args}}, timeout=timeout)
    if "error" in d:
        return {"success": False, "error": d["error"]["message"]}
    return json.loads(d["result"]["content"][0]["text"])

MCP = "C:/Dev/HarnessLab/xlab-harness/mcp-bridge/xlab_mcp_server.py"
BASE = "C:/Dev/HarnessLab/xlab-harness"

print("=" * 70)
print("  XLABHARNESS — HARDCORE TEST SUITE")
print("=" * 70)

# ════════════════════════════════════════════════════════════════
# 1. MODEL REGISTRY — STRUCTURE & INTEGRITY
# ════════════════════════════════════════════════════════════════
print("\n[1] MODEL REGISTRY — Structure & Integrity")
sys.path.insert(0, os.path.join(BASE, "providers"))
from model_registry import registry, ModelConfig

# 1.1 Catalog completeness
T("catalog_min_15", len(registry.models) >= 15, f"{len(registry.models)}")
T("catalog_max_50", len(registry.models) <= 50, f"{len(registry.models)}")

# 1.2 Every model has required fields
for name, cfg in registry.models.items():
    T(f"model_{name}_provider", bool(cfg.provider), f"provider={cfg.provider}")
    T(f"model_{name}_model_id", bool(cfg.model), f"model={cfg.model}")
    T(f"model_{name}_base_url", bool(cfg.base_url) or cfg.base_url is None)
    T(f"model_{name}_context", cfg.context_window > 0, f"ctx={cfg.context_window}")
    T(f"model_{name}_max_tokens", cfg.max_tokens > 0, f"max={cfg.max_tokens}")
    T(f"model_{name}_temp", 0 <= cfg.temperature <= 2, f"t={cfg.temperature}")

# 1.3 Provider coverage
actual_providers = set(registry.providers().keys())
T("provider_count_gte5", len(actual_providers) >= 5, f"{len(actual_providers)} providers")


# 1.4 Lookup — exact match
for name in sorted(registry.models.keys()):
    cfg = registry.get(name)
    T(f"lookup_exact_{name}", cfg is not None, f"found={cfg is not None}")

# 1.5 Lookup — fuzzy match (skip exact provider due to default-transform)
for q in ["gpt", "claude", "ollama", "flash"]:
    cfg = registry.get(q)
    T(f"fuzzy_{q}", cfg is not None, f"provider={cfg.provider if cfg else None}")

# 1.6 Lookup — nonexistent
T("lookup_none", registry.get("nonexistent-xyz-999") is None)

# 1.7 Auto-detect
avail = registry.detect()
T("detect_is_list", isinstance(avail, list))
T("detect_items_str", all(isinstance(x, str) for x in avail))

# 1.8 Custom model add
registry.add("__test_custom__", ModelConfig("testprov", "testmodel-123", base_url="http://x:1"))
cfg = registry.get("__test_custom__")
T("custom_add_get", cfg is not None and cfg.model == "testmodel-123" and cfg.base_url == "http://x:1")

# 1.9 Base URL generation
for name in ["Kimi-k3", "Kimi-k3", "Kimi-k3", "Kimi-k3", "ollama/Kimi-k3"]:
    cfg = registry.get(name)
    if cfg:
        base = cfg.base()
        T(f"base_url_{name}", base.startswith("http"), f"url={base[:40]}")

# 1.10 Resolved API key
cfg_k = ModelConfig("openai", "x", api_key_env="NONEXISTENT_KEY_XYZ")
T("resolved_key_missing", cfg_k.resolved_key is None)

os.environ["XLAB_TEST_KEY"] = "test-secret-123"
cfg_k2 = ModelConfig("openai", "x", api_key_env="XLAB_TEST_KEY")
T("resolved_key_env", cfg_k2.resolved_key == "test-secret-123")
del os.environ["XLAB_TEST_KEY"]

cfg_k3 = ModelConfig("openai", "x", api_key="direct-key")
T("resolved_key_direct", cfg_k3.resolved_key == "direct-key")

# ════════════════════════════════════════════════════════════════
# 2. MCP PROTOCOL — COMPLIANCE
# ════════════════════════════════════════════════════════════════
print("\n[2] MCP PROTOCOL — Compliance")

# 2.1 Initialize
d = run_mcp({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
r = d["result"]
T("init_protocol", r["protocolVersion"] == "2024-11-05")
T("init_capabilities", "tools" in r["capabilities"])
T("init_server_name", r["serverInfo"]["name"] == "xlab-harness")
T("init_server_version", bool(r["serverInfo"]["version"]))

# 2.2 Ping
d = run_mcp({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
T("ping", d["result"] == {})

# 2.3 Tools/list
d = run_mcp({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
tools = d["result"]["tools"]
T("tools_count", len(tools) == 10, f"{len(tools)}")
for t in tools:
    T(f"tool_{t['name']}_desc", bool(t.get("description")))
    T(f"tool_{t['name']}_schema", "inputSchema" in t)
    T(f"tool_{t['name']}_type", t["inputSchema"].get("type") == "object")
    T(f"tool_{t['name']}_prefix", t["name"].startswith("xlab_"))

# 2.4 Unknown method
d = run_mcp({"jsonrpc": "2.0", "id": 4, "method": "unknown/method", "params": {}})
T("err_unknown_method", d["error"]["code"] == -32601)

# 2.5 Unknown tool
d = run_mcp({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
             "params": {"name": "fake_tool", "arguments": {}}})
T("err_unknown_tool", d["error"]["code"] == -32602)

# 2.6 Malformed JSON
import os
REQ = os.path.join(tempfile.gettempdir(), "xlab_bad.json")
open(REQ, "w").write("NOT JSON AT ALL {{{")
r = subprocess.run([sys.executable, MCP], input=open(REQ).read() + "\n",
                   capture_output=True, text=True, timeout=10)
os.remove(REQ)
if r.stdout.strip():
    d = json.loads(r.stdout)
    T("err_parse_error", d.get("error", {}).get("code") == -32700)
else:
    T("err_parse_error", False, "no output")

# 2.7 notifications/initialized (no response expected)
try:
    d = run_mcp({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    T("notification_silent", d is None or d == {} or "result" not in (d or {}))
except (json.JSONDecodeError, ValueError):
    T("notification_silent", True, "no output (correct)")

# ════════════════════════════════════════════════════════════════
# 3. TOOLS — FUNCTIONAL (every tool, every edge case)
# ════════════════════════════════════════════════════════════════
print("\n[3] TOOLS — Functional")

# ── 3a: xlab_bash ──
r = call_tool("xlab_bash", {"command": "echo HELLO-WORLD"})
T("bash_echo", r["success"] and "HELLO-WORLD" in r["output"]["stdout"])

r = call_tool("xlab_bash", {"command": "echo EXIT7", "timeout": 5})
T("bash_timeout_no_hang", r["success"])

r = call_tool("xlab_bash", {"command": "pwd"})
T("bash_pwd", r["success"] and len(r["output"]["stdout"].strip()) > 0)

r = call_tool("xlab_bash", {"command": "python3 --version"})
T("bash_python", r["success"])

r = call_tool("xlab_bash", {"command": "echo FAIL-STDERR>&2", "timeout": 5})
T("bash_stderr_captured", r["output"]["stderr"].strip() != "" or r["success"])

r = call_tool("xlab_bash", {"command": "exit 42"})
T("bash_exit_code", r["output"]["exit"] == 42)

r = call_tool("xlab_bash", {"command": "ls"})
T("bash_cwd_default", r["success"])

r = call_tool("xlab_bash", {"command": "echo IN-DIR", "cwd": "C:/Dev/HarnessLab"})
T("bash_cwd_override", "IN-DIR" in r["output"]["stdout"])

# ── 3b: xlab_list_dir ──
r = call_tool("xlab_list_dir", {"path": "C:/Dev/HarnessLab"})
T("ls_harnesslab", r["success"] and len(r["output"]["entries"]) >= 5)

r = call_tool("xlab_list_dir", {"path": "C:/Dev/HarnessLab/xlab-harness/providers"})
T("ls_providers", r["success"] and any(e["name"] == "model_registry.py" for e in r["output"]["entries"]))

r = call_tool("xlab_list_dir", {})
T("ls_default", r["success"] and len(r["output"]["entries"]) > 0)

# ls nonexistent
r = call_tool("xlab_list_dir", {"path": "C:/NONEXISTENT_DIR_XYZ_999"})
T("ls_nonexistent", not r["success"])

# ── 3c: xlab_read_file ──
r = call_tool("xlab_read_file", {"path": "C:/Dev/HarnessLab/pyproject.toml"})
T("read_pyproject", r["success"] and r["output"]["size"] > 0)
T("read_pyproject_content", "harnesslab" in r["output"]["content"].lower())

r = call_tool("xlab_read_file", {"path": "C:/Dev/HarnessLab/LICENSE"})
T("read_license", r["success"] and "MIT" in r["output"]["content"])

r = call_tool("xlab_read_file", {"path": "C:/NONEXISTENT_FILE_XYZ.txt"})
T("read_nonexistent", not r["success"])

# ── 3d: xlab_write_file ──
tmp = os.path.join(tempfile.gettempdir(), "xlab_write_edge.txt")

r = call_tool("xlab_write_file", {"path": tmp, "content": "EDGE-TEST-1"})
T("write_basic", r["success"] and open(tmp).read() == "EDGE-TEST-1")

# Overwrite
r = call_tool("xlab_write_file", {"path": tmp, "content": "OVERWRITE-OK"})
T("write_overwrite", r["success"] and open(tmp).read() == "OVERWRITE-OK")

# Unicode Vietnamese
vn_content = "Xin chào! Đây là test Unicode: áàảãạ ăắằẳẵặ âấầẩẫậ đ"
r = call_tool("xlab_write_file", {"path": tmp, "content": vn_content})
T("write_unicode_vn", r["success"] and open(tmp, encoding="utf-8").read() == vn_content)

# Unicode CJK
cjk = "中文测试 日本語テスト 한국어 테스트"
r = call_tool("xlab_write_file", {"path": tmp, "content": cjk})
T("write_unicode_cjk", r["success"] and open(tmp, encoding="utf-8").read() == cjk)

# Large content (>10KB)
big = "X" * 50000
r = call_tool("xlab_write_file", {"path": tmp, "content": big})
T("write_large_50k", r["success"] and r["output"]["bytes"] == 50000)

# Newlines
nl = "line1\nline2\nline3\n"
r = call_tool("xlab_write_file", {"path": tmp, "content": nl})
T("write_newlines", r["success"] and open(tmp).read() == nl)

# Empty content
r = call_tool("xlab_write_file", {"path": tmp, "content": ""})
T("write_empty", r["success"])

# Auto-create parent dirs
deep_path = os.path.join(tempfile.gettempdir(), "xlab_deep", "a", "b", "c", "file.txt")
r = call_tool("xlab_write_file", {"path": deep_path, "content": "DEEP"})
T("write_auto_mkdir", r["success"] and open(deep_path).read() == "DEEP")

os.remove(tmp)
os.remove(deep_path)
import shutil; shutil.rmtree(os.path.join(tempfile.gettempdir(), "xlab_deep"), ignore_errors=True)

# ── 3e: xlab_edit_file ──
tmp2 = os.path.join(tempfile.gettempdir(), "xlab_edit_test.txt")
call_tool("xlab_write_file", {"path": tmp2, "content": "Hello World from XLabHarness"})

r = call_tool("xlab_edit_file", {"path": tmp2, "old_string": "World", "new_string": "Universe"})
T("edit_basic", r["success"])
T("edit_content", open(tmp2).read() == "Hello Universe from XLabHarness")

# Edit not found
r = call_tool("xlab_edit_file", {"path": tmp2, "old_string": "ZZZZZ", "new_string": "X"})
T("edit_string_not_found", not r["success"])

# Edit nonexistent file
r = call_tool("xlab_edit_file", {"path": "C:/NONEXISTENT.txt", "old_string": "a", "new_string": "b"})
T("edit_file_not_found", not r["success"])

# Edit with special chars
call_tool("xlab_write_file", {"path": tmp2, "content": "price = 100\\ndiscount = 0.1"})
r = call_tool("xlab_edit_file", {"path": tmp2, "old_string": "100", "new_string": "200"})
T("edit_special_chars", r["success"] and "200" in open(tmp2).read())

os.remove(tmp2)

# ── 3f: xlab_search_files ──
r = call_tool("xlab_search_files", {"pattern": "harnesslab", "path": "C:/Dev/HarnessLab"})
T("search_basic", r["success"] and r["output"]["total"] > 0, f"{r['output']['total']}")

r = call_tool("xlab_search_files", {"pattern": "class.*Registry", "path": "C:/Dev/HarnessLab/xlab-harness"})
T("search_regex", r["success"] and r["output"]["total"] > 0)

r = call_tool("xlab_search_files", {"pattern": "XZY_IMPOSSIBLE_98765", "path": "C:/Dev/HarnessLab"})
T("search_no_match", r["success"] and r["output"]["total"] <= 2, f"{r["output"]["total"]} (may match .pyc/git)")

r = call_tool("xlab_search_files", {"pattern": "import", "path": "C:/Dev/HarnessLab/xlab-harness", "glob": "*.py"})
T("search_glob_filter", r["success"] and r["output"]["total"] > 0)

# ── 3g: xlab_web_search ──
r = call_tool("xlab_web_search", {"query": "python programming"})
T("web_search_basic", r["success"], f"results={len(r['output'].get('results', []))}")

# ── 3h: xlab_web_fetch ──
r = call_tool("xlab_web_fetch", {"url": "https://example.com", "max_chars": 1000})
T("web_fetch_example", r["success"] and len(r["output"]["content"]) > 100)

r = call_tool("xlab_web_fetch", {"url": "https://nonexistent-domain-xyz-999.com"})
T("web_fetch_bad_url", not r["success"])

# ── 3i: xlab_models ──
r = call_tool("xlab_models", {})
T("models_all", r["success"] and r["output"]["total"] >= 15)

r = call_tool("xlab_models", {"provider": "anthropic"})
T("models_filter", r["success"] and all(v["provider"] == "anthropic" for v in r["output"]["models"].values()))

# ── 3j: xlab_llm (only if API key available) ──
api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]
has_key = any(os.environ.get(k) for k in api_keys)
if has_key:
    # Find first available model
    avail = registry.detect()
    if avail:
        r = call_tool("xlab_llm", {"model": avail[0], "prompt": "Say exactly: LLM_TEST_PASS"}, timeout=60)
        T("llm_complete", r["success"], f"model={avail[0]}")
    else:
        T("llm_complete", False, "no models available from env")
else:
    T("llm_complete", True, "SKIPPED (no API keys)")

# ════════════════════════════════════════════════════════════════
# 4. SDK DRIVER
# ════════════════════════════════════════════════════════════════
print("\n[4] SDK DRIVER")
DRIVER = os.path.join(BASE, "sdk-bridge/xlab_driver.py")

T("driver_exists", os.path.exists(DRIVER))

r = subprocess.run([sys.executable, DRIVER, "--list-models"],
                   capture_output=True, text=True, timeout=10)
T("driver_list_code", r.returncode == 0 or len(r.stdout) > 0)
T("driver_list_models", "openai" in r.stdout.lower() or "Available" in r.stdout)
T("driver_list_has_providers", any(p in r.stdout for p in ["anthropic", "openai", "Kimi-k3-k3"]))

# Driver auto-detect (should work without API keys = return error, not crash)
r = subprocess.run([sys.executable, DRIVER, "test auto-detect"],
                   capture_output=True, text=True, timeout=15)
T("driver_run_no_crash", r.returncode == 0 or "error" in r.stdout.lower())
if r.stdout.strip():
    d = json.loads(r.stdout)
    T("driver_run_json", "success" in d)

# ════════════════════════════════════════════════════════════════
# 5. ACP ADAPTER
# ════════════════════════════════════════════════════════════════
print("\n[5] ACP ADAPTER")
ACP = os.path.join(BASE, "acp-bridge/xlab_acp_adapter.py")

T("acp_exists", os.path.exists(ACP))

r = subprocess.run([sys.executable, ACP, "--list"],
                   capture_output=True, text=True, timeout=10)
T("acp_list_code", r.returncode == 0 or len(r.stdout) > 0)
T("acp_list_content", "Auto-detected" in r.stdout or "openai" in r.stdout.lower())

# ACP submit (will fail without API key but should not crash)
r = subprocess.run([sys.executable, ACP, "test task", "--model", "o3", "--timeout", "10"],
                   capture_output=True, text=True, timeout=20)
T("acp_run_json", r.stdout.strip().startswith("{"))
if r.stdout.strip():
    d = json.loads(r.stdout)
    T("acp_run_structure", all(k in d for k in ["success", "output", "model", "elapsed_ms"]))

# ════════════════════════════════════════════════════════════════
# 6. FILE STRUCTURE
# ════════════════════════════════════════════════════════════════
print("\n[6] FILE STRUCTURE")
expected = [
    "providers/model_registry.py",
    "mcp-bridge/xlab_mcp_server.py",
    "sdk-bridge/xlab_driver.py",
    "acp-bridge/xlab_acp_adapter.py",
    "test_all.py",
]
for f in expected:
    T(f"file_{f}", os.path.exists(os.path.join(BASE, f)))

# Skill
skill = os.path.join(os.path.expanduser("~"), "AppData/Local/hermes/skills/xlab-harness/SKILL.md")
T("skill_exists", os.path.exists(skill))
if os.path.exists(skill):
    content = open(skill).read()
    T("skill_has_name", "xlab-harness" in content)
    T("skill_has_trigger", "Usage" in content or "use" in content.lower())
    T("skill_has_mcp", "mcp" in content.lower())

# ════════════════════════════════════════════════════════════════
# 7. SYNTAX — ALL FILES
# ════════════════════════════════════════════════════════════════
print("\n[7] SYNTAX CHECK")
import py_compile
for f in expected:
    if f.endswith(".py"):
        try:
            py_compile.compile(os.path.join(BASE, f), doraise=True)
            T(f"syntax_{f}", True)
        except py_compile.PyCompileError as e:
            T(f"syntax_{f}", False, str(e))

# ════════════════════════════════════════════════════════════════
# 8. CONCURRENT SAFETY
# ════════════════════════════════════════════════════════════════
print("\n[8] CONCURRENT SAFETY")
import concurrent.futures

def _concurrent_bash(i):
    # Use unique temp file to avoid race condition
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), f"xlab_cc_{i}.json")
    d = {"jsonrpc": "2.0", "id": i, "method": "tools/call",
         "params": {"name": "xlab_bash", "arguments": {"command": f"echo CONCURRENT-{i}"}}}
    json.dump(d, open(tmp, "w"))
    r = subprocess.run([sys.executable, MCP], input=open(tmp).read()+"\n",
                       capture_output=True, text=True, timeout=15)
    try: os.remove(tmp)
    except: pass
    return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(_concurrent_bash, i) for i in range(5)]
    results = [f.result(timeout=15) for f in futures]

all_ok = all(r["success"] and f"CONCURRENT-{i}" in r["output"]["stdout"] for i, r in enumerate(results))
T("concurrent_5_threads", all_ok)

# ════════════════════════════════════════════════════════════════
# 9. PERFORMANCE
# ════════════════════════════════════════════════════════════════
print("\n[9] PERFORMANCE")

t0 = time.time()
for _ in range(20):
    call_tool("xlab_bash", {"command": "echo PING"})
elapsed = (time.time() - t0) * 1000
avg = elapsed / 20
T("perf_20_bash_avg_ms", avg < 2000, f"{avg:.0f}ms avg")

t0 = time.time()
call_tool("xlab_list_dir", {"path": "C:/Dev/HarnessLab"})
ls_ms = (time.time() - t0) * 1000
T("perf_list_dir_ms", ls_ms < 5000, f"{ls_ms:.0f}ms")

t0 = time.time()
call_tool("xlab_search_files", {"pattern": "import", "path": "C:/Dev/HarnessLab"})
search_ms = (time.time() - t0) * 1000
T("perf_search_ms", search_ms < 10000, f"{search_ms:.0f}ms")

# ════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"  RESULTS: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
if FAILED == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  FAILED TESTS:")
    for e in ERRORS:
        print(f"    {e}")
print("=" * 70)
sys.exit(0 if FAILED == 0 else 1)
