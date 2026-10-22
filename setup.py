"""Packaging hook: ship the repository-root ``skills/`` tree inside the package.

The agent-skill source lives at ``skills/`` beside ``src/``; at build time it is
copied into ``tex_tool/skills/`` so installed distributions carry it and
``tex-tool skills-path`` can point at it.
"""
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

SKILLS_SOURCE = Path("skills")


class BuildPyWithSkills(build_py):
    def run(self) -> None:
        super().run()
        destination = Path(self.build_lib, "tex_tool", "skills")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(SKILLS_SOURCE, destination)


setup(cmdclass={"build_py": BuildPyWithSkills})
