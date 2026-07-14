import gzip
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.lexicon.publish_manifest import (
    ASSET_NAME,
    ManifestPublishError,
    build_pointer_payload,
    gzip_manifest,
    publish_manifest,
    validate_pointer_freshness,
    versioned_asset_name,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def test_build_pointer_payload_records_manifest_version_and_fingerprint(tmp_path: Path) -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "abc123"}
    manifest = {
        "version": "0.1",
        "generated_at": "2026-06-23T00:00:00+00:00",
        "manifest_fingerprint": fingerprint,
        "entries": [],
    }
    manifest_path = tmp_path / "lexicon-manifest.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    gzip_path = tmp_path / "lexicon-manifest.json.gz"
    _write_json(manifest_path, manifest)
    _write_json(fingerprint_path, fingerprint)

    gzip_bytes = gzip_manifest(manifest_path, gzip_path)
    payload = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        fingerprint_path=fingerprint_path,
        repo="learn-ukrainian/example",
    )

    manifest_bytes = manifest_path.read_bytes()
    assert gzip.decompress(gzip_bytes) == manifest_bytes
    expected_name = versioned_asset_name(_sha256(manifest_bytes))
    assert payload["asset_url"].endswith(f"/learn-ukrainian/example/releases/download/atlas-manifest/{expected_name}")
    assert payload["manifest_version"] == "0.1"
    assert payload["manifest_fingerprint"] == "abc123"
    assert payload["fingerprint_schema_version"] == 1
    assert payload["json_sha256"] == _sha256(manifest_bytes)
    assert payload["gz_sha256"] == _sha256(gzip_path.read_bytes())


def test_publish_manifest_uploads_versioned_and_canonical_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "abc123"}
    manifest = {
        "version": "0.1",
        "generated_at": "2026-06-23T00:00:00+00:00",
        "manifest_fingerprint": fingerprint,
        "entries": [],
    }
    manifest_path = tmp_path / "lexicon-manifest.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    gzip_path = tmp_path / ASSET_NAME
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_json(manifest_path, manifest)
    _write_json(fingerprint_path, fingerprint)
    expected_versioned_name = versioned_asset_name(_sha256(manifest_path.read_bytes()))
    upload_calls: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if args[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(args, 0, stdout='{"assets":[]}', stderr="")
        if args[:3] == ["gh", "release", "upload"]:
            assert Path(args[4]).exists()
            upload_calls.append(args)
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.download_published_manifest",
        lambda **kwargs: {"entries": []},
    )

    pointer = publish_manifest(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        fingerprint_path=fingerprint_path,
        repo="learn-ukrainian/example",
    )

    assert pointer["asset_url"].endswith(f"/{expected_versioned_name}")
    assert json.loads(pointer_path.read_text(encoding="utf-8")) == pointer
    assert [Path(call[4]).name for call in upload_calls] == [expected_versioned_name, ASSET_NAME]
    assert "--clobber" not in upload_calls[0]
    assert "--clobber" in upload_calls[1]


def test_publish_manifest_skips_existing_verified_versioned_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "abc123"}
    manifest = {
        "version": "0.1",
        "generated_at": "2026-06-23T00:00:00+00:00",
        "manifest_fingerprint": fingerprint,
        "entries": [],
    }
    manifest_path = tmp_path / "lexicon-manifest.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    gzip_path = tmp_path / ASSET_NAME
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_json(manifest_path, manifest)
    _write_json(fingerprint_path, fingerprint)
    expected_versioned_name = versioned_asset_name(_sha256(manifest_path.read_bytes()))
    upload_calls: list[list[str]] = []
    download_calls: list[str] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if args[:3] == ["gh", "release", "view"]:
            payload = {"assets": [{"name": expected_versioned_name}]}
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps(payload), stderr="")
        if args[:3] == ["gh", "release", "download"]:
            download_calls.append(args[5])
            return subprocess.CompletedProcess(args, 0, stdout=gzip_path.read_bytes(), stderr=b"")
        if args[:3] == ["gh", "release", "upload"]:
            upload_calls.append(args)
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.download_published_manifest",
        lambda **kwargs: {"entries": []},
    )

    publish_manifest(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        pointer_path=pointer_path,
        fingerprint_path=fingerprint_path,
        repo="learn-ukrainian/example",
    )

    assert download_calls == [expected_versioned_name]
    assert [Path(call[4]).name for call in upload_calls] == [ASSET_NAME]
    assert "--clobber" in upload_calls[0]


