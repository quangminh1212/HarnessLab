#!/usr/bin/env python3
"""XLabHarness Comprehensive Test Suite"""
import sys, json, subprocess, os

print("=" * 60)
print("XLABHARNESS — FULL TEST SUITE")
print("=" * 60)

MCP = "C:/Dev/HarnessLab/xlab-harness/mcp-bridge/xlab_mcp_server.py"
REQ = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "xlab_test.json")
passed = 0
failed = 0

def run_mcp(req_dict):
    json.dump(req_dict, open(REQ, "w"))
    r = subprocess.run([sys.executable, MCP], input=open(REQ).read()+"\n",
                       capture_output=True, text=True, timeout=10)
    return json.loads(r.stdout)

def assert_test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  OK {name}" + (f" ({detail})" if detail else ""))
    else:
        failed += 1
        print(f"  FAIL {name}" + (f" ({detail})" if detail else ""))

# ============================================================
# 1. MODEL REGISTRY
# ============================================================
print("\n[1] MODEL REGISTRY")
sys.path.insert(0, "C:/Dev/HarnessLab/xlab-harness/providers")
from model_registry import registry, ModelConfig

assert_test("catalog_count", len(registry.models) >= 15, f"{len(registry.models)} models")

for name in sorted(registry.models.keys()):
    cfg = registry.get(name)
    assert_test(f"lookup_{name}", cfg is not None and cfg.model and cfg.provider)

assert_test("fuzzy_gpt", registry.get("gpt") is not None)
assert_test("fuzzy_claude", registry.get("claude") is not None)
assert_test("providers", len(registry.providers()) >= 5, f"{len(registry.providers())}")
assert_test("detect_list", isinstance(registry.detect(), list))

registry.add("_test_custom_", ModelConfig("custom", "test-model"))
assert_test("custom_add", registry.get("_test_custom_") is not None)
print(f"  [{1 if failed==0 else 0}] REGISTRY")

# ============================================================
# 2. MCP PROTOCOL
# ============================================================
print("\n[2] MCP PROTOCOL")

d = run_mcp({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
assert_test("initialize", d["result"]["protocolVersion"] == "2024-11-05")
assert_test("capabilities", "tools" in d["result"]["capabilities"])

d = run_mcp({"jsonrpc":"2.0","id":2,"method":"ping","params":{}})
assert_test("ping", d["result"] == {})

d = run_mcp({"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}})
tools = d["result"]["tools"]
assert_test("tools_count", len(tools) == 10, f"{len(tools)} tools")
assert_test("tools_names", all(t["name"].startswith("xlab_") for t in tools))

d = run_mcp({"jsonrpc":"2.0","id":4,"method":"bogus/method","params":{}})
assert_test("unknown_method", d["error"]["code"] == -32601)

d = run_mcp({"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"nonexistent","arguments":{}}})
assert_test("unknown_tool", d["error"]["code"] == -32602)

# ============================================================
# 3. MCP TOOLS — FUNCTIONAL
# ============================================================
print("\n[3] MCP TOOLS")

def call_tool(name, args):
    d = run_mcp({"jsonrpc":"2.0","id":99,"method":"tools/call","params":{"name":name,"arguments":args}})
    return json.loads(d["result"]["content"][0]["text"])

# xlab_bash
r = call_tool("xlab_bash", {"command": "echo PASS-42"})
assert_test("bash", r["success"] and "PASS-42" in r["output"]["stdout"])

# xlab_list_dir
r = call_tool("xlab_list_dir", {"path": "C:/Dev/HarnessLab"})
assert_test("list_dir", r["success"] and len(r["output"]["entries"]) >= 5,
            f"{len(r['output']['entries'])} entries")

# xlab_read_file
r = call_tool("xlab_read_file", {"path": "C:/Dev/HarnessLab/pyproject.toml"})
assert_test("read_file", r["success"] and r["output"]["size"] > 0,
            f"{r['output']['size']} chars")

# xlab_write_file
tmp = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "xlab_write_test.txt")
r = call_tool("xlab_write_file", {"path": tmp, "content": "XLAB-WRITE-OK"})
assert_test("write_file", r["success"] and open(tmp).read() == "XLAB-WRITE-OK")
os.remove(tmp)

# xlab_search_files
r = call_tool("xlab_search_files", {"pattern": "harnesslab", "path": "C:/Dev/HarnessLab"})
assert_test("search_files", r["success"] and r["output"]["total"] > 0,
            f"{r['output']['total']} matches")

# xlab_web_fetch
r = call_tool("xlab_web_fetch", {"url": "https://example.com", "max_chars": 2000})
assert_test("web_fetch", r["success"] and len(r["output"]["content"]) > 0,
            f"{len(r['output']['content'])} chars")

# xlab_models
r = call_tool("xlab_models", {})
assert_test("models", r["success"] and r["output"]["total"] >= 15,
            f"{r['output']['total']} models")

# ============================================================
# 4. SDK DRIVER
# ============================================================
print("\n[4] SDK DRIVER")
DRIVER = "C:/Dev/HarnessLab/xlab-harness/sdk-bridge/xlab_driver.py"
assert_test("driver_exists", os.path.exists(DRIVER))

r = subprocess.run([sys.executable, DRIVER, "--list-models"],
                   capture_output=True, text=True, timeout=10)
assert_test("driver_list", "Available" in r.stdout or "openai" in r.stdout.lower())
print(f"  driver output lines: {len(r.stdout.splitlines())}")

# ============================================================
# 5. ACP ADAPTER
# ============================================================
print("\n[5] ACP ADAPTER")
ACP = "C:/Dev/HarnessLab/xlab-harness/acp-bridge/xlab_acp_adapter.py"
assert_test("acp_exists", os.path.exists(ACP))

r = subprocess.run([sys.executable, ACP, "--list"],
                   capture_output=True, text=True, timeout=10)
assert_test("acp_list", "Auto-detected" in r.stdout or "openai" in r.stdout.lower())

# ============================================================
# SUMMARY
# ============================================================
os.remove(REQ) if os.path.exists(REQ) else None
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed+failed} total")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"FAILED: {failed} tests")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
