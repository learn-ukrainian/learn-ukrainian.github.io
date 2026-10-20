"""Pinned word-card preview preparation and built-output checks (#11194)."""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts.deploy import prepare_word_card_preview as preview

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_PIN = REPO_ROOT / "site" / "src" / "data" / "word-card-preview-release.pointer.json"
SITE_PUBLIC_PIN = REPO_ROOT / "site" / "src" / "lib" / "lexicon" / "word-card-preview-inputs.ts"
RUNBOOK = REPO_ROOT / "docs" / "atlas" / "word-cards" / "public-preview.md"
FIXTURE_ROOT = REPO_ROOT / "site" / "tests" / "fixtures" / "word-card-preview"

# Frozen independently of the committed pin: the published word-cards-v0.1 assets.
REAL_DATASET = (2879813, "45bd9c9325a3b4221c86d1663d784e96a7edc096674415445d37113f793189e6")
REAL_MANIFEST = (3292, "ca182bf5829f3ed4daa80c2394eb87e28879c3f1dc5088eef689f495b97e4f75")
CARD_IDS = ("wc_000000000001", "wc_000000000002")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _release(
    *, card_ids: tuple[str, ...] = CARD_IDS, manifest_overrides: dict | None = None, dataset: bytes | None = None
) -> tuple[bytes, bytes]:
    if dataset is None:
        dataset = "".join(
            json.dumps({"card_id": card_id, "status": "CANDIDATE"}) + "\n" for card_id in card_ids
        ).encode()
    manifest = {
        "schema_version": "word-card-dataset.v1",
        "release_version": "v9.9.9-test",
        "dataset_file": "word-cards.jsonl",
        "dataset_sha256": _sha(dataset),
        "dataset_bytes": len(dataset),
        "card_count": len(card_ids),
        "certified_count": 0,
        "candidate_count": len(card_ids),
        "field_citation_count": 0,
    }
    manifest.update(manifest_overrides or {})
    return json.dumps(manifest).encode(), dataset


def _pin(manifest: bytes, dataset: bytes, **overrides) -> dict:
    pin = {
        "schema_version": "word-card-preview-release-pin.v1",
        "repository": "learn-ukrainian/learn-ukrainian.github.io",
        "release_tag": "word-cards-v9",
        "release_version": "v9.9.9-test",
        "provenance": "producer-declared",
        "assets": {
            "manifest.json": {"bytes": len(manifest), "sha256": _sha(manifest)},
            "word-cards.jsonl": {"bytes": len(dataset), "sha256": _sha(dataset)},
        },
    }
    pin.update(overrides)
    return pin


def _write_pin(tmp_path: Path, pin: dict) -> Path:
    path = tmp_path / "pin.json"
    path.write_text(json.dumps(pin), encoding="utf-8")
    return path


def _served(manifest: bytes, dataset: bytes, calls: list[str] | None = None):
    assets = {"manifest.json": manifest, "word-cards.jsonl": dataset}

    def fetch(url: str) -> bytes:
        if calls is not None:
            calls.append(url)
        return assets[url.rsplit("/", 1)[1]]

    return fetch


def _prepare(tmp_path: Path, pin: dict, manifest: bytes, dataset: bytes, environ: dict | None = None):
    return preview.prepare(
        _write_pin(tmp_path, pin), tmp_path / "release", environ=environ or {}, fetch=_served(manifest, dataset)
    )


# --- independently frozen negatives -------------------------------------------------------------


