"""Environment mappings whose diagnostic representation contains names only."""

from __future__ import annotations

from dataclasses import fields


class RedactedEnv(dict[str, str]):
    """Keep ordinary dict behavior while redacting values in repr and str."""

    def __repr__(self) -> str:
        return f"RedactedEnv(names={sorted(self)!r})"

    __str__ = __repr__

    def copy(self) -> RedactedEnv:
        return type(self)(self)

    def __reduce__(self):
        return type(self), (), None, None, iter(self.items())


def env_safe_dataclass_eq(self: object, other: object) -> bool:
    """Preserve dataclass equality without pytest's generated-equality drill-down.

    Pytest recursively expands mappings for generated dataclass equality,
    rebuilding plain dicts that bypass RedactedEnv's representation.
    """
    if self.__class__ is not other.__class__:
        return NotImplemented
    names = tuple(field.name for field in fields(self) if field.compare)
    return tuple(getattr(self, name) for name in names) == tuple(getattr(other, name) for name in names)
