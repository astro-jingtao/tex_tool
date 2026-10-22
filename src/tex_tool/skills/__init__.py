"""The agent-skill tree shipped as package data; run ``python -m tex_tool.skills`` to print its location."""
from pathlib import Path


def skills_dir() -> Path:
    """Return this package's directory — the root of the shipped skill tree."""
    directory = Path(__file__).resolve().parent
    if not (directory / "SKILL-DEPLOY.md").is_file():
        raise FileNotFoundError(f"packaged skills directory not found (looked in {directory})")
    return directory