def test_committed_pin_matches_the_published_release_runbook_and_site_selector() -> None:
    """A wrong committed byte size, digest, version or provenance must fail here before any build."""
    pin = preview.load_pin(COMMITTED_PIN)
    assert pin["repository"] == "learn-ukrainian/learn-ukrainian.github.io"
    assert pin["release_tag"] == "word-cards-v0.1"
    assert pin["release_version"] == "v0.1.0-pilot"
    assert pin["provenance"] == "producer-declared"
    assert (pin["assets"]["word-cards.jsonl"]["bytes"], pin["assets"]["word-cards.jsonl"]["sha256"]) == REAL_DATASET
    assert (pin["assets"]["manifest.json"]["bytes"], pin["assets"]["manifest.json"]["sha256"]) == REAL_MANIFEST

    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert f"| word-cards.jsonl | {REAL_DATASET[0]} | `{REAL_DATASET[1]}` |" in runbook
    assert f"| manifest.json | {REAL_MANIFEST[0]} | `{REAL_MANIFEST[1]}` |" in runbook

    # The site freezes its own public selector; the build pin must equal it field for field.
    source = SITE_PUBLIC_PIN.read_text(encoding="utf-8")
    block = source.split("export const publicReleasePin = {", 1)[1].split("}", 1)[0]
    site_selector = dict(re.findall(r"(\w+): '([^']*)'", block))
    assert json.loads(preview.site_pin(pin)) == site_selector


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p.update(provenance="synthetic-fixture"), "producer-declared"),
        (lambda p: p.update(schema_version="v0"), "unsupported release pin schema"),
        (lambda p: p.update(extra=1), "exactly the keys"),
        (lambda p: p.update(repository="evil/../repo"), "owner/name"),
        (lambda p: p.update(repository="owner/repo$(id)"), "owner/name"),
        (lambda p: p.update(release_tag="../../x"), "plain tag"),
        (lambda p: p.update(release_tag="v1;curl x"), "plain tag"),
        (lambda p: p.update(release_version=" "), "release_version"),
        (lambda p: p["assets"].update({"../evil": {"bytes": 1, "sha256": "0" * 64}}), "assets must be exactly"),
        (lambda p: p["assets"].pop("manifest.json"), "assets must be exactly"),
        (lambda p: p["assets"]["manifest.json"].update(url="https://example.invalid/x"), "exactly bytes and sha256"),
        (lambda p: p["assets"]["manifest.json"].update(bytes=True), "positive integer"),
        (lambda p: p["assets"]["manifest.json"].update(bytes=0), "positive integer"),
        (lambda p: p["assets"]["manifest.json"].update(sha256="A" * 64), "64 lowercase hex"),
    ],
)
def test_pin_refusals(tmp_path: Path, mutate, message: str) -> None:
    manifest, dataset = _release()
    pin = _pin(manifest, dataset)
    mutate(pin)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        preview.load_pin(_write_pin(tmp_path, pin))


def test_pin_must_be_strict_json(tmp_path: Path) -> None:
    path = tmp_path / "pin.json"
    path.write_text('{"schema_version": "a", "schema_version": "b"}', encoding="utf-8")
    with pytest.raises(preview.PreviewError, match="duplicate keys"):
        preview.load_pin(path)
    path.write_bytes(b"\xff")
    with pytest.raises(preview.PreviewError, match="not valid UTF-8 JSON"):
        preview.load_pin(path)
    with pytest.raises(preview.PreviewError, match="unreadable"):
        preview.load_pin(tmp_path / "missing.json")


@pytest.mark.parametrize("value", ["1", "0", "", "false"])
def test_controls_flag_is_refused_whatever_its_value(tmp_path: Path, value: str) -> None:
    manifest, dataset = _release()
    with pytest.raises(preview.PreviewError, match="must be absent"):
        _prepare(tmp_path, _pin(manifest, dataset), manifest, dataset, {preview.CONTROLS_FLAG: value})
    assert not (tmp_path / "release").exists()


