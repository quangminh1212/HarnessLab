"""Print-only recipes for Harness Open Source (no side effects)."""

from __future__ import annotations

from pathlib import Path

from nexuslab.doctor import default_clone_path

RECIPES = ("docker-run", "clone", "stop")


def list_recipes() -> list[str]:
    return list(RECIPES)


def render_recipe(name: str, *, data_dir: str | None = None) -> str:
    key = name.strip().lower().replace("_", "-")
    clone = default_clone_path()
    data = data_dir or str(Path(os_temp()) / "harness")

    if key == "docker-run":
        return f"""# NexusLab recipe: docker-run
# Requires Docker Desktop. UI: http://localhost:3000

docker run -d -p 3000:3000 -p 3022:3022 \\
  -v /var/run/docker.sock:/var/run/docker.sock \\
  -v "{data}:/data" \\
  --name harness --restart always harness/harness

# Logs:  docker logs -f harness
# Stop:  docker stop harness && docker rm harness
"""
    if key == "clone":
        return f"""# NexusLab recipe: clone
# Optional source checkout (large Go monorepo).

git clone https://github.com/harness/harness.git "{clone}"
cd "{clone}"
"""
    if key == "stop":
        return """# NexusLab recipe: stop
docker stop harness
docker rm harness
"""
    raise KeyError(f"unknown recipe: {name!r}; choose from {', '.join(RECIPES)}")


def os_temp() -> Path:
    import tempfile

    return Path(tempfile.gettempdir())
