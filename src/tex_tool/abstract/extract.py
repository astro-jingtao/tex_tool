r"""Extract abstract from a .tex file in arXiv-compatible format.

Pipeline:
  1. Read the .tex file.
  2. Parse \newcommand / \renewcommand / \providecommand from the preamble.
  3. Extract the \begin{abstract}...\end{abstract} block.
  4. Strip LaTeX comments.
  5. Expand user-defined macros iteratively to a fixed point.
  6. Wrap standalone LaTeX math commands (outside $...$) in $...$.
  7. Convert font/style commands outside math mode to arXiv-compatible MathJax.
  8. Replace special Unicode characters.
  9. Collapse whitespace.
"""

import argparse
from pathlib import Path
import re
from typing import Optional

# ---------------------------------------------------------------------------
# Known LaTeX math commands — when encountered *outside* math mode they are
# wrapped in $...$ so the arXiv abstract renderer (MathJax) recognises them.
# ---------------------------------------------------------------------------
_MATH_COMMANDS: set = {
    # Greek
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Epsilon",
    "Zeta",
    "Eta",
    "Theta",
    "Iota",
    "Kappa",
    "Lambda",
    "Mu",
    "Nu",
    "Xi",
    "Pi",
    "Rho",
    "Sigma",
    "Tau",
    "Upsilon",
    "Phi",
    "Chi",
    "Psi",
    "Omega",
    "varepsilon",
    "vartheta",
    "varpi",
    "varrho",
    "varsigma",
    "varphi",
    # Relations
    "leq",
    "geq",
    "ll",
    "gg",
    "neq",
    "equiv",
    "approx",
    "sim",
    "simeq",
    "propto",
    "doteq",
    "prec",
    "succ",
    "preceq",
    "succeq",
    "lesssim",
    "gtrsim",
    "lessgtr",
    "gtrless",
    "subset",
    "supset",
    "subseteq",
    "supseteq",
    "in",
    "ni",
    "notin",
    "mid",
    "parallel",
    "perp",
    "cong",
    "asymp",
    "bowtie",
    "models",
    "dashv",
    "vdash",
    "smile",
    "frown",
    # Binary operators
    "pm",
    "mp",
    "times",
    "div",
    "cdot",
    "ast",
    "star",
    "circ",
    "bullet",
    "diamond",
    "oplus",
    "ominus",
    "otimes",
    "cup",
    "cap",
    "setminus",
    "wedge",
    "vee",
    "sqcup",
    "sqcap",
    "triangleleft",
    "triangleright",
    "bigcirc",
    "bigtriangleup",
    "bigtriangledown",
    "land",
    "lor",
    "lnot",
    "neg",
    # Arrows
    "rightarrow",
    "leftarrow",
    "Rightarrow",
    "Leftarrow",
    "longrightarrow",
    "longleftarrow",
    "Longrightarrow",
    "Longleftarrow",
    "to",
    "mapsto",
    "leftrightarrow",
    "Leftrightarrow",
    "uparrow",
    "downarrow",
    "Uparrow",
    "Downarrow",
    "nearrow",
    "searrow",
    "swarrow",
    "nwarrow",
    "rightleftharpoons",
    "leftharpoonup",
    "rightharpoonup",
    "hookrightarrow",
    "hookleftarrow",
    # Misc math symbols
    "infty",
    "partial",
    "nabla",
    "forall",
    "exists",
    "nexists",
    "emptyset",
    "varnothing",
    "aleph",
    "top",
    "bot",
    "angle",
    "triangle",
    "square",
    "cdots",
    "vdots",
    "ddots",
    "ldots",
    "sum",
    "prod",
    "int",
    "oint",
    "coprod",
    "bigcup",
    "bigcap",
    "Re",
    "Im",
    "ell",
    "hbar",
    "imath",
    "jmath",
    "prime",
    "backslash",
    "surd",
    "pound",
    "S",
    "P",
    # Functions
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "exp",
    "log",
    "ln",
    "lg",
    "det",
    "dim",
    "hom",
    "ker",
    "deg",
    "arg",
    "gcd",
    "lim",
    "max",
    "min",
    "sup",
    "inf",
    "Pr",
    "limsup",
    "liminf",
    "injlim",
    "projlim",
    # Accents
    "hat",
    "tilde",
    "bar",
    "vec",
    "dot",
    "ddot",
    "widehat",
    "widetilde",
    "check",
    "breve",
    "acute",
    "grave",
    # Delimiters
    "langle",
    "rangle",
    "lceil",
    "rceil",
    "lfloor",
    "rfloor",
    # Sizing / spacing
    "big",
    "Big",
    "bigg",
    "Bigg",
    "quad",
    "qquad",
    "!",
    ",",
    ":",
    ";",
    # Modifier commands (used inside math mode but sometimes appear bare)
    "text",
    "textrm",
    "textsf",
    "texttt",
    # Units and special
    "AA",
    "Angstrom",
    "micron",
    "degree",
    "dag",
    "ddag",
    "copyright",
    "pounds",
    "LaTeX",
    "TeX",
}

