from __future__ import annotations

import inspect
import json
import sqlite3
from contextlib import nullcontext, suppress
from pathlib import Path
from types import SimpleNamespace

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon import grow_lexicon_from_content as grow
from scripts.lexicon.content_lexicon_reconciler import LemmaExample
from scripts.lexicon.heritage_classifier import classify_lemma

FIXTURE_DB = Path(__file__).resolve().parent / "fixtures" / "heritage_sample.db"
FIXTURE_VESUM_DB = Path(__file__).resolve().parent / "fixtures" / "vesum_sample.db"


def _clean_entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "lemma": "мама",
        "pos": "noun",
        "heritage_status": {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
            "calque_warning": None,
        },
        "enrichment": {
            "meaning": {
                "definitions": ["мати"],
                "source": "fixture",
            }
        },
    }
    entry.update(overrides)
    return entry


def test_split_candidates_gates_dictionary_pos_and_heritage_flags() -> None:
    auto = _clean_entry(lemma="авто")
    no_definition = _clean_entry(lemma="без-дефініції", enrichment={})
    no_pos = _clean_entry(lemma="без-позиції")
    no_pos.pop("pos")
    heritage_flag = _clean_entry(
        lemma="калька",
        heritage_status={
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
            "curated_calque": {"corrections": ["чинний"]},
        },
    )

    auto_merge, needs_review = grow.split_candidates([auto, no_definition, no_pos, heritage_flag])

    assert auto_merge == [auto]
    assert [item["entry"]["lemma"] for item in needs_review] == [
        "без-дефініції",
        "без-позиції",
        "калька",
    ]
    assert needs_review[0]["reason"] == "missing dictionary definition"
    assert needs_review[1]["reason"] == "unresolved pos"
    assert needs_review[2]["reason"] == "heritage_status flags curated_calque"


def test_build_skeleton_entry_uses_raw_vesum_pos(monkeypatch) -> None:
    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        if lemma == "авантюрний":
            return [{"pos": "adj"}]
        return [{"pos": "noun"}] if lemma == "мама" else []

    monkeypatch.setattr(grow.enrich_manifest, "_base_lemma", lambda lemma: lemma)
    monkeypatch.setattr(grow.enrich_manifest, "verify_lemma", fake_verify_lemma)

    assert grow.build_skeleton_entry("мама") == {"lemma": "мама", "pos": "noun"}
    assert grow.build_skeleton_entry("авантю\u0301рний") == {"lemma": "авантюрний", "pos": "adj"}
    assert grow.build_skeleton_entry("не-знайдено") == {"lemma": "не-знайдено"}


def test_build_skeleton_entry_prefers_non_archaic_exact_pos(monkeypatch) -> None:
    def fake_verify_lemma(lemma: str) -> list[dict[str, str]]:
        assert lemma == "наголос"
        return [
            {"word_form": "наголос", "pos": "adv", "tags": "adv:arch"},
            {"word_form": "наголос", "pos": "noun", "tags": "noun:inanim:m:v_naz"},
        ]

    monkeypatch.setattr(grow.enrich_manifest, "_base_lemma", lambda lemma: lemma)
    monkeypatch.setattr(grow.enrich_manifest, "verify_lemma", fake_verify_lemma)

    assert grow.build_skeleton_entry("наголос") == {"lemma": "наголос", "pos": "noun"}


def test_enrich_entry_attaches_heritage_status_with_fixture_classifier(monkeypatch) -> None:
    _patch_enrich_entry_heavy_helpers(monkeypatch)
    monkeypatch.setattr(
        enrich_manifest_module,
        "classify_lemma",
        lambda lemma: classify_lemma(
            lemma,
            db_path=FIXTURE_DB,
            vesum_db_path=FIXTURE_VESUM_DB,
        ),
    )

    entry = {"lemma": "глагол", "pos": "noun"}
    attached = enrich_manifest_module.enrich_entry(
        entry,
        sqlite3.connect(":memory:"),
        {},
        has_sum11_flags=False,
    )

    assert attached is False
    assert entry["heritage_status"]["classification"] == "authentic-archaism"
    assert entry["heritage_status"]["is_russianism"] is False


