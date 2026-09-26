"""``scripts.common.schema_check.check_schema`` keeps ``Draft202012Validator.check_schema`` semantics."""

from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator, SchemaError

from scripts.common import schema_check

VALID = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "required": ["a"]}


@pytest.fixture(autouse=True)
def _fresh_memo():
    schema_check._check_canonical.cache_clear()
    yield
    schema_check._check_canonical.cache_clear()


def _count_checks(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    calls: list[object] = []
    real = Draft202012Validator.check_schema

    def counting(schema, *args, **kwargs):
        calls.append(schema)
        return real(schema, *args, **kwargs)

    monkeypatch.setattr(Draft202012Validator, "check_schema", staticmethod(counting))
    return calls


def test_identical_content_is_checked_once_even_for_distinct_objects(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _count_checks(monkeypatch)
    for _ in range(3):
        schema_check.check_schema(copy.deepcopy(VALID))
    assert len(calls) == 1


def test_edited_content_is_checked_again_and_an_invalid_edit_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _count_checks(monkeypatch)
    schema_check.check_schema(VALID)
    edited = {**VALID, "required": "a"}  # ``required`` must be an array
    with pytest.raises(SchemaError):
        schema_check.check_schema(edited)
    assert len(calls) == 2


def test_an_invalid_schema_raises_on_every_call() -> None:
    invalid = {"type": "nonsense"}
    for _ in range(3):
        with pytest.raises(SchemaError):
            schema_check.check_schema(invalid)


def test_a_schema_that_does_not_round_trip_through_json_is_checked_directly_every_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _count_checks(monkeypatch)
    integer_key = {"type": "object", "x-meta": {1: 2}}  # JSON would rewrite the key to "1"
    schema_check.check_schema(integer_key)
    schema_check.check_schema(integer_key)
    assert len(calls) == 2


def test_json_coercion_never_turns_an_invalid_schema_valid() -> None:
    tuple_required = {"required": ("a",)}  # invalid as given; JSON would turn the tuple into a valid list
    for _ in range(2):
        with pytest.raises(SchemaError):
            schema_check.check_schema(tuple_required)
