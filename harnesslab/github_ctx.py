"""Pull GitHub issue/PR context via `gh` CLI (no token embedding)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any


def gh_available() -> bool:
    return shutil.which("gh") is not None


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, r.stdout or "", r.stderr or ""


def parse_github_ref(ref: str) -> dict[str, Any]:
    """Parse owner/repo#123, owner/repo/pull/1, or full GitHub URL."""
    ref = ref.strip()
    m = re.match(
        r"https?://github\.com/(?P<repo>[^/]+/[^/]+)/(?P<kind>issues|pull)/(?P<num>\d+)",
        ref,
    )
    if m:
        kind = "issue" if m.group("kind") == "issues" else "pr"
        return {"repo": m.group("repo"), "kind": kind, "number": int(m.group("num"))}
    m = re.match(r"(?P<repo>[^/\s]+/[^/\s]+)/(pull|issues)/(?P<num>\d+)", ref)
    if m:
        kind = "pr" if m.group(2) == "pull" else "issue"
        return {"repo": m.group("repo"), "kind": kind, "number": int(m.group("num"))}
    m = re.match(r"(?P<repo>[^#\s]+/[^#\s]+)#(?P<num>\d+)", ref)
    if m:
        return {"repo": m.group("repo"), "kind": "issue", "number": int(m.group("num"))}
    raise ValueError(
        f"cannot parse GitHub ref: {ref!r} "
        "(use owner/repo#123 or https://github.com/owner/repo/issues/123)"
    )


def pull_context(
    *,
    repo: str | None = None,
    number: int | None = None,
    kind: str = "issue",
    ref: str | None = None,
) -> dict[str, Any]:
    if ref:
        parsed = parse_github_ref(ref)
        repo = parsed["repo"]
        number = int(parsed["number"])
        kind = str(parsed["kind"])
    if not repo or not number:
        raise ValueError("repo and number required (or pass --ref)")

    if not gh_available():
        return {
            "kind": kind,
            "repo": repo,
            "number": number,
            "url": f"https://github.com/{repo}/{'pull' if kind == 'pr' else 'issues'}/{number}",
            "title": "(gh CLI not available — fill manually)",
            "body": "",
            "error": "gh_not_found",
        }

    def _view(k: str) -> tuple[int, str, str]:
        if k == "pr":
            return _run_gh(
                [
                    "pr",
                    "view",
                    str(number),
                    "--repo",
                    repo,
                    "--json",
                    "number,title,body,url,author,state,baseRefName,headRefName,files",
                ]
            )
        return _run_gh(
            [
                "issue",
                "view",
                str(number),
                "--repo",
                repo,
                "--json",
                "number,title,body,url,author,state,labels,comments",
            ]
        )

    code, out, err = _view(kind)
    # Auto-fallback issue↔pr when number exists as the other kind
    if code != 0:
        alt = "pr" if kind == "issue" else "issue"
        code2, out2, err2 = _view(alt)
        if code2 == 0:
            kind, code, out, err = alt, code2, out2, err2
    if code != 0:
        return {
            "kind": kind,
            "repo": repo,
            "number": number,
            "url": f"https://github.com/{repo}/{'pull' if kind == 'pr' else 'issues'}/{number}",
            "title": "(fetch failed)",
            "body": "",
            "error": err.strip() or f"gh exit {code}",
        }
    data = json.loads(out)
    body = data.get("body") or ""
    if kind == "issue" and data.get("comments"):
        # keep last 5 comments briefly
        snippets = []
        for c in (data.get("comments") or [])[-5:]:
            author = (c.get("author") or {}).get("login", "?")
            snippets.append(f"@{author}: {(c.get('body') or '')[:400]}")
        if snippets:
            body = body + "\n\n### Recent comments\n" + "\n---\n".join(snippets)
    files = data.get("files") or []
    file_list = ", ".join(
        (f.get("path") if isinstance(f, dict) else str(f)) for f in files[:30]
    )
    return {
        "kind": kind,
        "repo": repo,
        "number": int(data.get("number") or number),
        "url": data.get("url")
        or f"https://github.com/{repo}/{'pull' if kind == 'pr' else 'issues'}/{number}",
        "title": data.get("title") or "",
        "body": body,
        "state": data.get("state"),
        "author": (data.get("author") or {}).get("login")
        if isinstance(data.get("author"), dict)
        else data.get("author"),
        "files": file_list,
        "base": data.get("baseRefName"),
        "head": data.get("headRefName"),
    }


def recipe_comment(repo: str, number: int, kind: str = "issue") -> str:
    target = "pr" if kind == "pr" else "issue"
    return f"""# Post council summary to GitHub (after DECISION.md is ready)

gh {target} comment {number} --repo {repo} --body-file councils/<name>/DECISION.md
"""
