"""Pinned word-card preview preparation and built-output checks (#11194)."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
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


@pytest.mark.needs_sparse_tree("site/src/data")
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


# A controlled release whose rows carry the kinds and citations the inventory is reconciled with.
VERIFY_ROWS = (
    {"card_id": "wc_000000000001", "card_kind": "lexeme", "status": "CANDIDATE", "fields": [{}, {}]},
    {"card_id": "wc_000000000002", "card_kind": "mwe", "status": "CANDIDATE", "fields": [{}]},
    {"card_id": "wc_000000000003", "card_kind": "proper_name", "status": "CANDIDATE", "fields": [{}]},
)
KIT = "/lexicon-v2/word/кіт/"


def _route(path: str, kind: str, href: str | None = None) -> dict:
    return {"path": path, "href": href or path, "class": kind}


def _inventory(manifest: bytes, dataset: bytes) -> dict:
    """Atlas's inventory for VERIFY_ROWS, written out by hand: 10 routes, 3 cards, 2 entries on one page."""
    return {
        "schema_version": "word-card-preview-route-inventory.v1",
        "release": {
            "release_version": "v9.9.9-test",
            "dataset_sha256": _sha(dataset),
            "manifest_sha256": _sha(manifest),
            "provenance": "producer-declared",
            "dataset_bytes": len(dataset),
            "manifest_bytes": len(manifest),
        },
        "counts": {
            "source_cards": 3,
            "citations": 4,
            "page_keys": 2,
            "learner_pages": 1,
            "visible_entries": 2,
            "proper_entries_listed": 0,
            "proper_only_unlisted": 1,
            "refused_without_key": 0,
            "emitted_routes": 10,
            "routes_by_class": {
                "release-summary": 1,
                "compare-release-summary": 1,
                "card-diagnostic": 3,
                "compare-card-diagnostic": 3,
                "word-page": 1,
                "compare-word-page": 1,
                "unused-class": 0,
            },
        },
        "routes": [
            _route("/lexicon-v2/compare/release/", "compare-release-summary"),
            _route("/lexicon-v2/compare/release/wc_000000000001/", "compare-card-diagnostic"),
            _route("/lexicon-v2/compare/release/wc_000000000002/", "compare-card-diagnostic"),
            _route("/lexicon-v2/compare/release/wc_000000000003/", "compare-card-diagnostic"),
            _route(
                "/lexicon-v2/compare/word/кіт/", "compare-word-page", "/lexicon-v2/compare/word/%D0%BA%D1%96%D1%82/"
            ),
            _route("/lexicon-v2/release/", "release-summary"),
            _route("/lexicon-v2/release/wc_000000000001/", "card-diagnostic"),
            _route("/lexicon-v2/release/wc_000000000002/", "card-diagnostic"),
            _route("/lexicon-v2/release/wc_000000000003/", "card-diagnostic"),
            _route(KIT, "word-page", "/lexicon-v2/word/%D0%BA%D1%96%D1%82/"),
        ],
        "cards": [
            {
                "card_id": "wc_000000000001",
                "card_kind": "lexeme",
                "page": "кіт",
                "entry": 1,
                "listed": True,
                "reason": "Listed entry",
            },
            {
                "card_id": "wc_000000000002",
                "card_kind": "mwe",
                "page": "кіт",
                "entry": 2,
                "listed": True,
                "reason": "Listed entry",
            },
            {
                "card_id": "wc_000000000003",
                "card_kind": "proper_name",
                "page": "юнеско",
                "entry": None,
                "listed": False,
                "reason": "Proper name without a common entry on its page",
            },
        ],
    }


