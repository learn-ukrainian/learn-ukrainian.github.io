"""CLI behavior for the pinned literary year inventory.

Coordinates, classes and counts below are hand-computed from the fixture shape.
SHA-256 values use hashlib, the definition of the digest, not the inventory module.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "audit" / "literary_year_inventory.py"
DOT = "\u00b7"
NON_CLAIM = "Literal token equality does not establish source provenance, a birth date, or a publication date."
NAME_MATCH = "author_display_name_equals_scraper_name"
NAME_MISS = "author_display_name_unmatched"
YEAR_EQUAL = "label_year_token_equals_scraper_years_start"
YEAR_DIFFER = "label_year_token_differs_from_scraper_years_start"
YEAR_ABSENT = "label_year_token_absent"
YEAR_UNCERTIFIED = "label_year_token_present_unmatched_author_not_certified"
LABEL_MISSING = "label_missing"
LABEL_NON_STRING = "label_non_string"
LABEL_UNKNOWN = "label_unknown"
EQUAL_CLASSES = [NAME_MATCH, YEAR_EQUAL]
DIFFER_CLASSES = [NAME_MATCH, YEAR_DIFFER]
ABSENT_CLASSES = [NAME_MATCH, YEAR_ABSENT]
UNMATCHED_CLASSES = [NAME_MISS, YEAR_UNCERTIFIED]
MISSING_CLASSES = [LABEL_MISSING, LABEL_UNKNOWN]
NON_STRING_CLASSES = [LABEL_NON_STRING, LABEL_UNKNOWN]

MAIN_SCRAPER = (
    'META = {"meta": {"note": "skip"}}\n'
    "P1_AUTHORS = {\n"
    '    "one": {"name": "Author One", "years": "1900-1980"},\n'
    '    "two": {"name": "Author Two", "years": "1910-1990"},\n'
    '    "dup_a": {"name": "Author Dup", "years": "1800-1900"},\n'
    '    "dup_b": {"name": "Author Dup", "years": "2000-2010"},\n'
    '    "en": {"name": "Author En", "years": "1899\u20131950"},\n'
    "}\n"
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write(path: Path, raw: bytes) -> str:
    path.write_bytes(raw)
    return _sha256(raw)


def _write_json(path: Path, payload: object) -> str:
    return _write(path, json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _error(code: str) -> bytes:
    return json.dumps({"error": code}, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"


def _inprocess(args: list[str]) -> tuple[int, bytes, bytes]:
    from scripts.audit.literary_year_inventory import main

    out_buf = io.BytesIO()
    err_buf = io.BytesIO()
    stdout = io.TextIOWrapper(out_buf, encoding="utf-8", newline="\n")
    stderr = io.TextIOWrapper(err_buf, encoding="utf-8", newline="\n")
    previous = os.environ.get("COLUMNS")
    os.environ["COLUMNS"] = "80"
    saved_out, saved_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout, stderr
    try:
        code = main(args)
    finally:
        sys.stdout, sys.stderr = saved_out, saved_err
        if previous is None:
            os.environ.pop("COLUMNS", None)
        else:
            os.environ["COLUMNS"] = previous
        stdout.flush()
        stderr.flush()
        stdout.detach()
        stderr.detach()
    return code, out_buf.getvalue(), err_buf.getvalue()


def run_cli(args: list[str]) -> tuple[int, bytes, bytes]:
    """Run the script in a child process and again in-process; require the same bytes."""
    env = os.environ.copy()
    env["COLUMNS"] = "80"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
        env=env,
        timeout=60,
    )
    code, out, err = _inprocess(args)
    assert (code, out, err) == (proc.returncode, proc.stdout, proc.stderr)
    return proc.returncode, proc.stdout, proc.stderr


def _pins(manifest: Path, manifest_sha: str, scraper: Path, scraper_sha: str) -> list[str]:
    return [
        "--manifest",
        str(manifest),
        "--manifest-sha256",
        manifest_sha,
        "--scraper",
        str(scraper),
        "--scraper-sha256",
        scraper_sha,
    ]


def _packed(
    ordinal: int,
    coordinate: list[str | int],
    value_type: str,
    author: str | None,
    year: str | None,
    classes: list[str],
    witnesses: dict[str, object],
    label: str | None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "classes": classes,
        "coordinate": coordinate,
        "label_sha256": None if label is None else _sha256(label.encode("utf-8")),
        "label_value_type": value_type,
        "ordinal": ordinal,
        "parsed_author": author,
        "parsed_year": year,
    }
    row.update(witnesses)
    return row


def _reject_nonstandard(token: str) -> None:
    raise AssertionError(token)


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _load_success(stdout: bytes) -> dict[str, object]:
    assert stdout.endswith(b"\n")
    document = json.loads(stdout, parse_constant=_reject_nonstandard)
    assert isinstance(document, dict)
    assert _canonical(document) + b"\n" == stdout
    return document


def _assert_typed_refusal(outcome: tuple[int, bytes, bytes], error_code: str, *hidden: bytes) -> None:
    code, stdout, stderr = outcome
    assert code == 1
    assert stdout == b""
    assert stderr == _error(error_code)
    assert b"Traceback" not in stderr
    for secret in hidden:
        assert secret not in stderr


def _attestation(chunk: str, label: object | None = None, **extra: object) -> dict[str, object]:
    body: dict[str, object] = {"chunk_id": chunk, "source": "literary_fts"}
    if label is not None or "source_label" in extra:
        body["source_label"] = extra.pop("source_label", label)
    body.update(extra)
    return body


@pytest.fixture
def main_inputs(tmp_path: Path) -> tuple[Path, str, Path, str]:
    manifest = {
        "entries": [
            {
                "enrichment": {
                    "literary_attestation": _attestation(
                        "c0",
                        f"Author One {DOT} Work A {DOT} 1900",
                        source_url="https://example.test/0",
                        text="SECRET_BODY_TEXT",
                    )
                }
            },
            {
                "enrichment": {
                    "literary_attestation": _attestation(
                        "c1",
                        f"Author One {DOT} Work A {DOT} 1900",
                        body="SECRET_BODY_TEXT",
                    )
                }
            },
            {"enrichment": {"literary_attestation": _attestation("c2", f"Author Two {DOT} Work B {DOT} 1911")}},
            {"enrichment": {"literary_attestation": _attestation("c3", f"Nobody N. {DOT} Work C {DOT} 1900")}},
            {"enrichment": {"literary_attestation": _attestation("c4")}},
            {"enrichment": {"literary_attestation": _attestation("c5", source_label=None)}},
            {"enrichment": {"literary_attestation": _attestation("c6", source_label=1900)}},
            {"enrichment": {"literary_attestation": _attestation("c7", f"Author One {DOT} missing year")}},
            {"enrichment": {"literary_attestation": _attestation("c8", f"Author Dup {DOT} Later Title {DOT} 2000")}},
            {"enrichment": {"literary_attestation": _attestation("c9", f"Author Dup {DOT} Early Title {DOT} 1800")}},
            {"enrichment": {"literary_attestation": _attestation("c10", f"Author En {DOT} Dash Title {DOT} 1899")}},
            {
                "enrichment": {
                    "literary_attestation": _attestation(
                        "c11",
                        f"Author One {DOT} Super Title {DOT} \u00b9\u2079\u2070\u2070",
                    )
                }
            },
            {
                "enrichment": {
                    "literary_attestation": {
                        "source": "not_literary_fts",
                        "source_label": f"Author One {DOT} Work A {DOT} 1900",
                        "text": "OTHER_SOURCE_SECRET",
                    }
                }
            },
            {
                "enrichment": {
                    "literary_attestation": [
                        {
                            "source": "literary_fts",
                            "source_label": f"Author One {DOT} Work A {DOT} 1900",
                            "text": "LIST_SECRET",
                        }
                    ]
                }
            },
        ],
        "before": {
            "literary_attestation": _attestation(
                "child",
                f"Author One {DOT} Child Title {DOT} 1900",
                text="CHILD_SECRET_BODY",
            )
        },
        "literary_attestation": {
            "chunk_id": "root",
            "nested": {
                "literary_attestation": _attestation(
                    "inner",
                    f"Author Two {DOT} Inner Title {DOT} 1910",
                    text="INNER_SECRET_BODY",
                )
            },
            "source": "literary_fts",
            "source_label": f"Author One {DOT} Root Title {DOT} 1900",
            "text": "ROOT_SECRET_BODY",
        },
    }
    manifest_path = tmp_path / "manifest.json"
    scraper_path = tmp_path / "scraper.py"
    return (
        manifest_path,
        _write_json(manifest_path, manifest),
        scraper_path,
        _write(scraper_path, MAIN_SCRAPER.encode("utf-8")),
    )


def _main_rows() -> list[dict[str, object]]:
    def at(index: int) -> list[str | int]:
        return ["entries", index, "enrichment", "literary_attestation"]

    def witness(chunk: str, **extra: object) -> dict[str, object]:
        found: dict[str, object] = {"chunk_id": chunk, "source": "literary_fts"}
        found.update(extra)
        return found

    # Walk order: the root object's own attestation, then entries, then "before",
    # then the nested attestation inside the root attestation.
    return [
        _packed(
            0,
            ["literary_attestation"],
            "str",
            "Author One",
            "1900",
            EQUAL_CLASSES,
            witness("root"),
            f"Author One {DOT} Root Title {DOT} 1900",
        ),
        _packed(
            1,
            at(0),
            "str",
            "Author One",
            "1900",
            EQUAL_CLASSES,
            witness("c0", source_url="https://example.test/0"),
            f"Author One {DOT} Work A {DOT} 1900",
        ),
        _packed(
            2,
            at(1),
            "str",
            "Author One",
            "1900",
            EQUAL_CLASSES,
            witness("c1"),
            f"Author One {DOT} Work A {DOT} 1900",
        ),
        _packed(
            3, at(2), "str", "Author Two", "1911", DIFFER_CLASSES, witness("c2"), f"Author Two {DOT} Work B {DOT} 1911"
        ),
        _packed(
            4,
            at(3),
            "str",
            "Nobody N.",
            "1900",
            UNMATCHED_CLASSES,
            witness("c3"),
            f"Nobody N. {DOT} Work C {DOT} 1900",
        ),
        _packed(5, at(4), "missing", None, None, MISSING_CLASSES, witness("c4"), None),
        _packed(6, at(5), "null", None, None, NON_STRING_CLASSES, witness("c5"), None),
        _packed(7, at(6), "int", None, None, NON_STRING_CLASSES, witness("c6"), None),
        _packed(
            8,
            at(7),
            "str",
            "Author One",
            None,
            ABSENT_CLASSES,
            witness("c7"),
            f"Author One {DOT} missing year",
        ),
        _packed(
            9,
            at(8),
            "str",
            "Author Dup",
            "2000",
            EQUAL_CLASSES,
            witness("c8"),
            f"Author Dup {DOT} Later Title {DOT} 2000",
        ),
        _packed(
            10,
            at(9),
            "str",
            "Author Dup",
            "1800",
            DIFFER_CLASSES,
            witness("c9"),
            f"Author Dup {DOT} Early Title {DOT} 1800",
        ),
        _packed(
            11,
            at(10),
            "str",
            "Author En",
            "1899",
            DIFFER_CLASSES,
            witness("c10"),
            f"Author En {DOT} Dash Title {DOT} 1899",
        ),
        _packed(
            12,
            at(11),
            "str",
            "Author One",
            "\u00b9\u2079\u2070\u2070",
            DIFFER_CLASSES,
            witness("c11"),
            f"Author One {DOT} Super Title {DOT} \u00b9\u2079\u2070\u2070",
        ),
        _packed(
            13,
            ["before", "literary_attestation"],
            "str",
            "Author One",
            "1900",
            EQUAL_CLASSES,
            witness("child"),
            f"Author One {DOT} Child Title {DOT} 1900",
        ),
        _packed(
            14,
            ["literary_attestation", "nested", "literary_attestation"],
            "str",
            "Author Two",
            "1910",
            EQUAL_CLASSES,
            witness("inner"),
            f"Author Two {DOT} Inner Title {DOT} 1910",
        ),
    ]


def test_help_documents_pins_stdout_and_no_side_effects() -> None:
    code, stdout, stderr = run_cli(["--help"])

    assert code == 0
    assert stderr == b""
    text = " ".join(stdout.decode("utf-8").split())
    assert "--manifest" in text
    assert "--manifest-sha256" in text
    assert "--scraper" in text
    assert "--scraper-sha256" in text
    assert "64 hexadecimal" in text
    assert "no default" in text.lower() or "No default" in text
    assert "stdout" in text
    assert "does not write" in text
    assert "not imported or executed" in text
    assert "U+00B7" in text
    assert "last duplicate name wins" in text
    assert "last duplicate key" in text
    assert "Exit codes:" in text
    assert "#10853" in text
    assert "str.isdigit" in text
    assert "finite numbers" in text
    assert "Objects, arrays" in text
    assert "limits are left unchanged" in text


def test_synthetic_fixture_preserves_slots_classes_and_digest(main_inputs: tuple[Path, str, Path, str]) -> None:
    manifest, manifest_sha, scraper, scraper_sha = main_inputs
    before_manifest = manifest.read_bytes()
    before_scraper = scraper.read_bytes()
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert code == 0
    assert stderr == b""
    assert manifest.read_bytes() == before_manifest
    assert scraper.read_bytes() == before_scraper
    document = _load_success(stdout)
    expected_rows = _main_rows()
    assert document["rows"] == expected_rows
    assert document["rows_membership_sha256"] == _sha256(_canonical(expected_rows))
    assert document["denominator"] == {"literary_fts_dictionary_attestations": 15}
    assert document["probe_compatible_counts"] == {
        "labels": 15,
        "labels_ukrlib_author": 11,
        "labels_ukrlib_year_eq_author_years_start": 6,
        "labels_with_year": 11,
        "ukrlib_authors_parsed": 4,
    }
    assert document["class_counts"] == {
        NAME_MATCH: 11,
        NAME_MISS: 1,
        LABEL_MISSING: 1,
        LABEL_NON_STRING: 2,
        LABEL_UNKNOWN: 3,
        YEAR_ABSENT: 1,
        YEAR_DIFFER: 4,
        YEAR_EQUAL: 6,
        YEAR_UNCERTIFIED: 1,
    }
    assert document["excluded_literary_attestation_counts"] == {
        "list_valued": 1,
        "other_non_dict": 0,
        "other_source": 1,
    }
    assert document["scraper_author_records"] == {
        "collision_count": 1,
        "distinct_name_count": 4,
        "record_count": 5,
    }
    assert document["inputs"] == {"manifest_sha256": manifest_sha, "scraper_sha256": scraper_sha}
    assert document["kind"] == "literary_year_inventory"
    assert document["non_claim"] == NON_CLAIM
    limitation = document["limitation"]
    assert isinstance(limitation, str)
    assert "U+00B7" in limitation
    assert "en dash" in limitation
    assert "last duplicate key" in limitation
    assert "literary_texts" in limitation
    equality_ordinals = [
        row["ordinal"]
        for row in document["rows"]
        if YEAR_EQUAL in row["classes"]  # type: ignore[operator]
    ]
    assert equality_ordinals == [0, 1, 2, 9, 13, 14]
    for forbidden in (b'"text":', b'"body":', b'"source_label":', b"SECRET_", b"dated", b"authentic", b"birth_year"):
        assert forbidden not in stdout
    allowed = {
        "chunk_id",
        "classes",
        "coordinate",
        "label_sha256",
        "label_value_type",
        "ordinal",
        "parsed_author",
        "parsed_year",
        "source",
        "source_url",
    }
    for row in document["rows"]:
        assert set(row) <= allowed  # type: ignore[arg-type]


def test_repeat_run_is_byte_identical(main_inputs: tuple[Path, str, Path, str]) -> None:
    manifest, manifest_sha, scraper, scraper_sha = main_inputs
    args = _pins(manifest, manifest_sha, scraper, scraper_sha)

    first = run_cli(args)
    second = run_cli(args)

    assert first == second
    assert first[0] == 0


def test_uppercase_pin_is_accepted_and_recorded_lowercase(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_sha = _write_json(manifest, {})
    scraper_sha = _write(scraper, b'P1_AUTHORS = {"one": {"name": "Author One", "years": "1900-1980"}}\n')
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha.upper(), scraper, scraper_sha.upper()))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    assert document["inputs"] == {"manifest_sha256": manifest_sha, "scraper_sha256": scraper_sha}
    assert document["denominator"] == {"literary_fts_dictionary_attestations": 0}
    assert document["probe_compatible_counts"]["ukrlib_authors_parsed"] == 1  # type: ignore[index]


def test_open_ended_years_and_scalar_witnesses(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    label = f"  Author Open  {DOT} Title {DOT}  1930 "
    manifest_sha = _write_json(
        manifest,
        {
            "literary_attestation": {
                "chunk_id": "chunk-open",
                "source": "literary_fts",
                "source_label": label,
                "source_url": None,
                "text": "SECRET_BODY_TEXT",
            }
        },
    )
    scraper_sha = _write(scraper, b'P1_AUTHORS = {"open": {"name": "Author Open", "years": "1930-"}}\n')
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    expected = _packed(
        0,
        ["literary_attestation"],
        "str",
        "Author Open",
        "1930",
        EQUAL_CLASSES,
        {"chunk_id": "chunk-open", "source": "literary_fts", "source_url": None},
        label,
    )
    assert document["rows"] == [expected]
    assert document["probe_compatible_counts"]["labels_ukrlib_year_eq_author_years_start"] == 1  # type: ignore[index]
    assert b"SECRET_BODY_TEXT" not in stdout


def _refusal_inputs(tmp_path: Path, raw: bytes) -> tuple[Path, bytes, Path, bytes, list[str]]:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    scraper_raw = b"pass\n"
    manifest_sha = _write(manifest, raw)
    scraper_sha = _write(scraper, scraper_raw)
    return manifest, raw, scraper, scraper_raw, _pins(manifest, manifest_sha, scraper, scraper_sha)


@pytest.mark.parametrize(
    ("field", "value", "hidden"),
    [
        ("chunk_id", {"secret": "NESTED_SECRET"}, b"NESTED_SECRET"),
        ("chunk_id", ["SECRET_LIST"], b"SECRET_LIST"),
        ("source_url", {"secret": "URL_SECRET"}, b"URL_SECRET"),
        ("source_url", ["URL_LIST"], b"URL_LIST"),
    ],
)
def test_compound_witness_values_are_refused(tmp_path: Path, field: str, value: object, hidden: bytes) -> None:
    manifest, raw, scraper, scraper_raw, args = _refusal_inputs(
        tmp_path,
        json.dumps({"literary_attestation": {"source": "literary_fts", "source_label": "Alpha", field: value}}).encode(
            "utf-8"
        ),
    )
    _assert_typed_refusal(run_cli(args), "witness_value_unsupported", hidden)
    assert manifest.read_bytes() == raw
    assert scraper.read_bytes() == scraper_raw


def test_present_scalar_and_missing_witnesses_are_preserved(tmp_path: Path) -> None:
    specs: list[dict[str, object]] = [
        {},
        {"chunk_id": None},
        {"source_url": None},
        {"chunk_id": None, "source_url": None},
        {"chunk_id": "chunk"},
        {"source_url": "https://example.test/a"},
        {"chunk_id": "NaN", "source_url": "Infinity"},
        {"chunk_id": "-Infinity", "source_url": "1e999"},
        {"chunk_id": True, "source_url": False},
        {"chunk_id": 0, "source_url": 0},
        {"chunk_id": 1, "source_url": -2},
        {"chunk_id": -3, "source_url": 4},
        {"chunk_id": 0.0, "source_url": 0.0},
        {"chunk_id": 1.5, "source_url": -3.25},
        {"chunk_id": -4.5, "source_url": 2.5},
        {"chunk_id": 10**20, "source_url": -(10**20)},
    ]
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    payload = [{"literary_attestation": {"source": "literary_fts", "source_label": "Alpha", **spec}} for spec in specs]
    manifest_sha = _write_json(manifest, payload)
    scraper_sha = _write(scraper, b"pass\n")
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    rows = document["rows"]
    assert isinstance(rows, list)
    assert len(rows) == len(specs)
    for row, spec in zip(rows, specs, strict=True):
        assert isinstance(row, dict)
        assert row["source"] == "literary_fts"
        for key in ("chunk_id", "source_url"):
            if key in spec:
                assert row[key] == spec[key]
            else:
                assert key not in row


@pytest.mark.parametrize("field", ["chunk_id", "source_url"])
@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_nonstandard_witness_constants_are_refused(tmp_path: Path, field: str, token: str) -> None:
    raw = (
        '{"literary_attestation":{"source":"literary_fts","source_label":"Alpha","' + field + '":' + token + "}}"
    ).encode()
    manifest, stored, scraper, scraper_raw, args = _refusal_inputs(tmp_path, raw)
    _assert_typed_refusal(run_cli(args), "json_nonstandard_constant", token.encode("ascii"))
    assert manifest.read_bytes() == stored
    assert scraper.read_bytes() == scraper_raw


def test_nonstandard_constant_outside_a_witness_is_refused(tmp_path: Path) -> None:
    manifest, raw, scraper, scraper_raw, args = _refusal_inputs(tmp_path, b'{"note":NaN}')
    _assert_typed_refusal(run_cli(args), "json_nonstandard_constant", b"NaN")
    assert manifest.read_bytes() == raw
    assert scraper.read_bytes() == scraper_raw


@pytest.mark.parametrize("field", ["chunk_id", "source_url"])
@pytest.mark.parametrize("token", ["1e999", "-1e999"])
def test_witness_float_overflow_is_refused(tmp_path: Path, field: str, token: str) -> None:
    raw = (
        '{"literary_attestation":{"source":"literary_fts","source_label":"Alpha","' + field + '":' + token + "}}"
    ).encode()
    manifest, stored, scraper, scraper_raw, args = _refusal_inputs(tmp_path, raw)
    _assert_typed_refusal(run_cli(args), "witness_nonfinite_number", token.encode("ascii"), b"Infinity")
    assert manifest.read_bytes() == stored
    assert scraper.read_bytes() == scraper_raw


def test_overflow_label_remains_non_string_and_strict_json(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    raw = b'{"literary_attestation":{"source":"literary_fts","source_label":1e999}}'
    manifest_sha = _write(manifest, raw)
    scraper_sha = _write(scraper, b"pass\n")
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    rows = document["rows"]
    assert isinstance(rows, list)
    assert rows[0]["label_value_type"] == "float"  # type: ignore[index]
    assert b"Infinity" not in stdout
    assert b"NaN" not in stdout


@pytest.mark.parametrize(
    ("payload", "hidden"),
    [
        (
            {"literary_attestation": {"source": "literary_fts", "source_label": "SECRET\ud800", "chunk_id": "c"}},
            b"SECRET",
        ),
        (
            {"literary_attestation": {"source": "literary_fts", "source_label": "Alpha", "source_url": "SECRET\udc00"}},
            b"SECRET",
        ),
        (
            {"SECRET\ud800": {"literary_attestation": {"source": "literary_fts", "source_label": "Alpha"}}},
            b"SECRET",
        ),
    ],
)
def test_unpaired_surrogates_are_typed(tmp_path: Path, payload: dict[str, object], hidden: bytes) -> None:
    raw = json.dumps(payload).encode("utf-8")
    manifest, stored, scraper, scraper_raw, args = _refusal_inputs(tmp_path, raw)
    _assert_typed_refusal(run_cli(args), "json_string_not_utf8", hidden)
    assert manifest.read_bytes() == stored
    assert scraper.read_bytes() == scraper_raw


def test_oversized_unused_integer_is_typed(tmp_path: Path) -> None:
    digits = b"9" * 4400
    manifest, raw, scraper, scraper_raw, args = _refusal_inputs(tmp_path, b'{"unused":' + digits + b"}")
    _assert_typed_refusal(run_cli(args), "json_integer_limit", digits)
    assert manifest.read_bytes() == raw
    assert scraper.read_bytes() == scraper_raw


@pytest.mark.parametrize("depth", [1100, 10000])
def test_excessive_nesting_is_typed(tmp_path: Path, depth: int) -> None:
    raw = b"[" * depth + b"0" + b"]" * depth
    manifest, stored, scraper, scraper_raw, args = _refusal_inputs(tmp_path, raw)
    _assert_typed_refusal(run_cli(args), "json_nesting_limit")
    assert manifest.read_bytes() == stored
    assert scraper.read_bytes() == scraper_raw


def test_canonical_json_refuses_nonfinite_and_deep_output() -> None:
    from scripts.audit.literary_year_inventory import InventoryError, canonical_json

    with pytest.raises(InventoryError) as nonfinite:
        canonical_json({"chunk_id": float("inf")})
    assert nonfinite.value.code == "witness_nonfinite_number"

    nested: object = 0
    for _ in range(10000):
        nested = [nested]
    with pytest.raises(InventoryError) as deep:
        canonical_json(nested)
    assert deep.value.code == "json_nesting_limit"


def test_canonical_json_does_not_swallow_unrelated_value_errors() -> None:
    from scripts.audit.literary_year_inventory import canonical_json

    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(ValueError, match="Circular reference"):
        canonical_json(cycle)


def test_compound_witness_on_excluded_source_stays_outside_the_denominator(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_sha = _write_json(
        manifest,
        {
            "literary_attestation": {
                "chunk_id": {"secret": "EXCLUDED_SECRET"},
                "source": "other",
                "source_url": ["EXCLUDED_URL"],
            }
        },
    )
    scraper_sha = _write(scraper, b"pass\n")
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    assert document["rows"] == []
    assert document["excluded_literary_attestation_counts"] == {
        "list_valued": 0,
        "other_non_dict": 0,
        "other_source": 1,
    }
    assert b"EXCLUDED_SECRET" not in stdout
    assert b"EXCLUDED_URL" not in stdout


def test_non_string_labels_are_unknown_and_not_emitted(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_sha = _write_json(
        manifest,
        [
            {"literary_attestation": {"source": "literary_fts", "source_label": 1.5}},
            {"literary_attestation": {"source": "literary_fts", "source_label": False}},
            {"literary_attestation": {"source": "literary_fts", "source_label": ["SECRET_LIST_LABEL"]}},
            {"literary_attestation": {"source": "literary_fts", "source_label": {"a": "SECRET_DICT_LABEL"}}},
            {"literary_attestation": {"source": "literary_fts", "source_label": ""}},
            {"literary_attestation": {"source": "literary_fts", "source_label": 0}},
        ],
    )
    scraper_sha = _write(scraper, b'P1_AUTHORS = {"one": {"name": "Author One", "years": "1900-1980"}}\n')
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    rows = document["rows"]
    assert rows == [
        _packed(
            0, [0, "literary_attestation"], "float", None, None, NON_STRING_CLASSES, {"source": "literary_fts"}, None
        ),
        _packed(
            1, [1, "literary_attestation"], "bool", None, None, NON_STRING_CLASSES, {"source": "literary_fts"}, None
        ),
        _packed(
            2, [2, "literary_attestation"], "list", None, None, NON_STRING_CLASSES, {"source": "literary_fts"}, None
        ),
        _packed(
            3, [3, "literary_attestation"], "dict", None, None, NON_STRING_CLASSES, {"source": "literary_fts"}, None
        ),
        _packed(
            4, [4, "literary_attestation"], "str", "", None, [NAME_MISS, YEAR_ABSENT], {"source": "literary_fts"}, ""
        ),
        _packed(
            5, [5, "literary_attestation"], "int", None, None, NON_STRING_CLASSES, {"source": "literary_fts"}, None
        ),
    ]
    assert document["probe_compatible_counts"] == {
        "labels": 6,
        "labels_ukrlib_author": 0,
        "labels_ukrlib_year_eq_author_years_start": 0,
        "labels_with_year": 0,
        "ukrlib_authors_parsed": 1,
    }
    assert b"SECRET_LIST_LABEL" not in stdout
    assert b"SECRET_DICT_LABEL" not in stdout


def test_excluded_shapes_have_counts_and_integer_coordinates(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    scraper_sha = _write(scraper, b'P1_AUTHORS = {"one": {"name": "Author One", "years": "1900-1980"}}\n')
    excluded_sha = _write_json(
        manifest,
        {
            "literary_attestation": "SECRET_SCALAR",
            "nested": {"literary_attestation": {"chunk_id": "z", "source": "other"}},
        },
    )
    code, stdout, stderr = run_cli(_pins(manifest, excluded_sha, scraper, scraper_sha))
    assert (code, stderr) == (0, b"")
    document = _load_success(stdout)
    assert document["rows"] == []
    assert document["denominator"] == {"literary_fts_dictionary_attestations": 0}
    assert document["excluded_literary_attestation_counts"] == {
        "list_valued": 0,
        "other_non_dict": 1,
        "other_source": 1,
    }
    assert b"SECRET_SCALAR" not in stdout

    root_sha = _write(manifest, b'"SECRET_ROOT"')
    code, stdout, stderr = run_cli(_pins(manifest, root_sha, scraper, scraper_sha))
    assert (code, stderr) == (0, b"")
    assert json.loads(stdout)["rows"] == []
    assert b"SECRET_ROOT" not in stdout

    listed_sha = _write_json(
        manifest,
        [
            {
                "literary_attestation": {
                    "chunk_id": "L",
                    "source": "literary_fts",
                    "source_label": f"Author One {DOT} Title {DOT} 1900",
                }
            }
        ],
    )
    code, stdout, stderr = run_cli(_pins(manifest, listed_sha, scraper, scraper_sha))
    assert (code, stderr) == (0, b"")
    rows = json.loads(stdout)["rows"]
    assert rows[0]["coordinate"] == [0, "literary_attestation"]
    assert rows[0]["ordinal"] == 0
    assert rows[0]["classes"] == EQUAL_CLASSES
    assert isinstance(rows[0]["coordinate"][0], int)


@pytest.mark.parametrize(
    "scraper_raw",
    [
        pytest.param(b"+" * 8000 + b"1\n", id="unary-stack"),
        pytest.param(b"1" + b"+1" * 12000 + b"\n", id="binary-recursion"),
    ],
)
def test_scraper_parser_limits_are_typed(tmp_path: Path, scraper_raw: bytes) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_raw = b"{}"
    manifest_sha = _write(manifest, manifest_raw)
    scraper_sha = _write(scraper, scraper_raw)
    _assert_typed_refusal(
        run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha)),
        "scraper_parse_failed",
    )
    assert manifest.read_bytes() == manifest_raw
    assert scraper.read_bytes() == scraper_raw


@pytest.mark.parametrize("limit_error", [MemoryError, RecursionError])
def test_literal_eval_parser_limits_are_typed(
    monkeypatch: pytest.MonkeyPatch,
    limit_error: type[BaseException],
) -> None:
    import scripts.audit.literary_year_inventory as inventory

    def raise_limit(_value: object) -> object:
        raise limit_error

    monkeypatch.setattr(inventory.ast, "literal_eval", raise_limit)
    with pytest.raises(inventory.InventoryError) as caught:
        inventory._parse_scraper_authors(b'WRAP = {"a": {"name": "Author One", "years": "1900-1980"}}\n')
    assert caught.value.code == "scraper_parse_failed"


def test_scraper_source_is_not_executed(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_sha = _write_json(
        manifest,
        {"literary_attestation": {"source": "literary_fts", "source_label": f"Author One {DOT} Title {DOT} 1900"}},
    )
    scraper_text = (
        "import pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text('executed')\n"
        'WRAP = {"bad": {"name": some_name, "years": "1800-1900"}, '
        '"ok": {"name": "Author One", "years": "1900-1980"}}\n'
    )
    scraper_sha = _write(scraper, scraper_text.encode("utf-8"))
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, scraper, scraper_sha))

    assert code == 0
    assert stderr == b""
    assert not marker.exists()
    document = _load_success(stdout)
    assert document["scraper_author_records"] == {
        "collision_count": 0,
        "distinct_name_count": 1,
        "record_count": 1,
    }
    assert document["rows"][0]["classes"] == EQUAL_CLASSES  # type: ignore[index]


@pytest.mark.parametrize(
    ("manifest_raw", "scraper_raw", "manifest_pin", "scraper_pin", "error_code", "hidden"),
    [
        (b"{}", b"pass\n", "abc", None, "manifest_sha256_invalid", b"abc"),
        (b"{}", b"pass\n", None, "xyz", "scraper_sha256_invalid", b"xyz"),
        (b'{"a": 1, "a": 2}', b"pass\n", "0" * 64, None, "manifest_sha256_mismatch", b'"a"'),
        (b"{}", b"pass\n", None, "0" * 64, "scraper_sha256_mismatch", b"pass"),
        (b"\xff", b"pass\n", None, None, "manifest_utf8_decode_failed", b"\xff"),
        (b"{}", b"\xff", None, None, "scraper_utf8_decode_failed", b"\xff"),
        (b'{"text": "SECRET_BODY_TEXT"', b"pass\n", None, None, "json_parse_failed", b"SECRET_BODY_TEXT"),
        (b'{"outer": [{"k": 1, "k": 2}]}', b"pass\n", None, None, "duplicate_json_key", b'"k"'),
        (b"{}", b"def (\n", None, None, "scraper_parse_failed", b"def"),
        (
            b"{}",
            b'P1_AUTHORS = {"a": {"name": ["SECRET_NAME"], "years": "1900-1980"}}\n',
            None,
            None,
            "scraper_author_name_unhashable",
            b"SECRET_NAME",
        ),
        (
            b"{}",
            b'P1_AUTHORS = {"a": {"name": "Author One", "years": 1900}}\n',
            None,
            None,
            "scraper_years_non_string",
            b"1900",
        ),
    ],
)
def test_pin_and_parse_failures_write_no_stdout(
    tmp_path: Path,
    manifest_raw: bytes,
    scraper_raw: bytes,
    manifest_pin: str | None,
    scraper_pin: str | None,
    error_code: str,
    hidden: bytes,
) -> None:
    manifest = tmp_path / "manifest.json"
    scraper = tmp_path / "scraper.py"
    manifest_sha = _write(manifest, manifest_raw)
    scraper_sha = _write(scraper, scraper_raw)
    code, stdout, stderr = run_cli(
        _pins(
            manifest,
            manifest_pin if manifest_pin is not None else manifest_sha,
            scraper,
            scraper_pin if scraper_pin is not None else scraper_sha,
        )
    )

    assert code == 1
    assert stdout == b""
    assert stderr == _error(error_code)
    assert hidden not in stderr
    assert manifest.read_bytes() == manifest_raw
    assert scraper.read_bytes() == scraper_raw


def test_invalid_pin_does_not_require_the_file_to_exist(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    scraper = tmp_path / "scraper.py"
    scraper_sha = _write(scraper, b"pass\n")
    code, stdout, stderr = run_cli(_pins(missing, "not-a-sha", scraper, scraper_sha))

    assert (code, stdout, stderr) == (1, b"", _error("manifest_sha256_invalid"))
    assert not missing.exists()


def test_unreadable_inputs_are_typed(tmp_path: Path) -> None:
    scraper = tmp_path / "scraper.py"
    scraper_sha = _write(scraper, b"pass\n")
    valid_sha = "0" * 64
    code, stdout, stderr = run_cli(_pins(tmp_path, valid_sha, scraper, scraper_sha))
    assert (code, stdout, stderr) == (1, b"", _error("manifest_unreadable"))

    manifest = tmp_path / "manifest.json"
    manifest_sha = _write(manifest, b"{}")
    code, stdout, stderr = run_cli(_pins(manifest, manifest_sha, tmp_path, valid_sha))
    assert (code, stdout, stderr) == (1, b"", _error("scraper_unreadable"))


def test_usage_error_is_exit_two(tmp_path: Path) -> None:
    code, stdout, _stderr = run_cli(["--manifest", str(tmp_path / "missing.json")])

    assert code == 2
    assert stdout == b""
