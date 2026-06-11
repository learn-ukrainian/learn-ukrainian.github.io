from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.lexicon import build_data_manifest as manifest_builder


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_puls_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE puls_cefr (
              id INTEGER PRIMARY KEY,
              word TEXT NOT NULL,
              guideword TEXT DEFAULT '',
              level TEXT DEFAULT '',
              pos TEXT DEFAULT '',
              type TEXT DEFAULT '',
              text TEXT NOT NULL DEFAULT '',
              source TEXT DEFAULT ''
            )
            """
        )
        conn.executemany(
            "INSERT INTO puls_cefr(word, level, text) VALUES (?, ?, ?)",
            [
                ("slovo", "A1", ""),
                ("inshyi", "B1", ""),
                ("poza", "B2", ""),
                ("phrase word", "A1", ""),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_default_scope_keeps_v1_module_set(monkeypatch) -> None:
    def fake_plan_records(module: dict[str, str | int]) -> list[dict]:
        return [
            {
                "lemma": f"plan-{module['slug']}",
                "gloss": "plan",
                "pos": None,
                "ipa": None,
                "source": "plan_required",
            }
        ]

    monkeypatch.setattr(manifest_builder, "_load_plan_hints", fake_plan_records)
    monkeypatch.setattr(manifest_builder, "_load_built_vocab", lambda _module: [])

    manifest = manifest_builder.build_manifest()

    assert manifest["version"] == "0.1"
    assert manifest["modules"] == manifest_builder.V1_MODULES
    assert manifest["stats"]["modules_covered"] == len(manifest_builder.V1_MODULES)
    assert manifest["stats"]["lemmas_total"] == len(manifest_builder.V1_MODULES)
    assert manifest["stats"]["from_built"] == 0
    assert manifest["stats"]["from_plan_only"] == len(manifest_builder.V1_MODULES)


def test_v2_spike_filters_curriculum_lemmas_to_single_word_puls(tmp_path, monkeypatch) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    plans_root = curriculum_root / "plans"
    sources_db = tmp_path / "data" / "sources.db"

    _write(
        curriculum_root / "curriculum.yaml",
        """
levels:
  a1:
    modules:
      - alpha
      - beta
""",
    )
    _write(
        plans_root / "a1" / "alpha.yaml",
        """
vocabulary_hints:
  required:
    - slovo (word)
    - poza (outside)
    - phrase word (phrase)
""",
    )
    _write(
        plans_root / "a1" / "beta.yaml",
        """
vocabulary_hints:
  recommended:
    - inshyi (other)
""",
    )
    _write(
        curriculum_root / "a1" / "alpha" / "vocabulary.yaml",
        """
- lemma: slovo
  translation: word
  pos: noun
  usage: Slovo.
""",
    )
    _write_puls_db(sources_db)

    monkeypatch.setattr(manifest_builder, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(manifest_builder, "PLANS_ROOT", plans_root)
    monkeypatch.setattr(manifest_builder, "SOURCES_DB", sources_db)

    manifest = manifest_builder.build_manifest("v2-spike")

    assert [entry["lemma"] for entry in manifest["entries"]] == ["inshyi", "slovo"]
    assert manifest["stats"] == {
        "lemmas_total": 2,
        "modules_covered": 2,
        "candidate_lemmas": 4,
        "from_built": 1,
        "from_plan": 1,
        "dropped_multi_word": 1,
        "dropped_not_in_puls": 1,
    }
