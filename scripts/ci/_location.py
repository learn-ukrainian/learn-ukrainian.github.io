"""Checkout-relative machinery paths and module names.

The package directory's name comes from ``machinery_root`` (where this code
lives), never from a spelled package name. A repository root joins
:func:`checkout_relative`. A module's own name comes from its spec when that
spec is already package-qualified, and from the file otherwise.
"""

from __future__ import annotations

from importlib.machinery import ModuleSpec
from pathlib import Path

from scripts.common.repo_root import machinery_path, machinery_root


def checkout_relative(*parts: str) -> Path:
    """Repository-relative path of a machinery file or directory.

    The result stays relative, so a caller can join it onto any checkout.
    It follows the package directory's name, including after a rename.
    """
    relative = "/".join(parts)
    located = machinery_path(relative).relative_to(machinery_root().parent)
    return Path(located.as_posix())


def module_name(spec: ModuleSpec | None, file: str) -> str:
    """Dotted name of the module at ``file``, qualified from the package root.

    ``python -m`` and a normal import already carry that name on ``spec``.
    A file execution has no spec. A load that puts the package directory on
    ``sys.path`` (``ci.gate``) is qualified with the package directory's name.
    """
    top = machinery_root().name
    if spec is not None and spec.name and spec.name != "__main__":
        name = spec.name
        if name == top or name.startswith(f"{top}."):
            return name
        return f"{top}.{name}"
    relative = Path(file).resolve().relative_to(machinery_root()).with_suffix("")
    parts = [top, *relative.parts]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)
