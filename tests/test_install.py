import tempfile
from pathlib import Path

from nexuslab.install import attach_to_hermes, uninstall_from_hermes


def test_attach_detach_junctions():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        (home / "skills").mkdir(parents=True)
        # simulate stock plain dir that must be replaceable
        stock = home / "skills" / "harness-integration"
        stock.mkdir()
        (stock / "SKILL.md").write_text("old", encoding="utf-8")

        linked = attach_to_hermes(home)
        assert any(p.name == "nexuslab" for p in linked)
        skill = home / "skills" / "nexuslab"
        assert skill.exists()
        assert (skill / "SKILL.md").is_file()
        assert "nexuslab" in (skill / "SKILL.md").read_text(encoding="utf-8").lower()
        alias = home / "skills" / "harness-integration"
        assert alias.exists()
        assert "nexuslab" in (alias / "SKILL.md").read_text(encoding="utf-8").lower()

        removed = uninstall_from_hermes(home)
        assert any(p.name == "nexuslab" for p in removed)
        assert not skill.exists()