def test_generate_candidates_writes_expected_json_shape(tmp_path, monkeypatch) -> None:
    missing = (
        LemmaExample("авто", "авто", tmp_path / "a.mdx"),
        LemmaExample("ревю", "ревю", tmp_path / "b.mdx"),
    )
    result = SimpleNamespace(missing_lemmas=missing)
    out = tmp_path / "grow_candidates.json"

    monkeypatch.setattr(grow, "discover_content_mdx_paths", lambda: [tmp_path / "a.mdx"])
    monkeypatch.setattr(grow, "reconcile_content", lambda paths, *, manifest_path: result)
    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(
        grow,
        "build_skeleton_entry",
        lambda lemma: {"lemma": lemma, "pos": "noun"},
    )

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
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

    payload = grow.generate_candidates(limit=2, out=out)
    written = json.loads(out.read_text(encoding="utf-8"))

    assert payload == written
    assert written["generated_from"] == grow.GENERATED_FROM
    assert written["counts"] == {
        "total_delta": 2,
        "processed": 2,
        "auto_merge": 1,
        "needs_review": 1,
    }
    assert written["auto_merge"][0]["lemma"] == "авто"
    assert written["needs_review"][0]["entry"]["lemma"] == "ревю"
    assert written["needs_review"][0]["reason"] == "missing dictionary definition"


def test_wiki_reference_cache_persists_across_runs(tmp_path, monkeypatch) -> None:
    cache = tmp_path / "wiki_reference.json"
    cache.write_text('{"старий": null}\n', encoding="utf-8")
    monkeypatch.setattr(grow.enrich_manifest, "WIKI_REFERENCE_CACHE", cache)
    monkeypatch.setattr(grow.enrich_manifest, "_WIKI_REFERENCE_CACHE_DATA", {"старий": None, "новий": {"title": "Новий"}})
    monkeypatch.setattr(grow.enrich_manifest, "_WIKI_REFERENCE_CACHE_DIRTY", True)

    with grow._preserve_wiki_reference_cache():
        pass

    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert "новий" in saved
    assert saved["новий"]["title"] == "Новий"
    assert grow.enrich_manifest._WIKI_REFERENCE_CACHE_DIRTY is False


def test_load_checkpoint_handles_missing_corrupt_and_valid_payloads(tmp_path) -> None:
    non_existent = tmp_path / "non_existent.json"
    assert grow.load_checkpoint(non_existent) == {}

    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text("{not-valid-json", encoding="utf-8")
    assert grow.load_checkpoint(corrupted) == {}

    not_dict = tmp_path / "not_dict.json"
    not_dict.write_text("[\"item1\", \"item2\"]", encoding="utf-8")
    assert grow.load_checkpoint(not_dict) == {}

    valid = tmp_path / "valid.json"
    valid_payload = {
        "auto_merge": [{"lemma": "сонце", "pos": "noun"}],
        "needs_review": [{"entry": {"lemma": "зірка", "pos": "noun"}, "reason": "missing dictionary definition"}],
    }
    valid.write_text(json.dumps(valid_payload), encoding="utf-8")
    loaded = grow.load_checkpoint(valid)
    assert len(loaded) == 2
    assert loaded["сонце"]["lemma"] == "сонце"
    assert loaded["зірка"]["lemma"] == "зірка"


def test_write_candidates_is_atomic_and_does_not_corrupt_on_failure(tmp_path, monkeypatch) -> None:
    out = tmp_path / "target.json"
    initial_content = '{"initial": "safe"}\n'
    out.write_text(initial_content, encoding="utf-8")

    def failing_fsync(fd):
        raise OSError("Simulated disk error during fsync")

    monkeypatch.setattr(grow.os, "fsync", failing_fsync)

    with suppress(OSError):
        grow.write_candidates({"updated": "data"}, out=out)

    # The original file must remain intact and uncorrupted
    assert out.read_text(encoding="utf-8") == initial_content


