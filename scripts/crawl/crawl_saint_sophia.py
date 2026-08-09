#!/usr/bin/env python3
"""Create a failure-atomic, byte-preserving Saint Sophia API snapshot.

This crawler deliberately collects only the public text and metadata API.  It
does not discover or fetch any image, IIIF, annotation-media, RTI, mesh, or
geospatial endpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

API_ROOT = "https://saintsophia.dh.gu.se/api/"
PORTAL_ROOT = "https://saintsophia.dh.gu.se/"
COLLECTION_ID = "saint-sophia-inscriptions"
SCHEMA_VERSION = "historical-source-record.v1"
KNOWN_IDENTIFIED_TOTAL_LOWER_BOUND = 7000
DEFAULT_CE_MIN_YEAR = 0
DEFAULT_CE_MAX_YEAR = 2100

# These endpoints are intentionally an allow-list.  In particular, it excludes
# every endpoint that could expose media or a download URL.
ENDPOINTS = (
    "inscriptions/inscription/?depth=2",
    "inscriptions/language/",
    "inscriptions/writingsystem/",
    "inscriptions/tags/",
    "inscriptions/historicalperson/",
    "inscriptions/panel-metadata/",
    "inscriptions/inscription-contributors/",
    "inscriptions/genre-with-data/",
    "inscriptions/bibliography-item/",
    "inscriptions/inscriptiontype/",
    "inscriptions/extraalphabeticalsign/",
    "inscriptions/graffiticondition/",
    "inscriptions/graffitialignment/",
    "inscriptions/datingcriterium/",
    "inscriptions/author/",
    "inscriptions/medium/",
    "inscriptions/material/",
    "inscriptions/section/",
)
INSCRIPTION_ENDPOINT = ENDPOINTS[0]
NON_PAGINATED_ENDPOINTS = {"inscriptions/inscription-contributors/"}
MEDIA_URL_TERMS = ("image", "iiif", "korniienko-image", "annotation-media", "rti", "mesh", "geojson", "download")
FetchBytes = Callable[[str, float], bytes]


class CrawlError(RuntimeError):
    """Raised when an API response cannot support a complete snapshot."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_stable_json_bytes(value))


def _endpoint_directory(endpoint: str) -> str:
    return endpoint.split("?", 1)[0].strip("/").replace("/", "__")


def _with_page_size(url: str, page_size: int) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("page_size", str(page_size))
    return urlunparse(parsed._replace(query=urlencode(sorted(query.items()))))