def test_asset_size_and_digest_mismatches_refuse_before_writing(tmp_path: Path) -> None:
    manifest, dataset = _release()
    pin = _pin(manifest, dataset)
    with pytest.raises(preview.PreviewError, match=re.escape("word-cards.jsonl size mismatch")):
        _prepare(tmp_path, pin, manifest, dataset + b"\n")
    same_size = dataset.replace(b"000000000001", b"000000000003")
    assert len(same_size) == len(dataset)
    with pytest.raises(preview.PreviewError, match=re.escape("word-cards.jsonl sha256 mismatch")):
        _prepare(tmp_path, pin, manifest, same_size)
    with pytest.raises(preview.PreviewError, match=re.escape("manifest.json size mismatch")):
        _prepare(tmp_path, pin, b"", dataset)
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"schema_version": "word-card-dataset.v0"}, "manifest schema_version"),
        ({"release_version": "v0.0.0"}, "manifest release_version"),
        ({"dataset_file": "word-cards.json"}, "manifest dataset_file"),
        ({"dataset_sha256": "0" * 64}, "manifest dataset_sha256"),
        ({"dataset_bytes": 1}, "manifest dataset_bytes"),
        ({"withdrawal_notice_sha256": "0" * 64}, "withdrawal notice"),
        ({"certified_count": 1}, "certified_count 0"),
        ({"card_count": 3}, "card_count 3"),
    ],
)
def test_manifest_must_match_the_pin(tmp_path: Path, overrides: dict, message: str) -> None:
    manifest, dataset = _release(manifest_overrides=overrides)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        _prepare(tmp_path, _pin(manifest, dataset), manifest, dataset)
    assert not (tmp_path / "release").exists()


@pytest.mark.parametrize(
    ("dataset", "card_ids", "message"),
    [
        (b'{"card_id": "../../etc"}\n', ("x",), "no valid card_id"),
        (b'{"card_id": "wc_00000000000I"}\n', ("x",), "no valid card_id"),
        (b"[]\n", ("x",), "no valid card_id"),
        (b'{"card_id": "wc_000000000001"}\n{"card_id": "wc_000000000001"}\n', ("a", "b"), "repeats a card_id"),
        (b'{"card_id": "wc_000000000001", "card_id": "wc_000000000002"}\n', ("x",), "duplicate keys"),
        (b"\xff\n", ("x",), "not UTF-8"),
        (b"{not json\n", ("x",), "not valid UTF-8 JSON"),
        (b"\n", (), "card_count"),
    ],
)
def test_dataset_rows_are_checked(tmp_path: Path, dataset: bytes, card_ids: tuple[str, ...], message: str) -> None:
    manifest, dataset = _release(card_ids=card_ids, dataset=dataset)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        _prepare(tmp_path, _pin(manifest, dataset), manifest, dataset)


def test_manifest_must_be_a_json_object(tmp_path: Path) -> None:
    _, dataset = _release()
    manifest = b"[]"
    with pytest.raises(preview.PreviewError, match="JSON object"):
        _prepare(tmp_path, _pin(manifest, dataset), manifest, dataset)


def test_missing_asset_fails_after_bounded_retries(tmp_path: Path) -> None:
    manifest, dataset = _release()
    calls: list[str] = []

    def missing(url: str) -> bytes:
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    with pytest.raises(preview.PreviewError, match=re.escape("could not download manifest.json after 3 attempts")):
        preview.prepare(_write_pin(tmp_path, _pin(manifest, dataset)), tmp_path / "release", environ={}, fetch=missing)
    assert (
        calls
        == [
            "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/word-cards-v9/manifest.json"
        ]
        * 3
    )


def test_transient_download_error_is_retried(tmp_path: Path) -> None:
    manifest, dataset = _release()
    served = _served(manifest, dataset)
    failures = iter([True])

    def flaky(url: str) -> bytes:
        if next(failures, False):
            raise OSError("connection reset")
        return served(url)

    outputs = preview.prepare(
        _write_pin(tmp_path, _pin(manifest, dataset)), tmp_path / "release", environ={}, fetch=flaky
    )
    assert outputs["card-count"] == "2"


