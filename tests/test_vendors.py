from pathlib import Path

from harnesslab.council import init_council
from harnesslab.vendors import (
    copy_ahe_templates,
    format_status,
    list_loop_patterns,
    load_mad_config,
    mad_code_files,
    mad_prompts_for_topic,
    status_all,
)


def test_all_vendors_present():
    st = status_all()
    assert len(st) == 3
    missing = [s.key for s in st if not s.present]
    assert not missing, f"missing submodules: {missing}\n{format_status()}"


def test_mad_config_and_code():
    cfg = load_mad_config()
    assert "player_meta_prompt" in cfg
    assert "moderator_prompt" in cfg
    prompts = mad_prompts_for_topic("2+2=?")
    assert "2+2=?" in prompts["player_meta_prompt"]
    files = mad_code_files()
    assert any(p.name == "agent.py" for p in files)
    from harnesslab.vendors import mad_root

    assert (mad_root() / "interactive.py").is_file()


def test_ahe_templates_copy(tmp_path: Path):
    written = copy_ahe_templates(tmp_path / "ahe")
    names = {p.name for p in written}
    assert "PLAN.md" in names
    assert "IMPLEMENT.md" in names or "HARNESS_CHECKLIST.md" in names


def test_loop_patterns_exist():
    patterns = list_loop_patterns()
    assert len(patterns) >= 3
    stems = {p.stem for p in patterns}
    assert "pr-babysitter" in stems or "daily-triage" in stems


def test_council_profiles(tmp_path: Path):
    mad, _ = init_council(tmp_path, "m", "t", profile="mad", max_rounds=1)
    assert {r["id"] for r in mad.roles} >= {"devil", "angel", "judge"}
    gh, _ = init_council(tmp_path, "g", "t", profile="github", max_rounds=1)
    assert {r["id"] for r in gh.roles} >= {"proposer", "critic"}
    har, _ = init_council(tmp_path, "h", "t", profile="harness", max_rounds=1)
    assert {r["id"] for r in har.roles} >= {"observer", "planner", "actor"}
