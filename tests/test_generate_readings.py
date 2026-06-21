from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.readings.generate_readings import (
    CorpusText,
    PrimaryReadingCandidate,
    VerificationResult,
    generate_for_modules,
)

OI_SYVA_TEXT = """ОЙ СИВАЯ ТА І ЗОЗУЛЕЧКА

Ой сивая та і зозулечка.

Приспів:

Щедрий вечір, добрий вечір, 1

Добрим людям на здоров'я!

Усі сади та і облітала,

А в одному та і не бувала.

А в тім саду три тереми:

У першому — красне сонце,

У другому — ясен місяць,

А в третьому — дрібні зірки.

Ясен місяць — пан господар,

Красне сонце — жона його,

Дрібні зірки — його дітки.

1 Повторюється після кожного рядка."""


YAK_SHCHE_TEXT = """ЯК ЩЕ НЕ БУЛО ПОЧАТКУ СВІТА

Як ще не було початку світа,

Тогди не було неба, ні землі,

А но лем було синєє море,

А серед моря зелений явір."""


def test_generate_reading_from_primary_block_and_packet_hint(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, include_existing_carol=False)
    db_path = _write_sources_db(tmp_path)
    output_dir = tmp_path / "readings"

    summary = generate_for_modules([module_dir], output_dir=output_dir, sources_db=db_path)

    generated = output_dir / "shchedrivka-oi-syvaia-ta-i-zozulechka.mdx"
    assert [item.slug for item in summary.written] == ["shchedrivka-oi-syvaia-ta-i-zozulechka"]
    assert summary.skipped == ()
    text = generated.read_text(encoding="utf-8")
    assert 'title: "«Ой сивая та і зозулечка» (щедрівка з тріадою світил)"' in text
    assert 'public_domain: true' in text
    assert "<PrimaryReading>" in text
    assert "> Щедрий вечір, добрий вечір, 1" in text
    assert "source_chunk_id: 70435c0b_c0000" in text


def test_existing_hand_authored_reading_is_not_clobbered_and_generated_is_idempotent(
    tmp_path: Path,
) -> None:
    module_dir = _write_module(tmp_path, include_existing_carol=True)
    db_path = _write_sources_db(tmp_path)
    output_dir = tmp_path / "readings"
    output_dir.mkdir()
    hand_authored = output_dir / "koliadka-yak-shche-ne-bulo.mdx"
    hand_authored.write_text("hand-authored\n", encoding="utf-8")

    first = generate_for_modules([module_dir], output_dir=output_dir, sources_db=db_path)
    second = generate_for_modules([module_dir], output_dir=output_dir, sources_db=db_path)

    assert hand_authored.read_text(encoding="utf-8") == "hand-authored\n"
    assert [item.action for item in first.written] == ["created"]
    assert first.existing[0].action == "existing-hand-authored"
    assert second.written == ()
    assert sorted(item.action for item in second.existing) == [
        "existing-hand-authored",
        "unchanged",
    ]


def test_verification_failure_skips_without_writing(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path, include_existing_carol=False)
    db_path = _write_sources_db(tmp_path)
    output_dir = tmp_path / "readings"

    def fail_verifier(
        _candidate: PrimaryReadingCandidate,
        _corpus: CorpusText,
    ) -> VerificationResult:
        return VerificationResult(False, 0.0, "forced failure")

    summary = generate_for_modules(
        [module_dir],
        output_dir=output_dir,
        sources_db=db_path,
        quote_verifier=fail_verifier,
    )

    assert summary.written == ()
    assert summary.skipped[0].reason == "quote verification failed: forced failure"
    assert not (output_dir / "shchedrivka-oi-syvaia-ta-i-zozulechka.mdx").exists()


def _write_module(tmp_path: Path, *, include_existing_carol: bool) -> Path:
    module_dir = tmp_path / "curriculum" / "l2-uk-en" / "folk" / "koliadky-shchedrivky"
    module_dir.mkdir(parents=True)
    blocks = []
    if include_existing_carol:
        blocks.append(
            """:::primary-reading
> Як ще не було початку світа,
> Тогди не було неба, ні землі,

— Народна творчість, «Як ще не було початку світа» (космогонічна колядка)
::: """
        )
    blocks.append(
        """:::primary-reading
> Щедрий вечір, добрий вечір,
> Добрим людям на здоров'я!
>
> Усі сади та і облітала,
> А в одному та і не бувала.
> А в тім саду три тереми:
> У першому — красне сонце,
> У другому — ясен місяць,
> А в третьому — дрібні зірки.
> Ясен місяць — пан господар,
> Красне сонце — жона його,
> Дрібні зірки — його дітки.

— Народна творчість, «Ой сивая та і зозулечка» (щедрівка з тріадою світил)
::: """
    )
    (module_dir / "module.md").write_text("# Колядки та щедрівки\n\n" + "\n\n".join(blocks), encoding="utf-8")
    (module_dir / "resources.yaml").write_text(
        """
- title: Народна творчість, «Як ще не було початку світа» (космогонічна колядка)
  role: textbook
  source_ref: Народна творчість, «Як ще не було початку світа» (космогонічна колядка)
  packet_chunk_id: 61bfde21_c0000
  notes: corpus row
- title: Народна творчість, «Ой сивая та і зозулечка» (щедрівка з тріадою світил)
  role: textbook
  source_ref: Народна творчість, «Ой сивая та і зозулечка» (щедрівка з тріадою світил)
  packet_chunk_id: 70435c0b_c0000
  notes: corpus row
""",
        encoding="utf-8",
    )
    return module_dir


def _write_sources_db(tmp_path: Path) -> Path:
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
        [
            (
                "61bfde21_c0000",
                "Народна творчість",
                "Народна творчість. Як ще не було початку світа",
                "narodna_tvorchist_yak_shche_ne_bulo_pochatku_svita",
                1600,
                "carol",
                "middle_ukrainian",
                "ukrlib-narod-dumy",
                "https://example.test/yak",
                YAK_SHCHE_TEXT,
            ),
            (
                "70435c0b_c0000",
                "Народна творчість",
                "Народна творчість. Ой сивая та і зозуленька",
                "narodna_tvorchist_oy_syvaya_ta_i_zozulenka",
                1600,
                "carol",
                "middle_ukrainian",
                "ukrlib-narod-dumy",
                "https://example.test/oi",
                OI_SYVA_TEXT,
            ),
        ],
    )
    conn.commit()
    conn.close()
    return db_path
