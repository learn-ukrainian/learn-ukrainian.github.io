"""The shared strict GitHub payload boundary (#10792): one test per mechanical guarantee."""

from __future__ import annotations

import pytest

from scripts.common import github_payload as gp

# --- 1. strict JSON decoding -------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1, "a": 2}',
        '{"comments": [{"body": "secret"}], "comments": []}',
        '{"outer": {"inner": 1, "inner": 1}}',
        '[{"number": 5}, {"number": 6, "number": 7}]',
        '{"a": [[{"deep": {"x": 1, "x": 1}}]]}',
    ],
)
def test_duplicate_keys_at_any_depth_are_unavailable(text: str) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode(text)
    assert excinfo.value.reason == "duplicate_key"


def test_duplicate_key_reason_never_echoes_payload_text() -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode('{"secret-token-abc": 1, "secret-token-abc": 2}')
    assert "secret" not in str(excinfo.value)


@pytest.mark.parametrize(
    "text", ["NaN", "[Infinity]", '{"a": -Infinity}', '{"a": 1e400}', "[-1e400]", '{"a": {"b": NaN}}']
)
def test_non_finite_numbers_are_unavailable(text: str) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode(text)
    assert excinfo.value.reason == "non_finite_number"


@pytest.mark.parametrize("text", ["", " ", "not json", "{", "[1,", "\x00", '{"a": 1} trailing', "[" * 100_000])
def test_text_that_is_not_one_json_value_is_unavailable(text: str) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode(text)
    assert excinfo.value.reason == "not_json"


@pytest.mark.parametrize("value", [None, b"{}", 5, ["{}"], {"a": 1}])
def test_output_that_is_not_text_is_unavailable(value: object) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode(value)
    assert excinfo.value.reason == "not_text"


@pytest.mark.parametrize(("text", "root"), [("[]", dict), ("{}", list), ("null", dict), ("5", list), ('"x"', dict)])
def test_wrong_root_container_is_unavailable(text: str, root: type) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.decode(text, root=root)
    assert excinfo.value.reason == "root_type"


def test_valid_json_decodes_unchanged() -> None:
    assert gp.decode(' {"a": [1, 2.5, "x", null, true]} ', root=dict) == {"a": [1, 2.5, "x", None, True]}
    assert gp.decode("[]", root=list) == []
    assert gp.decode("null") is None


# --- 2. explicit failure evidence wins ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ({"total_count": 3, "error": "github_rate_limited"}, "error_member"),
        ({"title": "t", "errors": []}, "error_member"),
        ({"data": {"repository": {"errors": None}}}, "error_member"),
        ([{"number": 5}, {"number": 6, "meta": {"error": {"message": "x"}}}], "error_member"),
        ({"message": "Not Found", "documentation_url": "https://docs.github.com"}, "error_envelope"),
        ({"items": [{"message": "x", "documentation_url": "y", "number": 1}]}, "error_envelope"),
        ({"total_count": 0, "incomplete_results": True}, "incomplete_results"),
        ({"incomplete_results": None}, "incomplete_results"),
        ({"incomplete_results": "false"}, "incomplete_results"),
        ({"comments": [], "pageInfo": {"hasNextPage": True}}, "has_next_page"),
        ({"nodes": [], "pageInfo": {"hasNextPage": None}}, "has_next_page"),
        ([[{"hasNextPage": 1}]], "has_next_page"),
    ],
)
def test_failure_evidence_at_any_depth_is_unavailable(value: object, reason: str) -> None:
    with pytest.raises(gp.UnavailablePayload) as excinfo:
        gp.reject_failure_evidence(value)
    assert excinfo.value.reason == reason


@pytest.mark.parametrize(
    "value",
    [
        {"head_commit": {"message": "fix: x"}},  # a commit message alone is not an error envelope
        {"total_count": 3, "incomplete_results": False, "items": []},
        {"pageInfo": {"hasNextPage": False}},
        [1, "error", {"body": "errors in the text are data"}],
        None,
    ],
)
def test_payloads_without_failure_evidence_pass(value: object) -> None:
    gp.reject_failure_evidence(value)


def test_parse_combines_strict_decoding_and_failure_evidence() -> None:
    assert gp.parse('{"total_count": 1, "incomplete_results": false}', root=dict)["total_count"] == 1
    with pytest.raises(gp.UnavailablePayload, match="error_member"):
        gp.parse('{"total_count": 1, "incomplete_results": false, "error": "x"}', root=dict)
    with pytest.raises(gp.UnavailablePayload, match="duplicate_key"):
        gp.parse('{"total_count": 30, "total_count": 0}', root=dict)


# --- 3. typed accessors ------------------------------------------------------------------------


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, [1], {"n": 1}, 10**100, 2**31, -(2**31) - 1])
def test_require_int_accepts_only_exact_32_bit_ints(value: object) -> None:
    with pytest.raises(gp.UnavailablePayload):
        gp.require_int(value, "n")


