from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any

from scripts.audit import grow_lexicon_from_lemmas as grow


def test_generate_candidates_reads_lemma_file_and_splits_candidates(tmp_path, monkeypatch) -> None:
    lemmas_file = tmp_path / "lemmas.txt"
    lemmas_file.write_text("\n авто\u0301 \nавто\nревю\n", encoding="utf-8")
    out = tmp_path / "doc-candidates.json"
    seen: list[tuple[str, dict[str, bool], bool]] = []

    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow, "_preserve_wiki_reference_cache", lambda: nullcontext())
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {"fixture": True})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: True)
    monkeypatch.setattr(
        grow,
        "build_skeleton_entry",
        lambda lemma: {"lemma": lemma, "pos": "noun"},
    )

    def fake_enrich_entry(
        entry: dict[str, Any],
        conn: object,
        kaikki_lookup: dict[str, bool],
        *,
        has_sum11_flags: bool,
    ) -> bool:
        seen.append((entry["lemma"], kaikki_lookup, has_sum11_flags))
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        if entry["lemma"] == "авто":
            entry["enrichment"] = {
                "meaning": {
                    "definitions": ["автомобіль"],
                    "source": "fixture",
                }
            }
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = grow.generate_candidates(lemmas_file=lemmas_file, limit=3, out=out)
    written = json.loads(out.read_text(encoding="utf-8"))

    assert payload == written
    assert written["counts"] == {
        "total_delta": 2,
        "processed": 2,
        "auto_merge": 1,
        "needs_review": 1,
    }
    assert written["auto_merge"][0]["lemma"] == "авто"
    assert written["needs_review"][0]["entry"]["lemma"] == "ревю"
    assert written["needs_review"][0]["reason"] == "missing dictionary definition"
    assert seen == [
        ("авто", {"fixture": True}, True),
        ("ревю", {"fixture": True}, True),
    ]
