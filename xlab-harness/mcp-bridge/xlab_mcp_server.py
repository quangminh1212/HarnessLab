#!/usr/bin/env python3
"""
XLabHarness MCP Server — 10 tools + ALL providers
Thêm vào Hermes config.yaml:
  mcp_servers:
    xlab-harness:
      command: python
      args: ["C:/Dev/HarnessLab/xlab-harness/mcp-bridge/xlab_mcp_server.py"]
      enabled: true
"""
import json, os, re, subprocess, sys, time
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "providers"))
try:
    from model_registry import registry
except ImportError:
    registry = None


class R:
    def __init__(self, ok, out, err=None):
        self.ok = ok; self.out = out; self.err = err
    def d(self):
        d = {"success": self.ok, "output": self.out}
        if self.err: d["error"] = self.err
        return d


class Bash:
    def __init__(s,ws=None,t=300): s.ws=ws or os.getcwd(); s.t=t
    def run(s,cmd,timeout=None,cwd=None):
        try:
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=timeout or s.t,cwd=cwd or s.ws)
            return R(r.returncode==0,{"stdout":r.stdout,"stderr":r.stderr,"exit":r.returncode},r.stderr.strip() or None)
        except subprocess.TimeoutExpired: return R(False,None,f"Timeout {timeout or s.t}s")
        except Exception as e: return R(False,None,str(e))


class FS:
    def __init__(s,ws=None): s.ws=Path(ws or os.getcwd())
    def _p(s,p): return Path(p) if Path(p).is_absolute() else s.ws/p
    def read(s,p):
        try:
            fp=s._p(p)
            if not fp.exists(): return R(False,None,f"Not found: {fp}")
            return R(True,{"content":fp.read_text("utf-8","replace"),"path":str(fp),"size":fp.stat().st_size})
        except Exception as e: return R(False,None,str(e))
    def write(s,p,c):
        try: fp=s._p(p); fp.parent.mkdir(parents=True,exist_ok=True); fp.write_text(c,"utf-8"); return R(True,{"path":str(fp),"bytes":len(c.encode())})
        except Exception as e: return R(False,None,str(e))
    def edit(s,p,old,new):
        try:
            fp=s._p(p)
            if not fp.exists(): return R(False,None,f"Not found: {fp}")
            c=fp.read_text("utf-8","replace")
            if old not in c: return R(False,None,"String not found")
            fp.write_text(c.replace(old,new,1),"utf-8"); return R(True,{"path":str(fp)})
        except Exception as e: return R(False,None,str(e))
    def search(s,pat,path=None,glob=None):
        try:
            sp=Path(path) if path else s.ws; res=[]
            for f in sp.rglob(glob or "*"):
                if f.is_file() and f.stat().st_size<1e6:
                    try:
                        c=f.read_text("utf-8","ignore")
                        m=[(i+1,l.strip()) for i,l in enumerate(c.splitlines()) if re.search(pat,l,re.I)]
                        if m: res.append({"path":str(f),"matches":m[:10]})
                    except: pass
            return R(True,{"results":res[:50],"total":len(res)})
        except Exception as e: return R(False,None,str(e))
    def ls(s,p=None):
        try:
            dp=Path(p) if p else s.ws
            return R(True,{"path":str(dp),"entries":[{"name":i.name,"type":"dir" if i.is_dir() else "file","size":i.stat().st_size if i.is_file() else None} for i in sorted(dp.iterdir())]})
        except Exception as e: return R(False,None,str(e))


