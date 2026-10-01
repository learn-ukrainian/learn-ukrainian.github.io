"""Index curated metadata and existing external article/transcript text (#9409)."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
import yaml

CATALOGUES = (
    "podcasts/podcast_db.json",
    "podcasts/raw_lists/seasons_1_3.txt",
    "podcasts/raw_lists/seasons_4_5.txt",
    "podcasts/raw_lists/season_6_fmu.txt",
    "podcasts/ulp_mapping.yaml",
    "external_resources.yaml",
    "ulp-resources.yaml",
    "ulp-alphabet.yaml",
    "ulp-articles-index.yaml",
    "ulp-article-mappings.yaml",
    "trusted_sources.yaml",
    "dobraforma/dobraforma_db.json",
    "talkukrainian/talkukrainian_db.json",
    "verba/verba_db.json",
)
KINDS = ("podcast", "video", "article", "reference")
MAX_HITS = 20
MAX_HIT_BYTES = 24576
PROVENANCE_BUDGETS = {
    "source_files": 512,
    "source_entries": 2048,
    "discovery_evidence": 1024,
    "letter_evidence": 4096,
    "access_evidence": 2048,
}


class ResourceCatalogueMissingError(RuntimeError):
    """The incremental resource catalogue has not been ingested."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS resource_catalogue (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    season INTEGER,
    episode INTEGER,
    access TEXT NOT NULL,
    audio_access TEXT,
    notes_access TEXT,
    levels TEXT NOT NULL,
    modules TEXT NOT NULL,
    topics TEXT NOT NULL,
    letters TEXT NOT NULL DEFAULT '[]',
    letter_evidence TEXT NOT NULL DEFAULT '[]',
    access_evidence TEXT NOT NULL DEFAULT '[]',
    source_files TEXT NOT NULL,
    source_entries TEXT NOT NULL,
    discovery_evidence TEXT NOT NULL,
    search_text TEXT NOT NULL,
    http_status INTEGER,
    checked_at TEXT,
    link_check TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS resource_catalogue_fts USING fts5(
    title, search_text, content='resource_catalogue', content_rowid='id',
    tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS resource_catalogue_ai AFTER INSERT ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(rowid,title,search_text) VALUES(new.id,new.title,new.search_text);
END;
CREATE TRIGGER IF NOT EXISTS resource_catalogue_ad AFTER DELETE ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(resource_catalogue_fts,rowid,title,search_text)
    VALUES('delete',old.id,old.title,old.search_text);
END;
CREATE TRIGGER IF NOT EXISTS resource_catalogue_au AFTER UPDATE ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(resource_catalogue_fts,rowid,title,search_text)
    VALUES('delete',old.id,old.title,old.search_text);
    INSERT INTO resource_catalogue_fts(rowid,title,search_text) VALUES(new.id,new.title,new.search_text);
END;
"""


def normalise_url(url: str) -> str:
    """Canonicalize tracking, YouTube short links and known ULP episode aliases."""
    parts = urlsplit(url.strip())
    if parts.scheme == "sources":
        return url
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Resource URL must be an HTTP(S) URL without credentials")
    host = parts.netloc.lower()
    path = parts.path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_") and k not in {"fbclid", "gclid"}]
    if parts.hostname.lower() in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        video = path.lstrip("/") if parts.hostname.lower() == "youtu.be" else dict(query).get("v")
        if path.startswith(("/shorts/", "/embed/")):
            video = path.rsplit("/", 1)[-1]
        if video:
            return f"https://www.youtube.com/watch?v={video}"
    if parts.hostname.lower() in {"ukrainianlessons.com", "www.ukrainianlessons.com"}:
        host = "www.ukrainianlessons.com"
        match = re.fullmatch(r"/(?:lesson/?|lesson-|episode)(\d+)", path)
        if match:
            path = f"/episode{int(match[1])}"
        path += "/"
    return urlunsplit(
        (
            "https" if parts.scheme == "http" and host == "www.ukrainianlessons.com" else parts.scheme,
            host,
            path or "/",
            urlencode(sorted(query)),
            "",
        )
    )


def _walk_entries(node: Any, locator: str = "", context: dict | None = None):
    """Walk metadata containers completely, retaining exact source-entry locators."""
    context = dict(context or {})
    if isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_entries(item, f"{locator}/{i}", context)
    elif isinstance(node, dict):
        if "module_id" in node:
            context["module"] = node["module_id"]
        if "level" in node:
            context["level"] = node["level"]
        if any(k in node for k in ("url", "youtube_url", "path")) and any(k in node for k in ("title", "name")):
            yield node, locator, context
            return
        # trusted_sources includes three internal lookup collections with no URL.
        if node.get("type") == "rag" and "collection" in node:
            yield {**node, "url": f"sources://collection/{node['id']}"}, locator, context
            return
        for key, value in node.items():
            if not isinstance(value, (list, dict)):
                continue
            child = dict(context)
            if key in {"articles", "websites", "youtube", "videos", "recommended_episodes"}:
                child["kind"] = {"youtube": "video", "videos": "video", "recommended_episodes": "podcast"}.get(
                    key, "article"
                )
            if locator == "/resources" or (
                not locator and key not in {"resources", "sources", "mappings"} and isinstance(value, dict)
            ):
                child["module"] = key
            if re.fullmatch(r"[abc][12]", key):
                child["level"] = key.upper()
                child.pop("module", None)
            elif (
                context.get("level")
                and not locator.startswith("/mappings")
                and isinstance(value, list)
                and key not in {"articles", "videos"}
            ):
                child["module"] = f"{context['level'].lower()}-{key}"
            if "base_url" in node:
                child["base_url"] = node["base_url"]
            yield from _walk_entries(value, f"{locator}/{key}", child)


def load_catalogues(root: Path) -> list[dict]:
    """Parse every declared catalogue; absent or malformed files fail the run."""
    entries = []
    for relative in CATALOGUES:
        path = root / relative
        source_file = f"docs/resources/{relative}"
        if path.suffix == ".txt":
            parsed = []
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                match = re.fullmatch(r"(Season|Episode): (\d+), Title: (.+), URL: (https?://\S+)\s*", line)
                if not match:
                    raise ValueError(f"Malformed catalogue entry: {source_file}:{number}")
                parsed.append(
                    (
                        {
                            ("season" if match[1] == "Season" else "episode_number"): int(match[2]),
                            "title": match[3],
                            "url": match[4],
                        },
                        f"line:{number}",
                        {"kind": "podcast"},
                    )
                )
        else:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
            parsed = list(_walk_entries(data, context={"kind": "podcast"} if relative.startswith("podcasts/") else {}))
            if not parsed:
                raise ValueError(f"Empty resource catalogue: {source_file}")
        for item, locator, context in parsed:
            entries.append(_resource_entry(item, source_file, locator, context))
    return entries


def _resource_entry(item: dict, source_file: str, locator: str, context: dict) -> dict:
    original = item.get("url") or item.get("youtube_url") or urljoin(context.get("base_url", ""), item["path"])
    url = normalise_url(original)
    ulp = re.fullmatch(r"https://www\.ukrainianlessons\.com/episode(\d+)/", url)
    fmu = re.fullmatch(r"https://www\.ukrainianlessons\.com/fmu(\d+)/", url)
    title = item.get("title") or item["name"]
    episode = item.get("episode_number")
    season = item.get("season")
    identity = re.search(r"(?:ULP|FMU) (\d+)-(\d+)", title)
    if identity:
        season = season or int(identity[1])
        episode = episode or int(identity[2])
    if ulp or fmu:
        episode = int((ulp or fmu)[1])
        season = season or (1 if fmu else (episode - 1) // 40 + 1)
    kind = "podcast" if ulp or fmu else item.get("type", context.get("kind", "article"))
    if source_file.endswith("trusted_sources.yaml"):
        kind = "reference"
    if kind not in KINDS:
        kind = context.get("kind", "article")
    module = context.get("module")
    # Bare article mapping slugs in this A1 mapping file become fully qualified.
    if module and source_file.endswith("ulp-article-mappings.yaml"):
        module = f"a1-{module}"
    level = item.get("suggested_level") or context.get("level")
    if not level and module:
        match = re.match(r"([abc][12])-", module, re.I)
        level = match[1].upper() if match else None
    topics = [*item.get("tags", []), *item.get("topics", [])]
    topics.extend(
        str(item[k]) for k in ("category", "summary", "match_reason", "description", "coverage") if item.get(k)
    )
    podcast = kind == "podcast" and urlsplit(url).hostname == "www.ukrainianlessons.com"
    access = item.get("access") or "unknown"
    if item.get("paid") is True or item.get("free") is False:
        access = "paid"
    elif item.get("free") is True:
        access = "free"
    if podcast:
        access = "mixed"  # Free audio does not make premium notes free.
    letters = item.get("letters", [])
    letter_evidence = item.get("letter_evidence", [])
    access_evidence = item.get("access_evidence", [])
    if access == "free" and not access_evidence:
        raise ValueError("Free catalogue access requires explicit evidence")
    if not isinstance(letters, list) or any(
        not isinstance(letter, str) or len(letter) != 1 or not letter.isalpha() for letter in letters
    ):
        raise ValueError("Catalogue letters must be single alphabetic characters")
    if letters and (
        not letter_evidence
        or any(not any(letter in evidence.get("letters", []) for evidence in letter_evidence) for letter in letters)
    ):
        raise ValueError("Catalogue letters require explicit pairing evidence")
    for evidence in [*letter_evidence, *access_evidence]:
        if not evidence.get("locator") or not re.fullmatch(r"[0-9a-f]{64}", evidence.get("source_sha256", "")):
            raise ValueError("Catalogue evidence requires a source hash and locator")
        if not (evidence.get("source_url") or evidence.get("source_file")):
            raise ValueError("Catalogue evidence requires a source URL or file")
    return {
        "url": url,
        "kind": kind,
        "title": title,
        "channel": item.get("channel") or item.get("source") or urlsplit(url).hostname or "internal collection",
        "season": season,
        "episode": episode,
        "access": access,
        "audio_access": "free" if podcast else None,
        "notes_access": "premium" if podcast else None,
        "levels": [str(level).upper()] if level else [],
        "modules": [module] if module else [],
        "topics": topics,
        "letters": sorted({letter.upper() for letter in letters}),
        "letter_evidence": letter_evidence,
        "access_evidence": access_evidence,
        "source_file": source_file,
        "source_entry": {
            "source_file": source_file,
            "locator": locator,
            "original_url": original,
            "title": title,
            "module": module,
            "level": level,
            "related_urls": [item[k] for k in ("youtube_url", "ulp_page") if item.get(k)],
        },
    }


def deduplicate(entries: list[dict]) -> list[dict]:
    """Merge URL identities without losing aliases, mappings or provenance."""
    groups: dict[str, dict] = {}
    for entry in entries:
        url = entry["url"]
        if url not in groups:
            groups[url] = {
                **entry,
                "source_entries": [],
                "source_files": [],
                "titles": [],
                "levels": [],
                "modules": [],
                "topics": [],
                "letters": [],
                "letter_evidence": [],
                "access_evidence": [],
                "access_values": set(),
                "discovery_evidence": [],
            }
        row = groups[url]
        for key in ("levels", "modules", "topics", "letters"):
            row[key] = sorted(set(row[key]) | set(entry[key]))
        for key in ("letter_evidence", "access_evidence"):
            for evidence in entry[key]:
                if evidence not in row[key]:
                    row[key].append(evidence)
        row["source_entries"].append(entry["source_entry"])
        row["source_files"] = sorted(set(row["source_files"]) | {entry["source_file"]})
        row["titles"].append(entry["title"])
        if entry["kind"] == "podcast":
            for key in ("kind", "season", "episode", "audio_access", "notes_access"):
                row[key] = entry[key]
        if entry["access"] != "unknown":
            row["access_values"].add(entry["access"])
        # Unknown aliases do not override evidenced access.
        if row["access"] == "unknown":
            row["access"] = entry["access"]
        elif entry["access"] != "unknown" and row["access"] != entry["access"]:
            row["access"] = "mixed"
            # A metadata conflict is not the evidenced free-audio/premium-notes split.
            row["audio_access"] = None
            row["notes_access"] = None
    for row in groups.values():
        access_values = row.pop("access_values")
        if len(access_values) > 1:
            row.update(access="mixed", audio_access=None, notes_access=None)
        row["search_text"] = " ".join(
            [
                *row["titles"],
                *row["topics"],
                *row["modules"],
                row["channel"],
                row["url"],
            ]
        )
    return [groups[url] for url in sorted(groups)]


def _episode_identity(url: str, title: str) -> tuple[str, int] | None:
    """Keep ULP and FMU episode numbers distinct; accept only publisher/video URLs."""
    parts = urlsplit(url)
    if parts.hostname not in {"www.ukrainianlessons.com", "www.youtube.com"}:
        return None
    if parts.hostname == "www.ukrainianlessons.com":
        match = re.fullmatch(r"/(episode|fmu)(\d+)/", parts.path)
        if match:
            return ("ULP" if match[1] == "episode" else "FMU", int(match[2]))
    match = re.search(r"\b(ULP|FMU)\s+\d+-(\d+)\b", title)
    return (match[1], int(match[2])) if match else None


def link_existing_text(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """Join existing external texts by URL or series/episode, retaining chunk witnesses."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='external_articles'").fetchone():
        return 0
    by_url: dict[str, list[dict]] = {}
    by_episode: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        urls = {row["url"]}
        for entry in row["source_entries"]:
            for url in [entry["original_url"], *entry["related_urls"]]:
                urls.add(normalise_url(url))
        for url in urls:
            by_url.setdefault(url, []).append(row)
        identity = _episode_identity(row["url"], row["title"])
        if identity:
            by_episode.setdefault(identity, []).append(row)
    linked = set()
    for chunk_id, url, title, text, source_file in conn.execute(
        "SELECT chunk_id,url,title,text,source_file FROM external_articles WHERE text != '' ORDER BY id"
    ):
        try:
            url = normalise_url(url)
        except ValueError:
            continue
        targets = {r["url"]: r for r in by_url.get(url, [])}
        identity = _episode_identity(url, title)
        if identity:
            targets.update({r["url"]: r for r in by_episode.get(identity, [])})
        for row in targets.values():
            row["search_text"] += " " + text
            row["discovery_evidence"].append(
                {
                    "chunk_id": chunk_id,
                    "source_file": source_file,
                    "source_url": url,
                    "relation": "url" if row in by_url.get(url, []) else "episode_identity",
                }
            )
            linked.add(row["url"])
    return len(linked)


