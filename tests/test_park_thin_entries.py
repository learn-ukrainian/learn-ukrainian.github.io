from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit.audit_atlas_poc_richness import audit_manifest
from scripts.lexicon import park_thin_entries as park
from scripts.lexicon.manifest_io import write_manifest


def test_parks_only_audit_thin_lemmas_and_preserves_guarded_entries(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    parked_path = tmp_path / "parked.json"

    result = park.park_thin_entries(
        manifest_path=manifest_path,
        parked_out=parked_path,
        write=True,
    )

    manifest = _read_json(manifest_path)
    remaining_lemmas = {entry["lemma"] for entry in manifest["entries"]}
    artifact = _read_json(parked_path)
    parked_lemmas = [record["entry"]["lemma"] for record in artifact["entries"]]

    assert parked_lemmas == ["звичайний", "курсовий", "спадковий"]
    assert {"ціль-адреса", "ціль-лема"} <= remaining_lemmas
    assert "два слова" in remaining_lemmas
    assert {"форма-адреса", "форма-лема"} <= remaining_lemmas
    assert artifact["pre_park_audit"]["poc_thin_pages"] == 6
    assert result.parked_count == 3
    assert result.guard_excluded == {"form_of_target": 2}
    assert result.projected_poc_thin_pages == 3
    assert result.projected_form_stub_broken == 0
    assert result.manifest_written is True
    assert result.parked_artifact_written is True


def test_course_and_heritage_correction_targets_remain_audit_eligible(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["entries"].append(_rich_entry("посилання"))
    manifest["entries"][-1]["heritage_status"] = {"correction_target": {"lemma": "спадковий", "url_slug": "спадковий"}}
    _refresh_stats(manifest)
    write_manifest(manifest_path, manifest)

    parked_path = tmp_path / "parked.json"
    result = park.park_thin_entries(manifest_path=manifest_path, parked_out=parked_path, write=True)
    artifact = _read_json(parked_path)

    assert result.parked_count == 3
    assert result.guard_excluded == {"form_of_target": 2}
    # ``курсовий`` has course_usage and ``спадковий`` is a correction target,
    # yet both remain selected because the audit classifies them as thin.
    assert {record["entry"]["lemma"] for record in artifact["entries"]} >= {"курсовий", "спадковий"}
    assert result.projected_poc_thin_pages == 3


def test_stats_are_recomputed_consistently_after_parking(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)

    park.park_thin_entries(
        manifest_path=manifest_path,
        parked_out=tmp_path / "parked.json",
        write=True,
    )

    stats = _read_json(manifest_path)["stats"]
    assert stats == {
        "lemmas_total": 6,
        "modules_covered": 42,
        "from_built": 5,
        "from_surzhyk_to_avoid": 1,
        "from_heritage_status_seed": 0,
        "form_of_count": 2,
        "enriched_count": 6,
    }


def test_restore_reinserts_verbatim_entries_and_reaudits_pre_park_count(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    initial = _read_json(manifest_path)
    parked_path = tmp_path / "parked.json"

    park.park_thin_entries(manifest_path=manifest_path, parked_out=parked_path, write=True)
    result = park.restore_parked_entries(manifest_path=manifest_path, parked_file=parked_path, write=True)

    restored = _read_json(manifest_path)
    assert restored["entries"] == initial["entries"]
    assert audit_manifest(restored, sample_limit=len(restored["entries"]))["poc_thin_pages"] == 6
    assert result.restored_count == 3
    assert result.projected_poc_thin_pages == 6
    assert result.manifest_written is True


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    parked_path = tmp_path / "parked.json"
    before = manifest_path.read_bytes()

    result = park.park_thin_entries(manifest_path=manifest_path, parked_out=parked_path)

    assert result.dry_run is True
    assert result.parked_count == 3
    assert manifest_path.read_bytes() == before
    assert not parked_path.exists()
    assert not (tmp_path / "lexicon-manifest.fingerprint.json").exists()


def test_cli_json_dry_run_honors_limit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    parked_path = tmp_path / "parked.json"
    before = manifest_path.read_bytes()

    assert (
        park.main(
            [
                "--manifest",
                str(manifest_path),
                "--parked-out",
                str(parked_path),
                "--dry-run",
                "--limit",
                "1",
                "--json",
            ]
        )
        == 0
    )

    summary = json.loads(capsys.readouterr().out)
    assert summary["parked_count"] == 1
    assert summary["projected_poc_thin_pages"] == 5
    assert manifest_path.read_bytes() == before
    assert not parked_path.exists()


def test_refuses_write_when_projected_manifest_has_broken_form_stub(tmp_path: Path) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    manifest = _read_json(manifest_path)
    manifest["entries"].append(
        _thin_entry(
            "зламана-форма",
            form_of={"lemma": "відсутня-ціль", "url_slug": "відсутня-ціль"},
        )
    )
    _refresh_stats(manifest)
    write_manifest(manifest_path, manifest)
    before = manifest_path.read_bytes()
    parked_path = tmp_path / "parked.json"

    with pytest.raises(ValueError, match="broken form stubs"):
        park.park_thin_entries(manifest_path=manifest_path, parked_out=parked_path, write=True)

    assert manifest_path.read_bytes() == before
    assert not parked_path.exists()


def test_artifact_is_written_before_manifest_shrinks_on_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_fixture_manifest(tmp_path)
    parked_path = tmp_path / "parked.json"
    before = manifest_path.read_bytes()
    calls: list[Path] = []

    def fail_manifest_write(path: Path | str, payload: dict[str, object]) -> None:
        resolved = Path(path)
        calls.append(resolved)
        if resolved == manifest_path:
            raise OSError("manifest write failure")
        write_manifest(resolved, payload)

    monkeypatch.setattr(park, "write_manifest", fail_manifest_write)

    with pytest.raises(OSError, match="manifest write failure"):
        park.park_thin_entries(manifest_path=manifest_path, parked_out=parked_path, write=True)

    assert calls == [parked_path, manifest_path]
    assert parked_path.exists()
    assert manifest_path.read_bytes() == before


def _write_fixture_manifest(tmp_path: Path) -> Path:
    entries = [
        _thin_entry("ціль-адреса"),
        _thin_entry("ціль-лема"),
        _thin_entry("звичайний"),
        _thin_entry(
            "курсовий",
            course_usage=[{"track": "a2", "module_num": 1, "slug": "fixture"}],
        ),
        _thin_entry("спадковий", primary_source="heritage_status_seed", seed_group="heritage-status-samples"),
        _thin_entry(
            "два слова",
            enrichment=_multiword_thin_enrichment(),
            primary_source="surzhyk_to_avoid",
            seed_group="surzhyk-to-avoid",
        ),
        _thin_entry(
            "форма-адреса",
            form_of={"url_slug": "ціль-адреса"},
        ),
        _thin_entry(
            "форма-лема",
            form_of={"lemma": "ціль-лема"},
        ),
        _rich_entry("не-ціль"),
    ]
    manifest = {
        "version": "fixture",
        "generated_at": "2026-07-10T00:00:00+00:00",
        "stats": {
            "lemmas_total": 9,
            "modules_covered": 42,
            "from_built": 7,
            "from_surzhyk_to_avoid": 1,
            "from_heritage_status_seed": 1,
            "form_of_count": 2,
            "enriched_count": 9,
        },
        "entries": entries,
    }
    path = tmp_path / "lexicon-manifest.json"
    write_manifest(path, manifest)
    return path


def _thin_entry(lemma: str, **overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": "fixture",
        "pos": "noun",
        "primary_source": "built_vocabulary",
        "course_usage": [],
        "enrichment": {
            "definition_cards": [
                {
                    "id": "fixture-definition",
                    "source": "fixture",
                    "definitions": ["Тестове значення."],
                }
            ],
            "morphology": {
                "pos": "noun",
                "forms": [{"form": lemma, "label": "називний"}],
                "source": "fixture",
            },
            "translation": {"en": ["fixture"], "source": "fixture"},
        },
        "sections": {},
    }
    entry.update(overrides)
    return entry


def _multiword_thin_enrichment() -> dict[str, object]:
    return {
        "definition_cards": [
            {
                "id": "fixture-definition",
                "source": "fixture",
                "definitions": ["Тестове значення."],
            }
        ],
        "morphology": {
            "pos": "noun",
            "forms": [{"form": "два слова", "label": "називний"}],
            "source": "fixture",
        },
    }


def _rich_entry(lemma: str) -> dict[str, object]:
    entry = _thin_entry(lemma)
    entry["enrichment"] = {
        **entry["enrichment"],
        "etymology": {"text": "Тестова етимологія.", "source": "fixture"},
        "literary_attestation": {"text": "Тестова атестація.", "source": "fixture"},
    }
    return entry


def _refresh_stats(manifest: dict[str, object]) -> None:
    entries = manifest["entries"]
    assert isinstance(entries, list)
    stats = manifest["stats"]
    assert isinstance(stats, dict)
    stats["lemmas_total"] = len(entries)
    stats["from_built"] = sum(
        1
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("primary_source", "")).startswith("built_vocabulary")
    )
    stats["from_surzhyk_to_avoid"] = sum(
        1 for entry in entries if isinstance(entry, dict) and entry.get("seed_group") == "surzhyk-to-avoid"
    )
    stats["from_heritage_status_seed"] = sum(
        1 for entry in entries if isinstance(entry, dict) and entry.get("seed_group") == "heritage-status-samples"
    )
    stats["form_of_count"] = sum(1 for entry in entries if isinstance(entry, dict) and "form_of" in entry)
    stats["enriched_count"] = sum(1 for entry in entries if isinstance(entry, dict) and entry.get("enrichment"))


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload
