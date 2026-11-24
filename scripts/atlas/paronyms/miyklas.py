"""Fetch and normalize public MiyKlas Ukrainian paronym pages with full provenance.

Each fetched page records canonical URL, HTTP status, UTC fetch timestamp,
SHA-256 of raw HTML bytes, SHA-256 of extracted UTF-8 text, and structured
plain text suitable for the shared paronym extractor.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from .extractor import SourceDocument

USER_AGENT = "learn-ukrainian-corpus-bot/1.0 (+https://github.com/learn-ukrainian/learn-ukrainian.github.io)"
SCHEMA_VERSION = "miyklas-paronyms-raw.v1"

# Publicly indexed MiyKlas Ukrainian language paronym theory and dictionary pages.
DEFAULT_MIYKLAS_PAGES: tuple[dict[str, str], ...] = (
    {
        "page_id": "miyklas-5-klas-slovnyk-paronimiv",
        "grade": "5",
        "kind": "dictionary",
        "title": "Короткий словник паронімів (5 клас НУШ)",
        "url": (
            "https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/"
            "leksikologiia-40143/paronimi-slovnik-paronimiv-40159/"
            "re-ff38c509-447b-4058-b9e5-8acc04e6c038"
        ),
    },
    {
        "page_id": "miyklas-5-klas-paronimy",
        "grade": "5",
        "kind": "theory",
        "title": "Пароніми (5 клас НУШ)",
        "url": (
            "https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/"
            "leksikologiia-40143/paronimi-slovnik-paronimiv-40159/"
            "re-2b8ff92a-2d6f-474d-952f-5f6290e2bbe9"
        ),
    },
    {
        "page_id": "miyklas-6-klas-paronimy",
        "grade": "6",
        "kind": "theory",
        "title": "Пароніми (6 клас НУШ)",
        "url": (
            "https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/"
            "leksika-40149/paronimi-448803/"
            "re-8f6c25c7-b816-4a41-9f08-fed96b9fa79b"
        ),
    },
    {
        "page_id": "miyklas-10-klas-paronimy",
        "grade": "10",
        "kind": "theory",
        "title": "Про пароніми та їхню роль у мовленні (10 клас)",
        "url": (
            "https://www.miyklas.com.ua/p/ukrainska-mova/10-klas/"
            "poniattia-normi-v-suchasnii-ukrayinskii-literaturnii-movi-326692/"
            "paronimi-zapobigannia-pomilok-u-vzhivanni-paronimiv-327792/"
            "re-a41e4695-f4ff-4642-af7f-e901c2e73a91"
        ),
    },
    {
        "page_id": "miyklas-11-klas-paronimy",
        "grade": "11",
        "kind": "theory",
        "title": "Пароніми (11 клас)",
        "url": (
            "https://www.miyklas.com.ua/p/ukrainska-mova/11-klas/"
            "stilistichna-norma-392237/"
            "stilistichne-vikoristannia-sinonimiv-antonimiv-i-paronimiv-393241/"
            "re-3f5815a8-529f-44ae-8aa6-372a9b5ecc9d"
        ),
    },
)

_DASH_RE = re.compile(r"\s+[–—−]\s+|\s+[–—−](?=\S)|(?<=\S)[–—−]\s+")
_SINGLE_LETTER_RE = re.compile(r"^[А-ЩЬЮЯЄІЇҐ]$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class MiyKlasFetchError(RuntimeError):
    """Raised when a MiyKlas page cannot be fetched or parsed."""


def _validate_miyklas_url(url: str) -> None:
    """Enforce HTTPS origin allowlist on miyklas.com.ua before any request or redirect."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "miyklas.com.ua" or host.endswith(".miyklas.com.ua")):
        raise MiyKlasFetchError(f"Refusing non-MiyKlas HTTPS URL: {url!r}")


class _MiyKlasRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Validate every HTTP redirect target against the MiyKlas HTTPS policy before following."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        target = urllib.parse.urljoin(req.full_url, newurl)
        _validate_miyklas_url(target)
        return super().redirect_request(req, fp, code, msg, headers, target)


@dataclass(frozen=True)
class MiyKlasPageRecord:
    page_id: str
    grade: str
    kind: str
    title: str
    url: str
    final_url: str
    http_status: int
    fetched_at_utc: str
    raw_html_sha256: str
    raw_html_bytes: int
    text_sha256: str
    text: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "page_id": self.page_id,
            "grade": self.grade,
            "kind": self.kind,
            "title": self.title,
            "url": self.url,
            "final_url": self.final_url,
            "http_status": self.http_status,
            "fetched_at_utc": self.fetched_at_utc,
            "raw_html_sha256": self.raw_html_sha256,
            "raw_html_bytes": self.raw_html_bytes,
            "text_sha256": self.text_sha256,
            "text": self.text,
        }