def _http_get(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "learn-ukrainian-sophia-crawler/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except URLError as error:
        raise CrawlError(f"request failed for {url}: {error}") from error


def _fetch_with_retries(fetch_bytes: FetchBytes, url: str, timeout: float, retries: int) -> bytes:
    last_error: Exception | None = None
    for _attempt in range(retries + 1):
        try:
            return fetch_bytes(url, timeout)
        except (CrawlError, OSError, TimeoutError, URLError) as error:
            last_error = error
    raise CrawlError(f"request failed after {retries + 1} attempt(s): {url}") from last_error


def _validate_url(url: str, api_root: str) -> None:
    candidate = urlparse(url)
    allowed = urlparse(api_root)
    if candidate.scheme != allowed.scheme or candidate.netloc != allowed.netloc:
        raise CrawlError(f"unexpected pagination scheme or host: {url}")
    if any(term in candidate.path.casefold() for term in MEDIA_URL_TERMS):
        raise CrawlError(f"refusing media or download endpoint: {url}")


def _secure_pagination_url(url: str | None, api_root: str) -> tuple[str | None, bool]:
    """Repair only the portal's same-host HTTP pagination downgrade."""
    if url is None:
        return None, False
    candidate = urlparse(url)
    allowed = urlparse(api_root)
    if candidate.scheme == "http" and allowed.scheme == "https" and candidate.netloc == allowed.netloc:
        return urlunparse(candidate._replace(scheme="https")), True
    return url, False


def _decode_page(raw: bytes, url: str, *, allow_bare_list: bool = False) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CrawlError(f"invalid JSON response: {url}") from error
    if allow_bare_list and isinstance(payload, list):
        return {"count": len(payload), "next": None, "results": payload}
    if not isinstance(payload, dict) or not isinstance(payload.get("count"), int) or not isinstance(payload.get("results"), list):
        raise CrawlError(f"unexpected paginated response shape: {url}")
    if payload.get("next") is not None and not isinstance(payload["next"], str):
        raise CrawlError(f"unexpected pagination next value: {url}")
    return payload


def fetch_endpoint(
    endpoint: str,
    *,
    api_root: str,
    raw_directory: Path,
    timeout: float,
    retries: int,
    page_size: int,
    fetch_bytes: FetchBytes,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch one fully paginated endpoint, retaining every response byte-for-byte."""
    initial_url = _with_page_size(urljoin(api_root, endpoint), page_size)
    endpoint_path = urlparse(initial_url).path
    url: str | None = initial_url
    seen_urls: set[str] = set()
    rows: list[dict[str, Any]] = []
    page_manifest: list[dict[str, Any]] = []
    expected_count: int | None = None
    page_number = 1
    page_dir = raw_directory / "pages" / _endpoint_directory(endpoint)
    page_dir.mkdir(parents=True, exist_ok=True)

    while url is not None:
        _validate_url(url, api_root)
        if urlparse(url).path != endpoint_path:
            raise CrawlError(f"pagination escaped the allowed endpoint path: {url}")
        if url in seen_urls:
            raise CrawlError(f"pagination loop for {endpoint}: {url}")
        seen_urls.add(url)
        raw = _fetch_with_retries(fetch_bytes, url, timeout, retries)
        payload = _decode_page(
            raw,
            url,
            allow_bare_list=endpoint in NON_PAGINATED_ENDPOINTS,
        )
        if expected_count is None:
            expected_count = payload["count"]
        elif expected_count != payload["count"]:
            raise CrawlError(f"pagination count changed for {endpoint}")
        page_path = page_dir / f"page-{page_number:06d}.json"
        page_path.write_bytes(raw)
        next_url, upgraded = _secure_pagination_url(payload["next"], api_root)
        page_manifest.append(
            {
                "path": page_path.relative_to(raw_directory.parent).as_posix(),
                "sha256": _sha256(raw),
                "requested_url": url,
                "pagination_http_to_https_upgrade": upgraded,
            }
        )
        page_rows = payload["results"]
        if not all(isinstance(row, dict) for row in page_rows):
            raise CrawlError(f"unexpected result row shape: {url}")
        rows.extend(page_rows)
        url = next_url
        page_number += 1

    if expected_count is None or len(rows) != expected_count:
        raise CrawlError(f"incomplete pagination for {endpoint}: expected {expected_count}, received {len(rows)}")
    return rows, page_manifest


def _field(record: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in record:
            return record[name]
    return None


def _reference_id(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _field(value, "id", "pk", "url")
    return value


def _lookup_label(row: Mapping[str, Any]) -> Any:
    return _field(row, "label", "name", "title", "display_name", "text")


def _lookup_index(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any | None]:
    """Index labels only when the corresponding source identifier is unique."""
    index: dict[str, Any | None] = {}
    for row in rows:
        identifier = _field(row, "id", "pk", "url")
        if identifier is None:
            continue
        key = str(identifier)
        if key in index:
            index[key] = None
        else:
            index[key] = _lookup_label(row)
    return index


def _resolve_lookup(value: Any, index: Mapping[str, Any | None]) -> tuple[Any, Any, bool]:
    """Return label, unmodified source ID, and whether a supplied ID resolved."""
    if value is None:
        return None, None, True
    raw_id = _reference_id(value)
    if raw_id is None and isinstance(value, Mapping):
        direct_label = _lookup_label(value)
        if direct_label is not None:
            return direct_label, raw_id, True
    label = index.get(str(raw_id))
    return label, raw_id, label is not None


def _text_value(record: Mapping[str, Any], *names: str) -> Any:
    """Copy a text-layer field exactly; missing is distinct from an empty string."""
    return _field(record, *names)


def _epidoc_values(record: Mapping[str, Any]) -> tuple[Any, Any]:
    text = _text_value(record, "epidoc_text", "epidoc", "tei_xml")
    interpretation = _text_value(record, "epidoc_interpretation", "epidoc_interpretative")
    if isinstance(text, Mapping):
        nested = text
        text = _field(nested, "text", "xml", "tei")
        if interpretation is None:
            interpretation = _field(nested, "interpretation", "interpretative")
    return text, interpretation


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _validate_epidoc(value: Any) -> bool:
    if not _nonempty_string(value):
        return True
    try:
        ElementTree.fromstring(value)
    except ElementTree.ParseError:
        return False
    return True


def _as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_source_record(
    raw_record: Mapping[str, Any],
    *,
    language_index: Mapping[str, Any | None],
    writing_system_index: Mapping[str, Any | None],
    ce_min_year: int = DEFAULT_CE_MIN_YEAR,
    ce_max_year: int = DEFAULT_CE_MAX_YEAR,
) -> dict[str, Any]:
    """Produce one derived row without changing any portal-supplied value."""
    raw_id = _field(raw_record, "id", "pk", "source_record_id")
    language_value = _field(raw_record, "language", "source_language")
    writing_value = _field(raw_record, "writingsystem", "writing_system", "source_writing_system")
    language_label, language_id, language_ok = _resolve_lookup(language_value, language_index)
    writing_label, writing_id, writing_ok = _resolve_lookup(writing_value, writing_system_index)
    epidoc_text, epidoc_interpretation = _epidoc_values(raw_record)
    min_year = _text_value(raw_record, "min_year", "year_from", "date_from", "start_year")
    max_year = _text_value(raw_record, "max_year", "year_to", "date_to", "end_year")
    min_year_number = _as_int(min_year)
    max_year_number = _as_int(max_year)
    flags: list[str] = []
    if raw_id in (None, ""):
        flags.append("missing_source_record_id")
    if not language_ok:
        flags.append("source_language_lookup_failure")
    if not writing_ok:
        flags.append("source_writing_system_lookup_failure")
    if not _validate_epidoc(epidoc_text) or not _validate_epidoc(epidoc_interpretation):
        flags.append("epidoc_parse_failure")
    if min_year_number is not None and max_year_number is not None and min_year_number > max_year_number:
        flags.append("date_range_inversion")
    for year in (min_year_number, max_year_number):
        if year is not None and not ce_min_year <= year <= ce_max_year:
            flags.append("year_outside_configured_ce_bounds")
            break

    original_transcription = _text_value(raw_record, "transcription", "original_transcription")
    interpretative_edition = _text_value(raw_record, "interpretative_edition", "interpretativeedition")
    romanisation = _text_value(raw_record, "romanisation", "romanization")
    translation_ukr = _text_value(raw_record, "translation_ukr", "ukrainian_translation")
    translation_eng = _text_value(raw_record, "translation_eng", "english_translation")
    commentary_ukr = _text_value(
        raw_record,
        "commentary_ukr",
        "comments_ukr",
        "ukrainian_commentary",
    )
    commentary_eng = _text_value(
        raw_record,
        "commentary_eng",
        "comments_eng",
        "english_commentary",
    )
    text_layers = (
        original_transcription,
        epidoc_text,
        epidoc_interpretation,
        interpretative_edition,
        romanisation,
        translation_ukr,
        translation_eng,
        commentary_ukr,
        commentary_eng,
    )
    disposition = "quarantined_metadata" if flags else "text_bearing" if any(map(_nonempty_string, text_layers)) else "non_textual_or_no_text"
    raw_hash = _sha256(_stable_json_bytes(raw_record))
    record_id = "" if raw_id is None else str(raw_id)
    source_url = _text_value(raw_record, "url", "source_url")
    if source_url is None and record_id:
        source_url = urljoin(PORTAL_ROOT, f"inscriptions/inscription/{record_id}/")
    return {
        "schema_version": SCHEMA_VERSION,
        "collection_id": COLLECTION_ID,
        "source_record_id": record_id,
        "title": _text_value(raw_record, "title", "name"),
        "source_url": source_url,
        "published": _text_value(raw_record, "published", "is_published"),
        "original_transcription": original_transcription,
        "epidoc_text": epidoc_text,
        "epidoc_interpretation": epidoc_interpretation,
        "interpretative_edition": interpretative_edition,
        "romanisation": romanisation,
        "translation_ukr": translation_ukr,
        "translation_eng": translation_eng,
        "commentary_ukr": commentary_ukr,
        "commentary_eng": commentary_eng,
        "source_language_label": language_label,
        "source_writing_system_label": writing_label,
        "min_year": min_year,
        "max_year": max_year,
        "stage_label": None,
        "disposition": disposition,
        "quality_flags": sorted(flags),
        "metadata": {
            "source_language_id": language_id,
            "source_writing_system_id": writing_id,
            "source_record": raw_record,
        },
        "raw_record_sha256": raw_hash,
    }


def _numeric_record_id(record: Mapping[str, Any]) -> int:
    try:
        return int(str(record["source_record_id"]))
    except (KeyError, TypeError, ValueError) as error:
        raise CrawlError("missing or non-numeric source_record_id") from error


def _validate_inscription_ids(records: Iterable[Mapping[str, Any]], expected_count: int) -> list[dict[str, Any]]:
    ordered = sorted((dict(record) for record in records), key=_numeric_record_id)
    ids = [record["source_record_id"] for record in ordered]
    if len(ordered) != expected_count or len(set(ids)) != len(ids) or any(not record_id for record_id in ids):
        raise CrawlError("duplicate, missing, or count-mismatched inscription IDs")
    return ordered


def _read_previous(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    previous: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
                record_id = str(row["source_record_id"])
                raw_hash = row["raw_record_sha256"]
            except (TypeError, KeyError, json.JSONDecodeError) as error:
                raise CrawlError(f"invalid previous JSONL at line {line_number}") from error
            if not isinstance(raw_hash, str) or record_id in previous:
                raise CrawlError(f"invalid or duplicate previous ID at line {line_number}")
            previous[record_id] = raw_hash
    return previous


def _id_list_hash(ids: Iterable[str]) -> str:
    return _sha256(_stable_json_bytes(list(ids)))


def _newline_sorted_id_hash(ids: Iterable[str]) -> str:
    """Compatibility-friendly set hash: one sorted identifier per UTF-8 line."""
    return _sha256("".join(f"{record_id}\n" for record_id in sorted(ids, key=int)).encode("utf-8"))


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("wb") as handle:
        for row in rows:
            handle.write(_stable_json_bytes(row))


def _output_hashes(directory: Path, relative_paths: Iterable[str]) -> dict[str, str]:
    return {relative: _sha256((directory / relative).read_bytes()) for relative in sorted(relative_paths)}


def crawl_snapshot(
    output_dir: Path,
    *,
    api_root: str = API_ROOT,
    timeout: float = 30.0,
    retries: int = 2,
    page_size: int = 100,
    previous_jsonl: Path | None = None,
    fetch_bytes: FetchBytes | None = None,
) -> Path:
    """Fetch the complete currently-public API universe and publish it atomically."""
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise CrawlError(f"output directory already contains data: {output_dir}")
    if timeout <= 0 or retries < 0 or page_size <= 0:
        raise CrawlError("timeout must be positive; retries non-negative; page size positive")
    _validate_url(api_root, api_root)
    fetch = fetch_bytes or _http_get
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    try:
        raw_dir = stage / "raw"
        raw_dir.mkdir()
        api_root_bytes = _fetch_with_retries(fetch, api_root, timeout, retries)
        (raw_dir / "api-root.json").write_bytes(api_root_bytes)
        all_rows: dict[str, list[dict[str, Any]]] = {}
        page_manifest = [{"path": "raw/api-root.json", "sha256": _sha256(api_root_bytes)}]
        for endpoint in ENDPOINTS:
            rows, manifest = fetch_endpoint(
                endpoint,
                api_root=api_root,
                raw_directory=raw_dir,
                timeout=timeout,
                retries=retries,
                page_size=page_size,
                fetch_bytes=fetch,
            )
            all_rows[endpoint] = rows
            page_manifest.extend(manifest)

        language_index = _lookup_index(all_rows["inscriptions/language/"])
        writing_system_index = _lookup_index(all_rows["inscriptions/writingsystem/"])
        source_rows = [
            build_source_record(raw_row, language_index=language_index, writing_system_index=writing_system_index)
            for raw_row in all_rows[INSCRIPTION_ENDPOINT]
        ]
        source_rows = _validate_inscription_ids(source_rows, len(all_rows[INSCRIPTION_ENDPOINT]))
        dispositions = [
            {
                "source_record_id": row["source_record_id"],
                "disposition": row["disposition"],
                "quality_flags": row["quality_flags"],
                "raw_record_sha256": row["raw_record_sha256"],
            }
            for row in source_rows
        ]
        if {row["source_record_id"] for row in dispositions} != {row["source_record_id"] for row in source_rows}:
            raise CrawlError("disposition IDs do not match source-record IDs")
        _write_jsonl(stage / "historical_source_records.jsonl", source_rows)
        _write_jsonl(stage / "dispositions.jsonl", dispositions)
        _write_json(raw_dir / "hash-manifest.json", {item["path"]: item["sha256"] for item in page_manifest})

        previous = _read_previous(previous_jsonl)
        current = {str(row["source_record_id"]): str(row["raw_record_sha256"]) for row in source_rows}
        added = sorted(set(current) - set(previous), key=int)
        removed = sorted(set(previous) - set(current), key=int)
        changed = sorted((record_id for record_id in set(current) & set(previous) if current[record_id] != previous[record_id]), key=int)
        disposition_counts = {name: sum(row["disposition"] == name for row in source_rows) for name in sorted({row["disposition"] for row in source_rows})}
        epidoc_values = [row["epidoc_text"] for row in source_rows] + [row["epidoc_interpretation"] for row in source_rows]
        receipt = {
            "schema_version": "saint-sophia-coverage-receipt.v1",
            "retrieved_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "portal_root": PORTAL_ROOT,
            "api_root": api_root,
            "api_root_sha256": _sha256(api_root_bytes),
            "endpoint_counts": {endpoint: len(rows) for endpoint, rows in all_rows.items()},
            "response_pages": page_manifest,
            "pagination_http_to_https_upgrade_count": sum(
                bool(page.get("pagination_http_to_https_upgrade"))
                for page in page_manifest
            ),
            "public_inscription_count": len(source_rows),
            "sorted_source_record_id_set_sha256": _id_list_hash([row["source_record_id"] for row in source_rows]),
            "id_set_sha256": _newline_sorted_id_hash([row["source_record_id"] for row in source_rows]),
            "disposition_counts": disposition_counts,
            "epidoc_nonempty_count": sum(_nonempty_string(value) for value in epidoc_values),
            "epidoc_parse_failure_count": sum("epidoc_parse_failure" in row["quality_flags"] for row in source_rows),
            "ce_year_bounds": {"minimum": DEFAULT_CE_MIN_YEAR, "maximum": DEFAULT_CE_MAX_YEAR},
            "known_identified_total_lower_bound": KNOWN_IDENTIFIED_TOTAL_LOWER_BOUND,
            "known_unexposed_residual": True,
            "diff": {
                "added_source_record_ids": added,
                "changed_source_record_ids": changed,
                "removed_source_record_ids": removed,
                "added_count": len(added),
                "changed_count": len(changed),
                "removed_count": len(removed),
                "added_source_record_ids_sha256": _id_list_hash(added),
                "changed_source_record_ids_sha256": _id_list_hash(changed),
                "removed_source_record_ids_sha256": _id_list_hash(removed),
            },
        }
        _write_json(stage / "coverage-receipt.json", receipt)
        receipt["output_hashes"] = _output_hashes(
            stage,
            ("historical_source_records.jsonl", "dispositions.jsonl", "raw/hash-manifest.json"),
        )
        _write_json(stage / "coverage-receipt.json", receipt)
        if output_dir.exists():
            output_dir.rmdir()  # The earlier guard established that it is empty.
        os.replace(stage, output_dir)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output_dir


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--previous-jsonl", type=Path)
    parser.add_argument("--api-root", default=API_ROOT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=100)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        crawl_snapshot(
            args.output_dir,
            api_root=args.api_root,
            timeout=args.timeout,
            retries=args.retries,
            page_size=args.page_size,
            previous_jsonl=args.previous_jsonl,
        )
    except CrawlError as error:
        print(f"crawl failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
