from pathlib import Path

from harnesslab.council import (
    init_council,
    load_state,
    prompt_for_next,
    save_state,
    state_path,
)
from harnesslab.github_ctx import parse_github_ref


def test_parse_github_refs():
    a = parse_github_ref("octocat/Hello-World#42")
    assert a["repo"] == "octocat/Hello-World"
    assert a["number"] == 42
    assert a["kind"] == "issue"

    b = parse_github_ref("https://github.com/octocat/Hello-World/pull/7")
    assert b["kind"] == "pr"
    assert b["number"] == 7


def test_council_roundtrip(tmp_path: Path):
    state, written = init_council(
        tmp_path,
        "demo",
        "Should we ship?",
        max_rounds=1,
        github={"kind": "issue", "repo": "o/r", "number": 1, "title": "t"},
    )
    assert any(p.name == "council.yaml" for p in written)
    assert (tmp_path / "councils" / "demo" / "CONTEXT.md").is_file()

    t1 = state.record_turn("CLAIM: ship | EVIDENCE: tests green | ASK: none", "proposer")
    assert t1["role_id"] == "proposer"
    save_state(state, state_path(tmp_path, "demo"))

    loaded = load_state(state_path(tmp_path, "demo"))
    assert len(loaded.turns) == 1
    prompt = prompt_for_next(loaded)
    assert "Critic" in prompt or "critic" in prompt.lower()

    loaded.record_turn("CLAIM: wait | EVIDENCE: no changelog | ASK: add notes", "critic")
    loaded.record_turn("CLAIM: conditional | EVIDENCE: both partial | ASK: fix notes", "verifier")
    loaded.record_turn("CLAIM: ship after notes | EVIDENCE: consensus | ASK: none", "synthesizer")
    assert loaded.status in {"debating", "decided"}