def test_pointer_freshness_guard_fails_on_stale_pointer_fixture() -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "current"}
    pointer = {
        "asset_url": "https://example.test/lexicon-manifest.json.gz",
        "release_tag": "atlas-manifest",
        "manifest_version": "0.1",
        "manifest_fingerprint": "stale",
        "fingerprint_schema_version": 1,
        "gz_sha256": "0" * 64,
        "json_sha256": "1" * 64,
        "gz_bytes": 10,
        "json_bytes": 20,
    }

    with pytest.raises(ManifestPublishError, match="fingerprint is stale"):
        validate_pointer_freshness(pointer, fingerprint)


def test_download_published_manifest_decodes_canonical_release_asset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.lexicon.publish_manifest import download_published_manifest

    release_manifest = {"version": "live", "entries": []}
    calls: list[tuple[str, str, str]] = []

    def fake_download(asset_name: str, *, release_tag: str, repo: str) -> bytes:
        calls.append((asset_name, release_tag, repo))
        return gzip.compress(json.dumps(release_manifest).encode("utf-8"))

    monkeypatch.setattr("scripts.lexicon.publish_manifest._download_release_asset", fake_download)

    assert download_published_manifest(release_tag="live-tag", repo="learn-ukrainian/example") == release_manifest
    assert calls == [(ASSET_NAME, "live-tag", "learn-ukrainian/example")]


def _richness_summary(*, thin: int, gloss: int, anchor: int, broken_stubs: int = 0) -> dict:
    return {
        "poc_thin_pages": thin,
        "search_no_visible_gloss": gloss,
        "old_gate_no_english_anchor": anchor,
        "form_stub_broken": broken_stubs,
    }


def _install_richness_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.audit.audit_atlas_poc_richness as richness

    monkeypatch.setattr(richness, "audit_manifest", lambda manifest: manifest["richness_summary"])


def test_richness_regression_blocks_before_packaging(tmp_path: Path, monkeypatch) -> None:
    """#4515: the publish chokepoint compares candidate and live baseline before gzip/upload."""
    import scripts.audit.audit_atlas_poc_richness as richness
    from scripts.lexicon.publish_manifest import assert_manifest_richness_publishable

    manifest_path = tmp_path / "lexicon-manifest.json"
    baseline = {"richness_summary": _richness_summary(thin=158, gloss=8, anchor=4)}
    _write_json(
        manifest_path,
        {"richness_summary": _richness_summary(thin=159, gloss=8, anchor=4)},
    )

    monkeypatch.setattr(richness, "audit_manifest", lambda manifest: manifest["richness_summary"])

    with pytest.raises(ManifestPublishError, match=r"poc_thin_pages 158→159"):
        assert_manifest_richness_publishable(manifest_path, baseline_manifest=baseline)

    # Wired into publish_manifest itself, and dry_run does NOT bypass it.
    gzip_calls: list[Path] = []
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.download_published_manifest",
        lambda **kwargs: baseline,
    )
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.gzip_manifest",
        lambda mp, gp: gzip_calls.append(mp),
    )
    with pytest.raises(ManifestPublishError, match=r"publish blocked \(#4515\)"):
        publish_manifest(
            manifest_path=manifest_path,
            gzip_path=tmp_path / "m.json.gz",
            pointer_path=tmp_path / "pointer.json",
            fingerprint_path=tmp_path / "fp.json",
            repo="learn-ukrainian/example",
            dry_run=True,
        )
    assert gzip_calls == [], "gate must fire before any packaging work"


