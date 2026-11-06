"""Shared test helpers."""

from __future__ import annotations

import functools
import os
from pathlib import Path


@functools.cache
def machinery_package() -> str:
    """The machinery package's directory name: ``scripts`` here, ``lu_machinery`` once renamed.

    Tests that build a checkout or name a machinery file write ``root / machinery_package() / ...``
    instead of spelling ``scripts/...``: the machinery-move rename rewrites imports and module
    names, not paths, so a spelled path would name a directory the extracted layout lacks. The
    name comes from the imported package's unresolved file location (design-v1 amendment 1).
    """
    from scripts.common import repo_root

    return Path(os.path.abspath(repo_root.__file__)).parents[1].name


def machinery_module(suffix: str) -> str:
    """The dotted name of the machinery module ``suffix`` (for example ``"review.closeout_cli"``)."""
    return f"{machinery_package()}.{suffix}"