# Mapping: {<font-tag> -> <MathJax-command>}
_FONT_TAG_MAP: dict[str, str] = {
    "tt": "tt",
    "rm": "rm",
    "sc": "text",
    "bf": "mathbf",
    "it": "mathit",
    "sl": "text",
    "sf": "mathsf",
}

_FONT_CMD_MAP: dict[str, str] = {
    r"\textbf": "mathbf",
    r"\textit": "mathit",
    r"\textsf": "mathsf",
    r"\texttt": "tt",
}


# ---------------------------------------------------------------------------
# Helper: balanced-brace extraction
# ---------------------------------------------------------------------------
def extract_balanced_braces(s: str, start: int) -> tuple[str, int]:
    """Return *(content, end_pos)* for balanced ``{...}`` starting at *start*.

    The opening brace at *start* and its matching close are stripped;
    ``content`` is the text between them.  Nested braces and escaped
    ``\\{`` / ``\\}`` are handled correctly.

    Raises :exc:`ValueError` if braces are unbalanced or *start* does
    not point at ``{``.
    """
    if start >= len(s) or s[start] != "{":
        raise ValueError(f"No opening brace at position {start}")
    depth = 1
    i = start + 1
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            i += 2  # skip escaped character (e.g. \{, \}, \\, etc.)
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1 : i], i + 1
        i += 1
    raise ValueError(f"Unbalanced braces starting at position {start}")


def _extract_balanced_brackets(s: str, start: int) -> tuple[str, int]:
    """Like :func:`extract_balanced_braces` but for ``[...]``."""
    if start >= len(s) or s[start] != "[":
        raise ValueError(f"No opening bracket at position {start}")
    depth = 1
    i = start + 1
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            i += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return s[start + 1 : i], i + 1
        i += 1
    raise ValueError(f"Unbalanced brackets starting at position {start}")


# ---------------------------------------------------------------------------
# Step 1: extract abstract block
# ---------------------------------------------------------------------------
def find_abstract_block(content: str) -> Optional[str]:
    """Return the text between ``\\begin{abstract}`` and ``\\end{abstract}``.

    Returns *None* if no abstract block is found.
    """
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
    if m is None:
        return None
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# Step 2: strip LaTeX comments
# ---------------------------------------------------------------------------
def clean_latex_comments(text: str) -> str:
    r"""Remove everything from an unescaped ``%`` to end-of-line.

    ``\%`` is preserved as ``%``.
    """
    # (?<!\\) matches if there isn't a backslash before the %.
    # We need a negative lookbehind for an ODD number of backslashes,
    # but for practical purposes (?<!\\)% is good enough.
    result = []
    for line in text.splitlines():
        # Find first unescaped %
        cleaned = re.sub(r"(?<!\\)%.*$", "", line)
        # Restore \% to %
        cleaned = cleaned.replace(r"\%", "%")
        result.append(cleaned)
    return "\n".join(result)


# ---------------------------------------------------------------------------
# Step 3: parse \newcommand definitions from preamble
# ---------------------------------------------------------------------------
_NEWCMD_START_RE = re.compile(
    r"""
    \\(?P<type>new|renew|provide)command\*?   # \newcommand, \renewcommand, \providecommand
    \s*
    (?:
        \{(?P<braced_name>[^}]*)\}            # {\cmdname}
        |
        (?P<bare_name>\\[a-zA-Z@]+)           # \cmdname (bare)
    )
    \s*
    (?:\[(?P<num_args>\d+)\])?                # optional [N]
    \s*
    (?:\[(?P<default>[^\]]*)\])?              # optional [default]
    \s*
    \{                                         # opening brace of body
    """,
    re.VERBOSE,
)