def test_kill_and_resume_preserves_completed_work_and_avoids_refetching(tmp_path, monkeypatch) -> None:
    missing = (
        LemmaExample("авто", "авто", tmp_path / "a.mdx"),
        LemmaExample("мама", "мама", tmp_path / "b.mdx"),
        LemmaExample("сонце", "сонце", tmp_path / "c.mdx"),
        LemmaExample("книга", "книга", tmp_path / "d.mdx"),
    )
    result = SimpleNamespace(missing_lemmas=missing)
    out = tmp_path / "grow_candidates.json"

    monkeypatch.setattr(grow, "discover_content_mdx_paths", lambda: [tmp_path / "a.mdx"])
    monkeypatch.setattr(grow, "reconcile_content", lambda paths, *, manifest_path: result)
    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(grow, "build_skeleton_entry", lambda lemma: {"lemma": lemma, "pos": "noun"})

    enriched_lemmas: list[str] = []

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
        lemma = entry["lemma"]
        enriched_lemmas.append(lemma)
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        entry["enrichment"] = {
            "meaning": {
                "definitions": [f"definition for {lemma}"],
                "source": "fixture",
            }
        }
        # Simulate a crash on the 3rd lemma after the 2-item checkpoint has been written
        if lemma == "сонце" and not hasattr(fake_enrich_entry, "run2"):
            raise KeyboardInterrupt("Simulated mid-run interruption")
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    # --- Run 1: Interrupted mid-way ---
    with suppress(KeyboardInterrupt):
        grow.generate_candidates(limit=4, out=out, checkpoint_interval=2, resume=True, quiet=True)

    # In run 1, "авто" and "мама" completed and "сонце" was interrupted
    assert enriched_lemmas == ["авто", "мама", "сонце"]
    # Checkpoint must have been saved at checkpoint_interval=2 containing "авто" and "мама"
    assert out.exists()
    checkpoint_payload = json.loads(out.read_text(encoding="utf-8"))
    assert checkpoint_payload["counts"]["processed"] == 2
    assert [e["lemma"] for e in checkpoint_payload["auto_merge"]] == ["авто", "мама"]

    # --- Run 2: Resumed ---
    fake_enrich_entry.run2 = True  # type: ignore[attr-defined]
    run2_enriched: list[str] = []

    def fake_enrich_entry_run2(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
        lemma = entry["lemma"]
        run2_enriched.append(lemma)
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        entry["enrichment"] = {
            "meaning": {
                "definitions": [f"definition for {lemma}"],
                "source": "fixture",
            }
        }
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry_run2)

    payload2 = grow.generate_candidates(limit=4, out=out, checkpoint_interval=2, resume=True, quiet=True)

    # Verify that run 2 ONLY enriched "сонце" and "книга", NOT "авто" or "мама"!
    assert run2_enriched == ["сонце", "книга"]
    assert payload2["counts"]["processed"] == 4
    assert [e["lemma"] for e in payload2["auto_merge"]] == ["авто", "мама", "сонце", "книга"]


def test_no_resume_flag_starts_fresh_and_reenriches_all(tmp_path, monkeypatch) -> None:
    missing = (
        LemmaExample("авто", "авто", tmp_path / "a.mdx"),
        LemmaExample("мама", "мама", tmp_path / "b.mdx"),
    )
    result = SimpleNamespace(missing_lemmas=missing)
    out = tmp_path / "grow_candidates.json"

    # Pre-seed checkpoint
    preseeded_payload = {
        "generated_from": grow.GENERATED_FROM,
        "counts": {"total_delta": 2, "processed": 1, "auto_merge": 1, "needs_review": 0},
        "limit": 2,
        "auto_merge": [{"lemma": "авто", "pos": "noun", "enrichment": {"meaning": {"definitions": ["car"]}}}],
        "needs_review": [],
    }
    out.write_text(json.dumps(preseeded_payload), encoding="utf-8")

    monkeypatch.setattr(grow, "discover_content_mdx_paths", lambda: [tmp_path / "a.mdx"])
    monkeypatch.setattr(grow, "reconcile_content", lambda paths, *, manifest_path: result)
    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(grow, "build_skeleton_entry", lambda lemma: {"lemma": lemma, "pos": "noun"})

    enriched_lemmas: list[str] = []

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
        lemma = entry["lemma"]
        enriched_lemmas.append(lemma)
        entry["heritage_status"] = {"classification": "standard", "is_russianism": False, "russian_shadow": False}
        entry["enrichment"] = {"meaning": {"definitions": [f"def {lemma}"]}}
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = grow.generate_candidates(limit=2, out=out, resume=False, quiet=True)
    # Both lemmas should have been re-enriched because resume=False
    assert enriched_lemmas == ["авто", "мама"]
    assert payload["counts"]["processed"] == 2


