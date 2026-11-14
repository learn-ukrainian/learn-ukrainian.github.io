"""Product entry for the installed lu-machinery dispatcher: dispatch, wait, status and every other verb.

The release derives no product checkout and no shared-state anchor from its own location
(``lu_machinery.common.repo_root``). This entry names the primary checkout of the checkout that holds
it as both, as the in-tree entry did by re-executing the primary's dispatcher: a linked worktree's
files never become the dispatcher's product inputs (its OPSEC linter, MCP configuration or sources
server). An inherited product root naming a directory outside this repository is a caller's explicit
product and is kept, as ``scripts/__init__.py`` keeps it; an inherited shared-state anchor is kept.

The entry first re-executes itself under ``-I`` (which implies ``-E``, ``-P`` and ``-s``), so no
``lu_machinery`` import, here or in the release, can come from ``PYTHONPATH``, the user site or this
file's directory, and no in-tree dispatcher code runs from any checkout.
"""

import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # This interpreter and fixed argv lists throughout; no shell runs.
    if not sys.flags.isolated:
        argv = [sys.executable, "-I", os.path.abspath(__file__), *sys.argv[1:]]
        os.execv(sys.executable, argv)  # nosemgrep: python.lang.security.audit.dangerous-os-exec-audit
    from lu_machinery.common.repo_root import PRIMARY_ROOT_ENV, PRODUCT_ROOT_ENV, main_checkout_root

    primary = main_checkout_root(Path(os.path.abspath(__file__)).parents[1])
    inherited = os.environ.get(PRODUCT_ROOT_ENV)
    # Another checkout of this repository shares its primary; anything else is configuration.
    if not inherited or main_checkout_root(Path(inherited)) == primary:
        os.environ[PRODUCT_ROOT_ENV] = str(primary)
    os.environ.setdefault(PRIMARY_ROOT_ENV, str(primary))
    argv = [sys.executable, "-I", "-m", "lu_machinery.dispatch", *sys.argv[1:]]
    os.execv(sys.executable, argv)  # nosemgrep: python.lang.security.audit.dangerous-os-exec-audit