def _clean_inline(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def _extract_dictionary_text(taskhtml: Tag) -> str:
    """Render MiyKlas dictionary DOM preserving blank-line paronym group boundaries."""
    lines: list[str] = ["Короткий словник паронімів", ""]
    pending_entry: str | None = None

    def flush_pending() -> None:
        nonlocal pending_entry
        if pending_entry is not None:
            lines.append(pending_entry)
            pending_entry = None

    def walk(node: Tag) -> None:
        nonlocal pending_entry
        classes = set(node.get("class") or [])
        if "gxst-reference" in classes:
            flush_pending()
            ref_text = _clean_inline(node.get_text(" ", strip=True))
            if ref_text:
                lines.append("")
                lines.append(ref_text)
            return
        if "gxst-title" in classes:
            flush_pending()
            letter = _clean_inline(node.get_text(" ", strip=True))
            if letter:
                lines.append("")
                lines.append(letter)
                lines.append("")
            return

        # Container div with nested divs: walk children in DOM order while still
        # preserving any direct text/span/br siblings (e.g. letter "Р" div).
        child_divs = [c for c in node.children if isinstance(c, Tag) and c.name == "div"]
        if child_divs:
            buf: list[str] = []

            def flush_buf() -> None:
                nonlocal pending_entry
                raw_chunk = "".join(buf)
                buf.clear()
                for part in raw_chunk.splitlines():
                    cleaned = _clean_inline(part)
                    if not cleaned:
                        continue
                    if _DASH_RE.search(cleaned):
                        flush_pending()
                        pending_entry = cleaned
                    elif pending_entry is not None:
                        pending_entry = f"{pending_entry} {cleaned}"
                    else:
                        lines.append(cleaned)

            for child in node.children:
                if isinstance(child, Tag) and child.name == "div":
                    flush_buf()
                    walk(child)
                elif isinstance(child, Tag) and child.name == "br":
                    buf.append("\n")
                elif isinstance(child, Tag):
                    buf.append(child.get_text("", strip=False))
                else:
                    buf.append(str(child))
            flush_buf()
            return

        # Leaf div: either a blank separator or one/more <br>-separated entries.
        parts: list[str] = []
        for child in node.children:
            if isinstance(child, Tag) and child.name == "br":
                parts.append("\n")
            elif isinstance(child, Tag):
                parts.append(child.get_text("", strip=False))
            else:
                parts.append(str(child))
        raw = "".join(parts)
        cleaned_lines = [_clean_inline(p) for p in raw.splitlines()]
        non_empty = [ln for ln in cleaned_lines if ln]
        if not non_empty:
            flush_pending()
            if lines and lines[-1] != "":
                lines.append("")
            return

        for ln in non_empty:
            if _SINGLE_LETTER_RE.fullmatch(ln):
                flush_pending()
                lines.append("")
                lines.append(ln)
                lines.append("")
            elif _DASH_RE.search(ln):
                flush_pending()
                pending_entry = ln
            elif pending_entry is not None:
                pending_entry = f"{pending_entry} {ln}"
            else:
                lines.append(ln)

    walk(taskhtml)
    flush_pending()

    # Collapse consecutive blank lines to at most one.
    compact: list[str] = []
    for ln in lines:
        if ln == "" and (not compact or compact[-1] == ""):
            continue
        compact.append(ln)
    return "\n".join(compact).strip()


def _extract_theory_text(taskhtml: Tag, title: str) -> str:
    """Render a MiyKlas theory page body to clean paragraph lines."""
    clone = BeautifulSoup(str(taskhtml), "html.parser")
    for br in clone.find_all("br"):
        br.replace_with("\n")
    for block in clone.find_all(["div", "p", "li", "h2", "h3", "h4", "tr"]):
        block.insert_before("\n")
        block.insert_after("\n")
    raw = clone.get_text("", strip=False)
    lines = [_clean_inline(ln) for ln in raw.splitlines()]
    non_empty = [ln for ln in lines if ln]
    if title and (not non_empty or title not in non_empty[0]):
        non_empty.insert(0, title)
    return "\n".join(non_empty).strip()


def parse_miyklas_html(raw_html: bytes, *, kind: str, title: str) -> str:
    """Extract normalized UTF-8 text from raw MiyKlas HTML bytes."""
    soup = BeautifulSoup(raw_html.decode("utf-8", errors="replace"), "html.parser")
    taskhtml = soup.select_one("#taskhtml") or soup.select_one("div.blockbody")
    if taskhtml is None:
        raise MiyKlasFetchError(f"MiyKlas page {title!r} missing #taskhtml content block")
    if kind == "dictionary":
        text = _extract_dictionary_text(taskhtml)
    elif kind == "theory":
        text = _extract_theory_text(taskhtml, title)
    else:
        raise ValueError(f"Unsupported MiyKlas page kind: {kind!r}")
    if not text.strip():
        raise MiyKlasFetchError(f"MiyKlas page {title!r} produced empty extracted text")
    return text


def fetch_miyklas_pages(
    pages: tuple[dict[str, str], ...] = DEFAULT_MIYKLAS_PAGES,
    *,
    timeout: float = 20.0,
    user_agent: str = USER_AGENT,
) -> dict[str, Any]:
    """Fetch public MiyKlas paronym pages and return a provenance-pinned snapshot dict."""
    records: list[dict[str, Any]] = []
    fetched_run_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    opener = urllib.request.build_opener(_MiyKlasRedirectHandler())
    for spec in pages:
        url = spec["url"]
        _validate_miyklas_url(url)
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with opener.open(req, timeout=timeout) as resp:
                status = int(resp.status)
                final_url = resp.geturl()
                raw_bytes = resp.read()
        except urllib.error.URLError as exc:
            raise MiyKlasFetchError(f"Failed fetching {url}: {exc}") from exc
        _validate_miyklas_url(final_url)
        if status != 200:
            raise MiyKlasFetchError(f"Unexpected HTTP {status} for {url}")
        text = parse_miyklas_html(raw_bytes, kind=spec["kind"], title=spec["title"])
        rec = MiyKlasPageRecord(
            page_id=spec["page_id"],
            grade=spec["grade"],
            kind=spec["kind"],
            title=spec["title"],
            url=url,
            final_url=final_url,
            http_status=status,
            fetched_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            raw_html_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            raw_html_bytes=len(raw_bytes),
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            text=text,
        )
        records.append(rec.as_dict())
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "miyklas.com.ua",
        "fetched_at_utc": fetched_run_at,
        "user_agent": user_agent,
        "page_count": len(records),
        "pages": records,
    }


