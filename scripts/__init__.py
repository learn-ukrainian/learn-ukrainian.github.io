"""learn-ukrainian product code.

The installed lu_machinery package derives no product and no shared-state anchor: a process
names them through ``LU_PRODUCT_ROOT`` and ``LEARN_UKRAINIAN_PRIMARY_REPO_ROOT``
(``lu_machinery.common.repo_root``). Importing this package names the checkout it is in as
the product, and that checkout's primary as the shared-state anchor, unless the caller
configured another value.

The values this package derives go into ``os.environ``, so every child process inherits them.
A derived value is exported together with a mark (the same value under the name with a
``_DERIVED`` suffix). An inherited value equal to its mark was derived by an ancestor process
for that ancestor's checkout, not configured: it is replaced for this process's own checkout
(the dispatcher sandbox runs a disposable repository's ``scripts/dispatch.py`` with the test
process's environment). An inherited product value naming another checkout of this repository
(it shares this checkout's primary) is replaced too: product code reads its own checkout's
files. Any other value is the caller's explicit configuration (a launcher, a test product tree,
a release snapshot's unit) and is kept, and a stale mark is dropped with it.

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
    _PRIMARY = main_checkout_root(_CHECKOUT)
    _PRODUCT_MARK = f"{PRODUCT_ROOT_ENV}_DERIVED"
    _PRIMARY_MARK = f"{PRIMARY_ROOT_ENV}_DERIVED"

    _INHERITED = os.environ.get(PRODUCT_ROOT_ENV)
    if (
        not _INHERITED
        or os.environ.get(_PRODUCT_MARK) == _INHERITED
        or main_checkout_root(Path(_INHERITED)) == _PRIMARY
    ):
        os.environ[PRODUCT_ROOT_ENV] = os.environ[_PRODUCT_MARK] = str(_CHECKOUT)
    else:
        os.environ.pop(_PRODUCT_MARK, None)

    _INHERITED = os.environ.get(PRIMARY_ROOT_ENV)
    if not _INHERITED or os.environ.get(_PRIMARY_MARK) == _INHERITED:
        os.environ[PRIMARY_ROOT_ENV] = os.environ[_PRIMARY_MARK] = str(_PRIMARY)
    else:
        os.environ.pop(_PRIMARY_MARK, None)
