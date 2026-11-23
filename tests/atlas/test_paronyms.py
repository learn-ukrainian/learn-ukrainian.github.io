"""Synthetic-fixture unit tests for the Atlas paronym extractor and builder.

No live SQLite databases, VESUM store, or network calls are touched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.atlas.paronyms.build import build_paronym_registry
from scripts.atlas.paronyms.extractor import SourceDocument, extract_from_document
from scripts.atlas.paronyms.miyklas import load_miyklas_documents, parse_miyklas_html


def _doc(text: str, *, source_type: str = "textbook", chunk_id: str = "book_s0001") -> SourceDocument:
    return SourceDocument(
        source_type=source_type,
        source_file="synthetic-book",
        chunk_id=chunk_id,
        locator="Сторінка 1",
        title="Сторінка 1",
        text=text,
    )


def test_pdf_line_wrap_dehyphenation_and_inline_gloss_extraction() -> None:
    """Defect class: PDF line-wrap hyphens splitting Ukrainian paronyms across lines."""
    doc = _doc(
        "§ 9. Пароніми\n"
        "Пароніми можуть бути: однокореневими словами: організаційний — ор-\n"
        "ганізований; еміграція — іммігра-\n"
        "ція.\n"
        "Наприклад: абонемент (документ на користування) — абонент (власник абонемента).\n"
    )
    atts = extract_from_document(doc)
    by_pair = {(a.member_a.word, a.member_b.word): a for a in atts}

    assert ("організаційний", "організований") in by_pair
    assert ("еміграція", "імміграція") in by_pair
    assert ("абонемент", "абонент") in by_pair
    ab = by_pair[("абонемент", "абонент")]
    assert ab.member_a.meaning == "документ на користування"
    assert ab.member_b.meaning == "власник абонемента"
    assert ab.chunk_id == "book_s0001"
    assert "абонемент" in ab.quoted_line


def test_rejects_antonyms_multiple_choice_distractors_and_disclaimers() -> None:
    """Defect class: false-positive extraction of antonyms, test distractors, and disclaimers."""
    doc = _doc(
        "§ 45. Стилістичне використання синонімів, антонімів і паронімів\n"
        "Пароніми — це слова, близькі за звучанням: ефектний — ефективний.\n"
        "Не є паронімічними слова типу газ — гас, короб — короп.\n"
        "Антонімами називають протилежні за значенням слова: чорний — білий, високий — низький.\n"
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


def test_slash_dictionary_extracts_triplets_with_meanings_and_examples() -> None:
    """Defect class: losing third triplet member or definitions in slash-headed dictionaries."""
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


def test_miyklas_html_parser_preserves_inline_morpheme_spans_and_groups(tmp_path: Path) -> None:
    """Defect class: splitting highlighted morphemes across <span> tags or merging dictionary groups."""
    dict_html = (
        '<div id="taskhtml">'
        '<div class="gxst-title"><span>А</span></div>'
        '<div><span>Абрис</span> – контур предмета.<br/>'
        '<span>Обрис</span> – загальний вигляд предмета.</div>'
        '<div>&nbsp;</div>'
        '<div><span>Інформативний</span> – повний інформації (інформативний виклад). '
        '<span>Інформаційний</span> – опрацьовує інформацію (інформаційне бюро).</div>'
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
    theory_atts = extract_from_document(
        _doc(theory_text, source_type="miyklas", chunk_id="mk-theory")
    )
    assert {(a.member_a.word, a.member_b.word) for a in theory_atts} == {
        ("передній", "передовий"),
        ("постановка", "установка"),
    }

    # Verify load_miyklas_documents fails closed on tampered SHA-256.
    snap = tmp_path / "bad.json"
    snap.write_text(
        json.dumps(
            {
                "schema_version": "miyklas-paronyms-raw.v1",
                "pages": [
                    {
                        "page_id": "mk-1",
                        "grade": "5",
                        "kind": "theory",
                        "title": "Пароніми",
                        "url": "https://example.invalid/paronimy",
                        "fetched_at_utc": "2026-11-23T00:00:00Z",
                        "raw_html_sha256": "0" * 64,
                        "text_sha256": hashlib.sha256(b"different").hexdigest(),
                        "text": theory_text,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        load_miyklas_documents(snap)


def test_vesum_gating_lemmatization_and_a1_coverage_accounting() -> None:
    """Defect class: unverified/typo/multiword members leaking into verified pairs or miscounted A1 coverage."""
    tb_doc = _doc(
        "§ 7. Пароніми\n"
        "Приклади паронімів: адреса — адрес, мимохіть — михохідь, греби — гриби.\n"
        "1. Перепишіть, вибираючи з дужок потрібне слово.\n"
        "Суспільство поважає (громадську, громадянську) позицію.\n"
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
    }

    def fake_vesum(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {w: fake_vesum_db.get(w, []) for w in words}

    registry = build_paronym_registry(
        [tb_doc, mk_doc],
        vesum_lookup=fake_vesum,
        a1_lemma_sets={
            "inventory_lemmas": {"адреса", "книга"},
            "single_token_keys": {"адреса", "книга"},
            "slice_2_to_6_lemmas": {"адреса"},
        },
    )

    verified_by_id = {p["pair_id"]: p for p in registry["pairs"]}
    unverified_by_id = {u["pair_id"]: u for u in registry["unverified"]}

    assert set(verified_by_id) == {
        "адрес|адреса",
        "греби|гриби",
        "громадський|громадянський",
    }
    # Cross-POS surface pair stays on exact attested forms; same-POS choice exercise lemmatizes.
    assert verified_by_id["греби|гриби"]["surface_form_pair"] is True
    assert verified_by_id["громадський|громадянський"]["surface_form_pair"] is False
    assert verified_by_id["адрес|адреса"]["source_types"] == ["miyklas", "textbook"]

    # Unattested typo and multiword headword go strictly to `unverified` with typed reasons.
    assert set(unverified_by_id) == {"мимохіть|михохідь", "на протязі|протягом"}
    assert unverified_by_id["мимохіть|михохідь"]["unverified_members"] == [
        {"word": "михохідь", "reason": "not_attested_in_vesum"}
    ]
    assert unverified_by_id["на протязі|протягом"]["unverified_members"] == [
        {"word": "на протязі", "reason": "multiword_not_in_vesum"}
    ]

    assert registry["counts"]["verified_pairs"] == 3
    assert registry["counts"]["unverified_pairs"] == 2
    assert registry["counts"]["a1_inventory_lemmas_with_paronym"] == 1
    assert registry["counts"]["a1_slices_2_to_6_lemmas_with_paronym"] == 1
    assert registry["a1_coverage"]["matched_a1_lemmas"] == [
        {"lemma": "адреса", "paronyms": ["адрес"], "pair_ids": ["адрес|адреса"]}
    ]
