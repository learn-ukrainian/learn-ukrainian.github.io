"""Repository root and project-interpreter resolvers, and the one machinery root configuration.

Machinery roots (#12681). Five roots are kept distinct, and the four that can live
outside this checkout come from one configuration: environment variables read at the
call (a systemd ``EnvironmentFile=``, a launcher or a test can supply them). An unset or
empty variable keeps today's value, so the defaults are the behaviour before the
configuration existed.

========================  ====================================  =================================================
Root                      Variable                              Default (today's behaviour)
========================  ====================================  =================================================
runtime (machinery code)  none: the checkout this file is in    ``Path(__file__).parents[2]``
primary checkout          ``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT``  ``main_checkout_root`` of the runtime checkout
GitHub slug               ``LEARN_UKRAINIAN_GITHUB_SLUG``        ``learn-ukrainian/learn-ukrainian.github.io``
state root                ``LEARN_UKRAINIAN_STATE_ROOT``         the primary checkout (holds ``batch_state/``)
rules directory (policy)  ``LEARN_UKRAINIAN_RULES_DIR``          ``<checkout>/agents_extensions/shared/rules``
interpreter               ``LEARN_UKRAINIAN_PYTHON``             :func:`project_interpreter`'s resolution order
========================  ====================================  =================================================

``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT`` and ``LEARN_UKRAINIAN_PYTHON`` are the names the
project-state reporter wrapper already reads; the configuration reuses them so one
setting means one thing everywhere.

Path values must be absolute; a relative value raises :class:`MachineryConfigError`
(a ``ValueError``) rather than resolving against the working directory. The state root
must name the primary checkout: moving state to another store is the operator's state
cutover (machinery move step 9), so any other value is refused, which also keeps
modules that still anchor ``batch_state/`` on the primary from splitting from those
that read the state root.

The runtime root is never configured. It is the code that is running, and a re-exec
from a linked worktree (``scripts/dispatcher/primary.py``) still resolves that code's own
primary from Git metadata, not from this configuration.
"""

from __future__ import annotations

import importlib.util
import os
import re
import stat
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


def _install_redacted_environ() -> None:
    """Hide env values without importing the scripts package.

    Callers load this module as ``common.repo_root`` with ``scripts/`` on
    ``sys.path``. A package import of ``scripts`` fails on that path.
    A partial checkout that copied this module without ``scripts/lib`` still
    imports: the formatter is optional there.
    """
    name = "scripts.lib.redacted_environ"
    module = sys.modules.get(name)
    if module is None:
        path = Path(__file__).resolve().parents[1] / "lib" / "redacted_environ.py"
        if not path.is_file():
            return
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    module.install_redacted_environ_repr()


_install_redacted_environ()

# Directory and final-component symlink hops followed while identifying a venv
# entrypoint. POSIX SYMLOOP_MAX is commonly 40; longer chains fail closed.
_MAX_SYMLINK_HOPS = 40

PRIMARY_ROOT_ENV = "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"
GITHUB_SLUG_ENV = "LEARN_UKRAINIAN_GITHUB_SLUG"
STATE_ROOT_ENV = "LEARN_UKRAINIAN_STATE_ROOT"
RULES_DIR_ENV = "LEARN_UKRAINIAN_RULES_DIR"
INTERPRETER_ENV = "LEARN_UKRAINIAN_PYTHON"
MACHINERY_ENV_VARS = (PRIMARY_ROOT_ENV, GITHUB_SLUG_ENV, STATE_ROOT_ENV, RULES_DIR_ENV, INTERPRETER_ENV)
DEFAULT_GITHUB_SLUG = "learn-ukrainian/learn-ukrainian.github.io"
RULES_DIR_REL = "agents_extensions/shared/rules"
RUNTIME_ROOT = Path(__file__).resolve().parents[2]
# GitHub owner (alphanumerics and inner hyphens) / repository name.
_GITHUB_SLUG_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9._-]{1,100}")


class MachineryConfigError(ValueError):
    """A machinery root variable is set to a value that cannot be used; the message names it."""


