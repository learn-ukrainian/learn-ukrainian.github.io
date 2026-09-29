"""Runtime shard exporter verify tests, split for loadfile scheduling."""

from __future__ import annotations

import io
import json
import math
import random
import re
import shutil
import sys
from pathlib import Path

import pytest

from scripts.atlas import export_runtime_shards as exporter
from scripts.atlas.export_runtime_shards import verify_tree
from tests.test_export_runtime_shards import (
    _BAD_JSON_DOCS,
    _FAIL_CLOSED,
    _FAIL_CLOSED_JSON_DOCS,
    _HISTORICAL_CRASH,
    _JSON_DOCS,
    _VERIFY_CASES,
    _json_loads_outcome,
    _mutate,
    _outcome,
    _ref_verify_tree,
    _scan,
    _scan_outcome,
)

pytest_plugins = ("tests._export_runtime_shards_fixtures",)

@pytest.mark.parametrize("case", _VERIFY_CASES)
def test_streaming_verify_matches_historical_verify(verified_tree: Path, tmp_path: Path, case: str) -> None:
    out = tmp_path / "out"
    shutil.copytree(verified_tree, out)
    manifest_path = out / "atlas" / json.loads((out / "atlas" / "current.json").read_text())["manifestUrl"]
    manifest = json.loads(manifest_path.read_text())
    assert _outcome(verify_tree, out, manifest_path) == _outcome(_ref_verify_tree, out, manifest_path)
    _mutate(case, manifest_path.parent, manifest)
    expected = _outcome(_ref_verify_tree, out, manifest_path)
    actual = _outcome(verify_tree, out, manifest_path)
    if case in _HISTORICAL_CRASH:
        assert expected[0] not in ("ok", "ExportError"), expected
        assert actual[0] == "ExportError" and _HISTORICAL_CRASH[case] in actual[1], actual
    elif case in _FAIL_CLOSED:
        assert expected[0] == "ok", expected
        assert actual[0] == "ExportError" and _FAIL_CLOSED[case] in actual[1], actual
    else:
        assert actual == expected
    assert case in ("trailing-zero-padding", "second-gzip-member", "schema-version-float",
                    "schema-version-near-one", "duplicate-members-last-wins",
                    "bigint-overflow-surrogate-in-record", "extreme-numbers-in-record",
                    "extreme-exponent-duplicate-member", "extreme-exponent-deck") or actual[0] != "ok", actual


def test_verify_fast_pass_is_yajl() -> None:
    assert exporter._json_backend().backend_name == "yajl2_c"


@pytest.mark.parametrize("read_bytes", [1, 2, 3, 5, 6, 7, 13, 64, 1 << 16])
def test_json_stream_decodes_exactly_like_json_loads_at_every_read_size(read_bytes: int) -> None:
    for doc in _JSON_DOCS:
        assert _scan_outcome(doc, read_bytes) == _json_loads_outcome(doc), doc
        assert _scan_outcome(doc, read_bytes, exact_only=True) == _json_loads_outcome(doc), doc
        fast = exporter.scan_json_payload(io.BytesIO(doc), read_bytes=read_bytes)
        if re.search(rb"\\u[dD][89a-fA-F]", doc):
            assert not fast.values_exact, doc
        elif not re.search(rb"[0-9]{19}", doc):  # no exponent Decimal refuses, no integer int() refuses
            assert fast.values_exact, doc
    for doc in _BAD_JSON_DOCS:
        with pytest.raises(ValueError):
            json.loads(doc.decode("utf-8"))
        with pytest.raises(ValueError):
            _scan(doc, read_bytes)
        assert _scan_outcome(doc, read_bytes, exact_only=True) == ("invalid",), doc
    for doc in _FAIL_CLOSED_JSON_DOCS:
        json.loads(doc.decode("utf-8"))
        with pytest.raises(ValueError):
            _scan(doc, read_bytes)
        assert _scan_outcome(doc, read_bytes, exact_only=True) == ("invalid",), doc