class Built:
    def __init__(self, tmp_path: Path) -> None:
        dataset = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in VERIFY_ROWS).encode()
        self.manifest, self.dataset = _release(card_ids=tuple(r["card_id"] for r in VERIFY_ROWS), dataset=dataset)
        self.pin = _write_pin(tmp_path, _pin(self.manifest, self.dataset))
        self.release = tmp_path / "release"
        self.release.mkdir()
        (self.release / "manifest.json").write_bytes(self.manifest)
        (self.release / "word-cards.jsonl").write_bytes(self.dataset)
        self.inventory_path = tmp_path / "route-inventory.json"
        self.write_inventory(_inventory(self.manifest, self.dataset))
        self.dist = tmp_path / "dist"
        # Simulated Astro output: one index.html per independently listed route, decoded path on disk.
        for route in _inventory(self.manifest, self.dataset)["routes"]:
            page = self.dist / route["path"].strip("/") / "index.html"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(_page(), encoding="utf-8")
        (self.dist / "index.html").write_text("<html><head></head><body>home</body></html>", encoding="utf-8")
        (self.dist / "sitemap-index.xml").write_text("<sitemapindex><loc>https://x/sitemap-0.xml</loc></sitemapindex>")
        (self.dist / "sitemap-0.xml").write_text(
            "<urlset><url><loc>https://learn-ukrainian.github.io/</loc></url></urlset>"
        )
        (self.dist / "_astro").mkdir()
        (self.dist / "_astro" / "app.js").write_text("console.log('ok')", encoding="utf-8")

    def write_inventory(self, inventory: dict) -> None:
        self.inventory_path.write_text(json.dumps(inventory, ensure_ascii=False), encoding="utf-8")

    def inventory(self) -> dict:
        return json.loads(self.inventory_path.read_text(encoding="utf-8"))

    def verify(self, fixture_root: Path = FIXTURE_ROOT) -> dict:
        return preview.verify_dist(self.dist, self.release, self.pin, fixture_root, self.inventory_path)

    def cli(self, *extra: str) -> int:
        return preview.main(
            ["verify-dist", str(self.dist), "--release-dir", str(self.release), "--pin", str(self.pin), *extra]
        )


def test_verify_dist_accepts_exactly_the_inventoried_noindex_preview(tmp_path: Path, capsys) -> None:
    built = Built(tmp_path)
    assert built.verify() == {
        "routes": 10,
        "cards": 3,
        "citations": 4,
        "learner_pages": 1,
        "visible_entries": 2,
        "sitemaps": 2,
        "scripts_scanned": 1,
    }
    assert built.cli("--inventory", str(built.inventory_path)) == 0
    assert capsys.readouterr().out.strip() == (
        "word-card preview: 10 inventoried noindex routes for 3 cards (4 citations, 1 learner pages, "
        "2 visible entries); 2 sitemaps exclude them; 1 scripts fixture-free"
    )


def test_verify_dist_reads_the_atlas_inventory_by_default() -> None:
    assert preview.DEFAULT_INVENTORY == REPO_ROOT / "site/src/lib/lexicon/word-card-preview-route-inventory.json"
    verify = preview.build_parser().parse_args(["verify-dist", "site/dist", "--release-dir", "r"])
    assert verify.inventory == preview.DEFAULT_INVENTORY


def _dist_mutations():
    def remove(route: str):
        return lambda dist: (dist / route).unlink()

    def flag_off(dist: Path) -> None:
        shutil.rmtree(dist / "lexicon-v2")

    def legacy_shape_only(dist: Path) -> None:
        shutil.rmtree(dist / "lexicon-v2/word")
        shutil.rmtree(dist / "lexicon-v2/compare/word")

    def uninventoried_route(dist: Path) -> None:
        (dist / "lexicon-v2/word/юнеско").mkdir(parents=True)
        (dist / "lexicon-v2/word/юнеско/index.html").write_text(_page(), encoding="utf-8")

    def encoded_directory(dist: Path) -> None:
        (dist / "lexicon-v2/word/кіт").rename(dist / "lexicon-v2/word/%D0%BA%D1%96%D1%82")

    def write(route: str, text: str):
        return lambda dist: (dist / route).write_text(text, encoding="utf-8")

    card = "lexicon-v2/release/wc_000000000001/index.html"
    word = "lexicon-v2/compare/word/кіт/index.html"
    return [
        (remove("lexicon-v2/compare/release/wc_000000000002/index.html"), "1 missing"),
        (remove(word), "1 missing ['lexicon-v2/compare/word/кіт/index.html']"),
        (flag_off, "10 missing"),
        (legacy_shape_only, "2 missing"),
        (uninventoried_route, "1 unexpected ['lexicon-v2/word/юнеско/index.html']"),
        (encoded_directory, "1 missing ['lexicon-v2/word/кіт/index.html'], 1 unexpected"),
        (write(card, _page(robots=None)), "robots meta is []"),
        (write(word, _page(robots=None)), "compare/word/кіт/index.html: robots meta is []"),
        (write(card, _page(robots="index, follow")), "robots meta is ['index, follow']"),
        (write(card, _page() + '<meta name="robots" content="all">'), "robots meta is"),
        (
            write("lexicon-v2/release/index.html", _page(body="Configured release refused")),
            "Configured release refused",
        ),
        (write(card, _page(body="Real data unavailable")), "Real data unavailable"),
        (write(word, _page(body="synthetic-fixture")), "synthetic-fixture"),
        (write(card, _page(body="wc_0123456789ac")), "wc_0123456789ac"),
        (write(card, _page(body="v0.1.0-synthetic")), "v0.1.0-synthetic"),
        (write("_astro/app.js", "const id = 'wc_0123456789ab';"), "_astro/app.js: contains fixture marker"),
        (
            write("sitemap-0.xml", "<loc>https://learn-ukrainian.github.io/lexicon-v2/word/x/</loc>"),
            "lists a preview URL",
        ),
        (lambda dist: [p.unlink() for p in dist.glob("sitemap*.xml")], "no sitemap emitted"),
    ]


