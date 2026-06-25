from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml

from scripts.build import v7_build
from scripts.readings.generate_readings import (
    GenerationSummary,
    SkippedReading,
    WrittenReading,
    generate_from_plan,
)

SPRING_TEXT = """ОЙ ВЕСНА, ВЕСНА, ТИ КРАСНА

Ой весна, весна, ти красна,

Що ти нам, весно, принесла?"""

HINTED_TEXT = """ОЙ ВИЛИНЬ, ВИЛИНЬ, ГОГОЛЮ

Ой вилинь, вилинь, гоголю,

Винеси літо з собою."""

SPRING_CURATED_TEXT = """Ой весна, весна, ти красна,

Що ти нам, весно, принесла?"""

NORMALIZED_CURATED_TEXT = """Ой в полі з'явилася зірка
В небі ясная"""

NORMALIZED_CORPUS_TEXT = """Ой в полі зʼяви́лася   зірка

В небі ясная"""


def test_generate_from_plan_writes_curated_text_body_and_plan_slug(tmp_path: Path) -> None:
    plan_path = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой весна, весна, ти красна»",
                source="Народна творчість; корпус ukrlib-narod-dumy, chunk 2df42ee0_c0000",
                reading_slug="plan-curated-vesna-slug",
                text=SPRING_CURATED_TEXT,
            )
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="2df42ee0_c0000",
                work="Народна творчість. Ой весна, весна, ти красна",
                text=SPRING_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    summary = generate_from_plan(plan_path, output_dir=output_dir, sources_db=db_path)

    assert [item.slug for item in summary.written] == ["plan-curated-vesna-slug"]
    rendered_path = output_dir / "plan-curated-vesna-slug.mdx"
    rendered = rendered_path.read_text(encoding="utf-8")
    assert rendered_path.exists()
    assert not (output_dir / "vesnianka-oi-vesna-vesna-ty-krasna.mdx").exists()
    assert "> Ой весна, весна, ти красна," in rendered
    assert "> Що ти нам, весно, принесла?" in rendered
    assert "ОЙ ВЕСНА, ВЕСНА, ТИ КРАСНА" not in rendered
    assert "source_chunk_ids: [\"2df42ee0_c0000\"]" in rendered
    assert "text_match: \"exact\"" in rendered
    assert "— Народна творчість, «Ой весна, весна, ти красна» (Веснянка)" in rendered


def test_generate_from_plan_uses_source_chunk_as_lookup_hint(tmp_path: Path) -> None:
    plan_path = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой вилинь, вилинь, гоголю»",
                source="Народна творчість; запис Грушевського; корпус chunk da46aa92_c0284",
                reading_slug="vesnianka-oi-vylyn-hoholu",
                text="""Ой вилинь, вилинь, гоголю,

Винеси літо з собою.""",
            )
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="da46aa92_c0284",
                work="Unrelated corpus work title",
                text=HINTED_TEXT,
            )
        ],
    )

    summary = generate_from_plan(plan_path, output_dir=tmp_path / "readings", sources_db=db_path)

    assert [item.source_chunk_id for item in summary.written] == ["da46aa92_c0284"]
    assert summary.skipped == ()


def test_generate_from_plan_skips_non_public_domain_without_writing(tmp_path: Path) -> None:
    modern_plan = _write_plan(
        tmp_path / "modern",
        [
            _reading_entry(
                title="«Сучасний текст»",
                source="Сучасний автор; корпус chunk deadbeef_c0001",
                reading_slug="modern-text",
                text="Сучасний текст\n\nрядок",
            )
        ],
    )
    modern_db = _write_sources_db(
        tmp_path / "modern",
        [
            _corpus_row(
                chunk_id="deadbeef_c0001",
                author="Сучасний автор",
                work="Сучасний текст",
                year=2020,
                source_file="modern-source",
                text="Сучасний текст\n\nрядок",
            )
        ],
    )
    modern_output = tmp_path / "modern" / "readings"

    modern_summary = generate_from_plan(modern_plan, output_dir=modern_output, sources_db=modern_db)

    assert modern_summary.written == ()
    assert modern_summary.skipped[0].reason == "corpus row is not public-domain"
    assert not (modern_output / "modern-text.mdx").exists()


def test_generate_from_plan_skips_unattested_curated_text_without_writing(tmp_path: Path) -> None:
    drift_plan = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой весна, весна, ти красна»",
                source="Народна творчість; корпус chunk feedface_c0002",
                reading_slug="curated-drift",
                text="Цього рядка немає в корпусному чанку.",
            )
        ],
    )
    drift_db = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="feedface_c0002",
                work="Ой весна, весна, ти красна",
                text=SPRING_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    drift_summary = generate_from_plan(
        drift_plan,
        output_dir=output_dir,
        sources_db=drift_db,
    )

    assert drift_summary.written == ()
    assert (
        drift_summary.skipped[0].reason
        == "curated text not attested in corpus chunk feedface_c0002"
    )
    assert not (output_dir / "curated-drift.mdx").exists()


