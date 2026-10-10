"""Environment mappings whose diagnostic representation contains names only."""

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
