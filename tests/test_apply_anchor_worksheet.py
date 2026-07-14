from __future__ import annotations

from scripts.lexicon.apply_anchor_worksheet import ANCHOR_SOURCE, apply_anchor_worksheet


def test_applies_approved_anchor() -> None:
    manifest = _manifest(_entry("косуля"))
    worksheet = _worksheet(_record("косуля", "roe deer", status="approved"))

    result = apply_anchor_worksheet(manifest, worksheet)

    translation = manifest["entries"][0]["enrichment"]["translation"]
    assert translation == {"en": ["roe deer"], "source": ANCHOR_SOURCE}
    assert ANCHOR_SOURCE in manifest["entries"][0]["enrichment"]["sources"]
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


def _worksheet(record: dict[str, object]) -> dict[str, object]:
    return {"records": [record]}


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
