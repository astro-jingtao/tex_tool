<!-- Deployment guide for the skills shipped inside the tex_tool package.
     Written to stand alone: the reader is assumed to have no skill
     tooling beyond this file. -->

# Deploying the Skills Shipped in This Package

The tex_tool package ships Claude Agent Skills as package data under its `skills/` directory. This guide is written for the agent (or person) deploying them on a machine that carries no dedicated skill-deployment tooling — everything needed is in this file.

Where the skills live on this machine:

```bash
tex-tool skills-path
```

prints the skills directory (and points at this guide); `python -m tex_tool.skills` prints the same. In a repository checkout the tree sits inside the package at `src/tex_tool/skills/`. Below, `<skills-dir>` stands for that location.

## What a skill entry looks like

Each skill occupies two layers:

```text
<skills-dir>/<name>/       container
├── skill/                 the skill proper — SKILL.md plus supporting files
└── meta.yaml              external-dependency metadata — read, never deployed
```

Only `<name>/skill/` is deployed. `meta.yaml` stays behind: it declares what the skill expects from its environment, and you read it before linking (next section).

The package ships one skill: `tex-tool` (drive the `tex-tool` CLI).

## Before linking: install the package and read meta.yaml

The skill drives the `tex-tool` console script, so install this package first — from a checkout at the repository root:

```bash
pip install -e .
```

or without a checkout:

```bash
pip install git+https://github.com/astro-jingtao/tex_tool.git
```

Then read `<skills-dir>/<name>/meta.yaml` and settle its entries on this machine:

| field | meaning | what you do before deploying |
| ----- | ------- | ---------------------------- |
| `depends-on` | other skills this one hard-requires to function | deploy them together — the same link procedure for each |
| `requires` | environment requirements | per entry: verify on this machine now — run the entry's `check:` command when present; otherwise by its `kind` (a command on PATH, a python version spec, an importable package, an OS); a `platform:` naming another OS means the entry does not exist here |
| `claude-md` | content the environment's CLAUDE.md should carry | land it in the CLAUDE.md at its `scope` — global → the user's `~/.claude/CLAUDE.md`, project → the target project's `CLAUDE.md`. Check for equivalent existing content first; insert only what is missing, wrapped in the marker pair below |
| `integrates-with`, `notes` | informational linkage and operator notes | read; no action |

An unsatisfied `depends-on` or `requires` entry is a report to the user — the user fixes the gap or consciously continues; never a silent skip. An `install:` command on a missing requirement runs only after the user confirms.

claude-md marker pair — wrap inserted content so future readers can recognize machine-landed blocks:

```markdown
<!-- agent-skill:<skill>/<id> -->
…content…
<!-- /agent-skill:<skill>/<id> -->
```

## Deployment is a directory link

Make a skill visible to Claude Code by linking its `skill/` directory into a skills directory:

| target | link path | points at |
| ------ | --------- | --------- |
| user level (every project) | `~/.claude/skills/<name>` | `<skills-dir>/<name>/skill` |
| project level (one project) | `<project>/.claude/skills/<name>` | same target |

Prefer a link over a copy — a link reflects the installed package as it updates; a copy drifts the moment either side changes. When a link is impossible (privilege, filesystem), copy the directory instead and note that package updates will not reach the copy.

Commands — replace `<skills-dir>` with the `tex-tool skills-path` output:

Linux / macOS:

```bash
ln -s <skills-dir>/<name>/skill ~/.claude/skills/<name>
```

Windows (PowerShell):

```powershell
New-Item -ItemType SymbolicLink -Path "$HOME\.claude\skills\<name>" -Target "<skills-dir>\<name>\skill"
```

Windows requires Developer Mode or the "Create symbolic links" account right to create a symlink; a failure mentioning privilege or WinError 1314 means neither is present — enable one, or fall back to a copy:

```powershell
Copy-Item -Recurse <skills-dir>\<name>\skill "$HOME\.claude\skills\<name>"
```

Create a directory symlink, never a Windows junction: recursive removers (`git worktree remove`, `git clean`) walk through a junction into its target and can delete the source content, while a symlink is removed as the link itself.

## Safety rules

- Show the plan first — which skills, which links, which findings — before creating anything.
- A real directory or file already sitting at a link destination is a conflict: report it, never delete it. The most you may do, with the user's knowledge, is rename it aside (`<name>.bak.<timestamp>`).
- The procedure is idempotent — re-running it leaves an existing correct link alone.

## After linking

- Verify each deployment: `<skills-dir>/<name>/SKILL.md` is reachable through the link, and the frontmatter `name:` equals `<name>`.
- To remove a deployment, remove the link itself — on Windows, confirm first that it is a symlink rather than a junction: `Get-Item <path> | Select-Object LinkType` should show `SymbolicLink`.
