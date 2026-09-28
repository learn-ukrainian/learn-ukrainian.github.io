#!/usr/bin/env bash
# Project-interpreter resolution for shell callers (#9118).
#
# Mirrors scripts/common/repo_root.py `main_checkout_root` + `project_interpreter`
# without asking git, so no environment variable and no worktree-controlled
# `commondir` file can redirect the lookup to a planted interpreter:
#   - a linked worktree is accepted only when its `.git` gitfile says
#     `gitdir: <primary>/.git/worktrees/<name>` and `<primary>/.git` is a real
#     directory (not a symlink, no symlinked `worktrees/<name>`); `commondir` is
#     never read;
#   - the primary checkout's `.venv/bin/python` wins, even when the worktree
#     has its own `.venv`;
#   - the checkout's own `.venv` is used only when the checkout IS the primary
#     (a `.git` directory, or no `.git` at all as in a release snapshot);
#   - anything else (unrecognised gitfile, symlinked `.git`) is untrusted.
#
# project_interpreter_resolve <checkout-root>
#   stdout: absolute interpreter path (exit 0)
#   stderr: "Error: project interpreter not found: <paths tried>" (exit 1)
#
# Load-bearing tests: tests/test_deploy_extensions.py (real temporary repos).

# Collapse "." and ".." segments of an absolute path without following
# symlinks (a symlinked .git must stay visible to the checks below).
_project_interpreter_normalize() {
    local part
    local -a parts out=()
    IFS=/ read -r -a parts <<< "$1"
    for part in ${parts[@]+"${parts[@]}"}; do
        case "$part" in
            ''|.) ;;
            ..) [ "${#out[@]}" -gt 0 ] && unset "out[$((${#out[@]} - 1))]" ;;
            *) out+=("$part") ;;
        esac
    done
    printf '/%s' ${out[@]+"${out[@]}"}
    printf '\n'
}

# Prints the primary checkout root for <root>; when the checkout's git metadata
# is untrusted prints the reason instead and returns 1 (the caller captures
# stdout, so a global would be lost in the subshell).
_project_interpreter_primary_root() {
    local root="$1"
    local git_path="$root/.git"
    local line gitdir worktrees_dir common_git

    if [ -L "$git_path" ]; then
        printf '%s\n' "$git_path is a symlink"
        return 1
    fi
    if [ -d "$git_path" ] || [ ! -e "$git_path" ]; then
        printf '%s\n' "$root"
        return 0
    fi
    if [ ! -f "$git_path" ]; then
        printf '%s\n' "$git_path is not a file or directory"
        return 1
    fi

    IFS= read -r line < "$git_path" || true
    case "$line" in
        gitdir:*) ;;
        *)
            printf '%s\n' "$git_path is not a gitdir: pointer"
            return 1
            ;;
    esac
    gitdir="${line#gitdir:}"
    gitdir="${gitdir#"${gitdir%%[![:space:]]*}"}"
    gitdir="${gitdir%"${gitdir##*[![:space:]]}"}"
    case "$gitdir" in
        /*) ;;
        *) gitdir="$root/$gitdir" ;;
    esac
    gitdir="$(_project_interpreter_normalize "$gitdir")"
    worktrees_dir="$(dirname "$gitdir")"
    if [ "$(basename "$worktrees_dir")" != "worktrees" ] || [ ! -d "$gitdir" ]; then
        printf '%s\n' "$git_path gitdir is not <primary>/.git/worktrees/<name>"
        return 1
    fi
    common_git="$(dirname "$worktrees_dir")"
    if [ "$(basename "$common_git")" != ".git" ] \
        || [ -L "$common_git" ] || [ ! -d "$common_git" ] \
        || [ -L "$worktrees_dir" ] || [ -L "$gitdir" ]; then
        printf '%s\n' "$git_path gitdir is not under a real <primary>/.git directory"
        return 1
    fi
    dirname "$common_git"
}

project_interpreter_resolve() {
    local root primary primary_python tried

    root="$(cd -P "${1:?project_interpreter_resolve: checkout root required}" 2>/dev/null && pwd)" || {
        echo "Error: project interpreter not found: checkout root $1 does not exist" >&2
        return 1
    }
    if ! primary="$(_project_interpreter_primary_root "$root")"; then
        echo "Error: project interpreter not found: $root/.venv/bin/python not used ($primary)" >&2
        return 1
    fi
    primary_python="$primary/.venv/bin/python"
    if [ -f "$primary_python" ] && [ -x "$primary_python" ]; then
        printf '%s\n' "$primary_python"
        return 0
    fi
    tried="$primary_python"
    if [ "$primary" != "$root" ]; then
        tried="$tried (worktree-local $root/.venv/bin/python is not used)"
    fi
    echo "Error: project interpreter not found: $tried" >&2
    return 1
}