def test_extreme_numbers_read_like_json_loads() -> None:
    """The reviewer's deck, and each class of number literal no ``Decimal`` or yajl conversion holds."""
    deck = exporter.scan_json_payload(io.BytesIO(b'{"deckVersion":"d","unused":1e-99999999999999999999}'))
    assert deck.is_object and not deck.values_exact  # yajl judged the syntax; values come from the exact pass
    cases = {
        b"1e-99999999999999999999": 0.0, b"-1e-99999999999999999999": -0.0, b"1e99999999999999999999": math.inf,
        b"-1e99999999999999999999": -math.inf, b"0e99999999999999999999": 0.0, b"-0e99999999999999999999": -0.0,
        b"0.000e-99999999999999999999": 0.0, b"1E+000000000000000000000000001": 10.0, b"-0": 0, b"-0.0": -0.0,
        b"9" * 4300: int("9" * 4300), b"-" + b"9" * 4300: -int("9" * 4300),
    }
    for literal, expected in cases.items():
        doc = b'{"schemaVersion":' + literal + b',"records":[' + literal + b"]}"
        scanned = _scan(doc, 64, summarize=lambda value: value)
        assert json.loads(doc)["schemaVersion"] == expected
        for value in (scanned.schema_version, scanned.rows[0]):
            assert type(value) is type(expected) and repr(value) == repr(expected), literal[:30]
    with pytest.raises(ValueError, match="integer string conversion"):
        json.loads(b"[" + b"9" * 4301 + b"]")
    with pytest.raises(ValueError, match="integer string conversion"):
        _scan(b"[" + b"9" * 4301 + b"]", 64)


@pytest.mark.parametrize("limit", [0, 640])
def test_integer_digit_limit_matches_json_loads_at_every_read_size(limit: int) -> None:
    """The yajl guard follows ``sys.get_int_max_str_digits()`` (0: no limit, 640: the smallest allowed)."""
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(limit)
    try:
        for digits in (639, 640, 641, 5000):
            doc = b'{"records":[-' + b"7" * digits + b',"' + b"7" * digits + b'",0.' + b"7" * digits + b"]}"
            for read_bytes in (1, 5, 64, 1 << 16):
                assert _scan_outcome(doc, read_bytes) == _json_loads_outcome(doc), (limit, digits, read_bytes)
    finally:
        sys.set_int_max_str_digits(previous)


def test_json_stream_matches_json_loads_on_mutated_documents() -> None:
    """Seeded differential: random documents and byte-level corruptions of them."""
    rng = random.Random(8672)
    tokens = [
        b"{", b"}", b"[", b"]", b",", b":", b'"', b"\\", b"u", b"d", b"8", b"0", b"1", b"-", b"+", b".", b"e",
        b" ", b"\t", b"\n", b"\x0b", b"\x0c", b"\x00", b"\x01", b"\xff", b"\xed", b"t", b"n", b"x",
        "я".encode(), b"\\ud800", b"\\udc00", b"\\ud83d\\ude00", b'"records"', b'"schemaVersion"',
        b"e99999999999999999999", b"e-99999999999999999999", b"1e99999999999999999999", b"9" * 4301, b"0" * 4301,
    ]

    def value(depth: int):
        choice = rng.randrange(9 if depth < 4 else 6)
        if choice == 0:
            return rng.randrange(-10**30, 10**30)
        if choice == 1:
            return rng.uniform(-1e6, 1e6)
        if choice == 2:
            return "".join(rng.choice('aя"\\/\n\t😀é 𐀀') for _ in range(rng.randrange(0, 12)))
        if choice in (3, 4, 5):
            return (True, False, None)[choice - 3]
        if choice in (6, 7):
            return [value(depth + 1) for _ in range(rng.randrange(0, 5))]
        return {str(value(depth + 1))[:6]: value(depth + 1) for _ in range(rng.randrange(0, 5))}

    for _ in range(3000):
        document = {"schemaVersion": 1, "records": [value(0) for _ in range(rng.randrange(0, 6))], "x": value(0)}
        raw = bytearray(json.dumps(document, ensure_ascii=True, indent=rng.choice([None, 1])).encode())
        for _ in range(rng.randrange(0, 4)):
            position = rng.randrange(len(raw) + 1)
            raw[position : position + rng.randrange(2)] = rng.choice(tokens)
        doc = bytes(raw[: rng.randrange(len(raw) + 1)] if rng.random() < 0.2 else raw)
        read_bytes = rng.choice([1, 3, 5, 8, 50])
        expected = _json_loads_outcome(doc)
        assert _scan_outcome(doc, read_bytes) == expected, doc
        assert _scan_outcome(doc, read_bytes, exact_only=True) == expected, doc
