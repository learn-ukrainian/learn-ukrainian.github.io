"""Checkout-relative machinery paths and module names.

The package directory's name comes from this file's own path, with symlinks
left unresolved, so a checkout-relative identity matches git and catalog paths.
A repository root joins :func:`checkout_relative`. A module's own name comes
from its spec when that spec is already package-qualified, and from the file
otherwise.
"""

from __future__ import annotations

from importlib.machinery import ModuleSpec
from pathlib import Path


def _parts_under_package(file: str, top: str) -> tuple[str, ...]:
    """Path parts of ``file`` below the package directory, without resolving it."""
    parts = Path(file).with_suffix("").parts
    if top not in parts:
        return parts
    start = len(parts) - 1 - parts[::-1].index(top) + 1
    return parts[start:]


def package_dir_name() -> str:
    """Name of the package directory that contains this file.

    ``Path.parents`` does not resolve symlinks, so the name is the one the
    checkout uses. A resolved realpath can name a different directory.
    """
    return Path(__file__).parents[1].name


def checkout_relative(*parts: str) -> Path:
    """Repository-relative path of a machinery file or directory.

    The result stays relative, so a caller can join it onto any checkout.
    It follows the package directory's name, including after a rename.
    """
    return Path(package_dir_name(), *parts)


def module_name(spec: ModuleSpec | None, file: str) -> str:
    """Dotted name of the module at ``file``, qualified from the package root.

    ``python -m`` and a normal import already carry that name on ``spec``.
    A file execution has no spec. A load that puts the package directory on
    ``sys.path`` (``ci.gate``) is qualified with the package directory's name.
    """
    top = package_dir_name()
    if spec is not None and spec.name and spec.name != "__main__":
        name = spec.name
        if name == top or name.startswith(f"{top}."):
            return name
        return f"{top}.{name}"
    parts = [top, *_parts_under_package(file, top)]
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)
