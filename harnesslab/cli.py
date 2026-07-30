"""HarnessLab CLI — unified hub for 3 vendored labs + council/loop/handoff."""

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
from harnesslab.handoff import (
    example_handoff,
    load_handoff,
    validate_handoff,
    write_handoff,
    Handoff,
)
from harnesslab.install import attach_to_hermes, default_hermes_home, uninstall_from_hermes
from harnesslab.loop import init_loop, load_loop, loop_dir, save_loop, Phase
from harnesslab.pipeline import write_pipeline_scaffold
from harnesslab.profiles import list_profiles
from harnesslab.recipe import list_recipes, render_recipe
from harnesslab.scaffold import scaffold_project
from harnesslab.score import score_project
from harnesslab.vendors import (
    copy_ahe_templates,
    copy_loop_pattern,
    format_status,
    list_loop_patterns,
    list_loop_tools,
    load_mad_config,
    mad_code_files,
    mad_prompts_for_topic,
    mad_root,
    run_mad_interactive_hint,
    run_loop_node_tool,
)


def _ensure_utf8_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows consoles using cp1252."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _cmd_attach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    try:
        linked = attach_to_hermes(home)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Hermes home: {home}")
    for p in linked:
        print(f"  + {p}")
    print("Chat: /harnesslab")
    return 0


def _cmd_detach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    for p in uninstall_from_hermes(home):
        print(f"  - {p}")
    return 0


def _cmd_doctor(_a: argparse.Namespace) -> int:
    print(run_doctor().summary())
    print()
    print(format_status())
    r = run_doctor()
    return 0 if r.ok else 2


def _cmd_recipe(args: argparse.Namespace) -> int:
    if args.list:
        print("\n".join(list_recipes()))
        return 0
    try:
        print(render_recipe(args.name or "docker-run", data_dir=args.data_dir))
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_init_pipeline(args: argparse.Namespace) -> int:
    for p in write_pipeline_scaffold(Path(args.path)):
        print(f"  + {p}")
    return 0


def _cmd_vendors(_a: argparse.Namespace) -> int:
    print(format_status())
    return 0 if all(s.present for s in __import__("harnesslab.vendors", fromlist=["status_all"]).status_all()) else 1


def _cmd_mad_status(_a: argparse.Namespace) -> int:
    root = mad_root()
    print(f"MAD root: {root}")
    print(f"  present: {(root / 'code' / 'utils' / 'agent.py').is_file()}")
    files = mad_code_files()
    print(f"  python files: {len(files)}")
    for f in files:
        print(f"    - {f.relative_to(root)}")
    try:
        cfg = load_mad_config()
        print(f"  config keys: {', '.join(cfg.keys())}")
    except FileNotFoundError as e:
        print(f"  error: {e}")
        return 1
    print()
    print(run_mad_interactive_hint())
    return 0


def _cmd_mad_init(args: argparse.Namespace) -> int:
    """Init council with MAD profile + upstream prompts from config4all.json."""
    root = Path(args.root)
    try:
        prompts = mad_prompts_for_topic(args.topic)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    state, written = init_council(
        root,
        args.name,
        args.topic,
        max_rounds=args.rounds or 3,
        profile="mad",
        mad_prompts=prompts,
    )
    # write MAD prompt pack for Hermes
    pack = root / "councils" / args.name / "MAD_PROMPTS.json"
    import json

    pack.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(pack)
    print(status_text(state))
    for p in written:
        print(f"  + {p}")
    print("\nUpstream MAD engine (optional OpenAI):")
    print(f"  {mad_root() / 'interactive.py'}")
    return 0


def _cmd_ahe_templates(args: argparse.Namespace) -> int:
    dest = Path(args.dest)
    try:
        written = copy_ahe_templates(dest)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"copied {len(written)} AHE templates → {dest}")
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_loop_eng_list(args: argparse.Namespace) -> int:
    if args.tools:
        for t in list_loop_tools():
            print(t)
        return 0
    for p in list_loop_patterns():
        print(p.stem)
    return 0


def _cmd_loop_eng_copy(args: argparse.Namespace) -> int:
    dest = Path(args.dest) if args.dest else Path(f"patterns/{args.name}.md")
    try:
        p = copy_loop_pattern(args.name, dest)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"  + {p}")
    return 0