def validate_miyklas_page_dict(page: Any, *, verify_text_digest: bool = True) -> dict[str, Any]:
    """Fail closed if a MiyKlas snapshot page record lacks valid typed provenance."""
    if not isinstance(page, dict):
        raise ValueError(f"MiyKlas snapshot page must be a JSON object, got {type(page).__name__}")
    required_str_keys: tuple[str, ...] = (
        "page_id",
        "title",
        "url",
        "fetched_at_utc",
        "raw_html_sha256",
        "text_sha256",
    )
    if verify_text_digest:
        required_str_keys = (*required_str_keys, "text")
    for key in required_str_keys:
        val = page.get(key)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"MiyKlas snapshot page missing or invalid non-empty string key {key!r}")
    status = page.get("http_status")
    if isinstance(status, bool) or not isinstance(status, int) or status != 200:
        raise ValueError(
            f"MiyKlas snapshot page {page['page_id']!r} requires integer http_status == 200, got {status!r}"
        )
    parsed_url = urllib.parse.urlparse(page["url"])
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError(f"MiyKlas snapshot page {page['page_id']!r} requires https URL, got {page['url']!r}")
    for digest_key in ("raw_html_sha256", "text_sha256"):
        digest = page[digest_key]
        if not _SHA256_HEX_RE.fullmatch(digest):
            raise ValueError(f"MiyKlas snapshot page {page['page_id']!r} has invalid {digest_key}: {digest!r}")
    if "grade" in page and not isinstance(page["grade"], str):
        raise ValueError(f"MiyKlas snapshot page {page['page_id']!r} has non-string 'grade'")
    if "raw_html_bytes" in page:
        raw_len = page["raw_html_bytes"]
        if isinstance(raw_len, bool) or not isinstance(raw_len, int) or raw_len < 0:
            raise ValueError(f"MiyKlas snapshot page {page['page_id']!r} has invalid 'raw_html_bytes'")
    if verify_text_digest:
        actual_sha = hashlib.sha256(page["text"].encode("utf-8")).hexdigest()
        expected_sha = page["text_sha256"]
        if actual_sha != expected_sha:
            raise ValueError(f"Text SHA-256 mismatch for {page['page_id']}: expected {expected_sha}, got {actual_sha}")
    return page


def load_miyklas_documents(snapshot_path: Path) -> tuple[dict[str, Any], list[SourceDocument]]:
    """Load a saved MiyKlas snapshot JSON and validate its provenance and SHA-256 integrity."""
    try:
        raw = snapshot_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"MiyKlas snapshot not found at {snapshot_path}; pass --fetch-miyklas or --textbooks-only"
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Unreadable MiyKlas snapshot {snapshot_path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {snapshot_path.name}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported MiyKlas snapshot schema_version: "
            f"{payload.get('schema_version') if isinstance(payload, dict) else type(payload).__name__!r}"
        )
    pages = payload.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("MiyKlas snapshot contains no pages")
    docs: list[SourceDocument] = []
    for raw_page in pages:
        page = validate_miyklas_page_dict(raw_page, verify_text_digest=True)
        docs.append(
            SourceDocument(
                source_type="miyklas",
                source_file=f"miyklas-{page['page_id'].removeprefix('miyklas-')}",
                chunk_id=page["page_id"],
                locator=page["url"],
                title=page["title"],
                text=page["text"],
                grade=page.get("grade", ""),
                author="МійКлас",
                source_url=page["url"],
                fetch_date_utc=page["fetched_at_utc"],
                raw_html_sha256=page["raw_html_sha256"],
                text_sha256=page["text_sha256"],
            )
        )
    return payload, docs
