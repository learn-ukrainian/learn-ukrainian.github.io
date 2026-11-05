"""Compatibility module for shared runtime contracts, ``learn_ukrainian_v4_runtime.contracts``.

It stays a module of its own and forwards every attribute it does not define to the
canonical implementation. Patch the implementation module, never this one: a value set
here is not seen there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from learn_ukrainian_v4_runtime import contracts as _implementation

if not TYPE_CHECKING:
    # The forwarding is a runtime fact, as the ``sys.modules`` alias it replaces was, so
    # the type checker keeps the view of this module it had then.

    def __getattr__(name: str) -> Any:
        return getattr(_implementation, name)

    def __dir__() -> list[str]:
        return sorted({*globals(), *dir(_implementation)})
