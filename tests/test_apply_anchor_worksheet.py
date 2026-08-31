from __future__ import annotations

import json

import yaml

import scripts.lexicon.apply_anchor_worksheet as applier
from scripts.lexicon.apply_anchor_worksheet import AGY_EN_SOURCE, ANCHOR_SOURCE, apply_anchor_worksheet


def test_applies_approved_anchor() -> None:
    manifest = _manifest(_entry("косуля"))
    worksheet = _worksheet(_record("косуля", "roe deer", status="approved"))

    result = apply_anchor_worksheet(manifest, worksheet)

    translation = manifest["entries"][0]["enrichment"]["translation"]
    assert translation == {"en": ["roe deer"], "source": ANCHOR_SOURCE}
    assert ANCHOR_SOURCE in manifest["entries"][0]["enrichment"]["sources"]
    assert result.applied == ("косуля",)


def test_applies_agy_anchor_with_its_own_source() -> None:
    manifest = _manifest(_entry("косуля"))
    worksheet = _worksheet(
        _record("косуля", "roe deer", status="approved"),
        source_label="agy_en_proposal (Gemini; not a dictionary)",
    )

    result = apply_anchor_worksheet(manifest, worksheet)

    enrichment = manifest["entries"][0]["enrichment"]
    assert enrichment["translation"] == {"en": ["roe deer"], "source": AGY_EN_SOURCE}
    assert enrichment["sources"] == ["VESUM", AGY_EN_SOURCE]
    assert ANCHOR_SOURCE not in enrichment["sources"]
    assert "learner_english_gloss" not in enrichment["sources"]
    assert result.applied == ("косуля",)


def test_skips_null_proposal() -> None:
    manifest = _manifest(_entry("добові"))
    worksheet = _worksheet(_record("добові", None))

    result = apply_anchor_worksheet(manifest, worksheet)

    assert "translation" not in manifest["entries"][0]["enrichment"]
    assert result.skipped_null == 1


def test_never_overwrites_existing_anchor() -> None:
    entry = _entry("скрипт")
    entry["enrichment"]["translation"] = {"en": ["manuscript"], "source": "existing"}
    manifest = _manifest(entry)
    worksheet = _worksheet(_record("скрипт", "script", verified_by="reviewer"))

    result = apply_anchor_worksheet(manifest, worksheet)

    assert manifest["entries"][0]["enrichment"]["translation"] == {
        "en": ["manuscript"],
        "source": "existing",
    }
    assert result.applied == ()
    assert result.skipped_existing == ("скрипт",)


def test_never_overwrites_non_english_existing_translation() -> None:
    entry = _entry("слово")
    entry["enrichment"]["translation"] = {"en": ["переклад"], "source": "existing"}
    manifest = _manifest(entry)
    worksheet = _worksheet(
        _record("слово", "word", status="approved"),
        source_label="agy_en_proposal (Gemini; not a dictionary)",
    )

    result = apply_anchor_worksheet(manifest, worksheet)

    assert manifest["entries"][0]["enrichment"]["translation"] == {
        "en": ["переклад"],
        "source": "existing",
    }
    assert result.applied == ()
    assert result.skipped_existing == ("слово",)


def test_agy_dry_run_does_not_apply_legacy_cached_fill(tmp_path, monkeypatch) -> None:
    manifest = _manifest(_entry("косуля"))
    worksheet = _worksheet(
        _record("косуля", "roe deer", status="approved"),
        source_label="agy_en_proposal (Gemini; not a dictionary)",
    )
    manifest_path = tmp_path / "manifest.json"
    worksheet_path = tmp_path / "worksheet.yaml"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    worksheet_path.write_text(yaml.safe_dump(worksheet, allow_unicode=True), encoding="utf-8")

    def fail_if_called(_manifest: object) -> tuple[str, ...]:
        raise AssertionError("AGY worksheet must not apply the legacy cached fill")

    monkeypatch.setattr(applier, "_apply_cached_slovnyk_anchors", fail_if_called)
    result = applier.apply_from_paths(
        manifest_path=manifest_path,
        worksheet_path=worksheet_path,
        write=False,
    )

    assert result.cached_fills == ()
    assert result.applied == ("косуля",)
    assert "translation" not in json.loads(manifest_path.read_text(encoding="utf-8"))["entries"][0]["enrichment"]


def test_is_idempotent_after_applying_anchor() -> None:
    manifest = _manifest(_entry("рано-вранці"))
    worksheet = _worksheet(_record("рано-вранці", "early in the morning", status="approved"))

    first = apply_anchor_worksheet(manifest, worksheet)
    second = apply_anchor_worksheet(manifest, worksheet)

    assert first.applied == ("рано-вранці",)
    assert second.applied == ()
    assert second.skipped_existing == ("рано-вранці",)


def _manifest(entry: dict[str, object]) -> dict[str, object]:
    return {"entries": [entry]}


def _entry(lemma: str) -> dict[str, object]:
    return {"lemma": lemma, "url_slug": lemma, "enrichment": {"sources": ["VESUM"]}}


def _worksheet(
    record: dict[str, object], *, source_label: str | None = None
) -> dict[str, object]:
    worksheet: dict[str, object] = {"records": [record]}
    if source_label is not None:
        worksheet["meta"] = {"source_label_if_applied": source_label}
    return worksheet


def _record(
    lemma: str,
    proposed_anchor: str | None,
    *,
    status: str | None = None,
    verified_by: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "lemma": lemma,
        "url_slug": lemma,
        "proposed_anchor": proposed_anchor,
        "confidence": "low" if proposed_anchor is None else "high",
    }
    if status is not None:
        record["status"] = status
    if verified_by is not None:
        record["verified_by"] = verified_by
    return record
