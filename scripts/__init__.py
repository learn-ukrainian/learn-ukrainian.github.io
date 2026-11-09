"""learn-ukrainian product code.

The installed lu_machinery package derives no product and no shared-state anchor: a process
names them through ``LU_PRODUCT_ROOT`` and ``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT``
(``lu_machinery.common.repo_root``). Importing this package names the checkout it is in as
the product, always: product code reads its own checkout's files, and a value inherited from
a parent process that ran from another checkout (the dispatcher on the primary starting a
worker in a linked worktree) must not redirect it. The shared-state anchor is the primary of
that checkout unless the caller already set one (a launcher, a release snapshot's unit), as
the in-tree machinery copy derived both.

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
    os.environ[PRODUCT_ROOT_ENV] = str(_CHECKOUT)
    os.environ.setdefault(PRIMARY_ROOT_ENV, str(main_checkout_root(_CHECKOUT)))