def test_destination_must_be_absent_or_empty(tmp_path: Path) -> None:
    manifest, dataset = _release()
    (tmp_path / "release").mkdir()
    (tmp_path / "release" / "manifest.json").write_bytes(b"stale")
    with pytest.raises(preview.PreviewError, match="absent or an empty directory"):
        _prepare(tmp_path, _pin(manifest, dataset), manifest, dataset)
    file_dest = tmp_path / "file"
    file_dest.write_text("x", encoding="utf-8")
    with pytest.raises(preview.PreviewError, match="absent or an empty directory"):
        preview.prepare(
            _write_pin(tmp_path, _pin(manifest, dataset)), file_dest, environ={}, fetch=_served(manifest, dataset)
        )


def test_redirects_stay_on_https_github_release_hosts() -> None:
    handler = preview._HttpsGitHubRedirects()
    request = urllib.request.Request("https://github.com/o/r/releases/download/t/a")
    allowed = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://release-assets.githubusercontent.com/github-production-release-asset/1",
    )
    assert allowed.full_url.startswith("https://release-assets.githubusercontent.com/")
    for target in ("http://release-assets.githubusercontent.com/x", "https://example.invalid/x", "file:///etc/passwd"):
        with pytest.raises(urllib.error.HTTPError, match="refused release asset redirect"):
            handler.redirect_request(request, None, 302, "Found", {}, target)


def test_fetch_uses_the_shared_client_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def read(self) -> bytes:
            return b"bytes"

    def http_open(request, *, timeout, opener):
        seen.update(url=request.full_url, auth=request.get_header("Authorization"), timeout=timeout, opener=opener)
        return Response()

    monkeypatch.setattr(preview.github_client, "http_open", http_open)
    assert preview._fetch("https://github.com/o/r/releases/download/t/a") == b"bytes"
    assert seen == {
        "url": "https://github.com/o/r/releases/download/t/a",
        "auth": None,
        "timeout": 60,
        "opener": preview._OPENER.open,
    }


# --- valid preparation -----------------------------------------------------------------------------


def test_prepare_writes_verified_assets_and_the_exact_site_pin(tmp_path: Path) -> None:
    manifest, dataset = _release()
    calls: list[str] = []
    pin = _pin(manifest, dataset)
    outputs = preview.prepare(
        _write_pin(tmp_path, pin), tmp_path / "release", environ={"OTHER": "1"}, fetch=_served(manifest, dataset, calls)
    )
    base = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/word-cards-v9/"
    assert calls == [base + "manifest.json", base + "word-cards.jsonl"]
    assert (tmp_path / "release" / "manifest.json").read_bytes() == manifest
    assert (tmp_path / "release" / "word-cards.jsonl").read_bytes() == dataset
    assert sorted(p.name for p in (tmp_path / "release").iterdir()) == ["manifest.json", "word-cards.jsonl"]
    assert outputs["release-path"] == str((tmp_path / "release").resolve())
    assert outputs["card-count"] == "2"
    assert json.loads(outputs["pin"]) == {
        "release_version": "v9.9.9-test",
        "dataset_sha256": _sha(dataset),
        "manifest_sha256": _sha(manifest),
        "provenance": "producer-declared",
    }


def test_cli_prepare_writes_github_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    manifest, dataset = _release()
    pin_path = _write_pin(tmp_path, _pin(manifest, dataset))
    monkeypatch.setattr(preview, "_fetch", _served(manifest, dataset))
    monkeypatch.delenv(preview.CONTROLS_FLAG, raising=False)
    output = tmp_path / "github_output"
    output.write_text("previous=1\n", encoding="utf-8")
    rc = preview.main(
        ["prepare", "--pin", str(pin_path), "--dest", str(tmp_path / "release"), "--github-output", str(output)]
    )
    assert rc == 0
    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "previous=1"
    assert [line.split("=", 1)[0] for line in lines[1:]] == ["release-path", "pin", "card-count"]
    assert "verified 2 cards" in capsys.readouterr().out


