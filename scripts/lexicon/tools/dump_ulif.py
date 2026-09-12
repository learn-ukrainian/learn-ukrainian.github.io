#!/usr/bin/env python3
"""Standalone, resilient crawler/dumper for ULIF (УМІФ НАН України) DictUA.

Features:
- Self-contained: requires only python3, requests, and beautifulsoup4.
- Crash-resilient SQLite storage with automatic resume (Ctrl+C and restart anytime).
- Extracts official stress, declension/conjugation paradigms, synonyms,
  phraseology/idioms with citations, and antonyms.
- Polite rate-limiting (default 1.0s) with exponential backoff on HTTP 429/5xx.
- Live progress indicator with ETA, success rate, and error handling.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(
        "Missing required dependencies.\n"
        "Please install them via:\n"
        "  pip install requests beautifulsoup4\n"
        "or run with repository environment:\n"
        "  .venv/bin/python scripts/lexicon/tools/dump_ulif.py ...",
        file=sys.stderr,
    )
    sys.exit(1)

ULIF_URL = "https://lcorp.ulif.org.ua/dictua/"
DEFAULT_DELAY_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_USER_AGENT = (
    "learn-ukrainian-atlas/1.0 "
    "(noncommercial educational ULIF lexicon intake; https://github.com/learn-ukrainian)"
)

_REGISTER_RE = re.compile(
    r"\b(розм\.|діал\.|книжн\.|заст\.|вульг\.|ірон\.|жарт\.|фам\.|поет\.|рідко|перен\.|"
    r"фольк\.|пестл\.|зневажл\.|уроч\.|офіц\.|спец\.|церк\.|мат\.|мед\.|біол\.|бот\.|"
    r"зоол\.|грам\.|лінгв\.|юр\.|військ\.|мор\.|тех\.|спорт\.)",
    re.IGNORECASE,
)


class DictUACrawler:
    """Polite, robust HTTP client and parser for DictUA."""

    def __init__(
        self,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.last_request_at = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _wait_turn(self) -> None:
        elapsed = time.monotonic() - self.last_request_at
        if self.last_request_at and elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    def _request(self, method: str, data: dict[str, str] | None = None) -> requests.Response:
        backoff = 30.0
        max_backoff = 300.0
        while True:
            self._wait_turn()
            try:
                resp = self.session.request(
                    method,
                    ULIF_URL,
                    data=data,
                    timeout=self.timeout_seconds,
                )
                self.last_request_at = time.monotonic()

                if resp.status_code in {429, 500, 502, 503, 504}:
                    retry_after = resp.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else backoff
                    print(
                        f"\n[HTTP {resp.status_code}] Backing off for {sleep_time:.1f}s...",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(sleep_time)
                    backoff = min(backoff * 2, max_backoff)
                    continue

                return resp
            except requests.RequestException as exc:
                print(
                    f"\n[Network Error: {exc}] Retrying in {backoff:.1f}s...",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    @staticmethod
    def _extract_tokens(html: str) -> dict[str, str] | None:
        soup = BeautifulSoup(html, "html.parser")
        tokens: dict[str, str] = {}
        for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
            node = soup.find("input", attrs={"name": name})
            if node is not None and node.get("value") is not None:
                tokens[name] = str(node.get("value"))
        return tokens if tokens.get("__VIEWSTATE") and tokens.get("__EVENTVALIDATION") else None

    @staticmethod
    def _extract_headword(html: str, fallback: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find(id="ContentPlaceHolder1_article")
        if article is not None:
            text = " ".join(article.get_text(" ", strip=True).split())
            for sep in (" – ", " — ", " - "):
                if sep in text:
                    cand = text.split(sep, 1)[0].strip()
                    if cand:
                        return cand
        input_ctrl = soup.find("input", attrs={"name": "ctl00$ContentPlaceHolder1$tsearch"})
        if input_ctrl and input_ctrl.get("value"):
            return str(input_ctrl.get("value")).strip()
        return fallback

    @staticmethod
    def _has_control(html: str, control_name: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("input", attrs={"name": control_name}) is not None

    @staticmethod
    def _search_matches(html: str, query: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        result_list = soup.find(id="ContentPlaceHolder1_dgv")
        if result_list is None:
            return False
        norm_query = query.replace("\u0301", "").casefold()
        candidates = {
            " ".join(link.get_text(" ", strip=True).split()).replace("\u0301", "").casefold()
            for link in result_list.find_all("a")
        }
        return norm_query in candidates

    @staticmethod
    def _parse_paradigm(html: str) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id="ContentPlaceHolder1_dgv")
        if table is None:
            return None
        headers: list[str] = []
        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            th_cells = tr.find_all("th")
            if th_cells and not headers:
                headers = [" ".join(c.get_text(" ", strip=True).split()) for c in th_cells]
            td_cells = tr.find_all("td")
            if td_cells:
                rows.append([" ".join(c.get_text(" ", strip=True).split()) for c in td_cells])
        return {"headers": headers, "rows": rows} if rows else None

    @staticmethod
    def _parse_relation_tab(html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="ContentPlaceHolder1_article") or soup.find(
            id="ContentPlaceHolder1_dgv"
        )
        if container is None:
            return []

        results: list[dict[str, Any]] = []
        # Check for table format
        tables = container.find_all("table") if container.name != "table" else [container]
        for tbl in tables:
            for tr in tbl.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                if not cells:
                    continue
                cell_text = " ".join(cells[0].get_text(" ", strip=True).split())
                if not cell_text:
                    continue
                bolds = [
                    " ".join(b.get_text(" ", strip=True).split())
                    for b in cells[0].find_all(["b", "strong"])
                ]
                italics = [
                    " ".join(i.get_text(" ", strip=True).split())
                    for i in cells[0].find_all(["i", "em"])
                ]
                labels = [
                    m.group(0) for m in _REGISTER_RE.finditer(" ".join(italics))
                ]
                citations = re.findall(r"\(([^()]*)\)", cell_text)
                results.append({
                    "text": cell_text,
                    "terms": bolds,
                    "register_labels": sorted(set(labels)),
                    "citations": citations,
                })

        # Check for paragraph format if table gave nothing
        if not results:
            for p in container.find_all("p"):
                p_text = " ".join(p.get_text(" ", strip=True).split())
                if not p_text:
                    continue
                bolds = [
                    " ".join(b.get_text(" ", strip=True).split())
                    for b in p.find_all(["b", "strong"])
                ]
                italics = [
                    " ".join(i.get_text(" ", strip=True).split())
                    for i in p.find_all(["i", "em"])
                ]
                labels = [
                    m.group(0) for m in _REGISTER_RE.finditer(" ".join(italics))
                ]
                citations = re.findall(r"\(([^()]*)\)", p_text)
                results.append({
                    "text": p_text,
                    "terms": bolds,
                    "register_labels": sorted(set(labels)),
                    "citations": citations,
                })

        return results

    def fetch_word(self, word: str) -> dict[str, Any]:
        """Fetch all data (paradigm, syn, phras, ant) for a single word."""
        clean_query = re.sub(r"\(.*?\)", "", word).strip() or word.strip()
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()

        # Step 1: Initial GET for WebForms tokens
        initial = self._request("GET")
        tokens = self._extract_tokens(initial.text)
        if not tokens:
            return {
                "lemma": word,
                "canonical_headword": word,
                "status": "parse_error",
                "retrieved_at": timestamp,
                "raw_responses": {"initial": initial.text},
            }

        # Step 2: Search POST
        search_data = {
            **tokens,
            "ctl00$ContentPlaceHolder1$tsearch": clean_query,
            "ctl00$ContentPlaceHolder1$search.x": "10",
            "ctl00$ContentPlaceHolder1$search.y": "10",
        }
        search = self._request("POST", data=search_data)
        raw_responses = {"initial": initial.text, "paradigm": search.text}

        if search.status_code == 404 or not self._search_matches(search.text, clean_query):
            return {
                "lemma": word,
                "canonical_headword": word,
                "status": "not_found",
                "retrieved_at": timestamp,
                "raw_responses": raw_responses,
            }

        headword = self._extract_headword(search.text, word)
        paradigm = self._parse_paradigm(search.text)

        tab_tokens = self._extract_tokens(search.text)
        sections: dict[str, Any] = {"paradigm": paradigm}

        # Step 3: Fetch relation tabs
        if tab_tokens:
            tab_controls = [
                ("synonyms", "ctl00$ContentPlaceHolder1$syn"),
                ("phraseology", "ctl00$ContentPlaceHolder1$phras"),
                ("antonyms", "ctl00$ContentPlaceHolder1$ant"),
            ]
            for kind, ctrl in tab_controls:
                if not self._has_control(search.text, ctrl):
                    continue
                tab_data = {
                    **tab_tokens,
                    "ctl00$ContentPlaceHolder1$tsearch": headword,
                    f"{ctrl}.x": "10",
                    f"{ctrl}.y": "10",
                }
                tab_resp = self._request("POST", data=tab_data)
                raw_responses[kind] = tab_resp.text
                sections[kind] = self._parse_relation_tab(tab_resp.text)

                next_tokens = self._extract_tokens(tab_resp.text)
                if next_tokens:
                    tab_tokens = next_tokens

        return {
            "lemma": word,
            "canonical_headword": headword,
            "status": "ok",
            "retrieved_at": timestamp,
            "paradigm": sections.get("paradigm"),
            "synonyms": sections.get("synonyms", []),
            "phraseology": sections.get("phraseology", []),
            "antonyms": sections.get("antonyms", []),
            "raw_responses": raw_responses,
        }


class DumpDB:
    """Manages SQLite storage and resume state."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ulif_entries (
                    lemma TEXT PRIMARY KEY,
                    canonical_headword TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'error', 'parse_error')),
                    retrieved_at TEXT NOT NULL DEFAULT '',
                    paradigm_json TEXT,
                    synonyms_json TEXT,
                    phraseology_json TEXT,
                    antonyms_json TEXT,
                    raw_html_json TEXT
                );
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ulif_entries_status
                ON ulif_entries(status);
            """)

    def get_completed_lemmas(self) -> set[str]:
        cursor = self.conn.execute(
            "SELECT lemma FROM ulif_entries WHERE status IN ('ok', 'not_found');"
        )
        return {row[0] for row in cursor.fetchall()}

    def store_entry(self, entry: dict[str, Any], include_html: bool = False) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO ulif_entries (
                    lemma, canonical_headword, status, retrieved_at,
                    paradigm_json, synonyms_json, phraseology_json, antonyms_json, raw_html_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lemma) DO UPDATE SET
                    canonical_headword=excluded.canonical_headword,
                    status=excluded.status,
                    retrieved_at=excluded.retrieved_at,
                    paradigm_json=excluded.paradigm_json,
                    synonyms_json=excluded.synonyms_json,
                    phraseology_json=excluded.phraseology_json,
                    antonyms_json=excluded.antonyms_json,
                    raw_html_json=excluded.raw_html_json;
                """,
                (
                    entry["lemma"],
                    entry.get("canonical_headword", ""),
                    entry.get("status", "error"),
                    entry.get("retrieved_at", ""),
                    json.dumps(entry.get("paradigm"), ensure_ascii=False)
                    if entry.get("paradigm")
                    else None,
                    json.dumps(entry.get("synonyms"), ensure_ascii=False)
                    if entry.get("synonyms")
                    else None,
                    json.dumps(entry.get("phraseology"), ensure_ascii=False)
                    if entry.get("phraseology")
                    else None,
                    json.dumps(entry.get("antonyms"), ensure_ascii=False)
                    if entry.get("antonyms")
                    else None,
                    json.dumps(entry.get("raw_responses"), ensure_ascii=False)
                    if include_html and entry.get("raw_responses")
                    else None,
                ),
            )

    def close(self) -> None:
        self.conn.close()


