from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.lexicon.fill_from_content import fill_manifest_from_vocab


def test_fill_manifest_from_folk_vocab_adds_only_vesum_verified_single_token_lemmas(
    tmp_path: Path,
) -> None:
    curriculum_root = _write_curriculum(tmp_path)
    manifest_path = _write_manifest(tmp_path, ["колядка"])

    result = fill_manifest_from_vocab(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        write=True,
        enrich=False,
        update_fingerprint=False,
        vesum_lookup=_fake_vesum,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {entry["lemma"]: entry for entry in payload["entries"]}
    assert result.modules_scanned == 1
    assert result.missing_candidates == ("щедрівка", "світове дерево", "вигаданець")
    assert [item.lemma for item in result.added] == ["щедрівка"]
    assert {item.lemma: item.reason for item in result.skipped} == {
        "світове дерево": "not a single-token lemma",
        "вигаданець": "VESUM did not confirm this as a lemma",
    }
    assert entries["щедрівка"] == {
        "lemma": "щедрівка",
        "url_slug": "щедрівка",
        "gloss": "New Year ritual song",
        "pos": "noun",
        "ipa": None,
        "primary_source": "built_vocabulary",
        "course_usage": [
            {
                "track": "folk",
                "module_num": 1,
                "slug": "koliadky-shchedrivky",
                "context": "built_vocabulary",
            }
        ],
    }
    assert payload["stats"]["lemmas_total"] == 2
    assert payload["stats"]["from_built"] == 2


def test_fill_manifest_from_folk_vocab_is_idempotent(tmp_path: Path) -> None:
    curriculum_root = _write_curriculum(tmp_path)
    manifest_path = _write_manifest(tmp_path, ["колядка"])

    first = fill_manifest_from_vocab(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        write=True,
        enrich=False,
        update_fingerprint=False,
        vesum_lookup=_fake_vesum,
    )
    second = fill_manifest_from_vocab(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        write=True,
        enrich=False,
        update_fingerprint=False,
        vesum_lookup=_fake_vesum,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item.lemma for item in first.added] == ["щедрівка"]
    assert second.added == ()
    assert [entry["lemma"] for entry in payload["entries"]].count("щедрівка") == 1


def _write_curriculum(tmp_path: Path) -> Path:
    root = tmp_path / "curriculum" / "l2-uk-en"
    module_dir = root / "folk" / "koliadky-shchedrivky"
    module_dir.mkdir(parents=True)
    (root / "curriculum.yaml").write_text(
        """
levels:
  folk:
    modules:
      - koliadky-shchedrivky
""",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        """
- lemma: колядка
  translation: Christmas carol
  pos: noun
- lemma: щедрівка
  translation: New Year ritual song
  pos: noun
- lemma: світове дерево
  translation: world tree
  pos: noun
- lemma: вигаданець
  translation: fabricated token
  pos: noun
""",
        encoding="utf-8",
    )
    return root


def _write_manifest(tmp_path: Path, lemmas: list[str]) -> Path:
    path = tmp_path / "lexicon-manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "stats": {"lemmas_total": len(lemmas), "from_built": len(lemmas)},
                "modules": [],
                "entries": [
                    {
                        "lemma": lemma,
                        "url_slug": lemma,
                        "gloss": lemma,
                        "pos": "noun",
                        "primary_source": "built_vocabulary",
                        "course_usage": [],
                    }
                    for lemma in lemmas
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
    matches = {
        "щедрівка": [{"lemma": "щедрівка", "pos": "noun", "tags": "inanim:f:v_naz"}],
        "вигаданець": [],
    }
    return {word: matches.get(word, []) for word in words}