def test_checkpoint_interval_saves_periodically(tmp_path, monkeypatch) -> None:
    missing = tuple(LemmaExample(f"w{i}", f"w{i}", tmp_path / "a.mdx") for i in range(10))
    result = SimpleNamespace(missing_lemmas=missing)
    out = tmp_path / "grow_candidates.json"

    monkeypatch.setattr(grow, "discover_content_mdx_paths", lambda: [tmp_path / "a.mdx"])
    monkeypatch.setattr(grow, "reconcile_content", lambda paths, *, manifest_path: result)
    monkeypatch.setattr(grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(grow, "build_skeleton_entry", lambda lemma: {"lemma": lemma, "pos": "noun"})

    checkpoints: list[int] = []
    real_write_checkpoint = grow.write_checkpoint

    def tracking_write_checkpoint(entries, *, total_delta, limit, out):
        checkpoints.append(len(entries))
        return real_write_checkpoint(entries, total_delta=total_delta, limit=limit, out=out)

    monkeypatch.setattr(grow, "write_checkpoint", tracking_write_checkpoint)

    def fake_enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
        entry["heritage_status"] = {"classification": "standard", "is_russianism": False, "russian_shadow": False}
        entry["enrichment"] = {"meaning": {"definitions": [f"def {entry['lemma']}"]}}
        return True

    monkeypatch.setattr(grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = grow.generate_candidates(limit=10, out=out, checkpoint_interval=3, quiet=True)

    # With 10 items and interval=3, checkpoints should be triggered at 3, 6, and 9 items
    assert checkpoints == [3, 6, 9]
    assert payload["counts"]["processed"] == 10
    # Final file has all 10 items
    assert len(json.loads(out.read_text(encoding="utf-8"))["auto_merge"]) == 10


def test_cli_parsing_and_main(tmp_path, monkeypatch, capsys) -> None:
    out = tmp_path / "out.json"
    called_kwargs: dict[str, object] = {}

    def fake_generate_candidates(**kwargs):
        called_kwargs.update(kwargs)
        return {
            "counts": {"total_delta": 5, "processed": 5, "auto_merge": 3, "needs_review": 2},
            "auto_merge": [],
            "needs_review": [],
        }

    monkeypatch.setattr(grow, "generate_candidates", fake_generate_candidates)

    exit_code = grow.main(["--limit", "5", "--out", str(out), "--checkpoint-interval", "2", "--no-resume", "--report", "--quiet"])
    assert exit_code == 0
    assert called_kwargs["limit"] == 5
    assert called_kwargs["out"] == out
    assert called_kwargs["checkpoint_interval"] == 2
    assert called_kwargs["resume"] is False
    assert called_kwargs["quiet"] is True

    captured = capsys.readouterr()
    assert "total_delta: 5" in captured.out
    assert "processed: 5" in captured.out


def test_enrich_entry_exists_and_enrich_delegates_to_it() -> None:
    assert callable(enrich_manifest_module.enrich_entry)
    enrich_source = inspect.getsource(enrich_manifest_module.enrich)

    # enrich() must delegate enrichment to enrich_entry() rather than reimplement it.
    # Collapse whitespace so the assertion is robust to call formatting (single- vs
    # multi-line) and to appended kwargs such as pointer_synonym_relations (#4950).
    compact = "".join(enrich_source.split())
    assert "enrich_entry(entry,conn,kaikki_lookup,has_sum11_flags=has_sum11_flags" in compact


def _patch_enrich_entry_heavy_helpers(monkeypatch) -> None:
    monkeypatch.setattr(enrich_manifest_module, "_slovnyk_cache", lambda lemma: {})
    monkeypatch.setattr(enrich_manifest_module, "_definition_cards", lambda *args, **kwargs: [])
    monkeypatch.setattr(enrich_manifest_module, "_warning_slovnyk", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_curated_calque", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_reverse_calques", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_pronunciation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_synonyms_mphdict", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_antonyms_wiktionary", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_idioms", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_stress_display_form", lambda *args, **kwargs: "")
    monkeypatch.setattr(enrich_manifest_module, "_kaikki_stress", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_cefr", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_morphology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_meaning", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_etymology", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_literary_attestation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_translation", lambda *args, **kwargs: None)
    monkeypatch.setattr(enrich_manifest_module, "_wiki_reference", lambda *args, **kwargs: None)
