#!/usr/bin/env bash
# Project-interpreter resolution for shell callers (#9118).
#
# Mirrors scripts/common/repo_root.py `main_checkout_root` + `project_interpreter`
# without asking git, so no environment variable and no worktree-controlled
# `commondir` file can redirect the lookup to a planted interpreter:
#   - a linked worktree is accepted only when its `.git` gitfile says
#     `gitdir: <primary>/.git/worktrees/<name>`, `<primary>/.git` is a real
#     directory (not a symlink, no symlinked `worktrees/<name>`), and that
#     entry's `gitdir` back-pointer names this worktree's `.git` (#9121);
#     `commondir` is never read;
#   - the primary checkout's `.venv/bin/python` wins, even when the worktree
#     has its own `.venv`;
#   - the checkout's own `.venv` is used only when the checkout IS the primary
#     (a `.git` directory, or no `.git` at all as in a release snapshot);
#   - anything else (unrecognised gitfile, symlinked `.git`) is untrusted.
#
# Residual (#9121): whoever can rewrite the gitfile can also build a complete
# fake primary (`<fake>/.git/worktrees/<name>/gitdir` pointing back here, plus
# `<fake>/.venv`). It is indistinguishable from the real primary using local
# metadata alone, so the back-pointer only stops a gitfile that borrows another
# repository's existing worktree entry. The only trust anchor outside the
# worktree is the operator-set CODEX_CANONICAL_REPO_ROOT on a Codex launch
# (launcher_resolve_roots in launcher_core.sh), which is also the only accepted
# way to name a primary Git cannot prove from the worktree (`--separate-git-dir`).
# The Python `main_checkout_root` checks the gitfile shape only.
#
# project_primary_root_resolve <checkout-root>
#   stdout: absolute physical primary checkout root (exit 0)
#   stderr: "Error: untrusted git metadata: <reason>" (exit 1)
#
# project_interpreter_resolve <checkout-root>
#   stdout: absolute interpreter path (exit 0)
#   stderr: "Error: project interpreter not found: <paths tried>" (exit 1)
#
# Load-bearing tests: tests/test_deploy_extensions.py (real temporary repos),
# tests/test_launcher_helper_root.py (every launcher helper site).

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
    if ! _project_interpreter_points_back "$gitdir" "$root"; then
        printf '%s\n' "$gitdir/gitdir does not point back at $git_path"
        return 1
    fi
    dirname "$common_git"
}

# True when <admin-dir>/gitdir (written by `git worktree add`, absolute or,
# with worktree.useRelativePaths, relative to <admin-dir>) names <root>/.git.
# <root> is physical; the pointer's directory is compared physically too.
_project_interpreter_points_back() {
    local admin_dir="$1" root="$2" pointer="" pointed_root

    [ -f "$admin_dir/gitdir" ] && [ ! -L "$admin_dir/gitdir" ] || return 1
    IFS= read -r pointer < "$admin_dir/gitdir" || true
    pointer="${pointer#"${pointer%%[![:space:]]*}"}"
    pointer="${pointer%"${pointer##*[![:space:]]}"}"
    [ -n "$pointer" ] || return 1
    case "$pointer" in
        /*) ;;
        *) pointer="$admin_dir/$pointer" ;;
    esac
    [ "$(basename "$pointer")" = ".git" ] || return 1
    pointed_root="$(cd -P "$(dirname "$pointer")" 2>/dev/null && pwd)" || return 1
    [ "$pointed_root" = "$root" ]
}

project_primary_root_resolve() {
    local root primary

    root="$(cd -P "${1:?project_primary_root_resolve: checkout root required}" 2>/dev/null && pwd)" || {
        echo "Error: untrusted git metadata: checkout root $1 does not exist" >&2
        return 1
    }
    if ! primary="$(_project_interpreter_primary_root "$root")"; then
        echo "Error: untrusted git metadata: $primary" >&2
        return 1
    fi
    printf '%s\n' "$primary"
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
