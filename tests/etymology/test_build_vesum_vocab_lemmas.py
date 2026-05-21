"""Tests for the Starlight vocab-table VESUM subset builder."""

import json
import sqlite3

from scripts.etymology.build_vesum_vocab_lemmas import (
    build_vesum_vocab_lemmas,
    extract_vocabulary_words_from_text,
    normalize_lemma,
)


def _write_manifest(path):
    manifest = {
        "entries": [
            {"lemma": "субота", "slug": "subota"},
            {"lemma": "прокидатися", "slug": "prokydatysia"},
            {"lemma": "робот", "slug": "robot"},
        ],
        "slug_groups": {
            "subota": ["subota-5-461"],
            "prokydatysia": ["prokydatysia-1-1"],
            "robot": ["robot-1-1"],
        },
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


def _write_vesum_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE forms (word_form TEXT NOT NULL, lemma TEXT NOT NULL, tags TEXT NOT NULL, pos TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO forms (word_form, lemma, tags, pos) VALUES (?, ?, ?, ?)",
        [
            ("суботу", "субота", "noun:inanim:f:v_zna", "noun"),
            ("прокидаюся", "прокидатися", "verb:rev:imperf:pres:s:1", "verb"),
            ("роботу", "робот", "noun:anim:m:v_zna", "noun"),
            ("роботу", "робота", "noun:inanim:f:v_zna", "noun"),
        ],
    )
    conn.commit()
    conn.close()


def test_normalize_lemma_strips_combining_marks():
    assert normalize_lemma("Субо́та") == "субота"
    assert normalize_lemma("краї́на й") == "країна й"


def test_extract_vocabulary_words_only_from_vocab_tabs():
    text = """
<TabItem label="Lesson">

| Word | English |
| --- | --- |
| кава | coffee |

</TabItem>
<TabItem label="Словник">

| Слово | Переклад |
| --- | --- |
| **суботу** | Saturday |
| доброго ранку | good morning |

</TabItem>
"""

    assert extract_vocabulary_words_from_text(text) == {"суботу", "доброго ранку"}


def test_build_subset_links_unambiguous_forms_and_skips_homonyms(tmp_path):
    content_root = tmp_path / "docs"
    content_root.mkdir()
    (content_root / "lesson.mdx").write_text(
        """
<TabItem label="Vocabulary">

| Word | IPA | English |
| --- | --- | --- |
| суботу |  | Saturday |
| прокидаюся |  | I wake up |
| роботу |  | work |

</TabItem>
""",
        encoding="utf-8",
    )
    manifest = tmp_path / "manifest.json"
    vesum_db = tmp_path / "vesum.db"
    _write_manifest(manifest)
    _write_vesum_db(vesum_db)

    output = build_vesum_vocab_lemmas(content_root=content_root, manifest_path=manifest, vesum_db=vesum_db)

    assert output["form_to_lemma"] == {
        "прокидаюся": "прокидатися",
        "суботу": "субота",
    }
    assert output["stats"]["ambiguous_or_missing"] == 1
