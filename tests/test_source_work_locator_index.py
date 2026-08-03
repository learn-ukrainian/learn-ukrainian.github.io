"""Strict metadata-only source/work locator index tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import source_work_locator_index as locators

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = (
    "anna-ohoiko-1000-words-2nd-ed",
    "anna-ohoiko-500-verbs",
    "ulp-1-00-lesson-notes",
    "ulp-2-00-lesson-notes",
    "ulp-3-00-lesson-notes",
    "ulp-4-00-lesson-notes",
    "ulp-5-00-lesson-notes",
    "ulp-6-00-lesson-notes",
)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    database = tmp_path / "data" / "sources.db"
    database.parent.mkdir(parents=True)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE literary_texts (source_file TEXT, work_id TEXT, source_url TEXT, title TEXT, author TEXT, year INTEGER, text TEXT)"
        )
        connection.executemany(
            "INSERT INTO literary_texts VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("lit", "book", "https://example.test/book.pdf#page=1", "Book", "Author", 1900, "LITERARY SECRET"),
                ("lit", "book", "https://example.test/book.pdf#page=2", "Book", "Author", 1900, "LITERARY SECRET"),
            ],
        )
        connection.execute(
            "CREATE TABLE textbooks (source_file TEXT, title TEXT, author TEXT, author_uk TEXT, grade TEXT, subject TEXT, text TEXT)"
        )
        connection.execute(
            "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("book", "Title", "author", "автор", "4", "math", "TEXTBOOK SECRET"),
        )
        for value in EXCLUDED:
            connection.execute(
                "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?, ?, ?)",
                (value, "Excluded", "author", "автор", "4", "math", "EXCLUDED SECRET"),
            )
        connection.execute(
            "CREATE TABLE external_articles (source_file TEXT, url_normalized TEXT, url TEXT, title TEXT, speaker TEXT, domain TEXT, publish_date TEXT, channel_id TEXT, text TEXT)"
        )
        connection.execute(
            "INSERT INTO external_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "external",
                "https://example.test/a",
                "https://example.test/a?raw=1",
                "Article",
                "Speaker",
                "example.test",
                "2026-01-01",
                "channel",
                "EXTERNAL SECRET",
            ),
        )
        connection.execute("CREATE TABLE wikipedia (fetched_at TEXT, title TEXT, url TEXT, text TEXT)")
        connection.execute(
            "INSERT INTO wikipedia VALUES (?, ?, ?, ?)",
            ("2026-01-01T00:00:00Z", "Page", "https://uk.wikipedia.org/wiki/Page", "WIKI SECRET"),
        )
    config = json.loads(
        (ROOT / "data/projects/open_model_data/evidence/source_work_locator_config_v1.json").read_text()
    )
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, tmp_path


def _build(tmp_path: Path) -> tuple[Path, list[dict]]:
    config, root = _fixture(tmp_path)
    output = tmp_path / "locators.jsonl"
    locators.build(config_path=config, input_root=root, output=output)
    return output, [json.loads(line) for line in output.read_text().splitlines()]


def test_config_is_valid_under_embedded_schema(tmp_path: Path) -> None:
    config, _root = _fixture(tmp_path)
    schema = json.loads(
        (ROOT / "data/projects/open_model_data/contracts/source_work_locator_v1.schema.json").read_text()
    )
    Draft202012Validator({"$ref": "#/$defs/config", "$defs": schema["$defs"]}).validate(json.loads(config.read_text()))


@pytest.mark.parametrize("family", ["literary", "public_textbooks", "external_articles", "wikipedia"])
def test_each_real_family_has_one_metadata_only_locator(tmp_path: Path, family: str) -> None:
    output, rows = _build(tmp_path)
    row = next(value for value in rows if value["source_family"] == family)
    assert row["affected_records"] >= 1 and row["schema_version"] == "source_work_locator_v1"
    assert "SECRET" not in output.read_text()


@pytest.mark.parametrize("excluded", EXCLUDED)
def test_all_eight_private_textbook_sources_are_excluded(tmp_path: Path, excluded: str) -> None:
    _output, rows = _build(tmp_path)
    assert all(row["source_locator"].get("source_file") != excluded for row in rows)


@pytest.mark.parametrize(
    ("family", "url"),
    [
        ("literary", "https://example.test/book.pdf"),
        ("public_textbooks", None),
        ("external_articles", "https://example.test/a"),
        ("wikipedia", "https://uk.wikipedia.org/wiki/Page"),
    ],
)
def test_canonical_url_policy(tmp_path: Path, family: str, url: str | None) -> None:
    _output, rows = _build(tmp_path)
    assert next(row for row in rows if row["source_family"] == family)["canonical_url"] == url


def test_build_is_deterministic_and_canonical_ordered(tmp_path: Path) -> None:
    output, rows = _build(tmp_path)
    before = output.read_bytes()
    config, root = _fixture(tmp_path / "again")
    other = tmp_path / "again" / "locators.jsonl"
    locators.build(config_path=config, input_root=root, output=other)
    assert before == other.read_bytes()
    assert rows == sorted(
        rows,
        key=lambda row: (
            row["source_family"],
            row["source_id"],
            row["work_id"],
            locators.canonical_json(row["source_locator"]),
        ),
    )


def test_unknown_config_key_and_bad_column_fail_schema(tmp_path: Path) -> None:
    config, root = _fixture(tmp_path)
    value = json.loads(config.read_text())
    value["unexpected"] = True
    config.write_text(json.dumps(value))
    with pytest.raises(locators.LocatorError, match="schema failure"):
        locators.build(config_path=config, input_root=root, output=tmp_path / "out")
    value.pop("unexpected")
    value["families"][0]["metadata_columns"] = ["text"]
    config.write_text(json.dumps(value))
    with pytest.raises(locators.LocatorError, match="schema failure"):
        locators.build(config_path=config, input_root=root, output=tmp_path / "out")


def test_missing_real_column_and_ambiguous_locator_fail_closed(tmp_path: Path) -> None:
    config, root = _fixture(tmp_path)
    value = json.loads(config.read_text())
    value["families"][0]["metadata_columns"] = ["missing"]
    config.write_text(json.dumps(value))
    with pytest.raises(locators.LocatorError):
        locators.build(config_path=config, input_root=root, output=tmp_path / "out")
    config, root = _fixture(tmp_path / "ambiguous")
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute(
            "INSERT INTO external_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "external",
                "https://example.test/a",
                "https://other.test/a",
                "Article",
                "Speaker",
                "example.test",
                "2026-01-01",
                "channel",
                "X",
            ),
        )
    with pytest.raises(locators.LocatorError, match="ambiguous locator"):
        locators.build(config_path=config, input_root=root, output=root / "out")


def test_same_locator_pair_with_conflicting_allowlisted_metadata_fails_closed(tmp_path: Path) -> None:
    config, root = _fixture(tmp_path)
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute(
            "INSERT INTO external_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "external",
                "https://example.test/a",
                "https://example.test/a?raw=1",
                "Changed title",
                "Speaker",
                "example.test",
                "2026-01-01",
                "channel",
                "X",
            ),
        )
    with pytest.raises(locators.LocatorError, match="ambiguous metadata"):
        locators.build(config_path=config, input_root=root, output=root / "out")


def test_invalid_row_unknown_field_is_rejected_by_contract(tmp_path: Path) -> None:
    _output, rows = _build(tmp_path)
    row = dict(rows[0])
    row["text"] = "forbidden"
    schema = json.loads(
        (ROOT / "data/projects/open_model_data/contracts/source_work_locator_v1.schema.json").read_text()
    )
    assert list(Draft202012Validator(schema).iter_errors(row))


def test_atomic_publication_failure_preserves_prior_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, _rows = _build(tmp_path)
    previous = output.read_bytes()

    def fail(_source: Path, _target: Path) -> None:
        raise OSError("planned publication failure")

    monkeypatch.setattr(locators, "_replace", fail)
    config, root = _fixture(tmp_path / "retry")
    with pytest.raises(OSError, match="planned publication failure"):
        locators.build(config_path=config, input_root=root, output=output)
    assert output.read_bytes() == previous
    assert not list(output.parent.glob(".*.tmp"))
