"""HarnessLab CLI — attach + doctor + recipes for Harness OSS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harnesslab import __version__
from harnesslab.doctor import run_doctor
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
    print(f"attached {len(linked)} path(s) (junction/symlink, SoT = HarnessLab repo)")
    for p in linked:
        print(f"  + {p}")
    print("In Hermes chat: /harnesslab  or  /harness-integration")
    print("Detach: harnesslab detach   or   scripts\\uninstall.ps1")
    return 0


def _cmd_detach(args: argparse.Namespace) -> int:
    home = Path(args.hermes_home) if args.hermes_home else default_hermes_home()
    removed = uninstall_from_hermes(home)
    print(f"Hermes home: {home}")
    if not removed:
        print("nothing to remove (already clean)")
        return 0
    print(f"detached {len(removed)} path(s)")
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


def _cmd_smoke(_args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parent.parent
    failed = 0
    for name in ("harnesslab", "harness-integration"):
        skill = root / "skills" / name / "SKILL.md"
        if not skill.is_file():
            print(f"  [FAIL] missing skill {name}")
            failed += 1
        else:
            text = skill.read_text(encoding="utf-8").lower()
            if "harness" not in text:
                print(f"  [FAIL] skill {name} content weak")
                failed += 1
            else:
                print(f"  [OK] skill {name}")
    for rec in list_recipes():
        try:
            body = render_recipe(rec)
            if "harness" not in body.lower():
                raise ValueError("weak recipe")
            print(f"  [OK] recipe {rec}")
        except Exception as e:
            print(f"  [FAIL] recipe {rec}: {e}")
            failed += 1
    report = run_doctor()
    print(report.summary().splitlines()[0])
    print(f"smoke: failed={failed}")
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="harnesslab",
        description="HarnessLab — external Hermes module for Harness Open Source",
    )
    p.add_argument("--version", action="version", version=f"harnesslab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("attach", help="Attach skills into Hermes via junctions")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_attach)

    s = sub.add_parser("detach", help="Detach HarnessLab junctions from Hermes")
    s.add_argument("--hermes-home", default=None)
    s.set_defaults(func=_cmd_detach)

    s = sub.add_parser("doctor", help="Check Docker/git/clone readiness")
    s.set_defaults(func=_cmd_doctor)

    s = sub.add_parser("recipe", help="Print clone/docker-run recipes")
    s.add_argument("name", nargs="?", default="docker-run")
    s.add_argument("--list", action="store_true")
    s.add_argument("--data-dir", default=None, help="Host bind path for /data")
    s.set_defaults(func=_cmd_recipe)

    s = sub.add_parser("init-pipeline", help="Scaffold .harness/pipelines example")
    s.add_argument("path", help="Project directory")
    s.set_defaults(func=_cmd_init_pipeline)

    s = sub.add_parser("smoke", help="Self-check skills + recipes")
    s.set_defaults(func=_cmd_smoke)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