def test_generate_from_plan_skips_missing_curated_text_without_chunk_dump(tmp_path: Path) -> None:
    no_text_plan = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой весна, весна, ти красна»",
                source="Народна творчість; корпус chunk 2df42ee0_c0000",
                reading_slug="no-curated-text",
            )
        ],
    )
    no_text_db = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="2df42ee0_c0000",
                work="Ой весна, весна, ти красна",
                text=SPRING_TEXT,
            )
        ],
    )
    no_text_output = tmp_path / "readings"

    no_text_summary = generate_from_plan(no_text_plan, output_dir=no_text_output, sources_db=no_text_db)

    assert no_text_summary.written == ()
    assert no_text_summary.skipped[0].reason == "no curated text: field"
    assert not (no_text_output / "no-curated-text.mdx").exists()


def test_generate_from_plan_skips_missing_corpus_without_writing(tmp_path: Path) -> None:
    missing_plan = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Немає в корпусі»",
                source="Народна творчість; корпус chunk abcdef12_c0001",
                reading_slug="missing-corpus",
                text="Немає в корпусі",
            )
        ],
    )
    output_dir = tmp_path / "readings"

    missing_summary = generate_from_plan(
        missing_plan,
        output_dir=output_dir,
        sources_db=tmp_path / "sources.db",
    )

    assert missing_summary.written == ()
    assert missing_summary.skipped[0].reason == "no matching corpus text"
    assert not (output_dir / "missing-corpus.mdx").exists()


def test_generate_from_plan_accepts_normalized_curated_text_match(tmp_path: Path) -> None:
    plan_path = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой в полі з'явилася зірка»",
                source="Народна творчість; корпус chunk abc12345_c0000",
                reading_slug="normalized-only-match",
                text=NORMALIZED_CURATED_TEXT,
            )
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="abc12345_c0000",
                work="Ой в полі з'явилася зірка",
                text=NORMALIZED_CORPUS_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    summary = generate_from_plan(plan_path, output_dir=output_dir, sources_db=db_path)

    assert [item.text_match for item in summary.written] == ["normalized"]
    rendered = (output_dir / "normalized-only-match.mdx").read_text(encoding="utf-8")
    assert "text_match: \"normalized\"" in rendered
    assert "> Ой в полі з'явилася зірка" in rendered
    assert "зʼяви́лася" not in rendered


def test_generate_from_plan_is_idempotent_and_preserves_hand_authored(tmp_path: Path) -> None:
    plan_path = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой весна, весна, ти красна»",
                source="Народна творчість; корпус chunk 2df42ee0_c0000",
                reading_slug="vesna-idempotent",
                text=SPRING_CURATED_TEXT,
            )
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="2df42ee0_c0000",
                work="Ой весна, весна, ти красна",
                text=SPRING_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    first = generate_from_plan(plan_path, output_dir=output_dir, sources_db=db_path)
    second = generate_from_plan(plan_path, output_dir=output_dir, sources_db=db_path)

    assert [item.action for item in first.written] == ["created"]
    assert second.written == ()
    assert [item.action for item in second.existing] == ["unchanged"]

    hand_output = tmp_path / "hand-authored"
    hand_output.mkdir()
    hand_path = hand_output / "vesna-idempotent.mdx"
    hand_path.write_text("---\ntitle: Hand authored\n---\n", encoding="utf-8")

    hand_summary = generate_from_plan(plan_path, output_dir=hand_output, sources_db=db_path)

    assert hand_summary.written == ()
    assert [item.action for item in hand_summary.existing] == ["existing-hand-authored"]
    assert hand_path.read_text(encoding="utf-8") == "---\ntitle: Hand authored\n---\n"


