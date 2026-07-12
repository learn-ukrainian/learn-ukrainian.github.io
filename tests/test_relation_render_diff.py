"""Tests for the rendered-manifest relation promotion diff gate."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lexicon import relation_render_diff


def _write_manifest(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def test_rendered_diff_reports_relation_losses_provenance_caps_and_source_buckets(tmp_path, capsys) -> None:
    baseline = _write_manifest(
        tmp_path / "baseline.json",
        [
            {
                "lemma": "ключ",
                "sections": {
                    "synonyms": {
                        "items": ["відмикач", "джерело", "живець"],
                        "source": " + ".join(
                            [
                                "Караванський: dictionary synonym → відмикач",
                                "Ukrajinet WordNet: gated synset → джерело",
                                "Ukrajinet WordNet: gated synset → живець",
                            ]
                        ),
                    }
                },
            },
            {
                "lemma": "втрата",
                "sections": {
                    "synonyms": {
                        "items": ["зникле"],
                        "source": "relation_pairs/miyklas.com.ua: corpus relation pair → зникле",
                    }
                },
            },
            {
                "lemma": "черга",
                "sections": {
                    "synonyms": {
                        "items": ["старий"],
                        "source": "Караванський: dictionary synonym → старий",
                    }
                },
            },
        ],
    )
    current = _write_manifest(
        tmp_path / "current.json",
        [
            {
                "lemma": "ключ",
                "sections": {
                    "synonyms": {
                        "items": ["відмикач"],
                        "source": "Караванський: dictionary synonym → відмикач",
                    }
                },
            },
            {"lemma": "втрата"},
            {
                "lemma": "черга",
                "sections": {
                    "synonyms": {
                        "items": [f"новий-{number}" for number in range(1, 9)],
                        "source": " + ".join(
                            f"relation_pairs/synonym_verdicts: corpus relation pair → новий-{number}"
                            for number in range(1, 9)
                        ),
                    }
                },
            },
        ],
    )

    report = relation_render_diff.run(baseline, current)
    output = capsys.readouterr().out

    assert report["relations"]["synonym"] == {"old": 5, "new": 9, "gained": 8, "lost": 4}
    assert report["sources"]["retained_source"] == {"old": 3, "new": 9, "gained": 8, "lost": 2}
    assert report["sources"]["ukrajinet_only"] == {"old": 2, "new": 0, "gained": 0, "lost": 2}
    assert report["nonempty_to_empty"] == [{"lemma": "втрата", "old": 1, "new": 0}]
    assert report["cap_displacements"] == [
        {
            "lemma": "черга",
            "relation": "synonym",
            "lost_target": "старий",
            "cap": 8,
            "new_targets": [f"новий-{number}" for number in range(1, 9)],
            "gained_targets": [f"новий-{number}" for number in range(1, 9)],
        }
    ]
    lost = {(item["lemma"], item["target"]): item["provenance"] for item in report["lost_provenance"]}
    assert lost[("ключ", "джерело")] == ["Ukrajinet WordNet: gated synset → джерело"]
    assert lost[("ключ", "живець")] == ["Ukrajinet WordNet: gated synset → живець"]
    assert "SOURCE TOTALS" in output
    assert "Ukrajinet-only" in output
    assert "NONEMPTY → EMPTY" in output
    assert "CAP DISPLACEMENTS" in output


def test_rendered_edges_normalize_displayed_targets_and_keep_display_order() -> None:
    manifest = {
        "entries": [
            {
                "lemma": "Ключ",
                "sections": {
                    "synonyms": {
                        "items": ["Кав’я́рня", "кава"],
                        "source": "Караванський: dictionary synonym",
                    },
                    "homonyms": {
                        "items": [
                            {"word": "ключ", "gloss": "знаряддя"},
                            {"word": "ключ", "gloss": "джерело"},
                        ],
                        "source": "СУМ-20: numbered homonym headwords",
                    },
                },
            }
        ]
    }

    edges = relation_render_diff.rendered_edges(manifest)

    assert [edge.displayed_target for edge in edges] == [
        "Кав’я́рня",
        "кава",
        "ключ — знаряддя",
        "ключ — джерело",
    ]
    assert edges[0].target_key == "кав'ярня"
    assert [edge.order for edge in edges[:2]] == [0, 1]
