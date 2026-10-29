# ub-mode

`ub-mode` is an agent skill that enforces disciplined software engineering principles when writing or changing code. It is loosely based on portions of [@poteto](https://github.com/poteto)'s rules (`poteto-mode` / `pstack`), reduced and paired with deterministic quality-gate tools:

1. **First Make it Work** — Laziness Protocol, Foundational Thinking, TDD, Redesign From First Principles, Attack the Premise, Subtract Before You Add, Outcome-Oriented Execution, Build the Lever, and Architecture (Model the Domain, Boundary Discipline, Type System Discipline, Make Operations Idempotent, Separate Before Serializing Shared State).
2. **Then Make it Right** — Fix Root Causes, Sequence Work into Verifiable Units, Test Behavior (Not Implementation), [Crapper](https://github.com/unclebob/crapper) (`CRAP < 10`), [Dryer](https://github.com/unclebob/dryer) (duplication `< 0.8`), [Mutator](https://github.com/unclebob/mutator) (cover the uncovered, kill the survivors, delete dead code), and Refactoring.
3. **Practice** — Keep a Log, Guard the Context Window, Worktree Cleanup, and Commit and Push in small ordered commits.

## Bundled Tools

`tools/` holds vendored copies (via `git subtree`) of the quality-gate tools, with Windows fixes:

- `tools/crapper` from [unclebob/crapper](https://github.com/unclebob/crapper) — cyclomatic complexity, coverage, and CRAP score per function (`< 10`).
- `tools/dryer` from [unclebob/dryer](https://github.com/unclebob/dryer) — structural duplication (`>= 0.8` similarity).
- `tools/mutator` from [unclebob/mutator](https://github.com/unclebob/mutator) — mutation testing.

## Requirements

- git
- Python 3.11+
- Windows only: Developer Mode on (mutator creates symlinks)

## Installation

Linux / macOS:

```bash
git clone <your-gitlab-url>/ub-mode.git /tmp/ub-mode
bash /tmp/ub-mode/install.sh <your-gitlab-url>/ub-mode.git
```

Windows (PowerShell):

```powershell
git clone <your-gitlab-url>/ub-mode.git $env:TEMP\ub-mode
powershell -ExecutionPolicy Bypass -File $env:TEMP\ub-mode\install.ps1 <your-gitlab-url>/ub-mode.git
```

The installer clones into `~/.claude/skills/ub-mode`, creates `.venv` there, and installs the three tools.
Set `UB_MODE_DIR` to install somewhere else. Run the installer again to update.

## Usage

In a Python project with a `.venv` that has `pytest` and `coverage`:

```
/ub-mode <your request>
```

## Updating the Bundled Tools

```bash
git subtree pull --prefix tools/crapper https://github.com/unclebob/crapper.git master --squash
git subtree pull --prefix tools/dryer https://github.com/unclebob/dryer.git master --squash
git subtree pull --prefix tools/mutator https://github.com/unclebob/mutator.git main --squash
```
