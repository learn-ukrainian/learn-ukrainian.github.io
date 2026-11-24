"""Synthetic-fixture unit tests for the Atlas paronym extractor and builder.

No live SQLite databases, VESUM store, or network calls are touched.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import pytest

from scripts.atlas.paronyms.build import A1InventoryError, build_paronym_registry, load_a1_lemma_sets
from scripts.atlas.paronyms.extractor import SourceDocument, extract_from_document
from scripts.atlas.paronyms.miyklas import (
    MiyKlasFetchError,
    _MiyKlasRedirectHandler,
    load_miyklas_documents,
    parse_miyklas_html,
)


def _doc(text: str, *, source_type: str = "textbook", chunk_id: str = "book_s0001") -> SourceDocument:
    return SourceDocument(
        source_type=source_type,
        source_file="synthetic-book",
        chunk_id=chunk_id,
        locator="Сторінка 1",
        title="Сторінка 1",
        text=text,
    )


def _fold(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def test_pdf_line_wrap_dehyphenation_and_inline_gloss_extraction() -> None:
    """Defect class: PDF line-wrap hyphens, note-boundary corruption, page footers, or raw quote drift."""
    doc = _doc(
        "§ 9. Пароніми\n"
        "Пароніми можуть бути: однокореневими словами: організаційний — ор-\n"
        "ганізований; еміграція — іммігра-\n"
        "ція.\n"
        "Наприклад: абонемент (документ на користування) — абонент (власник абонемента).\n"
        "6. Запам’ятайте значення паронімічних прикметників.\n"
        "Літний — який стосується польоту, літання. Літній — 1) який стосується\n"
        "літа; 2) немолодий.\n"
        "133 133\n"
        "Розрізняйте пароніми серцевий — сердешний.\n"
        "Серцевий — пов’язаний із серцем: серцевий м’яз.\n"
        "Сердешний — бідолашний, нещасний: Сердешна жінка припадала з горя (А. Кащенко).\n"
        "168\n"
        "Розрізняйте пароніми гривна — гривня.\n"
        "Гривна — давня прикраса.\n"
        "Гривня — назва грошової одиниці. Скорочено позначаємо грн (без крапки в кінці).\n"
    )
    atts = extract_from_document(doc)
    by_pair = {(a.member_a.word, a.member_b.word): a for a in atts}

    assert ("організаційний", "організований") in by_pair
    assert ("еміграція", "імміграція") in by_pair
    assert ("абонемент", "абонент") in by_pair
    assert ("літний", "літній") in by_pair
    assert ("сердешний", "серцевий") in by_pair
    assert ("гривна", "гривня") in by_pair

    # Every quoted_line must stay verbatim inside the raw source text after whitespace folding.
    folded_raw = _fold(doc.text)
    for att in atts:
        assert _fold(att.quoted_line) in folded_raw
    assert "ор- ганізований" in by_pair[("організаційний", "організований")].quoted_line

    ab = by_pair[("абонемент", "абонент")]
    assert ab.member_a.meaning == "документ на користування"
    assert ab.member_b.meaning == "власник абонемента"
    assert ab.chunk_id == "book_s0001"

    # Author credit stays attached to the literary example, and trailing page numbers are excluded.
    ss = by_pair[("сердешний", "серцевий")]
    assert ss.member_a.meaning == "бідолашний, нещасний"
    assert ss.member_a.example == "Сердешна жінка припадала з горя (А. Кащенко)"
    assert "168" not in ss.quoted_line

    # Abbreviation note is NOT misclassified as a usage example.
    gg = by_pair[("гривна", "гривня")]
    assert gg.member_b.meaning == "назва грошової одиниці. Скорочено позначаємо грн (без крапки в кінці)"
    assert gg.member_b.example is None

    # Paronymic-adjective definition box excludes trailing page footer.
    ll = by_pair[("літний", "літній")]
    assert ll.member_a.meaning == "який стосується польоту, літання"
    assert "133" not in ll.quoted_line


def test_rejects_antonyms_multiple_choice_distractors_and_disclaimers() -> None:
    """Defect class: false-positive extraction of antonyms, distractors, disclaimers, or leaked choice context."""
    doc = _doc(
        "§ 45. Стилістичне використання синонімів, антонімів і паронімів\n"
        "Пароніми — це слова, близькі за звучанням: ефектний — ефективний.\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
        "Не є паронімічними слова типу газ — гас, короб — короп.\n"
        "Антонімами називають протилежні за значенням слова: чорний — білий, високий — низький.\n"
        "2. Доберіть антоніми до поданих слів: вхід — вихід, добрий — недобрий.\n"
        "6. Пароніми вжито в рядку\n"
        "А упертий — покладистий\n"
        "Б чарівний — чепурний\n"
        "В логічний — алогічний\n"
        "Г ніжний — пестливий\n"
        "4. Випишіть лише ті пари слів, у яких заміна змінює значення.\n"
        "Вдома — удома, вранці — уранці.\n"
        "Ми ознайомилися з авторкою чудових картин — Катериною.\n"
    )
    atts = extract_from_document(doc)
    pairs = {(a.member_a.word, a.member_b.word) for a in atts}

    assert pairs == {("ефективний", "ефектний")}

    # Lowercase wrapped conjunction "і " must NOT split a paronym choice exercise, while a second
    # generic choice exercise must NOT inherit paronym context by chaining.
    wrapped_doc = _doc(
        "82. Прочитайте. Визначте пароніми.\n"
        "83. Перепишіть, вибираючи з дужок потрібне слово.\n"
        "Ставлення людей до подій\n"
        "і процесів називають (громадською, громадянською) думкою.\n"
        "84. Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
    )
    wrapped_pairs = {(a.member_a.word, a.member_b.word) for a in extract_from_document(wrapped_doc)}
    assert wrapped_pairs == {("громадською", "громадянською")}


def test_slash_dictionary_extracts_triplets_with_meanings_and_examples() -> None:
    """Defect class: losing third triplet member, definitions, or raw quote fidelity in slash-headed dictionaries."""
    doc = _doc(
        "Додаток 2\n"
        "СЛОВНИЧОК ПАРОНІМІВ\n"
        "Сердечний // сердешний // серцевий\n"
        "Сердечний – добрий, щирий. Сердечна людина.\n"
        "Сердешний – нещасний. Сердешна жінка.\n"
        "Серцевий – пов’язаний із серцем. Серцевий ритм.\n"
    )
    atts = extract_from_document(doc)
    by_pair = {(a.member_a.word, a.member_b.word): a for a in atts}

    assert set(by_pair) == {
        ("сердечний", "сердешний"),
        ("сердечний", "серцевий"),
        ("сердешний", "серцевий"),
    }
    pair = by_pair[("сердечний", "серцевий")]
    assert pair.member_a.meaning == "добрий, щирий"
    assert pair.member_a.example == "Сердечна людина"
    assert pair.member_b.meaning == "пов’язаний із серцем"
    assert pair.member_b.example == "Серцевий ритм"
    assert _fold(pair.quoted_line) in _fold(doc.text)


def test_miyklas_html_parser_preserves_inline_morpheme_spans_and_groups(tmp_path: Path) -> None:
    """Defect class: split morpheme spans, invalid snapshot provenance, or unvalidated off-domain redirects."""
    dict_html = (
        '<div id="taskhtml">'
        '<div class="gxst-title"><span>А</span></div>'
        "<div><span>Абрис</span> – контур предмета.<br/>"
        "<span>Обрис</span> – загальний вигляд предмета.</div>"
        "<div>&nbsp;</div>"
        "<div><span>Інформативний</span> – повний інформації (інформативний виклад). "
        "<span>Інформаційний</span> – опрацьовує інформацію (інформаційне бюро).</div>"
        "</div>"
    ).encode()
    dict_text = parse_miyklas_html(dict_html, kind="dictionary", title="Короткий словник паронімів")
    dict_atts = extract_from_document(_doc(dict_text, source_type="miyklas", chunk_id="mk-dict"))
    assert {(a.member_a.word, a.member_b.word) for a in dict_atts} == {
        ("абрис", "обрис"),
        ("інформативний", "інформаційний"),
    }

    theory_html = (
        '<div id="taskhtml">'
        "<div>Пароніми: Перед<span>н</span>ій — перед<span>ов</span>ий, "
        "<span>по</span>становка — <span>у</span>становка.</div>"
        "</div>"
    ).encode()
    theory_text = parse_miyklas_html(theory_html, kind="theory", title="Пароніми")
    assert "Передній — передовий" in theory_text
    assert "постановка — установка" in theory_text
    theory_atts = extract_from_document(_doc(theory_text, source_type="miyklas", chunk_id="mk-theory"))
    assert {(a.member_a.word, a.member_b.word) for a in theory_atts} == {
        ("передній", "передовий"),
        ("постановка", "установка"),
    }

    valid_page = {
        "page_id": "mk-1",
        "grade": "5",
        "kind": "theory",
        "title": "Пароніми",
        "url": "https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/paronimy",
        "http_status": 200,
        "fetched_at_utc": "2026-11-23T00:00:00Z",
        "raw_html_sha256": "a" * 64,
        "text_sha256": hashlib.sha256(theory_text.encode("utf-8")).hexdigest(),
        "text": theory_text,
    }

    def _write_snap(name: str, page_override: dict[str, object]) -> Path:
        p = tmp_path / name
        p.write_text(
            json.dumps({"schema_version": "miyklas-paronyms-raw.v1", "pages": [page_override]}),
            encoding="utf-8",
        )
        return p

    # Tampered text digest, missing/string http_status, and invalid raw_html_sha256 all fail closed.
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_miyklas_documents(_write_snap("bad-text.json", {**valid_page, "text_sha256": "b" * 64}))
    no_status = {k: v for k, v in valid_page.items() if k != "http_status"}
    with pytest.raises(ValueError, match="http_status"):
        load_miyklas_documents(_write_snap("no-status.json", no_status))
    with pytest.raises(ValueError, match="http_status"):
        load_miyklas_documents(_write_snap("str-status.json", {**valid_page, "http_status": "200"}))
    with pytest.raises(ValueError, match="raw_html_sha256"):
        load_miyklas_documents(_write_snap("bad-raw.json", {**valid_page, "raw_html_sha256": "not-hex"}))

    # Redirect handler refuses off-domain or non-HTTPS redirects BEFORE following them.
    handler = _MiyKlasRedirectHandler()
    req = urllib.request.Request("https://www.miyklas.com.ua/p/test")
    with pytest.raises(MiyKlasFetchError, match="Refusing non-MiyKlas HTTPS URL"):
        handler.redirect_request(req, None, 302, "Found", {}, "https://evil.invalid/steal")
    with pytest.raises(MiyKlasFetchError, match="Refusing non-MiyKlas HTTPS URL"):
        handler.redirect_request(req, None, 301, "Moved", {}, "http://www.miyklas.com.ua/p/test")


def test_vesum_gating_lemmatization_and_a1_coverage_accounting(tmp_path: Path) -> None:
    """Defect class: unverified/canonical-missing/multiword members leaking into pairs or malformed inventory accepted."""
    tb_doc = _doc(
        "§ 7. Пароніми\n"
        "Приклади паронімів: адреса — адрес, мимохіть — михохідь, греби — гриби.\n"
        "1. Перепишіть, вибираючи з дужок потрібне слово.\n"
        "Суспільство поважає (громадську, громадянську) позицію та (тактичну, тактовну) поведінку.\n"
    )
    mk_doc = _doc(
        "Короткий словник паронімів\n\n"
        "На протязі – під дією вітру.\n"
        "Протягом – упродовж часу.\n\n"
        "Адрес – письмове вітання.\n"
        "Адреса – місце проживання.\n",
        source_type="miyklas",
        chunk_id="mk-dict",
    )

    fake_vesum_db: dict[str, list[dict[str, str]]] = {
        "адрес": [{"lemma": "адрес", "pos": "noun"}],
        "адреса": [{"lemma": "адреса", "pos": "noun"}],
        "мимохіть": [{"lemma": "мимохіть", "pos": "adv"}],
        "михохідь": [],  # PDF typo, unattested in VESUM
        "протягом": [{"lemma": "протягом", "pos": "prep"}],
        "греби": [{"lemma": "гребти", "pos": "verb"}],
        "гриби": [{"lemma": "гриб", "pos": "noun"}],
        "громадську": [{"lemma": "громадський", "pos": "adj"}],
        "громадянську": [{"lemma": "громадянський", "pos": "adj"}],
        "громадський": [{"lemma": "громадський", "pos": "adj"}],
        "громадянський": [{"lemma": "громадянський", "pos": "adj"}],
        # Pass-1 inflected forms exist, but pass-2 canonical lemmas return empty analyses -> must route to unverified.
        "тактичну": [{"lemma": "тактичний", "pos": "adj"}],
        "тактовну": [{"lemma": "тактовний", "pos": "adj"}],
        "тактичний": [],
        "тактовний": [],
    }

    def fake_vesum(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {w: fake_vesum_db.get(w, []) for w in words}

    registry = build_paronym_registry(
        [tb_doc, mk_doc],
        vesum_lookup=fake_vesum,
        sum20_lookup=lambda words: {},
        a1_lemma_sets={
            "inventory_lemmas": {"адреса", "книга"},
            "single_token_keys": {"адреса", "книга"},
        },
    )

    verified_by_id = {p["pair_id"]: p for p in registry["pairs"]}
    unverified_by_id = {u["pair_id"]: u for u in registry["unverified"]}

    assert set(verified_by_id) == {
        "адрес|адреса",
        "греби|гриби",
        "громадський|громадянський",
    }
    for pair in registry["pairs"]:
        assert all(m["vesum_verified"] is True for m in pair["members"])
    assert verified_by_id["греби|гриби"]["surface_form_pair"] is True
    assert verified_by_id["громадський|громадянський"]["surface_form_pair"] is False
    assert verified_by_id["адрес|адреса"]["source_types"] == ["miyklas", "textbook"]

    # Unattested typo, multiword headword, and pass-2 canonical-missing pair all route to `unverified`.
    assert set(unverified_by_id) == {
        "мимохіть|михохідь",
        "на протязі|протягом",
        "тактичний|тактовний",
    }
    assert unverified_by_id["мимохіть|михохідь"]["unverified_members"] == [
        {"word": "михохідь", "reason": "not_attested_in_vesum"}
    ]
    assert unverified_by_id["на протязі|протягом"]["unverified_members"] == [
        {"word": "на протязі", "reason": "multiword_not_in_vesum"}
    ]
    assert unverified_by_id["тактичний|тактовний"]["unverified_members"] == [
        {"word": "тактичний", "reason": "not_attested_in_vesum"},
        {"word": "тактовний", "reason": "not_attested_in_vesum"},
    ]

    assert registry["counts"]["verified_pairs"] == 3
    assert registry["counts"]["unverified_pairs"] == 3
    assert registry["counts"]["a1_inventory_lemmas_with_paronym"] == 1
    assert registry["a1_coverage"]["matched_a1_lemmas"] == [
        {"lemma": "адреса", "paronyms": ["адрес"], "pair_ids": ["адрес|адреса"]}
    ]

    # Malformed A1 inventory (missing rows, missing resolved lemma, non-string lemma/key,
    # missing row id, or a missing file) fails closed with A1InventoryError naming the file.
    missing_rows = tmp_path / "missing-rows.json"
    missing_rows.write_text(json.dumps({"schema_version": "v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="rows"):
        load_a1_lemma_sets(missing_rows)

    missing_resolved_lemma = tmp_path / "missing-resolved-lemma.json"
    missing_resolved_lemma.write_text(
        json.dumps({"rows": [{"id": "r1", "key": "адреса", "mapping": {"resolution": "resolved"}}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="lemma"):
        load_a1_lemma_sets(missing_resolved_lemma)

    bad_lemma = tmp_path / "bad-lemma.json"
    bad_lemma.write_text(
        json.dumps({"rows": [{"id": "r1", "key": "адреса", "mapping": {"resolution": "resolved", "lemma": 123}}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="lemma"):
        load_a1_lemma_sets(bad_lemma)

    bad_key = tmp_path / "bad-key.json"
    bad_key.write_text(
        json.dumps({"rows": [{"id": "r1", "key": 42, "mapping": {"resolution": "resolved", "lemma": "адреса"}}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="key"):
        load_a1_lemma_sets(bad_key)

    missing_id = tmp_path / "a1-v1-inventory.json"
    missing_id.write_text(
        json.dumps(
            {
                "rows": [
                    {"id": "r1", "key": "адреса", "mapping": {"resolution": "resolved", "lemma": "адреса"}},
                    {"key": "мова", "mapping": {"resolution": "resolved", "lemma": "мова"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(A1InventoryError, match=r"row 'id' at index 1 in a1-v1-inventory\.json"):
        load_a1_lemma_sets(missing_id)

    with pytest.raises(A1InventoryError, match="Missing A1 inventory"):
        load_a1_lemma_sets(tmp_path / "absent" / "a1-v1-inventory.json")


def test_inline_paronym_definition_does_not_open_lesson_without_disclaimer() -> None:
    """Defect class: inline/wrapped paronym definitions or unnumbered prompts leaking lesson state without a disclaimer."""
    # Mixed-topic document: inline definition with NO disclaimer line before a generic choice exercise.
    dash_def_doc = _doc(
        "§ 45. Стилістичне використання синонімів, антонімів і паронімів\n"
        "Пароніми — це слова, близькі за звучанням: ефектний — ефективний.\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(dash_def_doc)} == {
        ("ефективний", "ефектний")
    }

    # Line-wrapped definition right after "Пароніми" or "1. Пароніми" (next line starts with dash or "(")
    # must NOT be treated as a dedicated heading.
    wrapped_dash_doc = _doc(
        "§ 45. Стилістичне використання синонімів, антонімів і паронімів\n"
        "Пароніми\n"
        "— це слова, близькі за звучанням: ефектний — ефективний.\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома).\n"
        "2. Перепишіть, вибираючи з дужок потрібне слово.\n"
        "Він вийшов (вранці, уранці).\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(wrapped_dash_doc)} == {
        ("ефективний", "ефектний")
    }

    wrapped_paren_doc = _doc(
        "Лексикологія\n"
        "1. Пароніми\n"
        "(від гр. para — біля) — це слова: адресат — адресант.\n"
        "2. Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(wrapped_paren_doc)} == {
        ("адресант", "адресат")
    }

    # Unnumbered generic choice exercise (indented next-line or same-line after `».`) after an
    # inline definition must NOT inherit its local cue.
    unnumbered_choice_doc = _doc(
        "§ 45. Стилістичне використання синонімів, антонімів і паронімів\n"
        "Пароніми — це слова, близькі за звучанням: ефектний — ефективний.\n"
        "   Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(unnumbered_choice_doc)} == {
        ("ефективний", "ефектний")
    }

    quoted_sameline_doc = _doc(
        "Лексикологія\n"
        "Пароніми — це слова типу «ефектний — ефективний». Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома) і вийшов (вранці, уранці).\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(quoted_sameline_doc)} == {
        ("ефективний", "ефектний")
    }

    # Explicit § heading followed by a lowercase pair list and bare dedicated heading later in a
    # mixed-topic chunk STILL open paronym lesson mode.
    section_lower_pair_doc = _doc(
        "§ 9. Пароніми\n"
        "ефектний — ефективний.\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "У нашій школі дуже (дружний, дружній) колектив.\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(section_lower_pair_doc)} == {
        ("дружний", "дружній"),
        ("ефективний", "ефектний"),
    }

    bare_later_heading_doc = _doc(
        "Антонімами називають протилежні за значенням слова: чорний — білий.\n"
        "Пароніми\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "У нашій школі дуже (дружний, дружній) колектив.\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(bare_later_heading_doc)} == {
        ("дружний", "дружній")
    }


def test_lesson_mode_starts_at_dedicated_heading_not_before() -> None:
    """Defect class: a dedicated paronym heading on lines 2-4 opening lesson mode for the text above it."""
    doc = _doc(
        "Виберіть із дужок потрібне слово.\n"
        "Він залишився (вдома, удома).\n"
        "§ 9. Пароніми\n"
        "1. Виберіть із дужок потрібне слово.\n"
        "У нашій школі дуже (дружний, дружній) колектив.\n"
    )
    assert {(a.member_a.word, a.member_b.word) for a in extract_from_document(doc)} == {("дружний", "дружній")}


def test_build_refuses_unpinned_corpus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defect classes: the one-shot extractor running on a corpus other than the reviewed one,
    and an input failure escaping the refusal boundary as an untyped traceback.

    An unpinned registry, a changed textbook result set or a changed MiyKlas snapshot must
    refuse under build and ``--check`` before extraction, leaving every file untouched. So must
    every input that cannot be loaded, whatever the failure (an error raised in the pin comparison,
    input that is not I-JSON, a broken A1 inventory).
    """
    import sqlite3

    from scripts.atlas.paronyms import build as paronym_build

    sources_db = tmp_path / "sources.db"
    with sqlite3.connect(sources_db) as conn:
        conn.execute(
            "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, "
            "title TEXT, grade TEXT, author TEXT, text TEXT)"
        )
        conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(text, content='textbooks', content_rowid='id')")
        conn.execute(
            "INSERT INTO textbooks VALUES (1, 'book_s0001', 'synthetic-book', 'Сторінка 1', '10', 'Автор', ?)",
            ("§ 9. Пароніми\nАдресат — адресант.\n",),
        )
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES ('rebuild')")

    page_text = "Пароніми: дружний — дружній."
    snapshot = {
        "schema_version": "miyklas-paronyms-raw.v1",
        "pages": [
            {
                "page_id": "miyklas-5-klas-paronimy",
                "grade": "5",
                "kind": "theory",
                "title": "Пароніми",
                "url": "https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/paronimy",
                "http_status": 200,
                "fetched_at_utc": "2026-11-23T00:00:00Z",
                "raw_html_sha256": "a" * 64,
                "text_sha256": hashlib.sha256(page_text.encode("utf-8")).hexdigest(),
                "text": page_text,
            }
        ],
    }
    snapshot_path = tmp_path / "miyklas.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    registry_path = tmp_path / "paronyms-v1.json"
    missing_a1 = tmp_path / "missing-a1-inventory.json"
    argv = [
        "--sources-db",
        str(sources_db),
        "--miyklas-raw",
        str(snapshot_path),
        "--output",
        str(registry_path),
        "--a1-inventory",
        str(missing_a1),
    ]

    def _assert_refused(registry_text: str, reason: str, run_argv: list[str] = argv) -> None:
        # Every refusal is exit 2, so each case also asserts its own reason: a later stage that
        # refuses for another cause must not stand in for the gate under test.
        registry_path.write_text(registry_text, encoding="utf-8")
        snapshot_bytes = snapshot_path.read_bytes()
        for mode in ([], ["--check"]):
            capsys.readouterr()
            assert paronym_build.main([*run_argv, *mode]) == 2
            err = capsys.readouterr().err
            assert err.startswith("REFUSED: ") and reason in err, err[:300]
            assert registry_path.read_text(encoding="utf-8") == registry_text
            assert snapshot_path.read_bytes() == snapshot_bytes

    # A registry without a recorded corpus fingerprint (the pre-pin shape) pins nothing.
    _assert_refused(
        json.dumps({"schema_version": "atlas-paronyms.v1", "sources_corpus": {}}),
        "records no sources_corpus.corpus_fingerprint",
    )

    # A registry pinned to a different textbook result set refuses the live corpus.
    stale_pin = {"textbooks_fts_query": "паронім*", "textbooks_result_rows": 1, "textbooks_result_sha256": "0" * 64}
    _assert_refused(
        json.dumps({"sources_corpus": {"corpus_fingerprint": stale_pin}}, ensure_ascii=False),
        "corpus differs from the reviewed corpus",
    )

    # Any exception in the pin comparison is a typed refusal. A pin nested deep enough to overflow
    # the stack raised RecursionError there (#13389); stack depth varies by host, so raise it directly.
    def _overflow(pinned: object, live: object) -> None:
        raise RecursionError("maximum recursion depth exceeded")

    with monkeypatch.context() as patched:
        patched.setattr(paronym_build, "require_pinned_corpus", _overflow)
        _assert_refused(
            json.dumps({"sources_corpus": {"corpus_fingerprint": stale_pin}}, ensure_ascii=False),
            "RecursionError: maximum recursion depth exceeded",
        )

    # The reviewed corpus passes the gate and reaches the next stage, the A1 inventory load,
    # whose failure is refused inside the same boundary.
    from scripts.atlas.paronyms.miyklas import load_miyklas_documents

    live = paronym_build.compute_corpus_fingerprint(
        paronym_build.load_textbook_paronym_documents(sources_db), load_miyklas_documents(snapshot_path)[0]
    )
    pinned_registry = json.dumps({"sources_corpus": {"corpus_fingerprint": live}}, ensure_ascii=False)
    _assert_refused(pinned_registry, f"REFUSED: {A1InventoryError.__name__}: Missing A1 inventory")

    # Every JSON input is parsed as I-JSON (RFC 7493): a duplicate member name refuses, even when
    # the parser would keep a valid last value, and so does a string that is not valid Unicode.
    _assert_refused('{"sources_corpus": "\\ud800", ' + pinned_registry[1:], "duplicate member name 'sources_corpus'")
    bad_a1 = tmp_path / "bad-a1-inventory.json"
    bad_row = {"id": "r1", "key": "адресат", "mapping": {"resolution": "resolved", "lemma": "\ud800"}}
    bad_a1.write_text(json.dumps({"rows": [bad_row]}), encoding="utf-8")
    _assert_refused(pinned_registry, "surrogates not allowed", [*argv[:-1], str(bad_a1)])

    # A changed MiyKlas snapshot under the same pin refuses.
    snapshot["pages"][0]["grade"] = "6"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    _assert_refused(pinned_registry, "miyklas_snapshot_sha256: pinned")

    # Changed page text that no longer matches its own text_sha256 is a typed refusal, not a traceback.
    snapshot["pages"][0]["grade"] = "5"
    snapshot["pages"][0]["text"] = page_text + " Пароніми."
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    _assert_refused(pinned_registry, "Text SHA-256 mismatch")

    # A field that is not valid Unicode (a lone surrogate) cannot be fingerprinted: typed refusal.
    snapshot["pages"][0]["text"] = page_text
    snapshot["pages"][0]["title"] = "\ud800"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    _assert_refused(pinned_registry, "surrogates not allowed")

    # An extra pinned key, even one set to null, is not the reviewed pin.
    snapshot["pages"][0]["title"] = "Пароніми"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    extra_key = json.dumps({"sources_corpus": {"corpus_fingerprint": {**live, "unknown_field": None}}})
    _assert_refused(extra_key, "unknown_field: pinned None")