@pytest.mark.parametrize(("mutate", "message"), _dist_mutations())
def test_verify_dist_refuses_built_output_that_differs_from_the_inventory(tmp_path: Path, mutate, message: str) -> None:
    built = Built(tmp_path)
    mutate(built.dist)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        built.verify()


def _counts(name: str, value):
    return lambda inv: inv["counts"].update({name: value})


def _route_at(index: int, **changes):
    return lambda inv: inv["routes"][index].update(changes)


def _card_at(index: int, **changes):
    return lambda inv: inv["cards"][index].update(changes)


def _inventory_mutations():
    other = "0" * 64
    return [
        (lambda inv: inv.update(extra=1), "exactly the keys"),
        (lambda inv: inv.pop("cards"), "exactly the keys"),
        (lambda inv: inv.update(schema_version="word-card-preview-route-inventory.v0"), "unsupported route inventory"),
        # A stale inventory for another release, version or byte count is refused.
        (lambda inv: inv["release"].update(dataset_sha256=other), "does not match the pin"),
        (lambda inv: inv["release"].update(manifest_sha256=other), "does not match the pin"),
        (lambda inv: inv["release"].update(release_version="v0.0.9"), "does not match the pin"),
        (lambda inv: inv["release"].update(provenance="synthetic-fixture"), "does not match the pin"),
        (lambda inv: inv["release"].update(dataset_bytes=1), "does not match the pin"),
        (lambda inv: inv["release"].pop("manifest_bytes"), "does not match the pin"),
        # Routes.
        (lambda inv: inv.update(routes=[]), "routes must be a non-empty list"),
        (lambda inv: inv.update(routes={}), "routes must be a non-empty list"),
        (lambda inv: inv["routes"].append(dict(inv["routes"][0])), "repeats route /lexicon-v2/compare/release/"),
        (_route_at(0, extra="x"), "exactly path, href and class"),
        (lambda inv: inv["routes"][0].pop("href"), "exactly path, href and class"),
        (_route_at(5, path="/lexicon/release/", href="/lexicon/release/"), "is not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/release", href="/lexicon-v2/release"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/", href="/lexicon-v2/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/../x/", href="/lexicon-v2/../x/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/./x/", href="/lexicon-v2/./x/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2//x/", href="/lexicon-v2//x/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/a%2Fb/", href="/lexicon-v2/a%252Fb/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/a\nb/", href="/lexicon-v2/a%0Ab/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path="/lexicon-v2/a\u202eb/", href="/lexicon-v2/a%E2%80%AEb/"), "not a /lexicon-v2/ route path"),
        (_route_at(5, path=5), "not a /lexicon-v2/ route path"),
        (_route_at(9, href=KIT), "does not encode /lexicon-v2/word/кіт/"),
        (_route_at(9, href="/lexicon-v2/word/%d0%ba%d1%96%d1%82/"), "does not encode"),
        (_route_at(9, **{"class": ""}), "has no class"),
        (_route_at(9, **{"class": None}), "has no class"),
        # Card dispositions must cover exactly the verified release, once each.
        (lambda inv: inv.update(cards={}), "cards must be a list"),
        (lambda inv: inv["cards"].pop(), "omit 1 release cards ['wc_000000000003']"),
        (lambda inv: inv.update(cards=[]), "omit 3 release cards"),
        (lambda inv: inv["cards"].append(dict(inv["cards"][0])), "repeats card wc_000000000001"),
        (_card_at(0, card_id="wc_0123456789ab"), "'wc_0123456789ab' is not in the verified release"),
        (_card_at(0, card_id=["wc_000000000001"]), "is not in the verified release"),
        (_card_at(0, extra=1), "must have exactly the keys"),
        (_card_at(0, card_kind="proper_name"), "kind 'proper_name' != release 'lexeme'"),
        (_card_at(0, listed="yes"), "boolean listed and a reason"),
        (_card_at(0, reason=""), "boolean listed and a reason"),
        (_card_at(0, page=""), "page must be a non-empty string or null"),
        (_card_at(0, page=7), "page must be a non-empty string or null"),
        (_card_at(0, page=None), "listed without a page and positive entry"),
        (_card_at(0, entry=None), "listed without a page and positive entry"),
        (_card_at(0, entry=0), "listed without a page and positive entry"),
        (_card_at(0, entry=True), "listed without a page and positive entry"),
        (_card_at(1, entry=1), "lists entry 1 of page 'кіт' twice"),
        (_card_at(2, entry=1), "unlisted but has entry 1"),
        # Every declared count is recomputed and must agree exactly.
        (_counts("source_cards", 2), "counts.source_cards declares 2, derived 3"),
        (_counts("citations", 3), "counts.citations declares 3, derived 4"),
        (_counts("page_keys", 1), "counts.page_keys declares 1, derived 2"),
        (_counts("learner_pages", 2), "counts.learner_pages declares 2, derived 1"),
        (_counts("visible_entries", 3), "counts.visible_entries declares 3, derived 2"),
        (_counts("proper_entries_listed", 1), "counts.proper_entries_listed declares 1, derived 0"),
        (_counts("proper_only_unlisted", 0), "counts.proper_only_unlisted declares 0, derived 1"),
        (_counts("refused_without_key", 1), "counts.refused_without_key declares 1, derived 0"),
        (_counts("emitted_routes", 11), "counts.emitted_routes declares 11, derived 10"),
        (_counts("emitted_routes", True), "counts.emitted_routes declares True"),
        (_counts("extra", 0), "counts must have exactly the keys"),
        (lambda inv: inv["counts"].pop("citations"), "counts must have exactly the keys"),
        (lambda inv: inv.update(counts=[]), "counts must have exactly the keys"),
        (_counts("routes_by_class", []), "must map classes to counts"),
        (_counts("routes_by_class", {"word-page": -1}), "must map classes to counts"),
        (
            lambda inv: inv["counts"]["routes_by_class"].update({"word-page": 2}),
            "routes_by_class['word-page'] declares 2, derived 1",
        ),
        (
            lambda inv: inv["counts"]["routes_by_class"].pop("compare-word-page"),
            "routes_by_class['compare-word-page'] declares None, derived 1",
        ),
        (
            lambda inv: inv["counts"]["routes_by_class"].update({"unused-class": 1}),
            "routes_by_class['unused-class'] declares 1, derived 0",
        ),
        (_route_at(9, **{"class": "card-diagnostic"}), "routes_by_class['card-diagnostic'] declares 3, derived 4"),
    ]


@pytest.mark.parametrize(("mutate", "message"), _inventory_mutations())
def test_verify_dist_refuses_an_inventory_inconsistent_with_the_release(tmp_path: Path, mutate, message: str) -> None:
    built = Built(tmp_path)
    inventory = built.inventory()
    mutate(inventory)
    built.write_inventory(inventory)
    with pytest.raises(preview.PreviewError, match=re.escape(message)):
        built.verify()


def test_verify_dist_refuses_a_missing_or_malformed_inventory(tmp_path: Path, capsys) -> None:
    built = Built(tmp_path)
    assert built.cli("--inventory", str(tmp_path / "absent.json")) == 1
    assert "route inventory unreadable" in capsys.readouterr().err
    for raw, message in (
        (b"{", "route inventory is not valid UTF-8 JSON"),
        (b"\xff", "route inventory is not valid UTF-8 JSON"),
        (b"[]", "exactly the keys"),
        (b'{"schema_version": 1, "schema_version": 2}', "route inventory has duplicate keys"),
    ):
        built.inventory_path.write_bytes(raw)
        with pytest.raises(preview.PreviewError, match=re.escape(message)):
            built.verify()


def _rebuilt_release(built: Built, tmp_path: Path, rows: list[dict], inventory_edit=None) -> None:
    dataset = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    manifest, dataset = _release(card_ids=tuple(r["card_id"] for r in rows), dataset=dataset)
    built.pin = _write_pin(tmp_path, _pin(manifest, dataset))
    (built.release / "manifest.json").write_bytes(manifest)
    (built.release / "word-cards.jsonl").write_bytes(dataset)
    inventory = _inventory(manifest, dataset)
    if inventory_edit:
        inventory_edit(inventory)
    built.write_inventory(inventory)


def test_verify_dist_refuses_release_rows_without_citation_lists_or_kinds(tmp_path: Path) -> None:
    built = Built(tmp_path)
    rows = [dict(row) for row in VERIFY_ROWS]
    del rows[1]["fields"]
    _rebuilt_release(built, tmp_path, rows)
    with pytest.raises(preview.PreviewError, match="release card wc_000000000002 has no fields list"):
        built.verify()
    # A release row without a kind cannot be matched by an inventory card that also has none.
    rows = [dict(row) for row in VERIFY_ROWS]
    del rows[0]["card_kind"]
    _rebuilt_release(built, tmp_path, rows, lambda inv: inv["cards"][0].update(card_kind=None))
    with pytest.raises(preview.PreviewError, match="card wc_000000000001 kind None != release None"):
        built.verify()


def test_verify_dist_rechecks_the_release_directory(tmp_path: Path, capsys) -> None:
    built = Built(tmp_path)
    data = (built.release / "word-cards.jsonl").read_bytes()
    (built.release / "word-cards.jsonl").write_bytes(b"x" * len(data))
    with pytest.raises(preview.PreviewError, match="no longer matches the pin"):
        built.verify()
    (built.release / "word-cards.jsonl").unlink()
    assert built.cli("--inventory", str(built.inventory_path)) == 1
    assert "::error title=Word-card preview refused::" in capsys.readouterr().err


def test_verify_dist_refuses_a_stale_inventory_or_a_pin_for_another_release(tmp_path: Path) -> None:
    built = Built(tmp_path)
    # A new release, pinned and prepared, with the previous release's inventory left in place.
    rows = [dict(row) for row in VERIFY_ROWS]
    rows[0]["fields"] = [{}, {}, {}]
    dataset = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    manifest, dataset = _release(card_ids=tuple(r["card_id"] for r in rows), dataset=dataset)
    stale_pin = built.pin
    built.pin = tmp_path / "new-pin.json"
    built.pin.write_text(json.dumps(_pin(manifest, dataset)), encoding="utf-8")
    (built.release / "manifest.json").write_bytes(manifest)
    (built.release / "word-cards.jsonl").write_bytes(dataset)
    with pytest.raises(preview.PreviewError, match=r"route inventory release .* does not match the pin"):
        built.verify()
    # The previous pin no longer describes the prepared release.
    built.pin = stale_pin
    with pytest.raises(preview.PreviewError, match="no longer matches the pin"):
        built.verify()


def test_fixture_sentinels_come_from_the_committed_synthetic_releases(tmp_path: Path) -> None:
    sentinels = preview.fixture_sentinels(FIXTURE_ROOT)
    assert {"wc_0123456789ab", "wc_0123456789ac", "v0.1.0-synthetic", "v0.1.1-synthetic"} <= sentinels
    assert "24c3b98a65f57294bec78795c179252950eb071ede008320ce03b06f6c5faf6d" in sentinels
    with pytest.raises(preview.PreviewError, match="no synthetic release fixtures"):
        preview.fixture_sentinels(tmp_path)


def test_sentinels_shared_with_the_real_release_are_not_false_positives(tmp_path: Path) -> None:
    built = Built(tmp_path)
    fixtures = tmp_path / "fixtures" / "pkg"
    fixtures.mkdir(parents=True)
    data = json.dumps([{"card_id": "wc_000000000001"}]).encode()
    (fixtures / "word-cards.json").write_bytes(data)
    (fixtures / "manifest.json").write_text(
        json.dumps({"release_version": "fixture-only-version", "dataset_file": "word-cards.json"}), encoding="utf-8"
    )
    card = built.dist / "lexicon-v2/release/wc_000000000001/index.html"
    card.write_text(_page(body="wc_000000000001"), encoding="utf-8")
    assert built.verify(tmp_path / "fixtures")["routes"] == 10
    (built.dist / "lexicon-v2/release/index.html").write_text(_page(body="fixture-only-version"), encoding="utf-8")
    with pytest.raises(preview.PreviewError, match="fixture-only-version"):
        built.verify(tmp_path / "fixtures")
