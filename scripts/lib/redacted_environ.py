"""Hide environment values when an env object is formatted.

``os.environ`` is an ``os._Environ`` mapping. Its default ``repr`` prints every
value, so a test failure or a debug log that formats the object publishes
secrets. Formatting the object shows only how many entries it has. Lookups,
iteration, and subprocess use of the mapping still return the real values.

``copy`` returns a ``dict`` subclass with the same formatting rule, because
callers pass that copy to child processes and also print it.
"""

from __future__ import annotations

import os

_INSTALLED = False


class RedactedEnvDict(dict[str, str]):
    """A real environment copy whose formatting omits values."""

    def __repr__(self) -> str:
        return f"<redacted environ n={len(self)}>"

    __str__ = __repr__

    def __format__(self, spec: str) -> str:
        return repr(self)

    def copy(self) -> RedactedEnvDict:
        return RedactedEnvDict(self)


def install_redacted_environ_repr() -> None:
    """Make ``os.environ`` formatting omit values. Safe to call more than once."""
    global _INSTALLED
    cls = type(os.environ)
    if _INSTALLED or getattr(cls, "_lu_redacted_environ", False):
        _INSTALLED = True
        return

    def _hide(self: object) -> str:
        try:
            count = len(self)  # type: ignore[arg-type]
        except TypeError:
            count = 0
        return f"<redacted environ n={count}>"

    def _format(self: object, _spec: str) -> str:
        return _hide(self)

    def _copy(self: os._Environ) -> RedactedEnvDict:
        return RedactedEnvDict(self)

    cls.__repr__ = _hide  # type: ignore[method-assign]
    cls.__str__ = _hide  # type: ignore[method-assign]
    cls.__format__ = _format  # type: ignore[method-assign]
    cls.copy = _copy  # type: ignore[method-assign]
    cls._lu_redacted_environ = True  # type: ignore[attr-defined]
    _INSTALLED = True
