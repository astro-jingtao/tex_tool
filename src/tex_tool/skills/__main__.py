"""Print the packaged skills directory and its deployment guide (``python -m tex_tool.skills``)."""
from pathlib import Path

root = Path(__file__).resolve().parent
print(root)
print(f"Deployment guide: {root / 'SKILL-DEPLOY.md'}")
