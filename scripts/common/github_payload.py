"""Strict decoding and typed access for GitHub payloads that feed a decision (#10792).

A caller that turns a GitHub response into a decision (an issue exists, a PR count admits a
dispatch, a pull request is absent, a PR text was scanned) must never read a malformed,
partial or failed payload as a clean answer. Every such payload goes through this module:

* :func:`decode` is strict JSON: duplicate object keys at any depth, ``NaN``/``Infinity`` and
  numbers that overflow to infinity are rejected, and the root must be the expected container.
* :func:`reject_failure_evidence` refuses a payload that carries explicit failure evidence at any
  depth (``error``/``errors`` members, a ``message`` + ``documentation_url`` error envelope,
  ``incomplete_results`` or ``hasNextPage`` other than ``false``) even when valid-looking success
  fields are present too.
* The ``require_*`` accessors read exact types: an int is never a bool and stays inside
  GitHub's 32-bit signed ``Int`` range unless the caller widens it (run ids are int64).
* :func:`require_complete_page` refuses a list that declares more data than it carries.

Every refusal raises :class:`UnavailablePayload` with a fixed, code-controlled ``reason``; each
caller maps it to its own unavailable outcome. Payload text is never echoed in a reason.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from typing import Any

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
INT64_MAX = 2**63 - 1


class UnavailablePayload(ValueError):
    """A payload that is not exactly the shape a decision needs; the answer is unknown."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"unavailable payload: {reason}")
        self.reason = reason


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise UnavailablePayload("duplicate_key")
        obj[key] = value
    return obj


def _reject_constant(_name: str) -> Any:
    raise UnavailablePayload("non_finite_number")


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise UnavailablePayload("non_finite_number")
    return value


def decode(text: Any, *, root: type | None = None) -> Any:
    """Strict ``json.loads`` of ``text``; ``root`` (``dict`` or ``list``) is the required container."""
    if not isinstance(text, str):
        raise UnavailablePayload("not_text")
    try:
        value = json.loads(
            text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant, parse_float=_finite_float
        )
    except UnavailablePayload:
        raise
    except (ValueError, RecursionError):
        raise UnavailablePayload("not_json") from None
    if root is not None and not isinstance(value, root):
        raise UnavailablePayload("root_type")
    return value


def reject_failure_evidence(value: Any) -> None:
    """Raise when any object at any depth carries failure or incompleteness evidence."""
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "error" in node or "errors" in node:
                raise UnavailablePayload("error_member")
            if "message" in node and "documentation_url" in node:
                raise UnavailablePayload("error_envelope")
            if "incomplete_results" in node and node["incomplete_results"] is not False:
                raise UnavailablePayload("incomplete_results")
            if "hasNextPage" in node and node["hasNextPage"] is not False:
                raise UnavailablePayload("has_next_page")
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


def parse(text: Any, *, root: type | None = None) -> Any:
    """:func:`decode` then :func:`reject_failure_evidence`: the default entry for a REST payload."""
    value = decode(text, root=root)
    reject_failure_evidence(value)
    return value


def require_object(value: Any, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UnavailablePayload(what)
    return value


def require_list(value: Any, what: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        raise UnavailablePayload(what)
    return value


def require_int(value: Any, what: str, *, minimum: int = INT32_MIN, maximum: int = INT32_MAX) -> int:
    """An exact int (never a bool, float or string) with ``minimum <= value <= maximum``."""
    if type(value) is not int or not minimum <= value <= maximum:
        raise UnavailablePayload(what)
    return value


def require_number(value: Any, what: str) -> float | int:
    """A finite int or float that is not a bool."""
    if type(value) not in (int, float) or not math.isfinite(value):
        raise UnavailablePayload(what)
    return value


def require_str(value: Any, what: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise UnavailablePayload(what)
    return value


def require_bool(value: Any, what: str) -> bool:
    if not isinstance(value, bool):
        raise UnavailablePayload(what)
    return value


def require_keys(obj: Any, what: str, keys: Iterable[str], *, exact: bool = False) -> dict[str, Any]:
    """``obj`` is an object holding every key in ``keys`` (and, when ``exact``, no other key)."""
    obj = require_object(obj, what)
    wanted = set(keys)
    if not wanted <= obj.keys() or (exact and obj.keys() != wanted):
        raise UnavailablePayload(what)
    return obj


def field(obj: dict[str, Any], key: str, what: str) -> Any:
    """The value of a required key (``null`` included; the accessor applied next decides)."""
    if key not in obj:
        raise UnavailablePayload(what)
    return obj[key]


def optional(obj: dict[str, Any], key: str, accessor: Callable[..., Any], what: str, **kwargs: Any) -> Any:
    """``None`` for an absent or ``null`` key; otherwise ``accessor(value, what, **kwargs)``."""
    value = obj.get(key)
    return None if value is None else accessor(value, what, **kwargs)


def require_complete_page(items: list[Any], total: int, what: str, *, page_size: int) -> None:
    """A first page of ``page_size`` must carry exactly ``min(total, page_size)`` items.

    Fewer items than that means the payload declares data it does not carry; more means the
    declared total is wrong. Either way the list is not the answer the caller asked for.
    """
    require_int(total, what, minimum=0)
    if len(items) != min(total, page_size):
        raise UnavailablePayload(what)


def graphql_errors(document: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``errors`` of a GraphQL response: ``[]`` when absent, else a validated non-empty list.

    The GraphQL specification (Response, ``errors``) says the entry is absent when no error
    was raised and is a non-empty list when present, each error carrying a ``message`` string;
    an empty, ``null`` or wrong-typed ``errors`` is therefore not a success document.
    """
    if "errors" not in document:
        return []
    errors = require_list(document["errors"], "errors", nonempty=True)
    for error in errors:
        require_str(field(require_object(error, "errors[]"), "message", "errors[].message"), "errors[].message")
    return errors
