"""Frozen VESUM consumers use release-owned bytes, never live replacements."""

import bz2
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness import build_scoring_dispositions as scoring
from scripts.projects.ua_eval_harness import verify_release_freeze as v010
from scripts.projects.ua_eval_harness import verify_release_freeze_v011 as v011
from scripts.projects.ua_eval_harness.release_sources import FROZEN_SOURCES, RELEASE_DIR, frozen_source_path

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release_root(tmp_path, monkeypatch):
    """Copy only the freeze inventory, then replace the active sources."""
    for verifier in (v010, v011):
        manifest = json.loads(verifier.DEFAULT_OUTPUT.read_text())
        paths = [verifier.DEFAULT_OUTPUT]
        paths.extend(verifier._frozen_artifact_path(Path(row["path"])) for row in manifest["artifacts"])
        for source in paths:
            target = tmp_path / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    entrypoint = Path("scripts/rag/build_vesum_shadow.py")
    (tmp_path / entrypoint).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / entrypoint, tmp_path / entrypoint)
    for logical in FROZEN_SOURCES:
        target = tmp_path / logical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('The live source has changed.\n')
    for module in (v010, v011, scoring):
        monkeypatch.setattr(module, "ROOT", tmp_path)
    return tmp_path


def test_live_sources_can_change_without_changing_either_freeze(release_root, capsys):
    for verifier in (v010, v011):
        freeze = json.loads(verifier.DEFAULT_OUTPUT.read_text())
        verifier.validate_freeze(freeze)
        assert verifier.build_freeze() == freeze
    assert v011.main(["--freeze", str(v011.DEFAULT_OUTPUT)]) == 0
    assert "Frozen VESUM lock SHA-256: 27362c3112579cbd8378314189c6c2032ac1d3db5f89f155f5557bb31a3d0fa6" in capsys.readouterr().out
    manifest = json.loads(scoring.DEFAULT_MANIFEST.read_text())
    config = json.loads(scoring.DEFAULT_CONFIG.read_text())
    dispositions = json.loads(scoring.DEFAULT_OUTPUT.read_text())
    scoring.validate_dispositions(dispositions, manifest=manifest, config=config)


@pytest.mark.parametrize("logical", list(FROZEN_SOURCES))
@pytest.mark.parametrize("mode", ["tamper", "missing"])
def test_frozen_sources_fail_closed_without_live_fallback(release_root, logical, mode):
    snapshot = frozen_source_path(release_root, logical)
    if mode == "tamper":
        snapshot.write_bytes(snapshot.read_bytes() + b"\n")
    else:
        snapshot.unlink()
    for verifier in (v010, v011):
        freeze = json.loads(verifier.DEFAULT_OUTPUT.read_text())
        with pytest.raises(verifier.FreezeError):
            verifier.validate_freeze(freeze)


def test_snapshot_provenance_matches_existing_release_pins():
    provenance = json.loads((ROOT / RELEASE_DIR / "source_snapshots.json").read_text())
    assert provenance["freeze_commit"] == "1497ad6a729ecdf97031bbd9d44059528a354608"
    manifest = json.loads(v011.DEFAULT_OUTPUT.read_text())
    pins = {row["path"]: row["sha256"] for row in manifest["artifacts"]}
    for logical, physical in FROZEN_SOURCES.items():
        digest = hashlib.sha256((ROOT / physical).read_bytes()).hexdigest()
        assert digest == provenance["sources"][physical.name] == pins[logical.as_posix()]
    assert frozen_source_path(ROOT, v010.PROMPT) == ROOT / v010.PROMPT


def test_scoring_build_executes_the_frozen_parser(release_root):
    """Use a miniature hash-pinned asset; live parser bytes are invalid Python."""
    asset = release_root / "miniature.txt.bz2"
    asset.write_bytes(bz2.compress("спікери noun:slang\n  Спікери noun:slang\n".encode()))
    lock_path = frozen_source_path(release_root, v010.VESUM_LOCK)
    lock = json.loads(lock_path.read_text())
    asset_digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    lock["release_asset"].update(sha256=asset_digest, size_bytes=asset.stat().st_size)
    lock_path.write_text(json.dumps(lock, ensure_ascii=False))
    config = json.loads(scoring.DEFAULT_CONFIG.read_text())
    config["evidence"].update(
        source_lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        release_asset_sha256=asset_digest,
    )
    manifest = json.loads(scoring.DEFAULT_MANIFEST.read_text())
    result = scoring.build_dispositions(manifest=manifest, config=config, asset_path=asset)
    scoring.validate_dispositions(result, manifest=manifest, config=config)
    assert result["counts"]["upstream_f_calque_annotations"] == 354
    layout = result["record_layout"]
    rows = [dict(zip(layout, row, strict=True)) for row in result["rows"]]
    speaker = next(row for row in rows if row["source_span"] == ["Спікери"])
    assert speaker["evidence"]["exact_form_evidence"][0]["style_markers"] == ["slang"]
    parser = scoring._frozen_vesum_parser(lock)
    assert Path(parser.__file__) == frozen_source_path(release_root, v010.VESUM_PARSER)


def test_frozen_parser_refuses_unpinned_bytes(release_root):
    lock = json.loads(frozen_source_path(release_root, v010.VESUM_LOCK).read_text())
    frozen_source_path(release_root, v010.VESUM_PARSER).write_text("raise RuntimeError('must never execute')\n")
    with pytest.raises(scoring.DispositionError, match="frozen VESUM parser hash mismatch"):
        scoring._frozen_vesum_parser(lock)


@pytest.mark.parametrize("logical", [v010.VESUM_LOCK, v010.VESUM_PARSER])
@pytest.mark.parametrize("mode", ["tamper", "missing"])
def test_scoring_checks_the_frozen_copy_without_live_fallback(release_root, logical, mode):
    snapshot = frozen_source_path(release_root, logical)
    if mode == "tamper":
        snapshot.write_bytes(snapshot.read_bytes() + b"\n")
    else:
        snapshot.unlink()
    config = json.loads(scoring.DEFAULT_CONFIG.read_text())
    manifest = json.loads(scoring.DEFAULT_MANIFEST.read_text())
    dispositions = json.loads(scoring.DEFAULT_OUTPUT.read_text())
    with pytest.raises(scoring.DispositionError):
        scoring.validate_dispositions(dispositions, manifest=manifest, config=config)
    with pytest.raises(scoring.DispositionError):
        scoring.build_dispositions(manifest=manifest, config=config, asset_path=release_root / "unused-asset")


@pytest.mark.parametrize("mode", ["--write", "--write-split-receipt"])
def test_verifier_cli_reproduces_immutable_receipts_using_frozen_sources(release_root, mode):
    output = release_root / "cli-output/v0.1.1"
    flag, name = ("--freeze", "freeze_manifest.json") if mode == "--write" else ("--split-receipt", "split_integrity.json")
    assert v011.main([mode, flag, str(output / name)]) == 0
    assert (output / name).read_bytes() == (ROOT / RELEASE_DIR / name).read_bytes()


def test_verifier_cli_reports_frozen_lock_tamper(release_root, capsys):
    snapshot = frozen_source_path(release_root, v010.VESUM_LOCK)
    snapshot.write_bytes(snapshot.read_bytes() + b"\n")
    assert v011.main(["--freeze", str(v011.DEFAULT_OUTPUT)]) == 1
    assert "frozen artifact hash mismatch" in capsys.readouterr().err