def parse_newcommands(content: str) -> dict[str, dict]:
    """Extract ``\\newcommand`` (and ``\\renewcommand``, ``\\providecommand``)
    definitions from *content*.

    Only the preamble (before ``\\begin{document}``) is scanned so that
    example / verbatim blocks in the body are ignored.

    Returns a dict keyed by command name (with leading backslash)::

        {"\\foo": {"body": "bar", "num_args": 0, "has_optional": False, "default": ""}}
    """
    # Use line-anchored search so we don't match a commented-out
    # \begin{document} inside the preamble instructions.
    m_doc = re.search(r"^\s*\\begin\{document\}", content, re.MULTILINE)
    preamble = content[: m_doc.start()] if m_doc else content

    # Clean comments so commented-out definitions are ignored.
    preamble = clean_latex_comments(preamble)

    definitions: dict[str, dict] = {}

    for m in _NEWCMD_START_RE.finditer(preamble):
        # Command name
        if m.group("braced_name") is not None:
            name = m.group("braced_name")
        else:
            name = m.group("bare_name")
        # Ensure leading backslash
        if not name.startswith("\\"):
            name = "\\" + name

        num_args = int(m.group("num_args")) if m.group("num_args") else 0
        has_optional = m.group("default") is not None
        default = m.group("default") if has_optional else ""

        # The regex ended at the opening brace of the body.
        body_start = m.end() - 1  # position of '{'
        try:
            body, _ = extract_balanced_braces(preamble, body_start)
        except ValueError:
            continue

        definitions[name] = {
            "body": body,
            "num_args": num_args,
            "has_optional": has_optional,
            "default": default,
        }

    return definitions


# ---------------------------------------------------------------------------
# Step 4: expand macros
# ---------------------------------------------------------------------------
def _expand_single_arg_command(text: str, cmd_name: str, defn: dict) -> str:
    """Expand all occurrences of *cmd_name* (which takes arguments) in *text*."""
    cmd_len = len(cmd_name)
    result: list[str] = []
    i = 0

    while i < len(text):
        # Look for the command
        if text[i : i + cmd_len] == cmd_name:
            next_pos = i + cmd_len
            # Word-boundary check: prevent \bx matching \bxerr
            if next_pos < len(text) and text[next_pos].isalpha():
                result.append(text[i])
                i += 1
                continue

            # Skip whitespace between command name and arguments
            j = next_pos
            while j < len(text) and text[j] in " \t":
                j += 1

            saved_j = j
            args: list[str] = []

            # Optional argument?
            if defn["has_optional"]:
                if j < len(text) and text[j] == "[":
                    try:
                        opt_content, j = _extract_balanced_brackets(text, j)
                        args.append(opt_content)
                    except ValueError:
                        args.append(defn["default"])
                        j = saved_j
                else:
                    args.append(defn["default"])

            # Mandatory arguments
            all_ok = True
            for _ in range(len(args), defn["num_args"]):
                # Skip whitespace
                while j < len(text) and text[j] in " \t":
                    j += 1
                if j < len(text) and text[j] == "{":
                    try:
                        arg_content, j = extract_balanced_braces(text, j)
                        args.append(arg_content)
                    except ValueError:
                        all_ok = False
                        break
                else:
                    all_ok = False
                    break

            if all_ok and len(args) == defn["num_args"]:
                # Substitute #1 .. #N in body
                body = defn["body"]
                for arg_idx in range(defn["num_args"], 0, -1):
                    body = body.replace(f"#{arg_idx}", args[arg_idx - 1])
                result.append(body)
                i = j
                continue

            # Parse failed — not a valid usage; skip the backslash
            result.append(text[i])
            i += 1
            continue

        result.append(text[i])
        i += 1

    return "".join(result)


def expand_macros(text: str, definitions: dict[str, dict]) -> str:
    """Expand user-defined macros in *text* iteratively to a fixed point.

    Only commands present in *definitions* are expanded — unknown
    ``\\commands`` are never touched.
    """
    if not definitions:
        return text

    zero_arg = {k: v for k, v in definitions.items() if v["num_args"] == 0}
    arg_cmds = {k: v for k, v in definitions.items() if v["num_args"] > 0}

    zero_arg_sorted = sorted(zero_arg.items(), key=lambda x: -len(x[0]))

    prev = None
    while prev != text:
        prev = text

        # Expand zero-argument commands (longest-name first to avoid
        # \bx matching inside \bxerr).
        for name, defn in zero_arg_sorted:
            body = defn["body"]
            # Word-boundary: name must not be followed by a letter.
            pattern = re.compile(re.escape(name) + r"(?![a-zA-Z@])")
            text = pattern.sub(lambda _m: body, text)

        # Expand commands that take arguments.
        for name in sorted(arg_cmds, key=len, reverse=True):
            text = _expand_single_arg_command(text, name, arg_cmds[name])

    return text


