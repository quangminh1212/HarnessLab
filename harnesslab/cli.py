"""HarnessLab CLI — multi-AI GitHub council harness + optional Harness OSS recipes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harnesslab import __version__
from harnesslab.council import (
    append_transcript,
    init_council,
    load_state,
    prompt_for_next,
    save_state,
    state_path,
    status_text,
    write_decision_scaffold,
)
from harnesslab.doctor import run_doctor
from harnesslab.github_ctx import pull_context, recipe_comment
from harnesslab.install import attach_to_hermes, default_hermes_home, uninstall_from_hermes
from harnesslab.pipeline import write_pipeline_scaffold
from harnesslab.recipe import list_recipes, render_recipe


def _cmd_attach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    try:
        linked = attach_to_hermes(home)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Hermes home: {home}")
    print(f"attached {len(linked)} path(s)")
    for p in linked:
        print(f"  + {p}")
    print("Chat: /harnesslab  (multi-AI GitHub council)")
    return 0


def _cmd_detach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    removed = uninstall_from_hermes(home)
    print(f"Hermes home: {home}")
    if not removed:
        print("nothing to remove")
        return 0
    for p in removed:
        print(f"  - {p}")
    return 0


def _cmd_doctor(_args: argparse.Namespace) -> int:
    report = run_doctor()
    print(report.summary())
    return 0 if report.ok else 2


def _cmd_recipe(args: argparse.Namespace) -> int:
    if args.list:
        for name in list_recipes():
            print(name)
        return 0
    try:
        print(render_recipe(args.name or "docker-run", data_dir=args.data_dir))
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_init_pipeline(args: argparse.Namespace) -> int:
    written = write_pipeline_scaffold(Path(args.path))
    print(f"scaffolded pipeline under {args.path}")
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_github_pull(args: argparse.Namespace) -> int:
    try:
        ctx = pull_context(
            ref=args.ref,
            repo=args.repo,
            number=args.number,
            kind=args.kind,
        )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.json:
        import json

        print(json.dumps(ctx, indent=2, ensure_ascii=False))
    else:
        print(f"kind:  {ctx.get('kind')}")
        print(f"repo:  {ctx.get('repo')}#{ctx.get('number')}")
        print(f"title: {ctx.get('title')}")
        print(f"url:   {ctx.get('url')}")
        if ctx.get("error"):
            print(f"error: {ctx['error']}", file=sys.stderr)
        body = (ctx.get("body") or "")[:2000]
        print("--- body ---")
        print(body)
    if args.out:
        Path(args.out).write_text(
            f"# {ctx.get('title')}\n\n{ctx.get('url')}\n\n{ctx.get('body') or ''}\n",
            encoding="utf-8",
        )
        print(f"wrote {args.out}")
    return 1 if ctx.get("error") == "gh_not_found" else 0


def _cmd_council_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    gh: dict = {}
    if args.ref or (args.repo and args.number):
        try:
            gh = pull_context(
                ref=args.ref,
                repo=args.repo,
                number=args.number,
                kind=args.kind,
            )
        except Exception as e:
            print(f"warning: github pull failed: {e}", file=sys.stderr)
    topic = args.topic
    if not topic and gh.get("title"):
        topic = f"{gh.get('kind')} {gh.get('repo')}#{gh.get('number')}: {gh.get('title')}"
    if not topic:
        print("error: --topic required (or provide GitHub ref)", file=sys.stderr)
        return 1
    state, written = init_council(
        root,
        args.name,
        topic,
        max_rounds=args.rounds,
        github=gh,
    )
    print(status_text(state))
    for p in written:
        print(f"  + {p}")
    print("\nNext: harnesslab council next", args.name, f"--root {root}")
    return 0


def _cmd_council_status(args: argparse.Namespace) -> int:
    path = state_path(Path(args.root), args.name)
    if not path.is_file() and not path.with_suffix(".json").is_file():
        print(f"error: no council {args.name} under {args.root}", file=sys.stderr)
        return 1
    p = path if path.is_file() else path.with_suffix(".json")
    state = load_state(p)
    print(status_text(state))
    return 0


def _cmd_council_next(args: argparse.Namespace) -> int:
    path = state_path(Path(args.root), args.name)
    p = path if path.is_file() else path.with_suffix(".json")
    if not p.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    state = load_state(p)
    text = prompt_for_next(state)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def _cmd_council_turn(args: argparse.Namespace) -> int:
    root = Path(args.root)
    path = state_path(root, args.name)
    p = path if path.is_file() else path.with_suffix(".json")
    if not p.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.content:
        content = args.content
    else:
        print("error: provide --file or --content", file=sys.stderr)
        return 1
    state = load_state(p)
    role_map = {r["id"]: r for r in state.roles}
    turn = state.record_turn(content, role_id=args.role)
    save_state(state, p if p.suffix else path)
    # ensure yaml path preferred
    if p.suffix == ".json" and path.suffix == ".yaml":
        save_state(state, path)
    title = role_map.get(turn["role_id"], {}).get("title", turn["role_id"])
    append_transcript(root, args.name, turn, title)
    if state.status == "decided":
        write_decision_scaffold(root, args.name, state)
    print(status_text(state))
    print(f"recorded turn as {turn['role_id']} round {turn['round']}")
    return 0


def _cmd_council_decide(args: argparse.Namespace) -> int:
    root = Path(args.root)
    path = state_path(root, args.name)
    p = path if path.is_file() else path.with_suffix(".json")
    if not p.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    state = load_state(p)
    state.status = "decided"
    save_state(state, p)
    out = write_decision_scaffold(root, args.name, state)
    print(status_text(state))
    print(f"  + {out}")
    gh = state.github
    if gh.get("repo") and gh.get("number"):
        print(recipe_comment(str(gh["repo"]), int(gh["number"]), str(gh.get("kind") or "issue")))
    return 0


def _cmd_smoke(_args: argparse.Namespace) -> int:
    import tempfile

    root = Path(__file__).resolve().parent.parent
    failed = 0
    for name in ("harnesslab", "harness-integration"):
        skill = root / "skills" / name / "SKILL.md"
        if not skill.is_file():
            print(f"  [FAIL] missing skill {name}")
            failed += 1
            continue
        text = skill.read_text(encoding="utf-8").lower()
        if "council" not in text and "debate" not in text and "harness" not in text:
            print(f"  [FAIL] skill {name} weak")
            failed += 1
        else:
            print(f"  [OK] skill {name}")
    for rec in list_recipes():
        try:
            body = render_recipe(rec)
            assert "harness" in body.lower()
            print(f"  [OK] recipe {rec}")
        except Exception as e:
            print(f"  [FAIL] recipe {rec}: {e}")
            failed += 1
    # council round-trip
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        state, _ = init_council(td_path, "smoke", "Should we merge?", max_rounds=1)
        state.record_turn("CLAIM: merge with tests | EVIDENCE: n/a | ASK: none", "proposer")
        state.record_turn("CLAIM: block | EVIDENCE: no tests | ASK: add tests", "critic")
        save_state(state, state_path(td_path, "smoke"))
        loaded = load_state(state_path(td_path, "smoke"))
        if len(loaded.turns) != 2:
            print("  [FAIL] council state")
            failed += 1
        else:
            print("  [OK] council init/turn")
        from harnesslab.github_ctx import parse_github_ref

        r = parse_github_ref("octocat/Hello-World#1")
        if r["repo"] != "octocat/Hello-World" or r["number"] != 1:
            print("  [FAIL] parse github ref")
            failed += 1
        else:
            print("  [OK] parse github ref")
    print(run_doctor().summary().splitlines()[0])
    print(f"smoke: failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="harnesslab",
        description=(
            "HarnessLab — multi-AI council harness on GitHub "
            "(agent harness engineering for Hermes)"
        ),
    )
    p.add_argument("--version", action="version", version=f"harnesslab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("attach", help="Attach skills into Hermes via junctions")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_attach)

    s = sub.add_parser("detach", help="Detach HarnessLab from Hermes")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_detach)

    s = sub.add_parser("doctor", help="Check Docker/git/gh readiness")
    s.set_defaults(func=_cmd_doctor)

    s = sub.add_parser("recipe", help="Print Harness OSS docker/clone recipes (secondary)")
    s.add_argument("name", nargs="?", default="docker-run")
    s.add_argument("--list", action="store_true")
    s.add_argument("--data-dir", default=None)
    s.set_defaults(func=_cmd_recipe)

    s = sub.add_parser("init-pipeline", help="Scaffold .harness/pipelines example")
    s.add_argument("path", help="Project directory")
    s.set_defaults(func=_cmd_init_pipeline)

    s = sub.add_parser("github", help="GitHub helpers")
    g = s.add_subparsers(dest="github_cmd", required=True)
    gp = g.add_parser("pull", help="Pull issue/PR context via gh")
    gp.add_argument("--ref", default=None, help="owner/repo#n or URL")
    gp.add_argument("--repo", default=None)
    gp.add_argument("--number", type=int, default=None)
    gp.add_argument("--kind", choices=("issue", "pr"), default="issue")
    gp.add_argument("--out", default=None)
    gp.add_argument("--json", action="store_true")
    gp.set_defaults(func=_cmd_github_pull)

    s = sub.add_parser("council", help="Multi-AI debate council on a topic/GitHub item")
    c = s.add_subparsers(dest="council_cmd", required=True)

    ci = c.add_parser("init", help="Create council workspace")
    ci.add_argument("name", help="Council id (slug)")
    ci.add_argument("--topic", default=None)
    ci.add_argument("--root", default=".", help="Project root (default .)")
    ci.add_argument("--rounds", type=int, default=2)
    ci.add_argument("--ref", default=None, help="GitHub ref owner/repo#n")
    ci.add_argument("--repo", default=None)
    ci.add_argument("--number", type=int, default=None)
    ci.add_argument("--kind", choices=("issue", "pr"), default="issue")
    ci.set_defaults(func=_cmd_council_init)

    cs = c.add_parser("status", help="Show council status")
    cs.add_argument("name")
    cs.add_argument("--root", default=".")
    cs.set_defaults(func=_cmd_council_status)

    cn = c.add_parser("next", help="Print prompt for next role turn")
    cn.add_argument("name")
    cn.add_argument("--root", default=".")
    cn.add_argument("--out", default=None)
    cn.set_defaults(func=_cmd_council_next)

    ct = c.add_parser("turn", help="Record a role turn")
    ct.add_argument("name")
    ct.add_argument("--root", default=".")
    ct.add_argument("--role", default=None)
    ct.add_argument("--file", default=None)
    ct.add_argument("--content", default=None)
    ct.set_defaults(func=_cmd_council_turn)

    cd = c.add_parser("decide", help="Mark decided + refresh DECISION.md")
    cd.add_argument("name")
    cd.add_argument("--root", default=".")
    cd.set_defaults(func=_cmd_council_decide)

    s = sub.add_parser("smoke", help="Self-check skills + council + recipes")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