def test_readings_prebuild_phase_core_level_is_noop(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    called = False

    def fake_generate_from_plan(*_args: Any, **_kwargs: Any) -> GenerationSummary:
        nonlocal called
        called = True
        return GenerationSummary((), (), ())

    monkeypatch.setattr(v7_build, "generate_from_plan", fake_generate_from_plan)
    events: list[tuple[str, dict[str, Any]]] = []

    summary = v7_build._run_readings_prebuild_phase(
        level="a1",
        slug="core-fixture",
        plan_path=tmp_path / "plan.yaml",
        output_dir=tmp_path / "readings",
        sources_db=tmp_path / "sources.db",
        dry_run=False,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert summary is None
    assert called is False
    assert events == []


def test_readings_prebuild_phase_emits_generation_and_skip_events(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    generated = WrittenReading(
        slug="hosted-reading",
        path=tmp_path / "readings" / "hosted-reading.mdx",
        action="created",
        source_chunk_id="2df42ee0_c0000",
    )
    skipped = SkippedReading("Missing", "missing-reading", "no matching corpus text")
    fake_summary = GenerationSummary((generated,), (skipped,), ())
    calls: list[dict[str, Any]] = []

    def fake_generate_from_plan(*args: Any, **kwargs: Any) -> GenerationSummary:
        calls.append({"args": args, "kwargs": kwargs})
        return fake_summary

    monkeypatch.setattr(v7_build, "generate_from_plan", fake_generate_from_plan)
    events: list[tuple[str, dict[str, Any]]] = []

    summary = v7_build._run_readings_prebuild_phase(
        level="folk",
        slug="seminar-fixture",
        plan_path=tmp_path / "plan.yaml",
        output_dir=tmp_path / "readings",
        sources_db=tmp_path / "sources.db",
        dry_run=True,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert summary == fake_summary
    assert calls[0]["args"] == (tmp_path / "plan.yaml",)
    assert calls[0]["kwargs"]["dry_run"] is True
    assert [event for event, _fields in events] == ["reading_generated", "reading_skipped"]
    assert events[0][1]["reading_slug"] == "hosted-reading"
    assert events[1][1]["reason"] == "no matching corpus text"


def test_generated_plan_reading_has_required_schema_fields(tmp_path: Path) -> None:
    plan_path = _write_plan(
        tmp_path,
        [
            _reading_entry(
                title="«Ой весна, весна, ти красна»",
                title_en="Oh spring, spring, you beautiful one",
                genre="Веснянка",
                source="Народна творчість; корпус chunk 2df42ee0_c0000",
                reading_slug="schema-vesna",
                text=SPRING_CURATED_TEXT,
            )
        ],
    )
    db_path = _write_sources_db(
        tmp_path,
        [
            _corpus_row(
                chunk_id="2df42ee0_c0000",
                work="Ой весна, весна, ти красна",
                text=SPRING_TEXT,
            )
        ],
    )
    output_dir = tmp_path / "readings"

    generate_from_plan(plan_path, output_dir=output_dir, sources_db=db_path)
    mdx = (output_dir / "schema-vesna.mdx").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(mdx.split("---", 2)[1])
    body = mdx.split("---", 2)[2]

    assert frontmatter["title"] == "«Ой весна, весна, ти красна»"
    assert frontmatter["title_en"] == "Oh spring, spring, you beautiful one"
    assert frontmatter["genre"] == "Веснянка"
    assert frontmatter["tracks"] == ["folk"]
    assert frontmatter["source_chunk_ids"] == ["2df42ee0_c0000"]
    assert frontmatter["text_match"] == "exact"
    assert frontmatter["public_domain"] is True
    assert "<PrimaryReading>" in body
    assert "Ой весна, весна, ти красна" in body


def _reading_entry(
    *,
    title: str,
    source: str,
    reading_slug: str,
    title_en: str = "Fixture reading",
    genre: str = "Веснянка",
    text: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "title": title,
        "title_en": title_en,
        "genre": genre,
        "source": source,
        "license": "public_domain",
        "hosting": "host",
        "reading_slug": reading_slug,
    }
    if text is not None:
        entry["text"] = text
    return entry


def _write_plan(tmp_path: Path, readings: list[dict[str, Any]]) -> Path:
    plan_dir = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "folk"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / "fixture-module.yaml"
    plan_path.write_text(
        yaml.safe_dump(
            {
                "level": "folk",
                "slug": "fixture-module",
                "sequence": 1,
                "title": "Fixture Module",
                "readings": readings,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return plan_path


def _write_sources_db(tmp_path: Path, rows: list[tuple[Any, ...]] | None = None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE literary_texts (
            chunk_id TEXT,
            author TEXT,
            work TEXT,
            work_id TEXT,
            year INTEGER,
            genre TEXT,
            language_period TEXT,
            source_file TEXT,
            source_url TEXT,
            text TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO literary_texts (
            chunk_id, author, work, work_id, year, genre,
            language_period, source_file, source_url, text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows or [],
    )
    conn.commit()
    conn.close()
    return db_path


def _corpus_row(
    *,
    chunk_id: str,
    work: str,
    text: str,
    author: str = "Народна творчість",
    year: int = 1600,
    source_file: str = "ukrlib-narod-dumy",
) -> tuple[Any, ...]:
    return (
        chunk_id,
        author,
        work,
        f"{chunk_id}_work",
        year,
        "song",
        "middle_ukrainian",
        source_file,
        "https://example.test/source",
        text,
    )
