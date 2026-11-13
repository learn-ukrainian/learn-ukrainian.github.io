#!/usr/bin/env bash
# Project-interpreter resolution for shell callers (#9118).
#
# Mirrors scripts/common/repo_root.py `main_checkout_root` + `project_interpreter`
# without asking git, so no worktree-controlled `commondir` file can redirect the
# lookup to a planted interpreter. The one environment input is the machinery
# roots configuration's interpreter (#12681): a non-empty LEARN_UKRAINIAN_PYTHON
# wins for every checkout, as it does in Python. It is operator-set environment,
# trusted like PATH; a relative path or a path that is not an executable file
# refuses instead of falling back. Unset or empty, the order is:
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
# project_interpreter_configured
#   stdout: the configured LEARN_UKRAINIAN_PYTHON, or nothing when unset (exit 0)
#   stderr: "Error: project interpreter not found: <reason>" (exit 1)
#
# project_interpreter_resolve <checkout-root>
#   stdout: absolute interpreter path (exit 0)
#   stderr: "Error: project interpreter not found: <paths tried>" (exit 1)
#
# project_python_command <python>
#   sets PROJECT_PYTHON_COMMAND to the argv prefix that starts <python> isolated
#   on this library's own machinery tree; append `-m <module> [args...]` or
#   `-c <code> [args...]`, exactly as after `python`
#
# project_python_run <python> (-m <module> | -c <code>) [args...]
#   runs that command; exit status and streams are the child's
#
# project_hook_roots_resolve / project_hook_context_resolve [<product-root>]
#   the one hook-boundary rule for the product, shared-state and interpreter
#   roots (see their definitions); exit 0 with the roots exported, else 1
#
# Load-bearing tests: tests/test_deploy_extensions.py (real temporary repos),
# tests/test_launcher_helper_root.py (every launcher helper site),
# tests/hooks/test_session_setup_isolation.py (every launcher-library child).

# The machinery tree that holds this file, from its unresolved location
# (design-v1 amendment 1): PROJECT_PACKAGE is the package directory's name,
# which is its import name, and PROJECT_CODE_ROOT the directory that holds it.
_project_interpreter_lib_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" \
    || _project_interpreter_lib_dir=''
PROJECT_PACKAGE="${_project_interpreter_lib_dir%/*}"
PROJECT_CODE_ROOT="${PROJECT_PACKAGE%/*}"
PROJECT_PACKAGE="${PROJECT_PACKAGE##*/}"
unset _project_interpreter_lib_dir

