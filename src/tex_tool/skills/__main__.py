"""Print the packaged skills directory and its deployment guide (``python -m tex_tool.skills``)."""

from tex_tool.skills import skills_dir

root = skills_dir()
print(root)
print(f"Deployment guide: {root / 'SKILL-DEPLOY.md'}")