class Web:
    def search(s,q,n=5):
        try:
            import urllib.request,urllib.parse
            r=urllib.request.urlopen(urllib.request.Request(f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}",headers={"User-Agent":"Mozilla/5.0"}),timeout=15)
            h=r.read().decode("utf-8","ignore")
            res=[]
            for m in re.finditer(r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?class="result__snippet">(.*?)</span>',h,re.DOTALL):
                res.append({"title":re.sub(r"<[^>]+>","",m.group(2)).strip(),"url":m.group(1),"snippet":re.sub(r"<[^>]+>","",m.group(3)).strip()})
                if len(res)>=n: break
            return R(True,{"query":q,"results":res})
        except Exception as e: return R(False,None,str(e))
    def fetch(s,url,mx=50000):
        try:
            import urllib.request
            c=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode("utf-8","replace")
            return R(True,{"url":url,"content":c[:mx],"truncated":len(c)>mx})
        except Exception as e: return R(False,None,str(e))


class LLM:
    def complete(s,model,messages,**kw):
        if not registry: return R(False,None,"Registry not available")
        cfg=registry.get(model)
        if not cfg: return R(False,None,f"Unknown model: {model}. Use xlab_models to list.")
        try:
            import urllib.request
            key=cfg.resolved_key
            hdrs={"Content-Type":"application/json"}
            if key:
                if cfg.provider=="anthropic": hdrs["x-api-key"]=key; hdrs["anthropic-version"]="2023-06-01"
                else: hdrs["Authorization"]=f"Bearer {key}"
            hdrs.update(cfg.headers)
            body=json.dumps({"model":cfg.model,"messages":messages,"max_tokens":kw.get("max_tokens",cfg.max_tokens),"temperature":kw.get("temperature",cfg.temperature),"stream":False}).encode()
            url=f"{cfg.base()}/messages" if cfg.provider=="anthropic" else f"{cfg.base()}/chat/completions"
            req=urllib.request.Request(url,data=body,headers=hdrs,method="POST")
            with urllib.request.urlopen(req,timeout=120) as resp: data=json.loads(resp.read().decode())
            if cfg.provider=="anthropic": text="".join(b.get("text","") for b in data.get("content",[]))
            else: text=data.get("choices",[{}])[0].get("message",{}).get("content","")
            return R(True,{"text":text,"model":cfg.model,"provider":cfg.provider,"usage":data.get("usage",{})})
        except Exception as e: return R(False,None,f"{cfg.provider}/{cfg.model}: {e}")


TOOLS={
    "xlab_bash":{"desc":"Execute shell command","args":{"command":{"type":"string"},"timeout":{"type":"integer"},"cwd":{"type":"string"}},"req":["command"]},
    "xlab_read_file":{"desc":"Read file","args":{"path":{"type":"string"}},"req":["path"]},
    "xlab_write_file":{"desc":"Write file","args":{"path":{"type":"string"},"content":{"type":"string"}},"req":["path","content"]},
    "xlab_edit_file":{"desc":"Edit file","args":{"path":{"type":"string"},"old_string":{"type":"string"},"new_string":{"type":"string"}},"req":["path","old_string","new_string"]},
    "xlab_search_files":{"desc":"Search by regex","args":{"pattern":{"type":"string"},"path":{"type":"string"},"glob":{"type":"string"}},"req":["pattern"]},
    "xlab_list_dir":{"desc":"List directory","args":{"path":{"type":"string"}},"req":[]},
    "xlab_web_search":{"desc":"Web search","args":{"query":{"type":"string"},"num_results":{"type":"integer"}},"req":["query"]},
    "xlab_web_fetch":{"desc":"Fetch URL","args":{"url":{"type":"string"}},"req":["url"]},
    "xlab_llm":{"desc":"LLM completion (any provider)","args":{"model":{"type":"string"},"prompt":{"type":"string"},"system":{"type":"string"},"max_tokens":{"type":"integer"}},"req":["model","prompt"]},
    "xlab_models":{"desc":"List models/providers","args":{"provider":{"type":"string"}},"req":[]},
}

class Handler:
    def __init__(s,ws=None): s.bash=Bash(ws); s.fs=FS(ws); s.web=Web(); s.llm=LLM(); s.skills=Path.home()/("AppData/Local/hermes/skills")
    def handle(s,req):
        m=req.get("method"); p=req.get("params",{}); i=req.get("id")
        if m=="initialize": return s._r(i,{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"xlab-harness","version":"1.0.0"}})
        if m=="notifications/initialized": return None
        if m=="tools/list": return s._r(i,{"tools":[{"name":n,"description":t["desc"],"inputSchema":{"type":"object","properties":t["args"],"required":t["req"]}} for n,t in TOOLS.items()]})
        if m=="tools/call": return s._call(i,p.get("name"),p.get("arguments",{}))
        if m=="ping": return s._r(i,{})
        return s._e(i,-32601,f"Unknown: {m}")
    def _call(s,i,n,a):
        if n not in TOOLS: return s._e(i,-32602,f"Unknown: {n}")
        try:
            d={"xlab_bash":lambda:s.bash.run(a["command"],a.get("timeout"),a.get("cwd")),
               "xlab_read_file":lambda:s.fs.read(a["path"]),
               "xlab_write_file":lambda:s.fs.write(a["path"],a["content"]),
               "xlab_edit_file":lambda:s.fs.edit(a["path"],a["old_string"],a["new_string"]),
               "xlab_search_files":lambda:s.fs.search(a["pattern"],a.get("path"),a.get("glob")),
               "xlab_list_dir":lambda:s.fs.ls(a.get("path")),
               "xlab_web_search":lambda:s.web.search(a["query"],a.get("num_results",5)),
               "xlab_web_fetch":lambda:s.web.fetch(a["url"]),
               "xlab_llm":lambda:s._llm(a),
               "xlab_models":lambda:s._models(a.get("provider"))}
            r=d[n](); return s._r(i,{"content":[{"type":"text","text":json.dumps(r.d(),ensure_ascii=False)}]})
        except Exception as e: return s._e(i,-32000,str(e))
    def _llm(s,a):
        msgs=[]
        if a.get("system"): msgs.append({"role":"system","content":a["system"]})
        msgs.append({"role":"user","content":a["prompt"]})
        return s.llm.complete(a["model"],msgs,max_tokens=a.get("max_tokens"))
    def _models(s,provider=None):
        if not registry: return R(True,{"models":{},"note":"Registry not loaded"})
        avail=registry.detect()
        models={k:{"provider":v.provider,"model":v.model,"ctx":v.context_window} for k,v in registry.models.items() if not provider or v.provider==provider}
        return R(True,{"models":models,"available":avail,"total":len(models)})
    def _r(s,i,r): return {"jsonrpc":"2.0","id":i,"result":r} if i is not None else None
    def _e(s,i,c,m): return {"jsonrpc":"2.0","id":i,"error":{"code":c,"message":m}}

if __name__=="__main__":
    ws=sys.argv[1] if len(sys.argv)>1 else os.getcwd()
    h=Handler(ws)
    for line in sys.stdin:
        line=line.strip()
        if not line: continue
        try:
            resp=h.handle(json.loads(line))
            if resp: print(json.dumps(resp),flush=True)
        except: print(json.dumps(h._e(None,-32700,"Parse error")),flush=True)