def test_require_int_bounds() -> None:
    assert gp.require_int(2**31 - 1, "n") == 2**31 - 1
    assert gp.require_int(-(2**31), "n") == -(2**31)
    assert gp.require_int(1, "n", minimum=1) == 1
    with pytest.raises(gp.UnavailablePayload):
        gp.require_int(0, "n", minimum=1)
    assert gp.require_int(2**40, "id", minimum=0, maximum=gp.INT64_MAX) == 2**40
    with pytest.raises(gp.UnavailablePayload):
        gp.require_int(2**63, "id", minimum=0, maximum=gp.INT64_MAX)


def test_require_str_bool_list_object_number() -> None:
    assert gp.require_str("x", "s") == "x"
    assert gp.require_str("", "s", nonempty=False) == ""
    for bad in ("", None, 5, ["x"], b"x"):
        with pytest.raises(gp.UnavailablePayload):
            gp.require_str(bad, "s")
    assert gp.require_bool(False, "b") is False
    for bad in (0, 1, "false", None):
        with pytest.raises(gp.UnavailablePayload):
            gp.require_bool(bad, "b")
    assert gp.require_list([], "l") == []
    with pytest.raises(gp.UnavailablePayload):
        gp.require_list([], "l", nonempty=True)
    for bad in ({}, None, "[]", ()):
        with pytest.raises(gp.UnavailablePayload):
            gp.require_list(bad, "l")
    for bad in ([], None, "x"):
        with pytest.raises(gp.UnavailablePayload):
            gp.require_object(bad, "o")
    assert gp.require_number(1.5, "n") == 1.5
    for bad in (True, "1", None, float("nan"), float("inf")):
        with pytest.raises(gp.UnavailablePayload):
            gp.require_number(bad, "n")


def test_require_keys_field_and_optional() -> None:
    obj = {"a": 1, "b": None}
    assert gp.require_keys(obj, "o", ("a",)) is obj
    assert gp.require_keys(obj, "o", ("a", "b"), exact=True) is obj
    with pytest.raises(gp.UnavailablePayload):
        gp.require_keys(obj, "o", ("a",), exact=True)
    with pytest.raises(gp.UnavailablePayload):
        gp.require_keys(obj, "o", ("c",))
    with pytest.raises(gp.UnavailablePayload):
        gp.require_keys([], "o", ())
    assert gp.field(obj, "b", "o.b") is None
    with pytest.raises(gp.UnavailablePayload):
        gp.field(obj, "c", "o.c")
    assert gp.optional(obj, "b", gp.require_int, "o.b") is None
    assert gp.optional(obj, "c", gp.require_int, "o.c") is None
    assert gp.optional(obj, "a", gp.require_int, "o.a", minimum=1) == 1
    with pytest.raises(gp.UnavailablePayload):
        gp.optional({"a": "1"}, "a", gp.require_int, "o.a")


def test_one_exception_type_for_every_refusal() -> None:
    assert issubclass(gp.UnavailablePayload, ValueError)
    assert gp.UnavailablePayload("why").reason == "why"


# --- 4. completeness contracts -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("count", "total", "page_size"),
    [(0, 1, 30), (1, 0, 30), (29, 40, 30), (31, 40, 30), (0, 30, 1), (2, 2, 1)],
)
def test_a_page_that_declares_more_or_less_than_it_carries_is_unavailable(count: int, total: int, page_size: int) -> None:
    with pytest.raises(gp.UnavailablePayload):
        gp.require_complete_page([{}] * count, total, "page", page_size=page_size)


@pytest.mark.parametrize(("count", "total", "page_size"), [(0, 0, 30), (3, 3, 30), (30, 45, 30), (1, 30, 1)])
def test_a_complete_first_page_passes(count: int, total: int, page_size: int) -> None:
    gp.require_complete_page([{}] * count, total, "page", page_size=page_size)


@pytest.mark.parametrize("total", [True, -1, 1.0, "1", None, 10**100])
def test_a_page_total_must_be_an_exact_count(total: object) -> None:
    with pytest.raises(gp.UnavailablePayload):
        gp.require_complete_page([], total, "page", page_size=30)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "document",
    [
        {"errors": []},
        {"errors": None},
        {"errors": {"message": "x"}},
        {"errors": [{}]},
        {"errors": [{"message": ""}]},
        {"errors": [{"message": 5}]},
        {"errors": ["x"]},
    ],
)
def test_graphql_errors_entry_must_be_a_non_empty_list_of_messages(document: dict) -> None:
    with pytest.raises(gp.UnavailablePayload):
        gp.graphql_errors(document)


def test_graphql_errors_absent_or_valid() -> None:
    assert gp.graphql_errors({"data": {}}) == []
    errors = [{"message": "boom", "type": "X"}]
    assert gp.graphql_errors({"data": None, "errors": errors}) == errors