def test_richness_improvement_passes_despite_nonzero_debt(tmp_path: Path, monkeypatch) -> None:
    from scripts.lexicon.publish_manifest import assert_manifest_richness_publishable

    manifest_path = tmp_path / "lexicon-manifest.json"
    baseline = {"richness_summary": _richness_summary(thin=800, gloss=158, anchor=4)}
    _write_json(
        manifest_path,
        {"richness_summary": _richness_summary(thin=700, gloss=120, anchor=1)},
    )
    _install_richness_audit(monkeypatch)

    record = assert_manifest_richness_publishable(manifest_path, baseline_manifest=baseline)
    assert record["candidate"]["search_no_visible_gloss"] == 120
    assert record["regressions"] == {}


def test_richness_equal_counts_pass(tmp_path: Path, monkeypatch) -> None:
    from scripts.lexicon.publish_manifest import assert_manifest_richness_publishable

    manifest_path = tmp_path / "lexicon-manifest.json"
    baseline = {"richness_summary": _richness_summary(thin=158, gloss=8, anchor=4)}
    _write_json(
        manifest_path,
        {"richness_summary": _richness_summary(thin=158, gloss=8, anchor=4)},
    )
    _install_richness_audit(monkeypatch)

    record = assert_manifest_richness_publishable(manifest_path, baseline_manifest=baseline)
    assert record["regressions"] == {}


def test_richness_override_requires_nonempty_reason(tmp_path: Path, monkeypatch) -> None:
    from scripts.lexicon.publish_manifest import assert_manifest_richness_publishable

    manifest_path = tmp_path / "lexicon-manifest.json"
    _write_json(
        manifest_path,
        {"richness_summary": _richness_summary(thin=159, gloss=8, anchor=4)},
    )
    _install_richness_audit(monkeypatch)

    with pytest.raises(ManifestPublishError, match="requires a non-empty reason"):
        assert_manifest_richness_publishable(
            manifest_path,
            baseline_manifest={"richness_summary": _richness_summary(thin=158, gloss=8, anchor=4)},
            allow_richness_regression_reason="  ",
        )


def test_richness_override_records_reason_in_publish_pointer(tmp_path: Path, monkeypatch) -> None:
    fingerprint = {"schema_version": 1, "fingerprint": "abc123"}
    baseline = {"richness_summary": _richness_summary(thin=158, gloss=8, anchor=4)}
    manifest = {
        "version": "0.1",
        "generated_at": "2026-06-23T00:00:00+00:00",
        "manifest_fingerprint": fingerprint,
        "entries": [],
        "richness_summary": _richness_summary(thin=159, gloss=8, anchor=4),
    }
    manifest_path = tmp_path / "lexicon-manifest.json"
    fingerprint_path = tmp_path / "lexicon-manifest.fingerprint.json"
    _write_json(manifest_path, manifest)
    _write_json(fingerprint_path, fingerprint)
    _install_richness_audit(monkeypatch)
    monkeypatch.setattr(
        "scripts.lexicon.publish_manifest.download_published_manifest",
        lambda **kwargs: baseline,
    )

    pointer = publish_manifest(
        manifest_path=manifest_path,
        gzip_path=tmp_path / "lexicon-manifest.json.gz",
        pointer_path=tmp_path / "lexicon-manifest.pointer.json",
        fingerprint_path=fingerprint_path,
        repo="learn-ukrainian/example",
        dry_run=True,
        allow_richness_regression_reason="operator approved source migration",
    )

    assert pointer["richness_gate"]["override_reason"] == "operator approved source migration"
    assert pointer["richness_gate"]["regressions"]["poc_thin_pages"] == {
        "baseline": 158,
        "candidate": 159,
    }


def test_richness_gate_blocks_publish_on_broken_form_stubs(tmp_path: Path, monkeypatch) -> None:
    from scripts.lexicon.publish_manifest import assert_manifest_richness_publishable

    manifest_path = tmp_path / "lexicon-manifest.json"
    _write_json(
        manifest_path,
        {"richness_summary": _richness_summary(thin=0, gloss=0, anchor=0, broken_stubs=2)},
    )
    _install_richness_audit(monkeypatch)

    with pytest.raises(ManifestPublishError, match=r"publish blocked \(#4220\).*2"):
        assert_manifest_richness_publishable(
            manifest_path,
            baseline_manifest={"richness_summary": _richness_summary(thin=0, gloss=0, anchor=0)},
        )
