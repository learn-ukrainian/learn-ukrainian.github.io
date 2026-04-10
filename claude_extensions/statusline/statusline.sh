#!/usr/bin/env bash
# Claude Code status line — learn-ukrainian project.
#
# Reads Claude Code status JSON from stdin and renders:
#   [MODEL] cwd-basename [wt:worktree-name] (branch*)
#
# Where:
#   - MODEL = .model.display_name (omitted if missing)
#   - cwd-basename = basename of .workspace.current_dir (or pwd fallback)
#   - [wt:...] = present ONLY when .workspace.git_worktree is set.
#       Uses basename defensively because Claude Code 2.1.98's format
#       for this field is not officially documented — could be a full
#       path or a short name. basename handles both.
#   - (branch*) = current git branch + dirty marker if working tree has
#       uncommitted changes.
#
# Graceful degradation:
#   - If jq is not installed, script exits silently (empty status line).
#   - If any .git rev-parse step fails, branch segment is omitted.
#   - If .workspace.git_worktree is absent (older Claude Code), that
#     segment is omitted.
#
# See issue #1181. Design provenance: Codex (bridge msg #28524).

set -u

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

input=$(cat)

json_get() {
  local filter=$1
  printf '%s' "$input" | jq -r "$filter" 2>/dev/null || true
}

model=$(json_get '.model.display_name // empty')
cwd=$(json_get '.workspace.current_dir // .cwd // empty')
if [ -z "$cwd" ]; then
  cwd=$(pwd)
fi
cwd_name=$(basename "$cwd")

worktree=$(json_get '.workspace.git_worktree // empty')
wt_short=""
if [ -n "$worktree" ]; then
  wt_short=$(basename "$worktree")
fi

branch=""
dirty=""
if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(
    git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null ||
    git -C "$cwd" rev-parse --short HEAD 2>/dev/null ||
    true
  )
  if [ -n "$(git -C "$cwd" status --porcelain 2>/dev/null)" ]; then
    dirty="*"
  fi
fi

parts=()
if [ -n "$model" ]; then
  parts+=("[$model]")
fi
parts+=("$cwd_name")
if [ -n "$wt_short" ]; then
  parts+=("[wt:$wt_short]")
fi
if [ -n "$branch" ]; then
  parts+=("($branch$dirty)")
fi

printf '%s\n' "${parts[*]}"
