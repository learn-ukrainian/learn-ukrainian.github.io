"""learn-ukrainian product code.

The installed lu_machinery package derives no product and no shared-state anchor: a process
names them through ``LU_PRODUCT_ROOT`` and ``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT``
(``lu_machinery.common.repo_root``). Importing this package names the checkout it is in as
the product unless the caller configured another product. Product code reads its own
checkout's files: a value naming another checkout of this repository was inherited from a
parent process that ran there (the dispatcher on the primary starting a worker in a linked
worktree) and must not redirect it, so it is replaced. A value naming a directory outside this
repository is the caller's explicit product (a launcher or a test product tree) and is kept.
The shared-state anchor is the primary of that checkout unless the caller already set one (a
launcher, a release snapshot's unit), as the in-tree machinery copy derived both.

This package still holds the retained in-tree machinery copy, and some product tools run on a
bare interpreter (the OPSEC scans in CI). Where the release is not installed, importing the
package binds nothing; product modules that need the release fail at their own import.
"""

import importlib.util
import os
from pathlib import Path

if importlib.util.find_spec("lu_machinery") is not None:
    from lu_machinery.common.repo_root import PRIMARY_ROOT_ENV, PRODUCT_ROOT_ENV, main_checkout_root

    _CHECKOUT = Path(os.path.abspath(__file__)).parents[1]
    _INHERITED = os.environ.get(PRODUCT_ROOT_ENV)
    # Another checkout of this repository shares its primary; anything else is configuration.
    if not _INHERITED or main_checkout_root(Path(_INHERITED)) == main_checkout_root(_CHECKOUT):
        os.environ[PRODUCT_ROOT_ENV] = str(_CHECKOUT)
    os.environ.setdefault(PRIMARY_ROOT_ENV, str(main_checkout_root(_CHECKOUT)))
