from pathlib import Path

import pytest

from tex_tool.abstract.extract import (
    _extract_balanced_brackets,
    clean_latex_comments,
    convert_font_commands,
    convert_special_chars,
    convert_to_arxiv,
    expand_macros,
    extract_abstract_from_tex,
    extract_balanced_braces,
    find_abstract_block,
    find_math_regions,
    main,
    parse_newcommands,
    wrap_standalone_math_commands,
)


class TestExtractAbstract:
    # ------------------------------------------------------------------
    # find_abstract_block
    # ------------------------------------------------------------------
    def test_find_abstract_block_found(self) -> None:
        content = r"""
\begin{document}
\begin{abstract}
This is the abstract text.
\end{abstract}
\end{document}
"""
        result = find_abstract_block(content)
        assert result == "This is the abstract text."

    def test_find_abstract_block_missing(self) -> None:
        content = r"\begin{document}\end{document}"
        assert find_abstract_block(content) is None

    def test_find_abstract_block_multiline(self) -> None:
        content = r"""
\begin{abstract}
Line one.
Line two.
\end{abstract}
"""
        result = find_abstract_block(content)
        assert result == "Line one.\nLine two."

    # ------------------------------------------------------------------
    # clean_latex_comments
    # ------------------------------------------------------------------
    def test_clean_latex_comments_removes_comments(self) -> None:
        text = "real content % this is a comment"
        assert clean_latex_comments(text) == "real content "

    def test_clean_latex_comments_preserves_escaped_percent(self) -> None:
        text = r"50\% complete % comment"
        result = clean_latex_comments(text)
        assert "50%" in result
        assert "comment" not in result

    def test_clean_latex_comments_multiline(self) -> None:
        text = "line1\n% comment line\nline3 % trailing"
        result = clean_latex_comments(text)
        lines = result.splitlines()
        assert lines[0] == "line1"
        assert lines[1].strip() == ""
        assert "trailing" not in lines[2]

    # ------------------------------------------------------------------
    # extract_balanced_braces
    # ------------------------------------------------------------------
    def test_extract_balanced_braces_simple(self) -> None:
        content, end = extract_balanced_braces("{abc}", 0)
        assert content == "abc"
        assert end == 5

    def test_extract_balanced_braces_nested(self) -> None:
        content, end = extract_balanced_braces("{a{b}c}", 0)
        assert content == "a{b}c"
        assert end == 7

    def test_extract_balanced_braces_escaped(self) -> None:
        s = r"{a\{b\}}"  # 8 chars: { a \ { b \ } }
        content, end = extract_balanced_braces(s, 0)
        assert content == r"a\{b\}"
        assert end == len(s)

    def test_extract_balanced_braces_within_text(self) -> None:
        text = "prefix {inner} suffix"
        content, end = extract_balanced_braces(text, 7)
        assert content == "inner"
        assert end == 14

    def test_extract_balanced_braces_unbalanced_raises(self) -> None:
        with pytest.raises(ValueError):
            extract_balanced_braces("{abc", 0)

    # ------------------------------------------------------------------
    # _extract_balanced_brackets
    # ------------------------------------------------------------------
    def test_extract_balanced_brackets_simple(self) -> None:
        content, end = _extract_balanced_brackets("[abc]", 0)
        assert content == "abc"
        assert end == 5

    def test_extract_balanced_brackets_nested(self) -> None:
        content, end = _extract_balanced_brackets("[a[b]c]", 0)
        assert content == "a[b]c"
        assert end == 7

    # ------------------------------------------------------------------
    # parse_newcommands
    # ------------------------------------------------------------------
    def test_parse_newcommands_zero_arg(self) -> None:
        content = r"\newcommand{\foo}{bar}"
        defs = parse_newcommands(content)
        assert "\\foo" in defs
        assert defs["\\foo"]["body"] == "bar"
        assert defs["\\foo"]["num_args"] == 0

    def test_parse_newcommands_with_args(self) -> None:
        content = r"\newcommand{\foo}[2]{#1 plus #2}"
        defs = parse_newcommands(content)
        assert defs["\\foo"]["num_args"] == 2
        assert defs["\\foo"]["body"] == "#1 plus #2"

    def test_parse_newcommands_optional_arg(self) -> None:
        content = r"\newcommand{\foo}[2][]{#2_#1}"
        defs = parse_newcommands(content)
        assert defs["\\foo"]["num_args"] == 2
        assert defs["\\foo"]["has_optional"] is True
        assert defs["\\foo"]["default"] == ""
        assert defs["\\foo"]["body"] == "#2_#1"

    def test_parse_newcommands_optional_with_default(self) -> None:
        content = r"\newcommand{\foo}[2][default]{#2_#1}"
        defs = parse_newcommands(content)
        assert defs["\\foo"]["has_optional"] is True
        assert defs["\\foo"]["default"] == "default"

    def test_parse_newcommands_brace_less_name(self) -> None:
        content = r"\newcommand\foo{bar}"
        defs = parse_newcommands(content)
        assert "\\foo" in defs
        assert defs["\\foo"]["body"] == "bar"

    def test_parse_newcommands_renewcommand(self) -> None:
        content = r"\newcommand{\foo}{first}\renewcommand{\foo}{second}"
        defs = parse_newcommands(content)
        assert defs["\\foo"]["body"] == "second"

    def test_parse_newcommands_providecommand(self) -> None:
        content = r"\providecommand{\foo}{provided}"
        defs = parse_newcommands(content)
        assert "\\foo" in defs

    def test_parse_newcommands_star_form(self) -> None:
        content = r"\newcommand*{\foo}{bar}"
        defs = parse_newcommands(content)
        assert "\\foo" in defs

    def test_parse_newcommands_commented_out(self) -> None:
        content = r"% \newcommand{\ignored}{bad}\n\newcommand{\kept}{good}"
        # The first is a comment line, the second is not.
        # clean_latex_comments is called inside parse_newcommands, so
        # we need to detect that the regex matches the right one.
        # We need a newline between them:
        content = "% \\newcommand{\\ignored}{bad}\n\\newcommand{\\kept}{good}"
        defs = parse_newcommands(content)
        assert "\\kept" in defs
        assert "\\ignored" not in defs

    def test_parse_newcommands_only_preamble(self) -> None:
        content = (
            "\\newcommand{\\before}{ok}\n"
            "\\begin{document}\n"
            "\\newcommand{\\after}{not_parsed}\n"
            "\\end{document}"
        )
        defs = parse_newcommands(content)
        assert "\\before" in defs
        assert "\\after" not in defs

    def test_parse_newcommands_nested_braces_in_body(self) -> None:
        content = r"\newcommand{\ICO}{{I_{\rm CO}}}"
        defs = parse_newcommands(content)
        assert defs["\\ICO"]["body"] == "{I_{\\rm CO}}"

    # ------------------------------------------------------------------
    # expand_macros
    # ------------------------------------------------------------------
    def test_expand_macros_zero_arg(self) -> None:
        text = r"Hello \foo world"
        defs = {"\\foo": {"body": "bar", "num_args": 0, "has_optional": False, "default": ""}}
        result = expand_macros(text, defs)
        assert result == "Hello bar world"

    def test_expand_macros_prefix_safety(self) -> None:
        text = r"\bx and \bxerr"
        defs = {
            "\\bx": {"body": "x", "num_args": 0, "has_optional": False, "default": ""},
            "\\bxerr": {"body": "x_err", "num_args": 0, "has_optional": False, "default": ""},
        }
        result = expand_macros(text, defs)
        assert result == "x and x_err"

    def test_expand_macros_with_args(self) -> None:
        text = r"\foo{hello}{world}"
        defs = {"\\foo": {"body": "#1+#2", "num_args": 2, "has_optional": False, "default": ""}}
        result = expand_macros(text, defs)
        assert result == "hello+world"

    def test_expand_macros_with_optional(self) -> None:
        text = r"\err[,i]{y}"
        defs = {"\\err": {"body": "#2_{#1}", "num_args": 2, "has_optional": True, "default": ""}}
        result = expand_macros(text, defs)
        assert result == "y_{,i}"

    def test_expand_macros_with_optional_default(self) -> None:
        text = r"\err{y}"
        defs = {"\\err": {"body": "#2_{err#1}", "num_args": 2, "has_optional": True, "default": ""}}
        result = expand_macros(text, defs)
        assert result == "y_{err}"

    def test_expand_macros_chain(self) -> None:
        text = r"\bxerr"
        defs = {
            "\\bx": {"body": "\\mathbf{x}", "num_args": 0, "has_optional": False, "default": ""},
            "\\bxerr": {"body": "\\err{\\bx}", "num_args": 0, "has_optional": False, "default": ""},
            "\\err": {"body": "#1", "num_args": 1, "has_optional": False, "default": ""},
        }
        result = expand_macros(text, defs)
        # \bxerr -> \err{\bx} -> \err{\mathbf{x}} -> \mathbf{x}
        assert result == "\\mathbf{x}"

    def test_expand_macros_undefined_left_alone(self) -> None:
        text = r"\foo and \bar"
        defs = {"\\foo": {"body": "ok", "num_args": 0, "has_optional": False, "default": ""}}
        result = expand_macros(text, defs)
        assert result == "ok and \\bar"

    def test_expand_macros_no_definitions(self) -> None:
        text = r"plain text"
        result = expand_macros(text, {})
        assert result == "plain text"

    # ------------------------------------------------------------------
    # find_math_regions
    # ------------------------------------------------------------------
    def test_find_math_regions_inline(self) -> None:
        regions = find_math_regions("text $x=1$ more")
        assert len(regions) == 1
        start, end = regions[0]
        assert "x=1" in "text $x=1$ more"[start:end]

    def test_find_math_regions_display(self) -> None:
        regions = find_math_regions("text $$x=1$$ more")
        assert len(regions) == 1

    def test_find_math_regions_paren(self) -> None:
        regions = find_math_regions(r"text \(x=1\) more")
        assert len(regions) == 1

    def test_find_math_regions_bracket(self) -> None:
        regions = find_math_regions(r"text \[x=1\] more")
        assert len(regions) == 1

    def test_find_math_regions_multiple(self) -> None:
        regions = find_math_regions("$a$ and $b$")
        assert len(regions) == 2

    # ------------------------------------------------------------------
    # wrap_standalone_math_commands
    # ------------------------------------------------------------------
    def test_wrap_math_commands_outside_math(self) -> None:
        text = r"\lesssim 100 pc"
        regions = find_math_regions(text)
        result = wrap_standalone_math_commands(text, regions)
        assert result == r"$\lesssim$ 100 pc"

    def test_wrap_math_commands_inside_math_unchanged(self) -> None:
        text = r"$\lesssim$ 100 pc"
        regions = find_math_regions(text)
        result = wrap_standalone_math_commands(text, regions)
        assert result == r"$\lesssim$ 100 pc"  # No double-wrapping

    def test_wrap_math_commands_alpha(self) -> None:
        text = r"\alpha particle"
        regions = find_math_regions(text)
        result = wrap_standalone_math_commands(text, regions)
        assert result == r"$\alpha$ particle"

    def test_wrap_math_commands_unknown_left_alone(self) -> None:
        text = r"\unknown outside math"
        regions = find_math_regions(text)
        result = wrap_standalone_math_commands(text, regions)
        assert result == r"\unknown outside math"

    # ------------------------------------------------------------------
    # convert_font_commands
    # ------------------------------------------------------------------
    def test_convert_tt(self) -> None:
        text = r"{\tt raddest}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\tt{raddest}$"

    def test_convert_rm(self) -> None:
        text = r"{\rm CO}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\rm{CO}$"

    def test_convert_sc(self) -> None:
        text = r"{\sc ii}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\text{ii}$"

    def test_convert_bf(self) -> None:
        text = r"{\bf bold}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\mathbf{bold}$"

    def test_convert_textbf(self) -> None:
        text = r"\textbf{bold}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\mathbf{bold}$"

    def test_convert_textit(self) -> None:
        text = r"\textit{italic}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"$\mathit{italic}$"

    def test_convert_textcolor(self) -> None:
        text = r"\textcolor{red}{CITE}"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == "CITE"

    def test_font_command_inside_math_preserved(self) -> None:
        text = r"${\rm CO}$"
        regions = find_math_regions(text)
        result = convert_font_commands(text, regions)
        assert result == r"${\rm CO}$"

    # ------------------------------------------------------------------
    # convert_special_chars
    # ------------------------------------------------------------------
    def test_convert_en_dash(self) -> None:
        text = "log\u2013log"  # en-dash
        result = convert_special_chars(text)
        assert result == "log-log"

    def test_convert_em_dash(self) -> None:
        text = "foo\u2014bar"  # em-dash
        result = convert_special_chars(text)
        assert result == "foo--bar"

    def test_convert_tilde(self) -> None:
        text = "H~II"
        result = convert_special_chars(text)
        assert result == "H II"

    def test_convert_double_quotes(self) -> None:
        text = "``quoted''"
        result = convert_special_chars(text)
        assert result == '"quoted"'

    # ------------------------------------------------------------------
    # convert_to_arxiv (orchestration)
    # ------------------------------------------------------------------
    def test_convert_to_arxiv_orchestrates_all_steps(self) -> None:
        text = r"{\tt code} and \lesssim 100 pc with H~{\sc ii}"
        result = convert_to_arxiv(text)
        # Font commands converted, math wrapped, special chars handled
        assert r"$\tt{code}$" in result
        assert r"$\lesssim$" in result
        assert " " in result  # ~ replaced

    # ------------------------------------------------------------------
    # extract_abstract_from_tex (full pipeline)
    # ------------------------------------------------------------------
    def test_integration_synthetic(self, tmp_path: Path) -> None:
        tex = tmp_path / "test.tex"
        tex.write_text(
            r"""
\documentclass{article}
\newcommand{\mycmd}{expanded}
\newcommand{\mytt}{{\tt code}}
\begin{document}
\begin{abstract}
We use \mycmd{} and \mytt{} with \lesssim 100 pc. % a comment
\end{abstract}
\end{document}
""",
            encoding="utf-8",
        )
        result = extract_abstract_from_tex(str(tex))
        assert "expanded" in result
        assert r"$\tt{code}$" in result
        assert r"$\lesssim$" in result
        assert "comment" not in result

    def test_integration_sample7(self) -> None:
        sample = Path(__file__).parent / "example" / "sample7.tex"
        if not sample.exists():
            pytest.skip("sample7.tex not found")
        result = extract_abstract_from_tex(str(sample))
        # User-defined macros expanded
        assert "I_{\\rm CO}" in result       # \ICO expanded
        assert r"$\tt{raddest}$" in result    # \raddest expanded + font conversion
        assert r"$\lesssim$" in result       # Math command wrapped
        # \edit expanded via \newcommand{\edit}[1]{#1}
        assert "\\edit" not in result
        # Comments removed
        assert "We suggest" not in result
        # En-dash converted
        assert "\u2013" not in result
        # Citations left as-is
        assert "\\citet{Jing2024}" in result

    def test_no_abstract_returns_empty(self, tmp_path: Path) -> None:
        tex = tmp_path / "no_abstract.tex"
        tex.write_text(r"\documentclass{article}\begin{document}No abstract\end{document}", encoding="utf-8")
        result = extract_abstract_from_tex(str(tex))
        assert result == ""

    # ------------------------------------------------------------------
    # CLI
    # ------------------------------------------------------------------
    def test_cli_stdout(self, tmp_path: Path, capsys) -> None:
        tex = tmp_path / "test.tex"
        tex.write_text(
            r"""
\documentclass{article}
\begin{document}
\begin{abstract}
Hello World
\end{abstract}
\end{document}
""",
            encoding="utf-8",
        )
        main([str(tex)])
        captured = capsys.readouterr()
        assert "Hello World" in captured.out

    def test_cli_output_file(self, tmp_path: Path) -> None:
        tex = tmp_path / "test.tex"
        out = tmp_path / "abstract.txt"
        tex.write_text(
            r"""
\documentclass{article}
\begin{document}
\begin{abstract}
Hello World
\end{abstract}
\end{document}
""",
            encoding="utf-8",
        )
        main([str(tex), "-o", str(out)])
        result = out.read_text(encoding="utf-8")
        assert "Hello World" in result