def load_atlas_manifest_lemmas(manifest_path: Path) -> list[str]:
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    lemmas: list[str] = []
    for entry in data.get("entries", []):
        lemma = entry.get("lemma") if isinstance(entry, dict) else entry
        if lemma and isinstance(lemma, str):
            lemmas.append(lemma.strip())
    # Preserves order while removing duplicates
    seen = set()
    deduped = []
    for l in lemmas:
        if l not in seen:
            seen.add(l)
            deduped.append(l)
    return deduped


def load_vesum_lemmas(vesum_db_path: Path) -> list[str]:
    conn = sqlite3.connect(str(vesum_db_path))
    cursor = conn.execute(
        "SELECT DISTINCT lemma FROM vesum_entries WHERE lemma != '' ORDER BY lemma;"
    )
    lemmas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return lemmas


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m {sec:02d}s"


def run(args: argparse.Namespace) -> int:
    # 1. Determine lemmas to fetch
    lemmas: list[str] = []
    if args.word:
        lemmas = [args.word.strip()]
    elif args.wordlist:
        path = Path(args.wordlist)
        lemmas = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    elif args.from_vesum:
        path = Path(args.from_vesum)
        print(f"Loading lemmas from VESUM DB: {path}...")
        lemmas = load_vesum_lemmas(path)
    else:
        manifest_path = Path(args.manifest)
        print(f"Loading Atlas cohort from manifest: {manifest_path}...")
        lemmas = load_atlas_manifest_lemmas(manifest_path)

    total_words = len(lemmas)
    print(f"Target word count: {total_words:,}")

    # 2. Open DB and check completed
    db = DumpDB(Path(args.db))
    completed = db.get_completed_lemmas()
    pending = [w for w in lemmas if w not in completed]
    print(f"Already completed: {len(completed):,} | Pending: {len(pending):,}")

    if not pending:
        print("All target words are already fetched! Done.")
        return 0

    if args.limit:
        pending = pending[: args.limit]
        print(f"Limiting to first {len(pending):,} words for this run.")

    # 3. Initialize crawler
    crawler = DictUACrawler(
        delay_seconds=args.delay,
        timeout_seconds=args.timeout,
    )

    # 4. Crawl loop
    print(f"\nStarting crawler with {args.delay:.1f}s delay. Press Ctrl+C to pause anytime.\n")
    start_time = time.monotonic()
    success_count = 0
    not_found_count = 0
    error_count = 0

    try:
        for idx, word in enumerate(pending, 1):
            try:
                res = crawler.fetch_word(word)
                status = res.get("status")
                if status == "ok":
                    success_count += 1
                elif status == "not_found":
                    not_found_count += 1
                else:
                    error_count += 1

                db.store_entry(res, include_html=args.save_html)
                headword = res.get("canonical_headword", word)
            except Exception as e:
                error_count += 1
                headword = word
                db.store_entry({"lemma": word, "status": "error", "retrieved_at": datetime.datetime.now(datetime.UTC).isoformat()})
                print(f"\n[Error on {word}]: {e}", file=sys.stderr)

            elapsed = time.monotonic() - start_time
            rate = elapsed / idx
            remaining_seconds = rate * (len(pending) - idx)
            pct = ((len(completed) + idx) / total_words) * 100

            progress_str = (
                f"\r[{len(completed) + idx:,}/{total_words:,}] ({pct:4.1f}%) | "
                f"ok: {success_count:,} | miss: {not_found_count:,} | err: {error_count} | "
                f"speed: {rate:.2f}s/w | ETA: {format_duration(remaining_seconds)} | "
                f"current: {headword[:25]:<25}"
            )
            sys.stdout.write(progress_str)
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\n[Paused by user]. All completed words have been safely saved to DB.")
        print("To resume, simply run the same command again.")
        return 130
    finally:
        db.close()

    total_elapsed = time.monotonic() - start_time
    print(f"\n\nRun finished in {format_duration(total_elapsed)}.")
    print(f"Successfully processed: {success_count:,} ok, {not_found_count:,} not found, {error_count} errors.")
    print(f"Database: {args.db}")
    return 0


