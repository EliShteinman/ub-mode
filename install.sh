#!/usr/bin/env bash
# Usage: ./install.sh <git-url-of-ub-mode>
#        ./install.sh                      (rerun: updates an existing install)
# Env:   UB_MODE_DIR  install location, default ~/.claude/skills/ub-mode
set -euo pipefail

REPO_URL="${1:-}"
SKILL_DIR="${UB_MODE_DIR:-$HOME/.claude/skills/ub-mode}"
TOOLS=(crapper dryer mutator)

fail() { echo "ERROR: $*" >&2; exit 1; }
step() { echo "==> $*"; }

require_git() {
  command -v git >/dev/null 2>&1 || fail "git is not installed."
}

find_python() {
  local candidate
  for candidate in python3.13 python3.12 python3.11 python3.14 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
      echo "$candidate"
      return
    fi
  done
  fail "Python 3.11 or newer is required."
}

default_repo_url() {
  local here
  here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  git -C "$here" remote get-url origin 2>/dev/null || true
}

sync_repo() {
  if [ -d "$SKILL_DIR/.git" ]; then
    step "Updating $SKILL_DIR"
    git -C "$SKILL_DIR" pull --ff-only
    return
  fi
  [ -n "$REPO_URL" ] || REPO_URL="$(default_repo_url)"
  [ -n "$REPO_URL" ] || fail "Pass the GitLab URL: ./install.sh <git-url>"
  [ ! -e "$SKILL_DIR" ] || fail "$SKILL_DIR exists and is not a git checkout. Move it away first."
  step "Cloning $REPO_URL into $SKILL_DIR"
  mkdir -p "$(dirname -- "$SKILL_DIR")"
  git clone "$REPO_URL" "$SKILL_DIR"
}

install_tools() {
  local python="$1" venv="$SKILL_DIR/.venv" tool
  step "Creating virtualenv with $("$python" --version)"
  [ -x "$venv/bin/python" ] || "$python" -m venv "$venv"
  "$venv/bin/python" -m pip install --quiet --upgrade pip
  local editable=()
  for tool in "${TOOLS[@]}"; do editable+=(-e "$SKILL_DIR/tools/$tool"); done
  step "Installing ${TOOLS[*]}"
  "$venv/bin/python" -m pip install --quiet "${editable[@]}"
}

verify_tools() {
  local tool
  for tool in "${TOOLS[@]}"; do
    "$SKILL_DIR/.venv/bin/$tool" --help >/dev/null || fail "$tool does not start."
  done
  step "Verified: ${TOOLS[*]}"
}

main() {
  require_git
  local python
  python="$(find_python)"
  sync_repo
  install_tools "$python"
  verify_tools
  echo
  echo "ub-mode is installed in $SKILL_DIR"
  echo "Open Claude Code in a Python project and run: /ub-mode <your request>"
}

main