def _env(env: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if env is None else env


def _configured_path(name: str, env: Mapping[str, str] | None) -> Path | None:
    """Absolute path named by ``name``, ``None`` when unset or empty; refuse a relative path."""
    value = _env(env).get(name, "")
    if not value:
        return None
    if not os.path.isabs(value):
        raise MachineryConfigError(f"{name} must be an absolute path, got {value!r}")
    return Path(value)


def configured_primary_root(env: Mapping[str, str] | None = None) -> Path | None:
    """The primary checkout named by the configuration, or ``None`` for the Git-derived default.

    Only a checkout whose ``.git`` is a real directory (not a symlink) holding no
    ``commondir`` file is accepted: that is the one shape whose Git common directory is
    its own ``.git``. Anything else (a gitfile, a ``.git`` symlink such as one to a
    linked worktree's administrative directory, a copied worktree gitdir, or no ``.git``)
    is refused, since anchoring state there would split task records from the locks
    closeout reads (#5171 class).
    """
    configured = _configured_path(PRIMARY_ROOT_ENV, env)
    if configured is not None and not _is_primary_git_layout(configured):
        raise MachineryConfigError(
            f"{PRIMARY_ROOT_ENV} must name a primary checkout, not a linked worktree: "
            f"{configured}/.git is not a real Git directory of its own"
        )
    return configured


def _is_primary_git_layout(checkout: Path) -> bool:
    """``checkout/.git`` is a non-symlink directory with no ``commondir`` file."""
    git_dir = checkout / ".git"
    try:
        if not stat.S_ISDIR(os.lstat(git_dir).st_mode):
            return False
    except OSError:
        return False
    return not os.path.lexists(git_dir / "commondir")


def runtime_primary_root(start: Path | None = None) -> Path:
    """The running code's own primary checkout, from its Git metadata; never configured.

    ``start`` is the caller's own checkout (``Path(__file__).resolve().parents[2]``),
    default this module's. Callers that start the dispatcher use this, as
    ``exec_primary`` does, so the configured target primary never selects which
    dispatcher code runs.
    """
    return main_checkout_root(RUNTIME_ROOT if start is None else start)


def primary_root(start: Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    """The configured primary checkout, else the primary that owns ``start`` (default: the runtime)."""
    configured = configured_primary_root(env)
    if configured is not None:
        return configured
    return main_checkout_root(RUNTIME_ROOT if start is None else start)


def configured_github_slug(env: Mapping[str, str] | None = None) -> str | None:
    """The configured ``owner/name`` GitHub slug, or ``None`` when unset or empty."""
    value = _env(env).get(GITHUB_SLUG_ENV, "")
    if not value:
        return None
    if not _GITHUB_SLUG_RE.fullmatch(value) or value.split("/")[1] in (".", ".."):
        raise MachineryConfigError(f"{GITHUB_SLUG_ENV} must be an owner/name GitHub slug, got {value!r}")
    return value


def github_slug(env: Mapping[str, str] | None = None) -> str:
    """The configured ``owner/name`` GitHub slug, else this repository's."""
    return configured_github_slug(env) or DEFAULT_GITHUB_SLUG


def state_root(start: Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    """The checkout whose ``batch_state/`` holds dispatch state: the primary checkout.

    A configured state root must be that same directory (compared after ``realpath``);
    any other value would point state at a new store, which only the operator's state
    cutover may do, so it is refused.
    """
    primary = primary_root(start, env)
    configured = _configured_path(STATE_ROOT_ENV, env)
    if configured is None:
        return primary
    if _realpath(configured) != _realpath(primary):
        raise MachineryConfigError(
            f"{STATE_ROOT_ENV} ({configured}) must be the primary checkout ({primary}); "
            "moving dispatch state to another store is the operator's state cutover"
        )
    return configured


def rules_dir(root: Path | None = None, env: Mapping[str, str] | None = None) -> Path:
    """The configured rules directory, else ``root``'s (default: the runtime's) rules directory."""
    configured = _configured_path(RULES_DIR_ENV, env)
    if configured is not None:
        return configured
    return (RUNTIME_ROOT if root is None else Path(root)) / RULES_DIR_REL


def configured_interpreter(env: Mapping[str, str] | None = None) -> Path | None:
    """The interpreter named by the configuration, or ``None`` for :func:`project_interpreter`'s order."""
    return _configured_path(INTERPRETER_ENV, env)


@dataclass(frozen=True)
class MachineryRoots:
    """The five distinct roots and the GitHub slug, as one resolved view."""

    runtime: Path
    primary: Path
    github_slug: str
    state: Path
    rules_dir: Path
    interpreter: Path


def machinery_roots(env: Mapping[str, str] | None = None) -> MachineryRoots:
    """Resolve every machinery root from the configuration and its defaults.

    Raises :class:`MachineryConfigError` for an unusable value and ``FileNotFoundError``
    when no interpreter can be resolved.
    """
    return MachineryRoots(
        runtime=RUNTIME_ROOT,
        primary=primary_root(env=env),
        github_slug=github_slug(env),
        state=state_root(env=env),
        rules_dir=rules_dir(env=env),
        interpreter=project_interpreter(env=env),
    )


def main_checkout_root(repo_root: Path) -> Path:
    """Return the primary checkout root that owns the shared ``.git`` dir.

    Only a ``gitdir:`` target with Git's exact ``.git/worktrees/<name>`` shape
    redirects a path. Primary checkouts, release snapshots, and every other
    malformed or non-Git root remain anchored to themselves.
    """
    git_path = repo_root / ".git"
    if git_path.is_dir():
        return repo_root
    if not git_path.is_file():
        return repo_root

    try:
        first_line = git_path.read_text().splitlines()[0]
    except (IndexError, OSError):
        return repo_root
    prefix = "gitdir:"
    if not first_line.startswith(prefix):
        return repo_root

    git_dir = Path(first_line[len(prefix) :].strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir
    git_dir = git_dir.resolve()
    if git_dir.parent.name != "worktrees":
        return repo_root
    common_git_dir = git_dir.parent.parent
    if common_git_dir.name != ".git":
        return repo_root
    return common_git_dir.parent


def _absolute_text(path: Path) -> str:
    text = os.fspath(path)
    if os.path.isabs(text):
        return text
    return os.path.join(os.getcwd(), text)


def _lexical_absolute(path: Path) -> Path:
    """Absolute path with ``.`` and ``..`` collapsed, without resolving symlinks."""
    return Path(os.path.normpath(_absolute_text(path)))


def _realpath(path: Path) -> Path:
    """``os.path.realpath`` of ``path``, or a normalized absolute path if that fails."""
    text = _absolute_text(path)
    try:
        resolved = os.path.realpath(text)
    except OSError:
        resolved = os.path.normpath(text)
    return Path(resolved)


def _symlink_target(path: Path) -> Path | None:
    """Target of ``path`` when it is a symlink, else ``None``.

    A path that cannot be inspected (``PermissionError`` and other
    ``OSError``s, a path that vanished before the check, or a link replaced
    between the check and the read) raises ``FileNotFoundError`` so callers
    see the named refusal they handle instead of an uncaught error or a
    silently accepted interpreter. ``os.lstat`` is used rather than
    ``Path.is_symlink`` because the latter reports ``False`` for a missing path.
    """
    try:
        if not stat.S_ISLNK(os.lstat(path).st_mode):
            return None
        return Path(os.readlink(path))
    except OSError as exc:
        raise FileNotFoundError(f"project interpreter not found: {path} cannot be inspected: {exc}") from exc


def _first_parent_symlink_hop(parent: Path) -> Path | None:
    """Expand the first directory symlink in an absolute parent path, if any.

    Keep the remaining components for the next pass so every intermediate
    ``<checkout>/.venv/bin`` view is classified before another hop is taken.
    """
    prefix = Path(parent.anchor)
    for index, part in enumerate(parent.parts[1:], start=1):
        if part == "..":
            prefix = prefix.parent
            continue
        next_path = prefix / part
        target = _symlink_target(next_path)
        if target is not None:
            if not target.is_absolute():
                target = prefix / target
            return target.joinpath(*parent.parts[index + 1 :])
        prefix = next_path
    return None


def _venv_python(checkout: Path) -> Path:
    """Path of ``checkout``'s project interpreter, whether or not the file exists."""
    # Resolver definition: this join names that checkout's interpreter.
    return checkout / ".venv" / "bin" / "python"


def _venv_bin_checkout(candidate: Path) -> Path | None:
    """Checkout that owns ``candidate`` when it sits directly in that checkout's ``.venv/bin``."""
    if candidate.parent.name != "bin":
        return None
    venv = candidate.parent.parent
    if venv.name != ".venv":
        return None
    return venv.parent


def _venv_owners(interpreter: Path) -> set[Path]:
    """Checkouts that own ``interpreter`` as a ``<checkout>/.venv/bin`` entrypoint.

    Any direct child of ``.venv/bin`` counts: ``python``, ``python3``, versioned
    ``python3.N``, and every other executable there. Each path is classified
    at every directory symlink hop, so both ``other/.venv -> venv-store`` and
    ``venv-alias -> other/.venv -> venv-store`` name ``other``. Owners are
    compared after ``realpath``. A later check refuses the interpreter when
    any owner is outside the requested checkout and its primary.

    A file-symlink hop is followed only when no directory view names a checkout, so
    a link that lands in ``.venv/bin`` counts even when the link's own path
    does not. The entrypoint is recognized before that hop is followed, so
    ``python3.12`` still counts when it points at a toolchain binary outside
    the venv. A toolchain interpreter such as ``hostedtoolcache/.../bin/python``
    names no checkout.
    """
    candidate = Path(_absolute_text(interpreter))
    seen: set[Path] = set()
    owners: set[Path] = set()
    for _ in range(_MAX_SYMLINK_HOPS + 1):
        view_u = _lexical_absolute(candidate)
        if candidate in seen:
            raise FileNotFoundError(f"project interpreter not found: {interpreter} is a symlink loop")
        seen.add(candidate)
        checkout = _venv_bin_checkout(view_u)
        if checkout is not None:
            owners.add(_realpath(checkout))
        parent_hop = _first_parent_symlink_hop(candidate.parent)
        if parent_hop is not None:
            candidate = parent_hop / candidate.name
            continue
        if owners:
            return owners
        target = _symlink_target(candidate)
        if target is None:
            return set()
        if not target.is_absolute():
            target = candidate.parent / target
        candidate = target
    raise FileNotFoundError(
        f"project interpreter not found: {interpreter} symlink chain exceeds {_MAX_SYMLINK_HOPS} hops"
    )


def project_interpreter(root: Path | None = None, *, env: Mapping[str, str] | None = None) -> Path:
    """Return the project interpreter for ``root`` or this checkout.

    Called when a spawn needs the interpreter, not while this module is
    imported. Import therefore succeeds when no project interpreter can be
    found; this function raises ``FileNotFoundError`` at the call.

    A configured ``LEARN_UKRAINIAN_PYTHON`` wins for every checkout: it must be an
    absolute path to an existing file, else this raises (``MachineryConfigError``
    for a relative path, ``FileNotFoundError`` for a missing file). The operator who
    sets it vouches for it, as for ``PATH``. Unset, the resolution order for the
    requested checkout is:

    1. The primary checkout's ``.venv/bin/python`` when the file exists.
       The primary is the git common-dir checkout ``main_checkout_root``
       finds for a linked worktree, and the checkout itself otherwise.
       Dispatch worktrees share that interpreter even when the worktree
       also has a ``.venv``.
    2. Otherwise that checkout's own ``.venv/bin/python`` when the file exists.
    3. Otherwise ``sys.executable``. This is the CI case: the runner has no
       project ``.venv``. The executable is classified at each directory
       symlink hop. A view containing ``<X>/.venv/bin/<entry>`` names ``X``
       (compared after ``realpath``), including ``python3.N``, a file symlink
       that resolves into that directory, a directory symlink such as
       ``venv-alias -> other/.venv -> venv-store``. The final executable symlink is not
       resolved: ``python3.N`` points at the toolchain binary, and following it
       would drop ``.venv``. If any named checkout is neither the requested
       checkout nor its primary checkout, the interpreter is refused. It is
       accepted when every named checkout is one of those two, and when no
       view names a checkout (hosted CI Python). Symlink loops, path
       components that cannot be inspected, and a link that changes between
       the check and the read fail closed with ``FileNotFoundError``.
    """
    configured = configured_interpreter(env)
    if configured is not None:
        if not configured.is_file():
            raise FileNotFoundError(f"project interpreter not found: {INTERPRETER_ENV}={configured} is not a file")
        return configured
    repo = RUNTIME_ROOT if root is None else Path(root)
    primary_root = main_checkout_root(repo)
    primary = _venv_python(primary_root)
    if primary.is_file():
        return primary
    own = _venv_python(repo)
    if primary_root != repo and own.is_file():
        return own
    current = Path(sys.executable)
    owners = _venv_owners(current)
    if owners:
        allowed = {_realpath(repo), _realpath(primary_root)}
        if not owners.issubset(allowed):
            raise FileNotFoundError(
                "project interpreter not found: "
                f"{primary} does not exist and {own} does not exist and "
                f"sys.executable ({current}) "
                "is not the requested checkout's .venv or its primary checkout's .venv"
            )
    return current


def resolve_repo_root(script_path: Path, parents: int) -> Path:
    """Anchor all dispatch state to the PRIMARY checkout, never a worktree copy.

    Every dispatch worktree carries its own copy of this script; running that
    copy used to anchor batch_state/ and .worktrees/ to the WORKTREE root,
    nesting worktrees and hiding tasks from the Monitor API (#5171).

    Consequence: sys.path inserts and relative-path resolution (e.g. a
    relative --cwd) also anchor to the primary checkout — a worktree copy
    of this script lazy-imports the PRIMARY's scripts/* modules, not the
    worktree branch's. Intentional: dispatch infrastructure is ground truth
    in the primary; cross-cutting changes to dispatch.py plus its lazy deps
    must land on main before they steer live dispatches.

    A configured ``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT`` names that primary
    directly, so machinery installed outside the checkout anchors state on
    the configured primary instead of on its own install location.
    """
    configured = configured_primary_root()
    if configured is not None:
        return configured
    return main_checkout_root(script_path.resolve().parents[parents])