def test_cli_refusal_exits_nonzero_with_annotation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    manifest, dataset = _release()
    monkeypatch.setenv(preview.CONTROLS_FLAG, "")
    rc = preview.main(
        ["prepare", "--pin", str(_write_pin(tmp_path, _pin(manifest, dataset))), "--dest", str(tmp_path / "r")]
    )
    assert rc == 1
    assert "::error title=Word-card preview refused::" in capsys.readouterr().err


def test_github_output_values_cannot_inject_lines(tmp_path: Path) -> None:
    with pytest.raises(preview.PreviewError, match="line break"):
        preview._write_outputs(tmp_path / "out", {"pin": "a\nATLAS_WORD_CARD_PREVIEW=0"})
    assert not (tmp_path / "out").exists()


def test_cli_help_documents_usage(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        preview.main(["--help"])
    assert exc.value.code == 0
    text = capsys.readouterr().out
    for needle in ("prepare", "verify-dist", "Examples:", "Outputs:", "Exit codes:", "#11194"):
        assert needle in text


# --- built-output verification ---------------------------------------------------------------------


def _page(robots: str | None = preview.ROBOTS, body: str = "Pinned release preview.") -> str:
    meta = f'<meta name="robots" content="{robots}">' if robots is not None else ""
    return f"<!DOCTYPE html><html><head><title>x</title>{meta}</head><body>{body}</body></html>"


def _built(tmp_path: Path, card_ids: tuple[str, ...] = CARD_IDS) -> tuple[Path, Path, Path]:
    manifest, dataset = _release(card_ids=card_ids)
    pin_path = _write_pin(tmp_path, _pin(manifest, dataset))
    release = tmp_path / "release"
    release.mkdir()
    (release / "manifest.json").write_bytes(manifest)
    (release / "word-cards.jsonl").write_bytes(dataset)
    dist = tmp_path / "dist"
    routes = ["lexicon-v2/release/index.html", "lexicon-v2/compare/release/index.html"]
    routes += [
        f"lexicon-v2/{prefix}release/{card_id}/index.html" for card_id in card_ids for prefix in ("", "compare/")
    ]
    for route in routes:
        (dist / route).parent.mkdir(parents=True, exist_ok=True)
        (dist / route).write_text(_page(), encoding="utf-8")
    (dist / "index.html").write_text("<html><head></head><body>home</body></html>", encoding="utf-8")
    (dist / "sitemap-index.xml").write_text("<sitemapindex><loc>https://x/sitemap-0.xml</loc></sitemapindex>")
    (dist / "sitemap-0.xml").write_text("<urlset><url><loc>https://learn-ukrainian.github.io/</loc></url></urlset>")
    (dist / "_astro").mkdir()
    (dist / "_astro" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return dist, release, pin_path


def test_verify_dist_accepts_exact_noindex_preview(tmp_path: Path) -> None:
    dist, release, pin_path = _built(tmp_path)
    counts = preview.verify_dist(dist, release, pin_path, FIXTURE_ROOT)
    assert counts == {"routes": 6, "cards": 2, "sitemaps": 2, "scripts_scanned": 1}
    rc = preview.main(["verify-dist", str(dist), "--release-dir", str(release), "--pin", str(pin_path)])
    assert rc == 0


def _mutations():
    def remove(dist: Path) -> None:
        (dist / "lexicon-v2/compare/release/wc_000000000002/index.html").unlink()

    def flag_off(dist: Path) -> None:
        import shutil

        shutil.rmtree(dist / "lexicon-v2")

    def fixture_route(dist: Path) -> None:
        (dist / "lexicon-v2/sample").mkdir(parents=True)
        (dist / "lexicon-v2/sample/index.html").write_text(_page(), encoding="utf-8")

    def write(route: str, text: str):
        return lambda dist: (dist / route).write_text(text, encoding="utf-8")

    card = "lexicon-v2/release/wc_000000000001/index.html"
    return [
        (remove, "1 missing"),
        (flag_off, "6 missing"),
        (fixture_route, "1 unexpected"),
        (write(card, _page(robots=None)), "robots meta is []"),
        (write(card, _page(robots="index, follow")), "robots meta is ['index, follow']"),
        (write(card, _page() + '<meta name="robots" content="all">'), "robots meta is"),
        (
            write("lexicon-v2/release/index.html", _page(body="Configured release refused")),
            "Configured release refused",
        ),
        (write(card, _page(body="Real data unavailable")), "Real data unavailable"),
        (write(card, _page(body="synthetic-fixture")), "synthetic-fixture"),
        (write(card, _page(body="wc_0123456789ac")), "wc_0123456789ac"),
        (write(card, _page(body="v0.1.0-synthetic")), "v0.1.0-synthetic"),
        (write("_astro/app.js", "const id = 'wc_0123456789ab';"), "_astro/app.js: contains fixture marker"),
        (
            write("sitemap-0.xml", "<loc>https://learn-ukrainian.github.io/lexicon-v2/release/</loc>"),
            "lists a preview URL",
        ),
        (lambda dist: [p.unlink() for p in dist.glob("sitemap*.xml")], "no sitemap emitted"),
    ]


@pytest.mark.parametrize(("mutate", "message"), _mutations())
def test_verify_dist_refusals(tmp_path: Path, mutate, message: str) -> None:
    dist, release, pin_path = _built(tmp_path)
    mutate(dist)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        preview.verify_dist(dist, release, pin_path, FIXTURE_ROOT)


def test_verify_dist_rechecks_the_release_directory(tmp_path: Path, capsys) -> None:
    dist, release, pin_path = _built(tmp_path)
    (release / "word-cards.jsonl").write_bytes(b"x" * len((release / "word-cards.jsonl").read_bytes()))
    with pytest.raises(preview.PreviewError, match="no longer matches the pin"):
        preview.verify_dist(dist, release, pin_path, FIXTURE_ROOT)
    (release / "word-cards.jsonl").unlink()
    rc = preview.main(["verify-dist", str(dist), "--release-dir", str(release), "--pin", str(pin_path)])
    assert rc == 1
    assert "::error title=Word-card preview refused::" in capsys.readouterr().err


def test_fixture_sentinels_come_from_the_committed_synthetic_releases(tmp_path: Path) -> None:
    sentinels = preview.fixture_sentinels(FIXTURE_ROOT)
    assert {"wc_0123456789ab", "wc_0123456789ac", "v0.1.0-synthetic", "v0.1.1-synthetic"} <= sentinels
    assert "24c3b98a65f57294bec78795c179252950eb071ede008320ce03b06f6c5faf6d" in sentinels
    with pytest.raises(preview.PreviewError, match="no synthetic release fixtures"):
        preview.fixture_sentinels(tmp_path)


def test_sentinels_shared_with_the_real_release_are_not_false_positives(tmp_path: Path) -> None:
    dist, release, pin_path = _built(tmp_path)
    fixtures = tmp_path / "fixtures" / "pkg"
    fixtures.mkdir(parents=True)
    rows = [{"card_id": "wc_000000000001"}]
    data = json.dumps(rows).encode()
    (fixtures / "word-cards.json").write_bytes(data)
    (fixtures / "manifest.json").write_text(
        json.dumps({"release_version": "fixture-only-version", "dataset_file": "word-cards.json"}), encoding="utf-8"
    )
    (dist / "lexicon-v2/release/wc_000000000001/index.html").write_text(_page(body="wc_000000000001"), encoding="utf-8")
    assert preview.verify_dist(dist, release, pin_path, tmp_path / "fixtures")["routes"] == 6
    (dist / "lexicon-v2/release/index.html").write_text(_page(body="fixture-only-version"), encoding="utf-8")
    with pytest.raises(preview.PreviewError, match="fixture-only-version"):
        preview.verify_dist(dist, release, pin_path, tmp_path / "fixtures")
