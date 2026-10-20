#!/usr/bin/env python3
"""Prepare and verify the pinned word-card candidate preview for the Pages build (#11194).

``prepare`` downloads the two public ``word-cards`` release assets named by the
committed pin ``site/src/data/word-card-preview-release.pin.json``, refuses any
asset whose byte size or SHA-256 differs from that pin, checks the manifest
against the same pin, and only then writes the verified files plus the
``ATLAS_WORD_CARD_RELEASE_PIN`` value the Astro build consumes. The release tag
only locates the assets; the pinned sizes and digests decide what is used.

``verify-dist`` runs after ``npm run build`` and fails the deployment unless the
built site contains exactly the expected preview routes (two summaries, one card
and one comparison page per release row), every preview page is
``noindex, nofollow``, no emitted sitemap lists a preview URL, and no refusal or
fixture marker reached the output. Run with ``--help`` for usage.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common import github_client

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIN = ROOT / "site" / "src" / "data" / "word-card-preview-release.pin.json"
DEFAULT_FIXTURE_ROOT = ROOT / "site" / "tests" / "fixtures" / "word-card-preview"
CARD_SCHEMA = ROOT / "schemas" / "word-card-v1.schema.json"

PIN_SCHEMA_VERSION = "word-card-preview-release-pin.v1"
MANIFEST_SCHEMA_VERSION = "word-card-dataset.v1"
MANIFEST_ASSET = "manifest.json"
DATASET_ASSET = "word-cards.jsonl"
PUBLIC_PROVENANCE = "producer-declared"
# Vite inlines this test-only flag; a public build must not see it at all.
CONTROLS_FLAG = "PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS"
PREVIEW_PREFIX = "lexicon-v2"
ROBOTS = "noindex, nofollow"
# Rendered only when the route serves a refusal or a non-release sample.
REFUSAL_MARKERS = ("Configured release refused", "Real data unavailable", "synthetic-fixture")
REDIRECT_HOSTS = frozenset({"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"})
DOWNLOAD_ATTEMPTS = 3

_REPOSITORY = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PreviewError(RuntimeError):
    """Release input or built output that must not be published."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json(data: bytes, what: str) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise PreviewError(f"{what} has duplicate keys")
        return dict(pairs)

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreviewError(f"{what} is not valid UTF-8 JSON: {exc}") from exc


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def load_pin(path: Path) -> dict[str, Any]:
    """Read and validate the committed release pin."""
    try:
        pin = _strict_json(path.read_bytes(), "release pin")
    except OSError as exc:
        raise PreviewError(f"release pin unreadable: {path}: {exc}") from exc
    expected = {"schema_version", "repository", "release_tag", "release_version", "provenance", "assets"}
    if not isinstance(pin, dict) or set(pin) != expected:
        raise PreviewError(f"release pin must have exactly the keys {sorted(expected)}")
    if pin["schema_version"] != PIN_SCHEMA_VERSION:
        raise PreviewError(f"unsupported release pin schema {pin['schema_version']!r}")
    if not isinstance(pin["repository"], str) or not _REPOSITORY.fullmatch(pin["repository"]):
        raise PreviewError("release pin repository must be owner/name")
    if not isinstance(pin["release_tag"], str) or not _TAG.fullmatch(pin["release_tag"]):
        raise PreviewError("release pin tag is not a plain tag name")
    if not isinstance(pin["release_version"], str) or not pin["release_version"].strip():
        raise PreviewError("release pin release_version must be a non-empty string")
    if pin["provenance"] != PUBLIC_PROVENANCE:
        raise PreviewError(f"public preview requires {PUBLIC_PROVENANCE!r} provenance, got {pin['provenance']!r}")
    assets = pin["assets"]
    if not isinstance(assets, dict) or set(assets) != {MANIFEST_ASSET, DATASET_ASSET}:
        raise PreviewError(f"release pin assets must be exactly {MANIFEST_ASSET} and {DATASET_ASSET}")
    for name, asset in assets.items():
        if not isinstance(asset, dict) or set(asset) != {"bytes", "sha256"}:
            raise PreviewError(f"release pin asset {name} must have exactly bytes and sha256")
        if not _is_count(asset["bytes"]):
            raise PreviewError(f"release pin asset {name} bytes must be a positive integer")
        if not isinstance(asset["sha256"], str) or not _SHA256.fullmatch(asset["sha256"]):
            raise PreviewError(f"release pin asset {name} sha256 must be 64 lowercase hex digits")
    return pin


