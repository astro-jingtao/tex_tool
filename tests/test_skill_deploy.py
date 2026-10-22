from pathlib import Path

from tex_tool.cli import main
from tex_tool.skill_deploy import skills_dir


class TestSkillsDir:
    def test_dir_holds_the_skill_tree(self) -> None:
        root = skills_dir()
        assert (root / "SKILL-DEPLOY.md").is_file()
        assert (root / "tex-tool" / "skill" / "SKILL.md").is_file()
        assert (root / "tex-tool" / "meta.yaml").is_file()


class TestSkillsPathCommand:
    def test_prints_dir_and_guide(self, capsys) -> None:
        main(["skills-path"])
        lines = capsys.readouterr().out.splitlines()
        assert Path(lines[0]) == skills_dir()
        assert "SKILL-DEPLOY.md" in lines[1]