def _cmd_loop_eng_run(args: argparse.Namespace) -> int:
    try:
        r = run_loop_node_tool(args.tool, args.args or [])
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    sys.stdout.write(r.stdout or "")
    sys.stderr.write(r.stderr or "")
    return r.returncode


def _cmd_github_pull(args: argparse.Namespace) -> int:
    try:
        ctx = pull_context(ref=args.ref, repo=args.repo, number=args.number, kind=args.kind)
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
        print("--- body ---")
        print((ctx.get("body") or "")[:3000])
    if args.out:
        Path(args.out).write_text(
            f"# {ctx.get('title')}\n\n{ctx.get('url')}\n\n{ctx.get('body') or ''}\n",
            encoding="utf-8",
        )
    return 1 if ctx.get("error") and "gh_not_found" in str(ctx.get("error")) else 0


def _cmd_council_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    gh: dict = {}
    if args.ref or (args.repo and args.number):
        try:
            gh = pull_context(ref=args.ref, repo=args.repo, number=args.number, kind=args.kind)
        except Exception as e:
            print(f"warning: github pull failed: {e}", file=sys.stderr)
    topic = args.topic
    if not topic and gh.get("title"):
        topic = f"{gh.get('kind')} {gh.get('repo')}#{gh.get('number')}: {gh.get('title')}"
    if not topic:
        print("error: --topic required (or GitHub ref)", file=sys.stderr)
        return 1
    profile = args.profile or "github"
    mad_prompts = None
    if profile == "mad":
        try:
            mad_prompts = mad_prompts_for_topic(topic)
        except FileNotFoundError as e:
            print(f"warning: {e}", file=sys.stderr)
    state, written = init_council(
        root,
        args.name,
        topic,
        max_rounds=args.rounds or 0,
        github=gh,
        profile=profile,
        mad_prompts=mad_prompts,
    )
    if mad_prompts:
        import json

        pack = root / "councils" / args.name / "MAD_PROMPTS.json"
        pack.write_text(json.dumps(mad_prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(pack)
    print(status_text(state))
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_council_status(args: argparse.Namespace) -> int:
    p = state_path(Path(args.root), args.name)
    path = p if p.is_file() else p.with_suffix(".json")
    if not path.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    print(status_text(load_state(path)))
    return 0


def _cmd_council_list(args: argparse.Namespace) -> int:
    """List council workspaces under root/councils/."""
    root = Path(args.root)
    base = root / "councils"
    if not base.is_dir():
        print(f"councils: (none under {base})")
        return 0
    found = 0
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        sp = d / "council.yaml"
        if not sp.is_file():
            sp = d / "council.json"
        if not sp.is_file():
            continue
        found += 1
        try:
            st = load_state(sp)
            print(f"  {d.name:20} profile={st.profile} status={st.status} topic={st.topic[:60]}")
        except Exception as e:
            print(f"  {d.name:20} (unreadable: {e})")
    if not found:
        print(f"councils: (none under {base})")
    return 0


def _cmd_council_next(args: argparse.Namespace) -> int:
    p = state_path(Path(args.root), args.name)
    path = p if p.is_file() else p.with_suffix(".json")
    if not path.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    text = prompt_for_next(load_state(path))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def _cmd_council_turn(args: argparse.Namespace) -> int:
    root = Path(args.root)
    p = state_path(root, args.name)
    path = p if p.is_file() else p.with_suffix(".json")
    if not path.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    content = Path(args.file).read_text(encoding="utf-8") if args.file else args.content
    if not content:
        print("error: --file or --content required", file=sys.stderr)
        return 1
    state = load_state(path)
    role_map = {r["id"]: r for r in state.roles}
    turn = state.record_turn(content, role_id=args.role)
    save_state(state, path)
    title = role_map.get(turn["role_id"], {}).get("title", turn["role_id"])
    append_transcript(root, args.name, turn, title)
    if state.status == "decided":
        write_decision_scaffold(root, args.name, state)
    print(status_text(state))
    return 0


def _cmd_council_decide(args: argparse.Namespace) -> int:
    root = Path(args.root)
    p = state_path(root, args.name)
    path = p if p.is_file() else p.with_suffix(".json")
    if not path.is_file():
        print(f"error: no council {args.name}", file=sys.stderr)
        return 1
    state = load_state(path)
    state.status = "decided"
    save_state(state, path)
    out = write_decision_scaffold(root, args.name, state)
    print(status_text(state))
    print(f"  + {out}")
    gh = state.github
    if gh.get("repo") and gh.get("number"):
        print(recipe_comment(str(gh["repo"]), int(gh["number"]), str(gh.get("kind") or "issue")))
    return 0


def _cmd_loop_init(args: argparse.Namespace) -> int:
    state, written = init_loop(Path(args.root), args.name, args.goal)
    print(state.panel())
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_loop_status(args: argparse.Namespace) -> int:
    sp = loop_dir(Path(args.root), args.name) / "loop.yaml"
    if not sp.is_file():
        print(f"error: no loop {args.name}", file=sys.stderr)
        return 1
    print(load_loop(sp).panel())
    return 0


def _cmd_loop_list(args: argparse.Namespace) -> int:
    """List OPAV loops under root/loops/."""
    root = Path(args.root)
    base = root / "loops"
    if not base.is_dir():
        print(f"loops: (none under {base})")
        return 0
    found = 0
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        sp = d / "loop.yaml"
        if not sp.is_file():
            continue
        found += 1
        try:
            st = load_loop(sp)
            print(f"  {d.name:20} phase={st.phase} goal={st.goal[:60]}")
        except Exception as e:
            print(f"  {d.name:20} (unreadable: {e})")
    if not found:
        print(f"loops: (none under {base})")
    return 0


def _cmd_loop_advance(args: argparse.Namespace) -> int:
    sp = loop_dir(Path(args.root), args.name) / "loop.yaml"
    if not sp.is_file():
        print(f"error: no loop {args.name}", file=sys.stderr)
        return 1
    state = load_loop(sp)
    if args.mutate:
        state.phase = Phase.ACT.value
        state.record_mutation()
    if args.verify is not None:
        state.phase = Phase.VERIFY.value
        state.record_verification(args.verify)
    else:
        state.advance()
    save_loop(state, sp)
    print(state.panel())
    return 0


def _cmd_handoff_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    import json

    import yaml

    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    errs = validate_handoff(data or {})
    if errs:
        print("INVALID")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("VALID handoff")
    return 0


def _cmd_handoff_example(args: argparse.Namespace) -> int:
    import yaml

    data = example_handoff()
    out = Path(args.out) if args.out else None
    if out:
        write_handoff(out, Handoff.from_dict(data))
        print(f"wrote {out}")
    else:
        print(yaml.safe_dump(data, sort_keys=False))
    return 0


def _cmd_scaffold(args: argparse.Namespace) -> int:
    written = scaffold_project(Path(args.path))
    # also pull AHE templates if present
    try:
        ahe = copy_ahe_templates(Path(args.path) / "templates" / "ahe")
        written.extend(ahe)
    except FileNotFoundError:
        pass
    print(f"scaffolded {args.path}")
    for p in written:
        print(f"  + {p}")
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    r = score_project(Path(args.path))
    print(r.summary())
    return 0 if r.score >= 50 else 2


def _cmd_sources(_a: argparse.Namespace) -> int:
    from harnesslab.sources import check_catalog, format_catalog

    print(format_catalog())
    return 0 if not check_catalog() else 1


def _cmd_smoke(_a: argparse.Namespace) -> int:
    import tempfile

    failed = 0
    # vendors
    from harnesslab.vendors import status_all

    for s in status_all():
        if s.present:
            print(f"  [OK] vendor {s.key}")
        else:
            print(f"  [FAIL] vendor {s.key} missing")
            failed += 1
    # mad config
    try:
        mad_prompts_for_topic("test topic")
        print("  [OK] MAD config4all.json")
    except Exception as e:
        print(f"  [FAIL] MAD config: {e}")
        failed += 1
    # ahe templates
    if (Path(__file__).resolve().parent.parent / "labs/awesome-harness-engineering/templates/PLAN.md").is_file():
        print("  [OK] AHE templates")
    else:
        print("  [FAIL] AHE templates")
        failed += 1
    # loop patterns
    if list_loop_patterns():
        print(f"  [OK] loop-engineering patterns ({len(list_loop_patterns())})")
    else:
        print("  [FAIL] loop-engineering patterns")
        failed += 1
    # council mad
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        try:
            st, _ = init_council(td_path, "t", "Q?", profile="mad", max_rounds=1)
            assert any(r["id"] == "devil" for r in st.roles)
            print("  [OK] council profile mad")
        except Exception as e:
            print(f"  [FAIL] council mad: {e}")
            failed += 1
        st2, _ = init_council(td_path, "g", "PR?", profile="github", max_rounds=1)
        assert any(r["id"] == "proposer" for r in st2.roles)
        print("  [OK] council profile github")
        st3, _ = init_council(td_path, "h", "goal", profile="harness", max_rounds=1)
        assert any(r["id"] == "observer" for r in st3.roles)
        print("  [OK] council profile harness")
        st4, _ = init_council(td_path, "ce", "eval answer quality", profile="chateval", max_rounds=1)
        assert any(r["id"] == "moderator" for r in st4.roles)
        print("  [OK] council profile chateval (ChatEval)")
        st5, _ = init_council(td_path, "sw", "fix issue #1", profile="swe", max_rounds=1)
        assert any(r["id"] == "locator" for r in st5.roles)
        print("  [OK] council profile swe (SWE-Debate)")
        init_loop(td_path, "L1", "do thing")
        print("  [OK] OPAV loop init")
        scaffold_project(td_path / "proj")
        sc = score_project(td_path / "proj")
        print(f"  [OK] score {sc.score}")
    from harnesslab.sources import check_catalog

    cat_probs = check_catalog()
    if cat_probs:
        print(f"  [FAIL] sources catalog: {cat_probs}")
        failed += 1
    else:
        print("  [OK] sources catalog")
    print(f"smoke: failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="harnesslab",
        description=(
            "HarnessLab — merge of MAD + awesome-harness-engineering + loop-engineering "
            "as vendored labs/, with council/loop/handoff CLI for Hermes"
        ),
    )
    p.add_argument("--version", action="version", version=f"harnesslab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, help_, func, **kwargs):
        s = sub.add_parser(name, help=help_)
        for k, v in kwargs.items():
            pass
        s.set_defaults(func=func)
        return s

    s = sub.add_parser("attach", help="Attach Hermes skill junctions")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_attach)

    s = sub.add_parser("detach", help="Detach from Hermes")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_detach)

    s = sub.add_parser("doctor", help="Env + vendored labs status")
    s.set_defaults(func=_cmd_doctor)

    s = sub.add_parser("vendors", help="Show 3 vendored labs status")
    s.set_defaults(func=_cmd_vendors)

    # MAD upstream
    s = sub.add_parser("mad", help="Multi-Agents-Debate upstream (labs/Multi-Agents-Debate)")
    ms = s.add_subparsers(dest="mad_cmd", required=True)
    m1 = ms.add_parser("status", help="Show MAD code paths + run hints")
    m1.set_defaults(func=_cmd_mad_status)
    m2 = ms.add_parser("init", help="Council with MAD profile + config4all prompts")
    m2.add_argument("name")
    m2.add_argument("--topic", required=True)
    m2.add_argument("--root", default=".")
    m2.add_argument("--rounds", type=int, default=3)
    m2.set_defaults(func=_cmd_mad_init)

    # AHE
    s = sub.add_parser("ahe", help="awesome-harness-engineering templates")
    asub = s.add_subparsers(dest="ahe_cmd", required=True)
    a1 = asub.add_parser("templates", help="Copy AHE templates into a directory")
    a1.add_argument("dest", nargs="?", default="templates/ahe")
    a1.set_defaults(func=_cmd_ahe_templates)

    # loop-engineering
    s = sub.add_parser("loop-eng", help="loop-engineering patterns/tools (GitHub multi-agent loops)")
    ls = s.add_subparsers(dest="le_cmd", required=True)
    l1 = ls.add_parser("list", help="List patterns or tools")
    l1.add_argument("--tools", action="store_true")
    l1.set_defaults(func=_cmd_loop_eng_list)
    l2 = ls.add_parser("copy", help="Copy a pattern markdown")
    l2.add_argument("name")
    l2.add_argument("--dest", default=None)
    l2.set_defaults(func=_cmd_loop_eng_copy)
    l3 = ls.add_parser("run", help="Run node tool from labs/loop-engineering/tools/<name>")
    l3.add_argument("tool")
    l3.add_argument("args", nargs="*")
    l3.set_defaults(func=_cmd_loop_eng_run)

    # github
    s = sub.add_parser("github", help="GitHub issue/PR helpers")
    gs = s.add_subparsers(dest="gh_cmd", required=True)
    gp = gs.add_parser("pull")
    gp.add_argument("--ref", default=None)
    gp.add_argument("--repo", default=None)
    gp.add_argument("--number", type=int, default=None)
    gp.add_argument("--kind", choices=("issue", "pr"), default="issue")
    gp.add_argument("--out", default=None)
    gp.add_argument("--json", action="store_true")
    gp.set_defaults(func=_cmd_github_pull)

    # council
    s = sub.add_parser("council", help="Multi-AI council (profiles: mad|github|harness)")
    cs = s.add_subparsers(dest="c_cmd", required=True)
    ci = cs.add_parser("init")
    ci.add_argument("name")
    ci.add_argument("--topic", default=None)
    ci.add_argument("--root", default=".")
    ci.add_argument("--rounds", type=int, default=0)
    ci.add_argument("--profile", choices=list_profiles(), default="github")
    ci.add_argument("--ref", default=None)
    ci.add_argument("--repo", default=None)
    ci.add_argument("--number", type=int, default=None)
    ci.add_argument("--kind", choices=("issue", "pr"), default="issue")
    ci.set_defaults(func=_cmd_council_init)
    cl = cs.add_parser("list", help="List council workspaces")
    cl.add_argument("--root", default=".")
    cl.set_defaults(func=_cmd_council_list)
    for cmd, fn in (
        ("status", _cmd_council_status),
        ("next", _cmd_council_next),
        ("turn", _cmd_council_turn),
        ("decide", _cmd_council_decide),
    ):
        c = cs.add_parser(cmd)
        c.add_argument("name")
        c.add_argument("--root", default=".")
        if cmd == "next":
            c.add_argument("--out", default=None)
        if cmd == "turn":
            c.add_argument("--role", default=None)
            c.add_argument("--file", default=None)
            c.add_argument("--content", default=None)
        c.set_defaults(func=fn)

    # OPAV loop
    s = sub.add_parser("loop", help="OPAV agent harness loop (awesome-harness style)")
    lps = s.add_subparsers(dest="loop_cmd", required=True)
    li = lps.add_parser("init")
    li.add_argument("name")
    li.add_argument("--goal", required=True)
    li.add_argument("--root", default=".")
    li.set_defaults(func=_cmd_loop_init)
    ll = lps.add_parser("list", help="List loops under root/loops/")
    ll.add_argument("--root", default=".")
    ll.set_defaults(func=_cmd_loop_list)
    ls2 = lps.add_parser("status")
    ls2.add_argument("name")
    ls2.add_argument("--root", default=".")
    ls2.set_defaults(func=_cmd_loop_status)
    la = lps.add_parser("advance")
    la.add_argument("name")
    la.add_argument("--root", default=".")
    la.add_argument("--mutate", action="store_true")
    la.add_argument("--verify", type=lambda x: x.lower() != "false", nargs="?", const=True, default=None)
    la.set_defaults(func=_cmd_loop_advance)

    # handoff
    s = sub.add_parser("handoff", help="Typed multi-agent handoffs")
    hs = s.add_subparsers(dest="h_cmd", required=True)
    hv = hs.add_parser("validate")
    hv.add_argument("path")
    hv.set_defaults(func=_cmd_handoff_validate)
    he = hs.add_parser("example")
    he.add_argument("--out", default=None)
    he.set_defaults(func=_cmd_handoff_example)

    s = sub.add_parser("scaffold", help="Scaffold project harness + AHE templates")
    s.add_argument("path", nargs="?", default=".")
    s.set_defaults(func=_cmd_scaffold)

    s = sub.add_parser("score", help="Harness readiness score 0–100")
    s.add_argument("path", nargs="?", default=".")
    s.set_defaults(func=_cmd_score)

    s = sub.add_parser("recipe", help="Optional Harness OSS docker recipes")
    s.add_argument("name", nargs="?", default="docker-run")
    s.add_argument("--list", action="store_true")
    s.add_argument("--data-dir", default=None)
    s.set_defaults(func=_cmd_recipe)

    s = sub.add_parser("init-pipeline", help="Scaffold .harness/pipelines")
    s.add_argument("path")
    s.set_defaults(func=_cmd_init_pipeline)

    s = sub.add_parser("sources", help="List equivalent GitHub projects + integration check")
    s.set_defaults(func=_cmd_sources)

    s = sub.add_parser("smoke", help="Full self-check including 3 vendored labs")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