# ---------------------------------------------------------------------------
# Step 5: math-region detection
# ---------------------------------------------------------------------------
def find_math_regions(text: str) -> list[tuple[int, int]]:
    """Return a sorted list of ``(start, end)`` index pairs for every
    ``$...$``, ``$$...$$``, ``\\(...\\)``, and ``\\[...\\]`` region.
    """
    regions: list[tuple[int, int]] = []

    # --- $$ ... $$ (display math) ---
    dd_positions: set = set()
    i = 0
    while True:
        pos = text.find("$$", i)
        if pos == -1:
            break
        end = text.find("$$", pos + 2)
        if end != -1:
            regions.append((pos, end + 2))
            dd_positions.update([pos, pos + 1, end, end + 1])
            i = end + 2
        else:
            i = pos + 2

    # --- \( ... \) and \[ ... \] ---
    for sd, ed in [(r"\(", r"\)"), (r"\[", r"\]")]:
        i = 0
        while True:
            s = text.find(sd, i)
            if s == -1:
                break
            e = text.find(ed, s + 2)
            if e == -1:
                break
            regions.append((s, e + 2))
            i = e + 2

    # --- $ ... $ (inline math, not part of $$) ---
    i = 0
    while i < len(text):
        if text[i] == "$" and i not in dd_positions:
            end = text.find("$", i + 1)
            while end != -1 and end in dd_positions:
                end = text.find("$", end + 1)
            if end != -1:
                regions.append((i, end + 1))
                i = end + 1
                continue
        i += 1

    return sorted(regions)


def _is_inside_math(pos: int, math_regions: list[tuple[int, int]]) -> bool:
    """Return *True* if *pos* falls inside any math region."""
    return any(start <= pos < end for start, end in math_regions)


# ---------------------------------------------------------------------------
# Step 6: wrap standalone math commands in $...$
# ---------------------------------------------------------------------------
def wrap_standalone_math_commands(text: str, math_regions: list[tuple[int, int]]) -> str:
    """Wrap known LaTeX math commands that appear **outside** math mode in
    ``$cmd$`` so the arXiv abstract renderer recognises them.
    """
    result: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            # Extract command name (alphabetic chars after backslash)
            j = i + 1
            while j < len(text) and text[j].isalpha():
                j += 1
            if j > i + 1:
                cmd_name = text[i + 1 : j]
                if cmd_name in _MATH_COMMANDS and not _is_inside_math(i, math_regions):
                    result.append("$" + text[i:j] + "$")
                    i = j
                    continue
        result.append(text[i])
        i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# Step 7: convert font / style commands outside math mode
# ---------------------------------------------------------------------------
def _replace_font_braced(
    text: str, tag: str, math_cmd: str, math_regions: list[tuple[int, int]]
) -> str:
    """Replace ``{\\tag ...}`` with ``$\\math_cmd{...}$`` (outside math)."""
    prefix = "{\\" + tag
    result: list[str] = []
    i = 0
    while i < len(text):
        pos = text.find(prefix, i)
        if pos == -1:
            result.append(text[i:])
            break

        result.append(text[i:pos])

        if _is_inside_math(pos, math_regions):
            result.append(text[pos])
            i = pos + 1
            continue

        # Extract content between the outer braces
        # For "{\tt raddest}", outer brace is at pos, content starts at "\tt"
        try:
            content, end_pos = extract_balanced_braces(text, pos)
            # content = "\tt raddest" (or similar — varies by tag)
            # Strip the leading "\tag" and any whitespace to get the payload.
            tag_prefix = "\\" + tag
            inner = content[len(tag_prefix) :].lstrip()
            replacement = "$\\" + math_cmd + "{" + inner + "}$"
            result.append(replacement)
            i = end_pos
        except ValueError:
            result.append(text[pos])
            i = pos + 1

    return "".join(result)


def _replace_font_cmd(
    text: str, cmd: str, math_cmd: str, math_regions: list[tuple[int, int]]
) -> str:
    """Replace ``\\cmd{...}`` with ``$\\math_cmd{...}$`` (outside math)."""
    prefix = cmd + "{"
    result: list[str] = []
    i = 0
    while i < len(text):
        pos = text.find(prefix, i)
        if pos == -1:
            result.append(text[i:])
            break

        result.append(text[i:pos])

        if _is_inside_math(pos, math_regions):
            result.append(text[pos])
            i = pos + 1
            continue

        brace_start = pos + len(cmd)
        try:
            content, end_pos = extract_balanced_braces(text, brace_start)
            replacement = "$\\" + math_cmd + "{" + content + "}$"
            result.append(replacement)
            i = end_pos
        except ValueError:
            result.append(text[pos])
            i = pos + 1

    return "".join(result)


