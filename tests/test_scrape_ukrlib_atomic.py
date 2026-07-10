"""Failure-atomic JSONL staging tests for the ukrlib scraper."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.rag import scrape_ukrlib as scrape

AUTHOR_INFO = {
    "id": 999,
    "name": "Тест Т.",
    "full_name": "Тестовий Автор",
    "years": "1900-1950",
    "genre_default": "prose",
    "period": "modern",
}
WORKS = [{"tid": 1, "title": "Перший твір"}, {"tid": 2, "title": "Другий твір"}]


def _chunk(tid: int | str) -> dict[str, object]:
    return {
        "chunk_id": f"chunk-{tid}",
        "text": "Тестовий український текст. " * 20,
        "source_url": f"https://example.test/printit.php?tid={tid}",
        "token_count": 20,
    }


def _complete_chunk(tid: int | str) -> dict[str, object]:
    return {
        **_chunk(tid),
        "work": "Тестовий Автор. Попередній твір",
        "author": "Тест Т.",
        "year": 1900,
        "genre": "prose",
        "language_period": "modern",
    }


def _chunk_for_source(*args, **_kwargs) -> list[dict[str, object]]:
    return [{**_chunk("new"), "source_url": args[2]}]


def _configure_author_scrape(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(scrape, "LITERARY_DIR", tmp_path)
    monkeypatch.setattr(scrape, "PROGRESS_DIR", tmp_path / ".ukrlib_progress")
    monkeypatch.setattr(scrape, "get_author_works", lambda _author_id: (WORKS, []))
    monkeypatch.setattr(
        scrape,
        "scrape_work_text",
        lambda tid, **_kwargs: ("Український текст. " * 20, f"https://example.test/?tid={tid}"),
    )
    monkeypatch.setattr(scrape.time, "sleep", lambda _seconds: None)
    return tmp_path / "ukrlib-test-author.jsonl"


def _assert_no_staging_file(tmp_path: Path, output_path: Path) -> None:
    assert not list(tmp_path.glob(f".{output_path.name}.*.building"))


def test_mid_scrape_interrupt_creates_no_output_and_cleans_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fatal second-work failure cannot publish the first work's rows."""
    output_path = _configure_author_scrape(monkeypatch, tmp_path)
    calls = 0

    def fail_after_first_chunk(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt()
        return [_chunk(1)]

    monkeypatch.setattr(scrape, "chunk_text", fail_after_first_chunk)

    with pytest.raises(KeyboardInterrupt):
        scrape.scrape_author("test-author", AUTHOR_INFO)

    assert not output_path.exists()
    assert not (tmp_path / ".ukrlib_progress" / "test-author.done").exists()
    _assert_no_staging_file(tmp_path, output_path)


def test_mid_scrape_interrupt_preserves_previous_output_and_cleans_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fatal second-work failure leaves the previous artifact byte-identical."""
    output_path = _configure_author_scrape(monkeypatch, tmp_path)
    previous = (json.dumps(_complete_chunk(999), ensure_ascii=False) + "\n").encode()
    output_path.write_bytes(previous)
    calls = 0

    def fail_after_first_chunk(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt()
        return [_chunk(1)]

    monkeypatch.setattr(scrape, "chunk_text", fail_after_first_chunk)

    with pytest.raises(KeyboardInterrupt):
        scrape.scrape_author("test-author", AUTHOR_INFO)

    assert output_path.read_bytes() == previous
    assert not (tmp_path / ".ukrlib_progress" / "test-author.done").exists()
    _assert_no_staging_file(tmp_path, output_path)


def test_successful_scrape_validates_stage_then_replaces_complete_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Writes occur in a sibling temp file, which is validated before rename."""
    output_path = _configure_author_scrape(monkeypatch, tmp_path)
    previous = (json.dumps(_complete_chunk(999), ensure_ascii=False) + "\n").encode()
    output_path.write_bytes(previous)
    monkeypatch.setattr(scrape, "chunk_text", _chunk_for_source)

    validated_paths: list[Path] = []
    real_validate = scrape._validate_staged_jsonl

    def record_validation(path: Path) -> int:
        validated_paths.append(path)
        assert path.parent == output_path.parent
        assert path != output_path
        assert path.exists()
        return real_validate(path)

    replacements: list[tuple[Path, Path]] = []
    real_replace = Path.replace

    def record_replace(source: Path, target: Path) -> Path:
        replacements.append((source, target))
        return real_replace(source, target)

    monkeypatch.setattr(scrape, "_validate_staged_jsonl", record_validation)
    monkeypatch.setattr(Path, "replace", record_replace)

    assert scrape.scrape_author("test-author", AUTHOR_INFO) == 3

    assert output_path.read_bytes() != previous
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    assert all(row.keys() >= scrape.JSONL_REQUIRED_FIELDS for row in rows)
    assert replacements == [(validated_paths[0], output_path)]
    assert not validated_paths[0].exists()
    assert (tmp_path / ".ukrlib_progress" / "test-author.done").exists()


def test_validation_failure_prevents_swap_and_cleans_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A staged row without a required field cannot replace the live JSONL."""
    output_path = _configure_author_scrape(monkeypatch, tmp_path)
    previous = (json.dumps(_complete_chunk(999), ensure_ascii=False) + "\n").encode()
    output_path.write_bytes(previous)
    monkeypatch.setattr(
        scrape,
        "chunk_text",
        lambda *_args, **_kwargs: [{"text": "bad staged row", "source_url": "https://example.test"}],
    )

    with pytest.raises(scrape.JsonlValidationError, match="chunk_id"):
        scrape.scrape_author("test-author", AUTHOR_INFO)

    assert output_path.read_bytes() == previous
    assert not (tmp_path / ".ukrlib_progress" / "test-author.done").exists()
    _assert_no_staging_file(tmp_path, output_path)


def test_recovery_after_marker_failure_does_not_duplicate_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A post-swap marker failure resumes from source tids without appending again."""
    output_path = _configure_author_scrape(monkeypatch, tmp_path)
    monkeypatch.setattr(scrape, "chunk_text", _chunk_for_source)
    real_mark_done = scrape.mark_done

    def fail_marker(*_args, **_kwargs) -> None:
        raise RuntimeError("progress marker failed")

    monkeypatch.setattr(scrape, "mark_done", fail_marker)
    with pytest.raises(RuntimeError, match="progress marker failed"):
        scrape.scrape_author("test-author", AUTHOR_INFO)
    published = output_path.read_bytes()

    monkeypatch.setattr(scrape, "mark_done", real_mark_done)
    monkeypatch.setattr(
        scrape,
        "chunk_text",
        lambda *_args, **_kwargs: pytest.fail("already-published tid was scraped again"),
    )

    assert scrape.scrape_author("test-author", AUTHOR_INFO) == 2
    assert output_path.read_bytes() == published


def test_staged_validation_rejects_invalid_json(tmp_path: Path) -> None:
    staged_path = tmp_path / "invalid.jsonl"
    staged_path.write_text("not json\n", encoding="utf-8")

    with pytest.raises(scrape.JsonlValidationError, match="not valid JSON"):
        scrape._validate_staged_jsonl(staged_path)
