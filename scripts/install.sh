#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${PDFTRANSLATE_REPO_URL:-https://github.com/Hujianboo/pdfTranslate.git}"
INSTALL_DIR="${PDFTRANSLATE_INSTALL_DIR:-$HOME/pdfTranslate}"
MARKETPLACE_NAME="pdftranslate-local"

info() {
  printf '\033[1;34m==>\033[0m %s\n' "$1" >&2
}

warn() {
  printf '\033[1;33mwarning:\033[0m %s\n' "$1" >&2
}

fail() {
  printf '\033[1;31merror:\033[0m %s\n' "$1" >&2
  exit 1
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

repo_root_from_script() {
  local source_path="${BASH_SOURCE[0]:-}"
  if [[ -n "$source_path" && -f "$source_path" ]]; then
    local script_dir
    script_dir="$(cd "$(dirname "$source_path")" && pwd)"
    local candidate
    candidate="$(cd "$script_dir/.." && pwd)"
    if [[ -f "$candidate/pyproject.toml" && -d "$candidate/plugins/pdftranslate-codex" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi
  return 1
}

resolve_repo_root() {
  if [[ -f "pyproject.toml" && -d "plugins/pdftranslate-codex" ]]; then
    pwd
    return 0
  fi

  if repo_root_from_script; then
    return 0
  fi

  has_command git || fail "git is required to clone pdfTranslate"
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Using existing repository: $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only >&2 || warn "git pull failed; continuing with existing checkout"
  else
    info "Cloning pdfTranslate into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR" >&2
  fi
  printf '%s\n' "$INSTALL_DIR"
}

ensure_uv() {
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if has_command uv; then
    info "uv found: $(uv --version)"
    return 0
  fi

  has_command curl || fail "curl is required to install uv automatically"
  info "Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  has_command uv || fail "uv installation finished, but uv is still not on PATH"
}

ensure_codex() {
  if has_command codex; then
    info "Codex CLI found: $(codex --version)"
    return 0
  fi

  if has_command npm; then
    info "Installing Codex CLI with npm"
    if npm install -g @openai/codex; then
      return 0
    fi
    warn "Codex CLI npm install failed"
  else
    warn "npm not found, so Codex CLI was not installed automatically"
  fi

  warn "Install Codex CLI manually, then run: codex login"
}

install_or_update_codex_plugin() {
  local repo_root="$1"
  local plugin_cache="$HOME/.codex/plugins/cache/$MARKETPLACE_NAME"

  info "Registering or refreshing pdfTranslate marketplace with Codex"
  rm -rf "$plugin_cache"
  codex plugin marketplace add "$repo_root" || warn "marketplace add failed; it may already be installed"
}

main() {
  local repo_root
  repo_root="$(resolve_repo_root)"
  cd "$repo_root"

  ensure_uv
  info "Installing Python dependencies"
  uv sync

  ensure_codex
  if has_command codex; then
    install_or_update_codex_plugin "$repo_root"
  fi

  cat <<EOF

pdfTranslate is ready.

Next steps:
  1. If Codex is not logged in, run:
       codex login

  2. Restart Codex or reopen this workspace, then enable:
       pdfTranslate Codex

  3. Translate a PDF:
       cd "$repo_root"
       uv run python plugins/pdftranslate-codex/scripts/translate_pdf_with_codex.py ./paper.pdf --output-dir ./translated/pdf

EOF
}

main "$@"