def _replace_textcolor(text: str, math_regions: list[tuple[int, int]]) -> str:
    """Replace ``\\textcolor{color}{content}`` with *content* (outside math)."""
    prefix = "\\textcolor{"
    result: list[str] = []
    i = 0
    while i < len(text):
        pos = text.find(prefix, i)
        if pos == -1:
            result.append(text[i:])
            break

        result.append(text[i:pos])

        if _is_inside_math(pos, math_regions):
            result.append(text[pos])
            i = pos + 1
            continue

        color_brace = pos + len(prefix) - 1
        try:
            _color, after_color = extract_balanced_braces(text, color_brace)
            if after_color < len(text) and text[after_color] == "{":
                content, end_pos = extract_balanced_braces(text, after_color)
                result.append(content)
                i = end_pos
            else:
                result.append(text[pos])
                i = pos + 1
        except ValueError:
            result.append(text[pos])
            i = pos + 1

    return "".join(result)


def convert_font_commands(text: str, math_regions: list[tuple[int, int]]) -> str:
    """Convert LaTeX font/style commands outside math mode to arXiv-compatible
    MathJax equivalents."""
    # {\tag ...} patterns
    for tag, math_cmd in _FONT_TAG_MAP.items():
        text = _replace_font_braced(text, tag, math_cmd, math_regions)

    # \cmd{...} patterns
    for cmd, math_cmd in _FONT_CMD_MAP.items():
        text = _replace_font_cmd(text, cmd, math_cmd, math_regions)

    # \textcolor{color}{content}
    text = _replace_textcolor(text, math_regions)

    return text


# ---------------------------------------------------------------------------
# Step 8: special character conversion
# ---------------------------------------------------------------------------
def convert_special_chars(text: str) -> str:
    """Replace Unicode characters and LaTeX ties with arXiv-compatible text."""
    # Non-breaking space / tie
    text = text.replace("~", " ")
    # En-dash and em-dash
    text = text.replace("\u2013", "-")  # –
    text = text.replace("\u2014", "--")  # —
    # Smart quotes: `` ... '' -> " ... "
    text = text.replace("``", '"').replace("''", '"')
    # Single smart quotes: ` ... ' -> ' ... '
    # (rare in LaTeX; trailing single quote handled by the '' rule above)
    # Curly quotes (Unicode)
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # " "
    text = text.replace("\u2018", "'").replace("\u2019", "'")  # ' '
    return text


# ---------------------------------------------------------------------------
# Step 9: orchestrate conversion
# ---------------------------------------------------------------------------
def convert_to_arxiv(text: str) -> str:
    """Run the full arXiv-compatibility conversion pipeline on *text*."""
    # 1. Convert font/style commands outside math → MathJax
    math_regions = find_math_regions(text)
    text = convert_font_commands(text, math_regions)

    # 2. Recompute math regions, then wrap standalone math commands
    math_regions = find_math_regions(text)
    text = wrap_standalone_math_commands(text, math_regions)

    # 3. Replace special characters
    text = convert_special_chars(text)

    # 4. Collapse multiple spaces (but not newlines) and strip
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------
def extract_abstract_from_tex(tex_path: str) -> str:
    """Extract and convert the abstract from a ``.tex`` file.

    Returns the arXiv-compatible abstract text.
    """
    content = Path(tex_path).read_text(encoding="utf-8")

    # Parse user-defined macros
    definitions = parse_newcommands(content)

    # Extract abstract block
    raw_abstract = find_abstract_block(content)
    if raw_abstract is None:
        return ""

    # Clean comments
    abstract = clean_latex_comments(raw_abstract)

    # Expand user macros
    abstract = expand_macros(abstract, definitions)

    # Convert to arXiv-compatible format
    abstract = convert_to_arxiv(abstract)

    return abstract


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
COMMAND = "abstract"
COMMAND_HELP = "Extract abstract from a .tex file in arXiv-compatible format"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(COMMAND, help=COMMAND_HELP)
    parser.add_argument(
        "input",
        help="Path to the .tex file",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: print to stdout)",
    )
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    result = extract_abstract_from_tex(args.input)
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Abstract written to: {args.output}")
    else:
        print(result)
