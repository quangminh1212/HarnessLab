import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "harnesslab", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_smoke():
    p = run("smoke")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "[OK] vendor mad" in p.stdout
    assert "[OK] council profile mad" in p.stdout


def test_recipe_docker():
    p = run("recipe", "docker-run")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "docker run" in p.stdout


def test_council_cli(tmp_path: Path):
    p = run(
        "council",
        "init",
        "cli-demo",
        "--topic",
        "Test topic",
        "--root",
        str(tmp_path),
        "--rounds",
        "1",
    )
    assert p.returncode == 0, p.stdout + p.stderr
    p2 = run("council", "next", "cli-demo", "--root", str(tmp_path))
    assert p2.returncode == 0, p2.stdout + p2.stderr
    assert "Proposer" in p2.stdout or "proposer" in p2.stdout
    p3 = run(
        "council",
        "turn",
        "cli-demo",
        "--root",
        str(tmp_path),
        "--role",
        "proposer",
        "--content",
        "CLAIM: yes | EVIDENCE: unit | ASK: none",
    )
    assert p3.returncode == 0, p3.stdout + p3.stderr
    p4 = run("council", "status", "cli-demo", "--root", str(tmp_path))
    assert p4.returncode == 0
    assert "turns:" in p4.stdout


def test_init_pipeline(tmp_path: Path):
    p = run("init-pipeline", str(tmp_path))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (tmp_path / ".harness" / "pipelines" / "xlab-smoke.yaml").is_file()


def test_doctor_runs():
    p = run("doctor")
    assert p.returncode in (0, 2), p.stdout + p.stderr
    assert "doctor:" in p.stdout
