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
    assert "[OK] skill harnesslab" in p.stdout


def test_recipe_docker():
    p = run("recipe", "docker-run")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "docker run" in p.stdout
    assert "3000" in p.stdout


def test_recipe_list():
    p = run("recipe", "--list")
    assert p.returncode == 0
    assert "docker-run" in p.stdout


def test_init_pipeline(tmp_path: Path):
    p = run("init-pipeline", str(tmp_path))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (tmp_path / ".harness" / "pipelines" / "xlab-smoke.yaml").is_file()


def test_doctor_runs():
    p = run("doctor")
    # 0 = healthy docker, 2 = warn — both acceptable for CI without Docker engine
    assert p.returncode in (0, 2), p.stdout + p.stderr
    assert "doctor:" in p.stdout
