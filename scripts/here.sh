#!/usr/bin/env bash
# Human-facing helper for the bare-primary layout.
#
# The repo root is often a *bare* git dir (no work tree). That makes plain
# `git status` fail and is confusing. Day-to-day coding happens in a linked
# worktree; services still start from the bare root.
#
# Usage (from repo root OR any subdir):
#   ./scripts/here.sh              # where am I / where should I work
#   ./scripts/here.sh ensure       # create/fix the human worktree
#   ./scripts/here.sh go           # print: cd <human-worktree>  (eval-friendly)
#   eval "$(./scripts/here.sh env)"  # export HERE / HERE_GIT for shell
#   ./scripts/here.sh status       # git status in the human worktree
#   ./scripts/here.sh pull         # fetch origin/main → update main + human wt
#   ./scripts/here.sh restart-api  # pull tip + ./services.sh restart api
#   ./scripts/here.sh fix-worktrees  # clear core.bare=true leak on linked wts
#   ./scripts/here.sh list         # git worktree list
#
# One-liner for a new shell:
#   cd "$(./scripts/here.sh path)"
#
# GitHub CI is unaffected — runners always use a normal non-bare checkout.

set -euo pipefail

# --- resolve bare (or normal) project root ---------------------------------

_find_project_root() {
  local dir
  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  # Prefer the tree that holds services.sh + .git (bare primary or checkout).
  if [[ -f "$dir/services.sh" && ( -d "$dir/.git" || -f "$dir/HEAD" ) ]]; then
    printf '%s\n' "$dir"
    return 0
  fi
  # Walk up from cwd
  dir="$(pwd)"
  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/services.sh" && ( -d "$dir/.git" || -f "$dir/HEAD" ) ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

PROJECT_ROOT="$(_find_project_root)" || {
  echo "error: cannot find project root (services.sh + .git)" >&2
  exit 1
}

# Bare primary stores objects under .git/; some bare layouts use root as git-dir.
if [[ -d "$PROJECT_ROOT/.git" ]]; then
  GIT_DIR_ABS="$PROJECT_ROOT/.git"
else
  GIT_DIR_ABS="$PROJECT_ROOT"
fi

HUMAN_REL=".worktrees/main"
HUMAN_WT="$PROJECT_ROOT/$HUMAN_REL"
HUMAN_BRANCH="main"

# Never inherit a poisoned GIT_DIR from the bare parent shell.
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR 2>/dev/null || true

git_bare() {
  git --git-dir="$GIT_DIR_ABS" "$@"
}

git_human() {
  # Prefer plain git inside the worktree once fixed; fall back to explicit paths.
  if [[ -d "$HUMAN_WT" ]] && (
    cd "$HUMAN_WT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1
  ); then
    (cd "$HUMAN_WT" && git "$@")
  else
    local admin="$GIT_DIR_ABS/worktrees/main"
    if [[ ! -d "$admin" ]]; then
      echo "error: human worktree admin missing — run: $0 ensure" >&2
      return 1
    fi
    git --git-dir="$admin" --work-tree="$HUMAN_WT" "$@"
  fi
}

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
red() { printf '\033[0;31m%s\033[0m\n' "$*"; }

# --- heal core.bare leak on linked worktrees --------------------------------
#
# IMPORTANT: never run `git --git-dir=.git/worktrees/X config --local …` —
# without a proper worktree context that writes into the *common* config and
# can flip primary core.bare=false. Use config.worktree (worktreeConfig) or
# --file on the worktree admin path instead.

fix_worktree_bare_flags() {
  local wt_admin name cfg bare fixed=0
  # Primary stays bare.
  git_bare config core.bare true
  shopt -s nullglob
  for wt_admin in "$GIT_DIR_ABS"/worktrees/*/; do
    name="$(basename "${wt_admin%/}")"
    cfg="${wt_admin}config.worktree"
    bare="$(git config --file="$cfg" --get core.bare 2>/dev/null || true)"
    # Also treat missing/true as needing false (linked worktrees are never bare).
    if [[ "$bare" != "false" ]]; then
      git config --file="$cfg" core.bare false
      yellow "fixed config.worktree core.bare=false: $name"
      fixed=$((fixed + 1))
    fi
  done
  shopt -u nullglob
  # Ensure extensions.worktreeConfig so config.worktree is honored.
  git_bare config extensions.worktreeConfig true
  if [[ $fixed -eq 0 ]]; then
    green "worktree core.bare flags ok (primary bare=true)"
  else
    green "fixed $fixed worktree(s); primary bare=true"
  fi
}

# --- ensure human worktree --------------------------------------------------

ensure_human() {
  git_bare fetch origin main --quiet 2>/dev/null || git_bare fetch origin main

  # Primary is intentionally bare (agent/services root). Never leave it non-bare
  # by accident — that makes "where do I work?" ambiguous again.
  git_bare config core.bare true

  # Keep bare main tip = origin/main (services.sh release uses HEAD/main).
  if git_bare show-ref --verify --quiet refs/heads/main; then
    git_bare update-ref refs/heads/main refs/remotes/origin/main
  else
    git_bare branch main origin/main
  fi

  if [[ ! -d "$HUMAN_WT" ]]; then
    bold "creating human worktree at $HUMAN_REL (branch $HUMAN_BRANCH)…"
    # If main is already checked out elsewhere, force a new linked worktree
    # with --force only when git complains? Prefer explicit path.
    if ! git_bare worktree add "$HUMAN_WT" "$HUMAN_BRANCH" 2>/tmp/here-wt-add.err; then
      # Re-try after prunning stale admin; still fail loudly.
      cat /tmp/here-wt-add.err >&2 || true
      if grep -qi 'already used by worktree' /tmp/here-wt-add.err 2>/dev/null; then
        yellow "branch $HUMAN_BRANCH already checked out — adding with force unlock…"
        git_bare worktree add --force "$HUMAN_WT" "$HUMAN_BRANCH"
      else
        return 1
      fi
    fi
  fi

  fix_worktree_bare_flags

  # Align human worktree to main tip if clean.
  if git_human rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local branch dirty
    branch="$(git_human rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    dirty="$(git_human status --porcelain 2>/dev/null || true)"
    if [[ "$branch" == "main" && -z "$dirty" ]]; then
      git_human merge --ff-only origin/main >/dev/null 2>&1 \
        || git_human reset --hard origin/main >/dev/null
    elif [[ "$branch" != "main" ]]; then
      yellow "human worktree is on branch '$branch' (left as-is)"
    elif [[ -n "$dirty" ]]; then
      yellow "human worktree has local changes (not fast-forwarding)"
    fi
  fi

  green "human worktree ready: $HUMAN_WT"
}

_is_primary_bare() {
  # Prefer core.bare (authoritative for this layout). Fall back to rev-parse.
  local bare
  bare="$(git_bare config --get core.bare 2>/dev/null || true)"
  if [[ "$bare" == "true" ]]; then
    return 0
  fi
  if [[ "$bare" == "false" ]]; then
    return 1
  fi
  git_bare rev-parse --is-bare-repository 2>/dev/null | grep -qx true
}

cmd_where() {
  local bare_flag inside cwd
  if _is_primary_bare; then
    bare_flag="true (services root — not a coding checkout)"
  else
    bare_flag="false"
  fi
  cwd="$(pwd)"

  bold "Layout"
  echo "  project root (services):  $PROJECT_ROOT"
  echo "  git bare:                 $bare_flag"
  echo "  human worktree:           $HUMAN_WT"
  echo "  you are in:               $cwd"
  echo

  if [[ "$cwd" == "$HUMAN_WT" || "$cwd" == "$HUMAN_WT"/* ]]; then
    green "✓ You are in the human worktree — git status works here."
  elif [[ "$cwd" == "$PROJECT_ROOT" ]] && _is_primary_bare; then
    yellow "✗ Bare primary — do NOT code here. Use the human worktree:"
    echo "    cd \$($0 path)"
    echo "    # or:  cd $HUMAN_WT"
  elif [[ "$cwd" == "$PROJECT_ROOT"/* && "$cwd" != "$PROJECT_ROOT/.worktrees"/* ]]; then
    if _is_primary_bare; then
      yellow "You are under the bare primary tree. Prefer the human worktree for git:"
      echo "    cd \$($0 path)"
    fi
  fi

  echo
  bold "Commands"
  echo "  cd \$(./scripts/here.sh path)     # go to human worktree"
  echo "  ./scripts/here.sh status          # git status there"
  echo "  ./scripts/here.sh pull            # update main + worktree"
  echo "  ./scripts/here.sh restart-api     # release from main tip + restart"
  echo
  bold "GitHub CI"
  echo "  Unrelated to bare primary — Actions always checks out a normal clone."
  echo

  if [[ -d "$HUMAN_WT" ]]; then
    inside="$(cd "$HUMAN_WT" && git rev-parse --is-inside-work-tree 2>/dev/null || echo false)"
    if [[ "$inside" != "true" ]]; then
      yellow "human worktree git discovery broken — run: ./scripts/here.sh fix-worktrees && ./scripts/here.sh ensure"
    else
      echo -n "  human HEAD: "
      git_human log -1 --oneline 2>/dev/null || true
      git_human status --short --branch 2>/dev/null | head -5 | sed 's/^/  /'
    fi
  else
    yellow "human worktree missing — run: ./scripts/here.sh ensure"
  fi
}

cmd_path() {
  ensure_human >/dev/null
  printf '%s\n' "$HUMAN_WT"
}

cmd_go() {
  ensure_human >/dev/null
  # Safe for: eval "$(./scripts/here.sh go)"
  printf 'cd %q\n' "$HUMAN_WT"
}

cmd_env() {
  ensure_human >/dev/null
  printf 'export HERE=%q\n' "$HUMAN_WT"
  printf 'export HERE_ROOT=%q\n' "$PROJECT_ROOT"
  printf 'export HERE_GIT_DIR=%q\n' "$GIT_DIR_ABS"
  printf 'cd %q\n' "$HUMAN_WT"
}

cmd_status() {
  ensure_human
  bold "git status ($HUMAN_REL)"
  git_human status --short --branch
}

cmd_pull() {
  ensure_human
  bold "fetch + update main tip + human worktree"
  git_bare fetch origin main
  git_bare update-ref refs/heads/main refs/remotes/origin/main
  local dirty
  dirty="$(git_human status --porcelain 2>/dev/null || true)"
  if [[ -n "$dirty" ]]; then
    yellow "human worktree dirty — fetch done; not resetting. Status:"
    git_human status --short --branch
    return 0
  fi
  git_human checkout main >/dev/null 2>&1 || true
  git_human merge --ff-only origin/main
  green "main @ $(git_human rev-parse --short HEAD) $(git_human log -1 --pretty=%s)"
}

cmd_restart_api() {
  cmd_pull
  bold "restarting Monitor API from main tip (release snapshot)…"
  (
    cd "$PROJECT_ROOT"
    ./services.sh restart api
  )
  sleep 2
  if curl -sf --max-time 3 "http://127.0.0.1:8765/api/health" >/dev/null; then
    green "API health ok"
    local routes
    routes="$(curl -sf --max-time 3 http://127.0.0.1:8765/openapi.json \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(p for p in sorted(d.get('paths',{})) if 'comms/v1' in p or 'ops/v1/retention' in p))" 2>/dev/null || true)"
    if [[ -n "$routes" ]]; then
      echo "  routes: $routes"
    fi
  else
    yellow "API health not ready yet — check logs/api.log"
  fi
}

cmd_list() {
  git_bare worktree list
}

cmd_help() {
  sed -n '2,28p' "$0" | sed 's/^# \?//'
}

main() {
  local cmd="${1:-where}"
  shift || true
  case "$cmd" in
    where|info|"") cmd_where ;;
    ensure|init) ensure_human ;;
    path|pwd) cmd_path ;;
    go|cd) cmd_go ;;
    env) cmd_env ;;
    status|st) cmd_status ;;
    pull|sync) cmd_pull ;;
    restart-api|api) cmd_restart_api ;;
    fix-worktrees|fix) fix_worktree_bare_flags ;;
    list|ls) cmd_list ;;
    help|-h|--help) cmd_help ;;
    *)
      red "unknown command: $cmd"
      cmd_help
      exit 2
      ;;
  esac
}

main "$@"
