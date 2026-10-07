"""Snapshot and restore import state for tests that evict modules.

Importing a child stores it in ``sys.modules`` and rebinds the same name on
the parent package. Putting the previous module back into ``sys.modules``
leaves that package attribute pointing at the fresh module, so ``from parent import
child`` and a later import through ``sys.modules`` can disagree (#9942).

The snapshot covers each named module, including names that are absent.
A stored ``None`` (the ``sys.modules[name] = None`` sentinel) is not absence.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from contextlib import contextmanager
from typing import NamedTuple

_ABSENT = object()


class _ImportBinding(NamedTuple):
    name: str
    module: object
    parent_name: str | None
    child: str | None
    attr: object


def _snapshot(module_names: tuple[str, ...]) -> tuple[_ImportBinding, ...]:
    bindings: list[_ImportBinding] = []
    for name in dict.fromkeys(module_names):
        parent_name: str | None = None
        child: str | None = None
        attr: object = _ABSENT
        if "." in name:
            parent_name, child = name.rsplit(".", 1)
            parent = sys.modules.get(parent_name)
            # The import machinery writes the child into the parent package
            # __dict__. Read that entry so a package __getattr__ cannot import
            # the child as a side effect of taking the snapshot.
            if isinstance(parent, types.ModuleType):
                attr = parent.__dict__.get(child, _ABSENT)
        module = sys.modules.get(name, _ABSENT)
        bindings.append(_ImportBinding(name, module, parent_name, child, attr))
    return tuple(bindings)


def _restore(bindings: tuple[_ImportBinding, ...]) -> None:
    for binding in bindings:
        if binding.module is _ABSENT:
            sys.modules.pop(binding.name, None)
        else:
            sys.modules[binding.name] = binding.module
    # Repair attributes after the cache, on the package object that is live
    # now. A child import rebinds that object, and the package itself may have
    # been imported only inside the block.
    for binding in bindings:
        if binding.parent_name is None or binding.child is None:
            continue
        parent = sys.modules.get(binding.parent_name)
        if not isinstance(parent, types.ModuleType):
            continue
        if binding.attr is _ABSENT:
            parent.__dict__.pop(binding.child, None)
        else:
            parent.__dict__[binding.child] = binding.attr


@contextmanager
def restore_import_state(*module_names: str) -> Iterator[None]:
    """Restore ``sys.modules`` entries and parent-package attributes on exit."""
    bindings = _snapshot(module_names)
    try:
        yield
    finally:
        _restore(bindings)