# Shell counterpart of common.repo_root.product_root's explicit selection.
# Installed resources have no implicit consumer. Keep the selected spelling,
# including symlinks, as the Python resolver does.
project_product_root_resolve() {
    local root="${1-${LU_PRODUCT_ROOT:-}}"
    if [[ "$root" != /* || ! -d "$root" ]]; then
        printf '%s\n' 'Error: product root requires an absolute existing directory (set LU_PRODUCT_ROOT or pass an explicit root)' >&2
        return 1
    fi
    printf '%s\n' "$root"
}

# The one module bootstrap for every launcher-library Python child (#100 R68).
# The child starts with -I, so the caller's PYTHONPATH, user site and cwd stay
# off its import path. The bootstrap loads only the package from
# PROJECT_CODE_ROOT by spec, so that directory never goes on sys.path and no
# other name can resolve there; the tree that holds the library supplies the
# code, whatever the interpreter or project has installed. It then runs
# `-m <module>` as __main__, or `-c <code>` with sys.argv[0] == "-c", as Python
# itself would. The environment is passed on unchanged.
PROJECT_MODULE_BOOTSTRAP='
import importlib.util, os, runpy, sys
root, name, mode, target = sys.argv[1:5]
del sys.argv[1:5]
pkg = os.path.join(root, name)
init = os.path.join(pkg, "__init__.py")
if mode not in ("-m", "-c"):
    sys.exit("module bootstrap: expected -m <module> or -c <code>, got %s" % mode)
if not os.path.isfile(init):
    sys.exit("module bootstrap: no %s package at %s" % (name, pkg))
spec = importlib.util.spec_from_file_location(name, init, submodule_search_locations=[pkg])
sys.modules[name] = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sys.modules[name])
if mode == "-m":
    runpy.run_module(target, run_name="__main__", alter_sys=True)
else:
    exec(compile(target, "<string>", "exec"), {"__name__": "__main__"})
'

project_python_command() {
    PROJECT_PYTHON_COMMAND=("${1:?project_python_command: interpreter required}" -I -c "$PROJECT_MODULE_BOOTSTRAP" \
        "$PROJECT_CODE_ROOT" "$PROJECT_PACKAGE")
}

project_python_run() {
    project_python_command "$1" || return 1
    shift
    "${PROJECT_PYTHON_COMMAND[@]}" "$@"
}

# The block between the two marker lines is also the resolver of every native
# hook command: agent_runtime/agy_hook_config.native_hook_command embeds it
# verbatim, so a hook validates its interpreter before any Python starts. It
# must stay self-contained: no function or variable defined outside it.
# LU_HOOK_RESOLVERS_BEGIN
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

# Prints the physical path of directory <dir>, or returns 1. The x sentinel keeps
# a trailing newline $(...) would strip, so a directory is never checked as its
# clean namesake; a physical path with a newline cannot be checked faithfully by
# these helpers (or exported intact), so it refuses (#100).
_project_physical_dir() {
    local dir
    dir="$(cd -P "$1" 2>/dev/null && pwd -P && printf x)" || return 1
    dir="${dir%$'\n'x}"
    [[ "$dir" != *$'\n'* ]] || return 1
    printf '%s\n' "$dir"
}

# Prints the primary checkout root for <root>; when the checkout's git metadata
# is untrusted prints the reason instead and returns 1 (the caller captures
# stdout, so a global would be lost in the subshell).
#
# A `.git` directory or no `.git` at all (release snapshot) resolves to <root>
# itself and never to any other directory. So a worktree whose gitfile was
# removed resolves to its own root: the launcher passes its own directory
# (LC_ROOT), whose code it is already running, so that grants nothing new
# (#9121; pinned by test_snapshot_resolves_only_to_the_launcher_root).
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
    pointed_root="$(_project_physical_dir "$(dirname "$pointer")")" || return 1
    [ "$pointed_root" = "$root" ]
}

project_primary_root_resolve() {
    local root primary

    root="$(_project_physical_dir "${1:?project_primary_root_resolve: checkout root required}")" || {
        echo "Error: untrusted git metadata: checkout root $1 does not exist or its path has a newline" >&2
        return 1
    }
    if ! primary="$(_project_interpreter_primary_root "$root")"; then
        echo "Error: untrusted git metadata: $primary" >&2
        return 1
    fi
    printf '%s\n' "$primary"
}

project_interpreter_configured() {
    local configured="${LEARN_UKRAINIAN_PYTHON:-}"

    [ -n "$configured" ] || return 0
    case "$configured" in
        /*) ;;
        *)
            echo "Error: project interpreter not found: LEARN_UKRAINIAN_PYTHON must be an absolute path, got $configured" >&2
            return 1
            ;;
    esac
    if [ ! -f "$configured" ] || [ ! -x "$configured" ]; then
        echo "Error: project interpreter not found: LEARN_UKRAINIAN_PYTHON=$configured is not an executable file" >&2
        return 1
    fi
    printf '%s\n' "$configured"
}

project_interpreter_resolve() {
    local root primary primary_python tried configured

    configured="$(project_interpreter_configured)" || return 1
    if [ -n "$configured" ]; then
        printf '%s\n' "$configured"
        return 0
    fi
    root="$(_project_physical_dir "${1:?project_interpreter_resolve: checkout root required}")" || {
        echo "Error: project interpreter not found: checkout root $1 does not exist or its path has a newline" >&2
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

# _project_hook_git_layout <checkout>
#   true when <checkout>/.git passes Git's own repository test, as
#   repo_root._is_primary_git_layout applies it (stricter here: a symlinked HEAD
#   refuses): a real directory without commondir, with objects, refs and a valid
#   HEAD (`ref: refs/...` or a 40/64-hex object id). An empty or stray .git is not
#   a primary.
_project_hook_git_layout() {
    local git_dir="$1/.git" head=""
    [[ -d "$git_dir" && ! -L "$git_dir" ]] || return 1
    [[ ! -e "$git_dir/commondir" && ! -L "$git_dir/commondir" ]] || return 1
    [[ -d "$git_dir/objects" && -d "$git_dir/refs" ]] || return 1
    [[ -f "$git_dir/HEAD" && ! -L "$git_dir/HEAD" ]] || return 1
    IFS= read -r head < "$git_dir/HEAD" || true
    case "$head" in
        ref:*)
            head="${head#ref:}"
            [[ "${head#"${head%%[![:space:]]*}"}" = refs/* ]]
            ;;
        *) [[ "$head" =~ ^[0-9a-fA-F]{40}([0-9a-fA-F]{24})?$ ]] ;;
    esac
}

# project_hook_roots_resolve [<product-root>]
#   exports LU_PRODUCT_ROOT and LEARN_UKRAINIAN_PRIMARY_REPO_ROOT (exit 0), or
#   exports nothing (exit 1). The product is the argument when one is given,
#   else LU_PRODUCT_ROOT, else CLAUDE_PROJECT_DIR, else the nearest physical
#   ancestor of the working directory that has a .git entry; never this
#   library's location. The first candidate given is the only one considered.
#   The shared-state anchor is LEARN_UKRAINIAN_PRIMARY_REPO_ROOT when set, else
#   the product's validated primary. A product with a .git entry must resolve
#   to a primary, and the anchor must be one: both pass _project_hook_git_layout.
#   A set LEARN_UKRAINIAN_STATE_ROOT must name the anchor. A release snapshot
#   (no .git) therefore needs an explicit anchor.
project_hook_roots_resolve() {
    local root="${1-${LU_PRODUCT_ROOT:-${CLAUDE_PROJECT_DIR:-}}}"
    local primary state_root state_config invocation
    # Configured roots keep precedence, but cannot hide malformed invocation metadata.
    # Every directory below is checked by its exact physical path; one whose path has
    # a newline refuses (_project_physical_dir).
    invocation="$(_project_physical_dir .)" || return 1
    while [[ ! -e "$invocation/.git" && ! -L "$invocation/.git" && "$invocation" != / ]]; do
        invocation="${invocation%/*}"
        [[ -n "$invocation" ]] || invocation=/
    done
    if [[ -e "$invocation/.git" || -L "$invocation/.git" ]]; then
        primary="$(project_primary_root_resolve "$invocation")" || return 1
        _project_hook_git_layout "$primary" || return 1
    fi
    if [[ -z "$root" ]]; then
        root="$(pwd -P)" || return 1
        while [[ ! -e "$root/.git" && ! -L "$root/.git" ]]; do
            [[ "$root" != / ]] || return 1
            root="${root%/*}"
            [[ -n "$root" ]] || root=/
        done
    fi
    [[ "$root" = /* && -d "$root" ]] || return 1
    primary="$(project_primary_root_resolve "$root")" || return 1
    # A product with a .git entry must resolve to a real primary, whatever
    # anchor is configured: an empty or stray .git directory would otherwise
    # make the product its own primary and its .venv the interpreter.
    if [[ -e "$root/.git" || -L "$root/.git" ]]; then
        _project_hook_git_layout "$primary" || return 1
    fi
    state_root="${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-$primary}"
    [[ "$state_root" = /* ]] || return 1
    state_root="$(_project_physical_dir "$state_root")" && _project_hook_git_layout "$state_root" || return 1
    if [[ -n "${LEARN_UKRAINIAN_STATE_ROOT:-}" ]]; then
        [[ "$LEARN_UKRAINIAN_STATE_ROOT" = /* ]] || return 1
        state_config="$(_project_physical_dir "$LEARN_UKRAINIAN_STATE_ROOT")" || return 1
        [[ "$state_config" = "$state_root" ]] || return 1
    fi
    export LU_PRODUCT_ROOT="$root"
    export LEARN_UKRAINIAN_PRIMARY_REPO_ROOT="$state_root"
}

# project_hook_context_resolve [<product-root>]
#   needs a configured LEARN_UKRAINIAN_PRIMARY_REPO_ROOT; then
#   project_hook_roots_resolve, and exports LEARN_UKRAINIAN_PYTHON: the
#   configured absolute executable, else the configured primary's .venv python
#   (exit 0); exit 1 otherwise, before any interpreter starts. The product's own
#   Git metadata never names the primary or the interpreter: whoever works in a
#   checkout can rewrite it, and no local check tells it from a real primary
#   (#100).
project_hook_context_resolve() {
    local interpreter
    [[ -n "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-}" ]] || return 1
    project_hook_roots_resolve "$@" || return 1
    interpreter="$(project_interpreter_resolve "$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT")" || return 1
    export LEARN_UKRAINIAN_PYTHON="$interpreter"
}
# LU_HOOK_RESOLVERS_END