def check_link(url: str, timeout: float = 10) -> dict:
    """Check HTTP headers only; errors are unknown, never a live-link assertion."""
    if url.startswith("sources:"):
        return {"http_status": None, "checked_at": None, "link_check": "not_applicable"}
    checked_at = datetime.now(UTC).isoformat()
    try:
        with requests.head(url, timeout=timeout, allow_redirects=True) as response:
            status = response.status_code
        if status in {405, 501}:
            with requests.get(url, timeout=timeout, stream=True) as response:
                status = response.status_code
        return {
            "http_status": status,
            "checked_at": checked_at,
            "link_check": "live" if 200 <= status < 400 else "http_error",
        }
    except requests.RequestException:
        return {"http_status": None, "checked_at": checked_at, "link_check": "network_error"}


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Install the table, external-content FTS and all mutation triggers."""
    # executescript commits implicitly; execute each complete statement instead.
    statement = ""
    for line in SCHEMA.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            conn.execute(statement)
            statement = ""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(resource_catalogue)")}
    for column in ("letters", "letter_evidence", "access_evidence"):
        if column not in columns:
            conn.execute(f"ALTER TABLE resource_catalogue ADD COLUMN {column} TEXT NOT NULL DEFAULT '[]'")


def ingest(
    conn: sqlite3.Connection, root: Path, *, no_network: bool = False, workers: int = 8, timeout: float = 10
) -> dict:
    """Validate all inputs before atomically replacing only this catalogue."""
    entries = load_catalogues(root)
    rows = deduplicate(entries)
    linked_resources = link_existing_text(conn, rows)
    if no_network:
        checks = [{"http_status": None, "checked_at": None, "link_check": "not_checked"} for _ in rows]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            checks = list(pool.map(lambda row: check_link(row["url"], timeout), rows))
    json_fields = {"levels", "modules", "topics", "letters", *PROVENANCE_BUDGETS}
    fields = (
        "url",
        "kind",
        "title",
        "channel",
        "season",
        "episode",
        "access",
        "audio_access",
        "notes_access",
        "levels",
        "modules",
        "topics",
        "letters",
        "letter_evidence",
        "access_evidence",
        "source_files",
        "source_entries",
        "discovery_evidence",
        "search_text",
        "http_status",
        "checked_at",
        "link_check",
    )
    with conn:
        ensure_schema(conn)
        previous = {
            url: (status, date, check)
            for url, status, date, check in conn.execute(
                "SELECT url,http_status,checked_at,link_check FROM resource_catalogue"
            )
        }
        conn.execute("DELETE FROM resource_catalogue")
        for row, check in zip(rows, checks, strict=True):
            if no_network and row["url"] in previous:
                check = dict(zip(("http_status", "checked_at", "link_check"), previous[row["url"]], strict=True))
            row.update(check)
            values = [json.dumps(row[k], ensure_ascii=False) if k in json_fields else row[k] for k in fields]
            conn.execute(
                f"INSERT INTO resource_catalogue({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", values
            )
        conn.execute("INSERT INTO resource_catalogue_fts(resource_catalogue_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO resource_catalogue_fts(resource_catalogue_fts,rank) VALUES('integrity-check',1)")
        report = reconcile(conn, entries)
    report["link_checks"] = dict(Counter(row["link_check"] for row in rows))
    report["linked_resources"] = linked_resources
    return report


def reconcile(conn: sqlite3.Connection, entries: list[dict]) -> dict:
    """Compare each input locator and URL with stored provenance, not just totals."""
    expected = Counter((e["source_file"], e["source_entry"]["locator"], e["url"]) for e in entries)
    actual = Counter()
    per_file_urls: dict[str, set] = {}
    for url, encoded in conn.execute("SELECT url,source_entries FROM resource_catalogue"):
        for entry in json.loads(encoded):
            actual[(entry["source_file"], entry["locator"], url)] += 1
            per_file_urls.setdefault(entry["source_file"], set()).add(url)
    if expected != actual:
        raise ValueError("Catalogue source-entry reconciliation mismatch")
    counts = Counter(e["source_file"] for e in entries)
    return {
        "entries_in": len(entries),
        "rows_out": conn.execute("SELECT count(*) FROM resource_catalogue").fetchone()[0],
        "per_file": {
            f: {"entries_in": count, "rows_out": len(per_file_urls[f])} for f, count in sorted(counts.items())
        },
    }


def _bounded_list(items: list, budget: int) -> list:
    """Return a complete-record prefix within a UTF-8 JSON byte budget."""
    result = []
    size = 2  # JSON brackets
    for item in items:
        item_size = len(json.dumps(item, ensure_ascii=False).encode("utf-8")) + (2 if result else 0)
        if size + item_size > budget:
            break
        result.append(item)
        size += item_size
    return result


def _compact_hit(row: sqlite3.Row) -> dict:
    """Bound every field, including provenance; leave the stored catalogue intact."""
    hit = dict(row)
    hit.pop("search_text")
    for field in ("levels", "modules", "topics", "letters", *PROVENANCE_BUDGETS):
        items = json.loads(hit[field])
        hit[field] = _bounded_list(items, PROVENANCE_BUDGETS.get(field, 512))
        hit[f"{field}_count"] = len(items)
        if len(hit[field]) < len(items):
            hit[f"{field}_truncated"] = True
    for field, value in list(hit.items()):
        if isinstance(value, str) and len(value.encode("utf-8")) > 256:
            hit[field] = value.encode("utf-8")[:256].decode("utf-8", errors="ignore")
            hit[f"{field}_truncated"] = True
    return hit


def search_resources(
    conn: sqlite3.Connection,
    query: str = "",
    *,
    mode: str = "text",
    kind: str | None = None,
    level: str | None = None,
    module: str | None = None,
    free_only: bool = False,
    live_only: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Search literal FTS by default; explicit letter mode uses only the evidenced index."""
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='resource_catalogue'").fetchone():
        raise ResourceCatalogueMissingError("Resource catalogue ingestion is required")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(resource_catalogue)")}
    if not {"letters", "letter_evidence", "access_evidence"} <= columns:
        raise ResourceCatalogueMissingError("Letter index ingestion is required")
    if kind is not None and kind not in KINDS:
        raise ValueError("Unknown resource kind")
    if mode not in {"text", "letter"}:
        raise ValueError("Unknown resource search mode")
    tokens = re.findall(r"[^\W_]+", query, re.UNICODE)
    clauses, parameters = [], []
    join = ""
    order = "r.title,r.url"
    letter = tokens[0].upper() if len(tokens) == 1 else ""
    if mode == "letter":
        if len(letter) != 1 or not letter.isalpha():
            return []
        clauses.append("EXISTS (SELECT 1 FROM json_each(r.letters) WHERE value=?)")
        parameters.append(letter)
        # Dedicated lessons precede resources covering multiple letters.
        order = "json_array_length(r.letters),r.url"
    elif tokens:
        join = "JOIN resource_catalogue_fts ON resource_catalogue_fts.rowid=r.id"
        clauses.append("resource_catalogue_fts MATCH ?")
        parameters.append(" AND ".join(f'"{token}"' for token in tokens))
        order = "resource_catalogue_fts.rank,r.url"
    elif query.strip():
        return []
    if kind:
        clauses.append("r.kind=?")
        parameters.append(kind)
    for column, value in (("levels", level.upper() if level else None), ("modules", module)):
        if value:
            clauses.append(f"EXISTS (SELECT 1 FROM json_each(r.{column}) WHERE value=?)")
            parameters.append(value)
    if free_only:
        clauses.append("(r.access='free' OR (r.access='mixed' AND r.audio_access='free' AND r.notes_access='premium'))")
    if live_only:
        clauses.append("r.link_check='live'")
    parameters.append(max(1, min(int(limit), MAX_HITS)))
    where = " AND ".join(clauses) or "1"
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT r.* FROM resource_catalogue r {join} WHERE {where} ORDER BY {order} LIMIT ?", parameters
    )
    return [_compact_hit(result) for result in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index every curated catalogue into sources.db with provenance and FTS.\n"
        "Use for discovery with existing external text; never downloads media or premium content.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  <shared-project-python> -m scripts.ingest.resource_catalogue_ingest --ingest --db data/sources-copy.db
  <shared-project-python> -m scripts.ingest.resource_catalogue_ingest --ingest --db data/sources-copy.db --no-network
Outputs: resource_catalogue and resource_catalogue_fts in the explicit local DB; JSON count reconciliation on stdout.
Exit codes: 0 reconciled; 1 input, storage, or database failure; 2 invalid arguments.
Related: docs/corpus-inventory.md; docs/DICTIONARY-PIPELINE-STATUS.md; #9409.
""",
    )
    parser.add_argument(
        "--ingest", action="store_true", required=True, help="Enable catalogue ingestion (required; default false)."
    )
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Explicit existing local SQLite database, e.g. data/sources-copy.db; no default.",
    )
    parser.add_argument(
        "--catalogue-root",
        type=Path,
        default=Path("docs/resources"),
        help="Catalogue directory (default docs/resources).",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Skip HTTP checks, preserving prior checks (default false); for tests/offline rehearsals.",
    )
    parser.add_argument("--workers", type=int, default=8, help="Concurrent HTTP header checks (default 8, range 1–16).")
    parser.add_argument(
        "--timeout", type=float, default=10, help="HTTP connect/read timeout in seconds (default 10; must be positive)."
    )
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 16 or args.timeout <= 0:
        parser.error("workers must be 1–16 and timeout must be positive")
    from scripts.storage.topology import is_network_filesystem_path

    if is_network_filesystem_path(args.db) or is_network_filesystem_path(args.db.resolve()):
        parser.error("SQLite database must be local")
    if not args.db.is_file():
        parser.error("database must already exist; use a local snapshot of sources.db")
    try:
        with sqlite3.connect(f"{args.db.resolve().as_uri()}?mode=rw", uri=True) as conn:
            report = ingest(
                conn, args.catalogue_root, no_network=args.no_network, workers=args.workers, timeout=args.timeout
            )
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (OSError, ValueError, sqlite3.Error, yaml.YAMLError) as exc:
        print(f"Catalogue ingest failed: {type(exc).__name__}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