def import_to_sources(dump_db_path: Path, sources_db_path: Path) -> int:
    try:
        from scripts.wiki.sources_db import store_ulif_dictua_entry
    except ImportError:
        print("Cannot import scripts.wiki.sources_db. Run within repo using .venv/bin/python.", file=sys.stderr)
        return 1

    dump_conn = sqlite3.connect(str(dump_db_path))
    cursor = dump_conn.execute(
        "SELECT lemma, canonical_headword, status, retrieved_at, paradigm_json, synonyms_json, phraseology_json, antonyms_json FROM ulif_entries;"
    )
    rows = cursor.fetchall()
    print(f"Importing {len(rows):,} entries from {dump_db_path} to {sources_db_path}...")
    imported = 0
    now_ts = datetime.datetime.now(datetime.UTC).isoformat()
    for lemma, canonical_headword, status, retrieved_at, paradigm_json, synonyms_json, phraseology_json, antonyms_json in rows:
        sections: dict[str, Any] = {}
        if paradigm_json:
            sections["paradigm"] = json.loads(paradigm_json)
        if synonyms_json:
            sections["synonyms"] = json.loads(synonyms_json)
        if phraseology_json:
            sections["phraseology"] = json.loads(phraseology_json)
        if antonyms_json:
            sections["antonyms"] = json.loads(antonyms_json)

        store_ulif_dictua_entry(
            word=lemma,
            canonical_headword=canonical_headword or lemma,
            sections=sections,
            raw_responses={},
            retrieved_at=retrieved_at or now_ts,
            parser_version="ulif-dictua-v2",
            status=status if status in {"ok", "not_found", "parse_error"} else "parse_error",
            db_path=sources_db_path,
        )
        imported += 1
        if imported % 1000 == 0 or imported == len(rows):
            print(f"Imported {imported:,}/{len(rows):,} entries...", flush=True)
    dump_conn.close()
    print(f"Done! {imported:,} entries imported into {sources_db_path}.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/ulif_dump.db",
        help="Path to output SQLite database (default: data/ulif_dump.db)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="site/src/data/lexicon-manifest.json",
        help="Path to lexicon-manifest.json (default: site/src/data/lexicon-manifest.json)",
    )
    parser.add_argument(
        "--wordlist",
        type=str,
        help="Path to text file with words (one per line)",
    )
    parser.add_argument(
        "--from-vesum",
        type=str,
        help="Path to vesum.db to dump all VESUM lemmas",
    )
    parser.add_argument(
        "--word",
        type=str,
        help="Single word to test",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Politeness delay between requests in seconds (default: {DEFAULT_DELAY_SECONDS})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of pending words to fetch in this session",
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Also store raw HTML responses in database (increases DB size)",
    )
    parser.add_argument(
        "--import-to-sources",
        type=str,
        metavar="SOURCES_DB_PATH",
        help="Import an existing ulif_dump.db directly into sources.db",
    )
    args = parser.parse_args(argv)
    if args.import_to_sources:
        return import_to_sources(Path(args.db), Path(args.import_to_sources))
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
