"""Synthetic dependencies for repositories exercising the tracked hook chain."""

import json
import shlex
import subprocess
from importlib.resources import files
from pathlib import Path

import yaml

from tests.opsec_fixtures import CATALOG, copy_publisher_scripts, make_tooling

# Settings the host binding asserts against itself (lu_machinery.host_context._assert_legacy).
# A fixture binding names its own checkouts and state, so the caller's values never apply.
BINDING_ASSERTED = (
    "LU_STATE_ROOT",
    "LEARN_UKRAINIAN_STATE_ROOT",
    "LU_TASKS_DIR",
    "LEARN_UKRAINIAN_BATCH_STATE_DIR",
    "FLEET_COMMS_ROOT",
    "LEARN_UKRAINIAN_OWNERSHIP_LEDGER",
    "LU_GITHUB_CACHE_DIR",
    "LU_GITHUB_SLUG",
    "LEARN_UKRAINIAN_GITHUB_SLUG",
    "LU_PRIMARY_REPO_ROOT",
    "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT",
    "LU_PRODUCT_ROOT",
    "LEARN_UK_REPO_ROOT",
    "LU_PYTHON",
    "LEARN_UKRAINIAN_PYTHON",
    "LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT",
    "LU_FLEET_REPO_SELECTOR_FILE",
    "MONITOR_PROJECT_STATE_URL",
    "LU_PROFILE_PATH",
    "LU_MONITOR_LOOPBACK",
    "MONITOR_API_BASE_URL",
    "MONITOR_API_URL",
    "AB_MONITOR_URL",
    "MONITOR_API_URLS",
    "AB_MONITOR_URLS",
    "MONITOR_BASE_URLS",
    "DELEGATE_MONITOR_API",
    "LU_REPOS_ROOT",
)

# Stands in for ``python -m lu_machinery.host_context shell`` (machinery R4). It validates the fixture
# binding with the release's own loader and projects it with the release's own functions. It omits
# only the checks a fixture cannot meet: the running interpreter's identity, the runtime version
# probe and the checkouts' registry origins.
_HOST_CONTEXT_SHELL = """
import shlex, sys
from pathlib import Path
from lu_machinery.host_context import (
    HostContext, HostContextError, hook_environment, invocation_checkout, load_host_context,
)

args = sys.argv[1:]
if not args or args[0] != "shell":
    sys.exit("fixture host context: only the shell command is supported")
try:
    context = load_host_context(role="state")
    if not isinstance(context, HostContext):
        raise HostContextError("invalid_role", "hook registration requires a full host binding")
    checkout = invocation_checkout(Path.cwd())
    if "--require-checkout" in args or "--install-hooks" in args:
        if checkout is None:
            raise HostContextError("invocation_git_missing", "Git hook requires an invocation checkout")
        if checkout[1] not in context.repos.values():
            raise HostContextError("invocation_repo_unbound", "Git hook checkout is outside the host repository bindings")
except HostContextError as exc:
    print(f"HOOK-BOOTSTRAP-FAILED: [{exc.code}] {exc}", file=sys.stderr)
    sys.exit(2)
for name, value in hook_environment(context).items():
    print(f"export {name}={shlex.quote(value)}")
if checkout is not None:
    print(f"worktree_root={shlex.quote(str(checkout[0]))}")
    print(f"main_root={shlex.quote(str(checkout[1]))}")
"""


def install_message_scanner(repo: Path) -> None:
    package = "lu_machinery"
    copy_publisher_scripts(Path(str(files(package))), repo / package)
    config = repo / package / "config/fleet_repos.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"repos": CATALOG}), encoding="utf-8")
    make_tooling(repo.parent / "private-fixture/tools/public_opsec_scan")


def bind_hook_host_context(
    base: Path,
    env: dict[str, str],
    *,
    product: Path,
    python: str,
    product_python: str | None = None,
    runtime_preamble: str = "",
) -> Path:
    """Bind ``env`` to a scratch ``machinery.host.v1`` file for the product checkout ``product``.

    ``LU_HOST_CONTEXT`` always names the scratch file, so a hook under test never reads the host's
    own binding. ``LU_PYTHON`` becomes a fixture runtime interpreter that runs ``python``, except that
    ``-I -B -m lu_machinery.host_context`` runs the stand-in above and ``runtime_preamble`` (shell)
    may answer other fixture calls first. ``product_python`` (default ``python``) is the binding's
    product interpreter, which ``scripts/pre_commit/project_python.sh`` runs. ``env`` also gets the
    binding's projection a launched session carries. The machinery checkout is a sibling of
    ``product``, so OPSEC tooling the fixture places beside it is found. Returns the binding's state
    root.
    """
    base = base.resolve()
    state = base / "host-state"
    state.mkdir(mode=0o700)
    # Hooks read machinery policy (OPSEC) from this primary checkout through LU_PRIMARY_REPO_ROOT.
    machinery = product.resolve().parent / "machinery-checkout"
    subprocess.run(["git", "init", "-q", str(machinery)], check=True, capture_output=True, timeout=60)
    shell_entry = base / "host_context_shell.py"
    shell_entry.write_text(_HOST_CONTEXT_SHELL, encoding="utf-8")
    runtime = base / "runtime-python"
    runtime.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ $# -ge 4 && "$1 $2 $3 $4" == "-I -B -m lu_machinery.host_context" ]]; then\n'
        f'  shift 4; exec {shlex.quote(python)} -I {shlex.quote(str(shell_entry))} "$@"\n'
        "fi\n" + runtime_preamble + f'exec {shlex.quote(python)} "$@"\n',
        encoding="utf-8",
    )
    runtime.chmod(0o755)
    unused = base / "unused-cto"
    binding = base / "host.v1.json"
    binding.write_text(
        json.dumps(
            {
                "schema": "machinery.host.v1",
                "state_root": str(state),
                "runtime": {"python": str(runtime), "lu_machinery": "fixture", "wheel_sha256": "0" * 64},
                "repos": {"machinery": str(machinery), "public": str(product.resolve())},
                "products": {"public": {"repo": "public", "python": product_python or python}},
                "default_product": "public",
                "private_tools": {},
                "cto": {"workspace": str(unused), "starter": str(unused / "start"), "config_dir": str(unused)},
                "selector_file": str(base / "unused-selector.yaml"),
                "monitor_url": "http://127.0.0.1:9",
            }
        ),
        encoding="utf-8",
    )
    binding.chmod(0o600)
    for name in BINDING_ASSERTED:
        env.pop(name, None)
    # A launched session carries the binding's projection (hook_environment), as the launcher exports it.
    env.update(
        LU_HOST_CONTEXT=str(binding),
        LU_PYTHON=str(runtime),
        LU_STATE_ROOT=str(state),
        LU_PRIMARY_REPO_ROOT=str(machinery),
        LU_PRODUCT_ROOT=str(product.resolve()),
    )
    return state


def binding_tasks_dir(state: Path) -> Path:
    """The task store a binding with state root ``state`` asserts (``LU_TASKS_DIR``)."""
    return state / "batch_state" / "tasks"
