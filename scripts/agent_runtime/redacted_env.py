"""Environment mappings whose diagnostic representation contains names only.

Known limit: a failed direct credential-value comparison such as
``assert plan.env_overrides["K"] == "x\\nother"`` exposes the real multiline
value in pytest's text diff at both ``-q`` and ``-vv``.
Plan and mapping comparisons keep the credential values redacted.
JSON dumps and ``str(value)`` keep the real value, as do subprocess environments.
A plan subclass that defines its own ``__post_init__`` must call
``super().__post_init__()`` to retain environment redaction.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


class _RedactedValue(str):
    """Preserve string payloads while hiding values in rebuilt diagnostics."""

    def __repr__(self) -> str:
        return "<redacted>"


class RedactedEnv(dict[str, str]):
    """Redact the mapping and values when diagnostic tools rebuild plain dicts."""

    def __init__(self, values: Mapping[str, str] | Iterable[tuple[str, str]] = (), /, **kwargs: str) -> None:
        super().__init__()
        self.update(values, **kwargs)

    def __setitem__(self, key: str, value: str) -> None:
        super().__setitem__(key, _RedactedValue(value) if isinstance(value, str) else value)

    def update(self, values: Mapping[str, str] | Iterable[tuple[str, str]] = (), /, **kwargs: str) -> None:
        for key, value in dict(values, **kwargs).items():
            self[key] = value

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def __ior__(self, other: Mapping[str, str] | Iterable[tuple[str, str]]) -> RedactedEnv:
        self.update(other)
        return self

    def __repr__(self) -> str:
        return f"RedactedEnv(names={sorted(self)!r})"

    __str__ = __repr__

    def copy(self) -> RedactedEnv:
        return type(self)(self)

    def __reduce__(self):
        return type(self), (), None, None, iter(self.items())