def asset_url(pin: Mapping[str, Any], name: str) -> str:
    return f"https://github.com/{pin['repository']}/releases/download/{pin['release_tag']}/{name}"


class _HttpsGitHubRedirects(urllib.request.HTTPRedirectHandler):
    """Follow only HTTPS redirects to GitHub's release download hosts."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urllib.parse.urlsplit(newurl)
        if parts.scheme != "https" or (parts.hostname or "") not in REDIRECT_HOSTS:
            raise urllib.error.HTTPError(newurl, code, "refused release asset redirect", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_HttpsGitHubRedirects)


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "learn-ukrainian-word-card-preview/1.0",
        },
    )
    with github_client.http_open(request, timeout=60, opener=_OPENER.open) as response:
        return response.read()


def download_asset(pin: Mapping[str, Any], name: str, fetch: Callable[[str], bytes] | None = None) -> bytes:
    """Download one pinned asset; refuse any size or digest that differs from the pin."""
    fetch = fetch or _fetch
    expected = pin["assets"][name]
    url = asset_url(pin, name)
    last_error: BaseException | None = None
    for _ in range(DOWNLOAD_ATTEMPTS):
        try:
            data = fetch(url)
            break
        except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
            last_error = exc
    else:
        raise PreviewError(f"could not download {name} after {DOWNLOAD_ATTEMPTS} attempts: {last_error}")
    if len(data) != expected["bytes"]:
        raise PreviewError(f"{name} size mismatch: pinned {expected['bytes']} bytes, got {len(data)}")
    digest = _sha256(data)
    if digest != expected["sha256"]:
        raise PreviewError(f"{name} sha256 mismatch: pinned {expected['sha256']}, got {digest}")
    return data


def _card_id_pattern() -> re.Pattern[str]:
    schema = json.loads(CARD_SCHEMA.read_text(encoding="utf-8"))
    return re.compile(schema["$defs"]["card_id"]["pattern"])


def check_release(pin: Mapping[str, Any], manifest_bytes: bytes, dataset_bytes: bytes) -> list[str]:
    """Check the verified manifest against the pin and return the dataset card ids in order."""
    manifest = _strict_json(manifest_bytes, MANIFEST_ASSET)
    if not isinstance(manifest, dict):
        raise PreviewError("manifest must be a JSON object")
    dataset = pin["assets"][DATASET_ASSET]
    expected = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release_version": pin["release_version"],
        "dataset_file": DATASET_ASSET,
        "dataset_sha256": dataset["sha256"],
        "dataset_bytes": dataset["bytes"],
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise PreviewError(f"manifest {key} is {manifest.get(key)!r}, pin requires {value!r}")
    if "withdrawal_notice_sha256" in manifest:
        raise PreviewError("manifest declares a withdrawal notice the pin does not cover")
    if manifest.get("certified_count") != 0:
        raise PreviewError("candidate preview pin expects certified_count 0")
    try:
        lines = [line for line in dataset_bytes.decode("utf-8").split("\n") if line.strip()]
    except UnicodeDecodeError as exc:
        raise PreviewError(f"{DATASET_ASSET} is not UTF-8: {exc}") from exc
    pattern = _card_id_pattern()
    card_ids: list[str] = []
    for number, line in enumerate(lines, start=1):
        row = _strict_json(line.encode("utf-8"), f"{DATASET_ASSET} line {number}")
        card_id = row.get("card_id") if isinstance(row, dict) else None
        if not isinstance(card_id, str) or not pattern.fullmatch(card_id):
            raise PreviewError(f"{DATASET_ASSET} line {number} has no valid card_id")
        card_ids.append(card_id)
    if len(set(card_ids)) != len(card_ids):
        raise PreviewError(f"{DATASET_ASSET} repeats a card_id")
    if not card_ids or manifest.get("card_count") != len(card_ids):
        raise PreviewError(f"manifest card_count {manifest.get('card_count')!r} != {len(card_ids)} dataset rows")
    return card_ids


def site_pin(pin: Mapping[str, Any]) -> str:
    """The exact ``ATLAS_WORD_CARD_RELEASE_PIN`` JSON the site's strict pin schema accepts."""
    return json.dumps(
        {
            "release_version": pin["release_version"],
            "dataset_sha256": pin["assets"][DATASET_ASSET]["sha256"],
            "manifest_sha256": pin["assets"][MANIFEST_ASSET]["sha256"],
            "provenance": pin["provenance"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def refuse_controls_flag(environ: Mapping[str, str]) -> None:
    if CONTROLS_FLAG in environ:
        raise PreviewError(f"{CONTROLS_FLAG} must be absent from the public build environment")


def prepare(
    pin_path: Path,
    dest: Path,
    *,
    environ: Mapping[str, str],
    fetch: Callable[[str], bytes] | None = None,
) -> dict[str, str]:
    """Download, verify and write the pinned release; return the build outputs."""
    refuse_controls_flag(environ)
    pin = load_pin(pin_path)
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise PreviewError(f"destination must be absent or an empty directory: {dest}")
    manifest_bytes = download_asset(pin, MANIFEST_ASSET, fetch)
    dataset_bytes = download_asset(pin, DATASET_ASSET, fetch)
    card_ids = check_release(pin, manifest_bytes, dataset_bytes)
    dest.mkdir(parents=True, exist_ok=True)
    for name, data in ((MANIFEST_ASSET, manifest_bytes), (DATASET_ASSET, dataset_bytes)):
        with (dest / name).open("xb") as handle:
            handle.write(data)
    return {"release-path": str(dest.resolve()), "pin": site_pin(pin), "card-count": str(len(card_ids))}


class _RobotsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.robots: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta" and (values.get("name") or "").lower() == "robots":
            self.robots.append(values.get("content"))


def robots_values(html: str) -> list[str | None]:
    parser = _RobotsParser()
    parser.feed(html)
    return parser.robots


def fixture_sentinels(fixture_root: Path) -> set[str]:
    """Identifiers of the committed synthetic release fixtures that must never be published."""
    sentinels: set[str] = set()
    for manifest_path in sorted(fixture_root.glob("*/manifest.json")):
        manifest_bytes = manifest_path.read_bytes()
        manifest = _strict_json(manifest_bytes, str(manifest_path))
        dataset_bytes = (manifest_path.parent / manifest["dataset_file"]).read_bytes()
        rows = (
            _strict_json(dataset_bytes, manifest["dataset_file"])
            if manifest["dataset_file"].endswith(".json")
            else [json.loads(line) for line in dataset_bytes.decode("utf-8").split("\n") if line.strip()]
        )
        sentinels.update({manifest["release_version"], _sha256(manifest_bytes), _sha256(dataset_bytes)})
        sentinels.update(row["card_id"] for row in rows)
    if not sentinels:
        raise PreviewError(f"no synthetic release fixtures found under {fixture_root}")
    return sentinels


def verify_dist(dist: Path, release_dir: Path, pin_path: Path, fixture_root: Path) -> dict[str, int]:
    """Fail unless ``dist`` holds exactly the pinned preview, noindexed and outside every sitemap."""
    pin = load_pin(pin_path)
    verified: dict[str, bytes] = {}
    for name, asset in pin["assets"].items():
        data = (release_dir / name).read_bytes()
        if len(data) != asset["bytes"] or _sha256(data) != asset["sha256"]:
            raise PreviewError(f"{release_dir / name} no longer matches the pin")
        verified[name] = data
    manifest_bytes, dataset_bytes = verified[MANIFEST_ASSET], verified[DATASET_ASSET]
    card_ids = check_release(pin, manifest_bytes, dataset_bytes)
    expected = {f"{PREVIEW_PREFIX}/release/index.html", f"{PREVIEW_PREFIX}/compare/release/index.html"}
    expected.update(
        f"{PREVIEW_PREFIX}/{prefix}release/{card_id}/index.html" for card_id in card_ids for prefix in ("", "compare/")
    )
    preview_root = dist / PREVIEW_PREFIX
    actual = (
        {path.relative_to(dist).as_posix() for path in preview_root.rglob("index.html")}
        if preview_root.is_dir()
        else set()
    )
    if actual != expected:
        missing, extra = sorted(expected - actual), sorted(actual - expected)
        raise PreviewError(
            f"preview routes differ: {len(missing)} missing {missing[:5]}, {len(extra)} unexpected {extra[:5]}"
        )

    sentinels = {s for s in fixture_sentinels(fixture_root) if s.encode() not in dataset_bytes + manifest_bytes}
    for relative in sorted(expected):
        html = (dist / relative).read_text(encoding="utf-8")
        robots = robots_values(html)
        if robots != [ROBOTS]:
            raise PreviewError(f"{relative}: robots meta is {robots}, expected [{ROBOTS!r}]")
        for marker in (*REFUSAL_MARKERS, *sentinels):
            if marker in html:
                raise PreviewError(f"{relative}: contains refusal or fixture marker {marker!r}")
    scripts = sorted(dist.rglob("*.js"))
    for script in scripts:
        text = script.read_text(encoding="utf-8", errors="replace")
        for marker in sentinels:
            if marker in text:
                raise PreviewError(f"{script.relative_to(dist)}: contains fixture marker {marker!r}")

    sitemaps = sorted(dist.glob("sitemap*.xml"))
    if not sitemaps:
        raise PreviewError("no sitemap emitted; preview exclusion cannot be proven")
    for sitemap in sitemaps:
        if f"/{PREVIEW_PREFIX}/" in sitemap.read_text(encoding="utf-8"):
            raise PreviewError(f"{sitemap.name} lists a preview URL")
    return {"routes": len(actual), "cards": len(card_ids), "sitemaps": len(sitemaps), "scripts_scanned": len(scripts)}


def _write_outputs(path: Path, outputs: Mapping[str, str]) -> None:
    for key, value in outputs.items():
        if "\n" in value or "\r" in value:
            raise PreviewError(f"output {key} contains a line break")
    with path.open("a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")


_EPILOG = """\
Examples:
  .venv/bin/python scripts/deploy/prepare_word_card_preview.py prepare \\
      --dest "$RUNNER_TEMP/word-card-preview-release" --github-output "$GITHUB_OUTPUT"
  .venv/bin/python scripts/deploy/prepare_word_card_preview.py verify-dist site/dist \\
      --release-dir "$RUNNER_TEMP/word-card-preview-release"

Outputs:
  prepare      writes manifest.json and word-cards.jsonl into --dest and appends
               release-path=, pin= and card-count= lines to --github-output.
  verify-dist  reads only; prints route, sitemap and script counts.

Exit codes:
  0  release verified / built preview verified
  1  refused: pin, download, size, digest, manifest, controls flag, routes,
     robots, sitemap or fixture marker check failed (reason on stderr)

Related: .github/workflows/deploy-pages.yml, docs/atlas/word-cards/public-preview.md,
  site/src/data/word-card-preview-release.pin.json, issue #11194.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and verify the pinned word-card candidate preview for the Pages build.\n"
            "Use in the deploy-pages workflow around `npm run build`; not for controlled "
            "fixture builds, which keep using the site's Playwright helpers."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    pin_help = "committed release pin JSON (default: site/src/data/word-card-preview-release.pin.json)"
    prep = commands.add_parser("prepare", help="download and verify the pinned release assets")
    prep.add_argument("--pin", type=Path, default=DEFAULT_PIN, help=pin_help)
    prep.add_argument(
        "--dest",
        type=Path,
        required=True,
        help="absent or empty directory for the verified assets, e.g. $RUNNER_TEMP/x",
    )
    prep.add_argument(
        "--github-output", type=Path, help="file to append release-path/pin/card-count lines to, e.g. $GITHUB_OUTPUT"
    )
    verify = commands.add_parser("verify-dist", help="check the built site's preview routes before upload")
    verify.add_argument("dist", type=Path, help="built site directory, e.g. site/dist")
    verify.add_argument("--release-dir", type=Path, required=True, help="directory written by `prepare --dest`")
    verify.add_argument("--pin", type=Path, default=DEFAULT_PIN, help=pin_help)
    verify.add_argument(
        "--fixture-root",
        type=Path,
        default=DEFAULT_FIXTURE_ROOT,
        help="synthetic release fixtures whose identifiers must not be published "
        "(default: site/tests/fixtures/word-card-preview)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            outputs = prepare(args.pin, args.dest, environ=os.environ)
            if args.github_output:
                _write_outputs(args.github_output, outputs)
            print(f"word-card preview: verified {outputs['card-count']} cards from the pinned release")
        else:
            counts = verify_dist(args.dist, args.release_dir, args.pin, args.fixture_root)
            print(
                f"word-card preview: {counts['routes']} noindex routes for {counts['cards']} cards; "
                f"{counts['sitemaps']} sitemaps exclude them; {counts['scripts_scanned']} scripts fixture-free"
            )
    except (PreviewError, OSError, KeyError, ValueError) as exc:
        print(f"::error title=Word-card preview refused::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
