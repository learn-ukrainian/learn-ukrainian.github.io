"""Extract owned reference works privately; publish only metadata accounting.

Archives are read in place. JSONL and state receipts belong outside every checkout;
all corpus writes use an explicitly selected local database. No extracted text,
private path, archive member name or exception message is a diagnostic.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import posixpath
import re
import sqlite3
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import unquote

import pymupdf
import yaml
from bs4 import BeautifulSoup
from docx import Document
from lxml import etree

from scripts.curriculum.evidence.publication import load_owned_rights
from scripts.ingest._section_coverage import LessonSection, ensure_section_schema, link_lesson_sections
from scripts.storage.topology import is_network_filesystem_path

REPOSITORY = Path(__file__).resolve().parents[2]
MEMBER_CAP = 200 * 1024 * 1024
CHUNK_SIZE = 6000
SKIPS = {"skip_audio", "skip_audio_and_decks", "skip_derived", "missing_source"}
STATES = SKIPS | {"already_ingested", "pdf_text_only"}
RIGHTS = {"owned_cite_only", "private_permission"}
UKRAINIAN_LETTERS = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
ALLOWED_LETTERS = frozenset(
    UKRAINIAN_LETTERS + UKRAINIAN_LETTERS.lower() + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class IngestError(Exception):
    """A closed diagnostic code, never a library exception message."""


def load_inventory(path: Path) -> list[dict]:
    """Validate the private denominator without exposing its contents."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        rows = document.get("works") if isinstance(document, dict) else None
        if not isinstance(rows, list) or not rows:
            raise IngestError("invalid_inventory")
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                raise IngestError("invalid_inventory")
            ident = row.get("id")
            files = row.get("files")
            if (
                not isinstance(ident, str)
                or not SLUG.fullmatch(ident)
                or ident in seen
                or row.get("rights") not in RIGHTS
                or (row.get("ingest") is not None and not isinstance(row["ingest"], str))
                or (
                    row["rights"] == "owned_cite_only"
                    and row.get("ingest") not in SKIPS | {"already_ingested"}
                    and (not isinstance(row.get("title"), str) or not row["title"].strip())
                )
                or (row.get("author") is not None and not isinstance(row["author"], str))
                or not isinstance(files, list)
                or any(not isinstance(p, str) or not p or Path(p).is_absolute() or ".." in Path(p).parts for p in files)
                or (row.get("ingest") not in SKIPS and not files)
            ):
                raise IngestError("invalid_inventory")
            source_identities(row)
            seen.add(ident)
        return rows
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        raise IngestError("invalid_inventory") from None


def source_identities(row: dict) -> list[str]:
    """Validate singular or plural legacy identities without disclosing inputs."""
    if "source_file" in row and "source_files" in row:
        raise IngestError("conflicting_source_identities")
    if row.get("ingest") != "already_ingested":
        return [f"owned-{row['id']}"]
    if "source_files" in row:
        identities = row["source_files"]
        if (
            not isinstance(identities, list)
            or not identities
            or any(not isinstance(s, str) or not SLUG.fullmatch(s) for s in identities)
            or len(set(identities)) != len(identities)
        ):
            raise IngestError("invalid_source_files")
        return identities
    identity = row.get("source_file")
    if not isinstance(identity, str) or not SLUG.fullmatch(identity):
        raise IngestError("invalid_source_file")
    return [identity]


def metadata(row: dict) -> tuple[str, str, str]:
    """Bibliography is inventory-owned; teacher identities never enter metadata."""
    if row["rights"] == "private_permission":
        title = {"teacher-a-slides": "Teacher materials A", "teacher-b-notes": "Teacher materials B"}.get(
            row["id"], "Private reference"
        )
        return title, "", ""
    return row["title"], row.get("author") or "", row.get("author_uk") or row.get("author") or ""


def page_text_status(text: str) -> str:
    """Classify extracted letters after NFC and unstressing; exactly 20% is kept."""
    normalised = unicodedata.normalize("NFC", text).replace("\u0301", "")
    letters = [c for c in normalised if unicodedata.category(c).startswith("L")]
    if not letters:
        return "page_no_text"
    disallowed = sum(c not in ALLOWED_LETTERS for c in letters)
    return "garbled_text_layer" if disallowed * 5 > len(letters) else "text"


def read_member(archive: zipfile.ZipFile, member: str | zipfile.ZipInfo) -> bytes:
    """Bound uncompressed members before reading and reject encrypted payloads."""
    try:
        info = archive.getinfo(member) if isinstance(member, str) else member
        if info.file_size > MEMBER_CAP:
            raise IngestError("member_too_large")
        if info.flag_bits & 1:
            raise IngestError("encrypted")
        with archive.open(info) as stream:
            payload = stream.read(MEMBER_CAP + 1)
        if len(payload) > MEMBER_CAP:
            raise IngestError("member_too_large")
        return payload
    except IngestError:
        raise
    except Exception:
        raise IngestError("corrupt") from None


def xml(payload: bytes) -> etree._Element:
    """Parse package XML without entities or external resources."""
    return etree.fromstring(payload, etree.XMLParser(resolve_entities=False, no_network=True))


def package_text(payload: bytes, extension: str) -> list[tuple[int, str]]:
    """Read EPUB spine order or PPTX presentation order, never filename order."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if extension == ".epub":
            container = xml(read_member(archive, "META-INF/container.xml"))
            paths = container.xpath('//*[local-name()="rootfile"]/@full-path')
            if not paths:
                raise IngestError("corrupt")
            opf = paths[0]
            book = xml(read_member(archive, opf))
            manifest = {e.get("id"): e.get("href") for e in book.xpath('//*[local-name()="manifest"]/*')}
            order = book.xpath('//*[local-name()="spine"]/*/@idref')
            if not order:
                raise IngestError("corrupt")
            result = []
            for index, ref in enumerate(order, 1):
                href = manifest[ref]
                target = posixpath.normpath(posixpath.join(posixpath.dirname(opf), unquote(href).split("#")[0]))
                soup = BeautifulSoup(read_member(archive, target), "lxml")
                for element in soup(["script", "style"]):
                    element.decompose()
                # Inline markup can split a word. Preserve those run boundaries
                # while separating block elements even in minified XHTML.
                for element in soup(["p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr", "td"]):
                    element.insert_before("\n")
                    element.insert_after("\n")
                result.append((index, soup.get_text().strip()))
            return result
        presentation = xml(read_member(archive, "ppt/presentation.xml"))
        relations = xml(read_member(archive, "ppt/_rels/presentation.xml.rels"))
        targets = {e.get("Id"): e.get("Target") for e in relations}
        order = presentation.xpath('//*[local-name()="sldId"]/@*[local-name()="id" and namespace-uri()!=""]')
        if not order:
            raise IngestError("corrupt")
        result = []
        for index, ref in enumerate(order, 1):
            target = targets[ref]
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("ppt", target))
            slide = xml(read_member(archive, target))
            ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            paragraphs = slide.xpath("//a:p", namespaces=ns)
            text = "\n".join("".join(p.xpath(".//a:t/text()", namespaces=ns)) for p in paragraphs)
            if not paragraphs:
                text = "".join(slide.xpath("//a:t/text()", namespaces=ns))
            result.append((index, text))
        return result


def extract(
    payload: bytes, extension: str, *, file_accounting: dict | None = None
) -> tuple[list[tuple[int, str]], list[dict], str]:
    """Extract content and page accounting; exceptions have class-only messages."""
    try:
        page_errors = set()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if extension in {".pdf", ".jpeg", ".jpg"}:
                old_errors = pymupdf.TOOLS.mupdf_display_errors()
                old_warnings = pymupdf.TOOLS.mupdf_display_warnings()
                try:
                    pymupdf.TOOLS.mupdf_display_errors(False)
                    pymupdf.TOOLS.mupdf_display_warnings(False)
                    if extension in {".jpeg", ".jpg"}:
                        pymupdf.Pixmap(payload)  # Decode, rather than accepting a lazy image wrapper.
                    with pymupdf.open(stream=payload, filetype=extension[1:]) as document:
                        if document.is_encrypted:
                            raise IngestError("encrypted")
                        if extension == ".pdf" and document.authenticate("") == 2 and file_accounting is not None:
                            file_accounting["owner_restricted"] = True
                        units = []
                        for i in range(len(document)):
                            try:
                                units.append((i + 1, document[i].get_text()))
                            except Exception:
                                units.append((i + 1, ""))
                                page_errors.add(i + 1)
                finally:
                    pymupdf.TOOLS.mupdf_display_errors(old_errors)
                    pymupdf.TOOLS.mupdf_display_warnings(old_warnings)
            elif extension == ".csv":
                # Grounding needs the serialized reference text, not inferred
                # columns. Preserve separators and quotes across CSV dialects.
                units = [(1, payload.decode("utf-8-sig"))]
            elif extension == ".docx":
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    for member in archive.infolist():
                        if member.file_size > MEMBER_CAP:
                            raise IngestError("member_too_large")
                        if member.flag_bits & 1:
                            raise IngestError("encrypted")
                document = Document(io.BytesIO(payload))
                # XML order retains paragraphs and tables (including nested cells).
                units = [
                    (1, "\n".join("".join(p.xpath(".//w:t/text()")) for p in document.element.body.xpath(".//w:p")))
                ]
            elif extension in {".epub", ".pptx"}:
                units = package_text(payload, extension)
            else:
                raise IngestError("unsupported_format")
        pages = [
            {
                "page": page,
                "status": ("error:corrupt" if page in page_errors else page_text_status(text)),
                "characters": len(text),
            }
            for page, text in units
        ]
        nonempty = [
            (page, text)
            for (page, text), accounting in zip(units, pages, strict=True)
            if accounting["status"] == "text"
        ]
        if page_errors:
            return nonempty, pages, "error:corrupt"
        no_text = sum(p["status"] == "page_no_text" for p in pages)
        garbled = sum(p["status"] == "garbled_text_layer" for p in pages)
        if extension in {".pdf", ".jpeg", ".jpg"} and no_text * 2 > len(units) - garbled:
            return [], pages, "skipped:scanned_needs_ocr"
        return (
            nonempty,
            pages,
            ("extracted" if nonempty else "skipped:garbled_text_layer" if garbled else "skipped:page_no_text"),
        )
    except IngestError:
        raise
    except Exception:
        raise IngestError("corrupt") from None


def collect(row: dict, files: list[Path]) -> tuple[list[tuple[str, int, str]], list[dict]]:
    """Account for every matched file and archive leaf without disclosing names."""
    units, accounting = [], []
    retained = []
    digests = {}

    def visit(payload: bytes | None, name: str, index: str, depth: int, path: Path | None = None) -> None:
        entry = {"file_index": index}
        accounting.append(entry)
        extension = Path(name).suffix.lower()
        try:
            if Path(name).name == ".DS_Store" or Path(name).name.startswith("._"):
                entry["status"] = "skipped:ignored_metadata"
                return
            if extension == ".zip":
                if depth > 1:
                    entry["status"] = "skipped:nested_archive_depth"
                    return
                with zipfile.ZipFile(path if path is not None else io.BytesIO(payload)) as archive:
                    members = sorted((m for m in archive.infolist() if not m.is_dir()), key=lambda m: m.filename)
                    count = 0
                    for member in members:
                        if (
                            "__MACOSX" in Path(member.filename).parts
                            or Path(member.filename).name == ".DS_Store"
                            or Path(member.filename).name.startswith("._")
                        ):
                            continue
                        count += 1
                        child = f"{index}.{count}"
                        extension = Path(member.filename).suffix.lower()
                        if (
                            member.file_size <= MEMBER_CAP
                            and not member.flag_bits & 1
                            and (
                                extension in {".mp3", ".m4b", ".wav", ".m4a", ".apkg"}
                                or (row.get("ingest") == "pdf_text_only" and extension not in {".pdf", ".zip"})
                            )
                        ):
                            reason = "pdf_text_only" if row.get("ingest") == "pdf_text_only" else "audio_or_deck"
                            accounting.append({"file_index": child, "status": f"skipped:{reason}"})
                            continue
                        try:
                            data = read_member(archive, member)
                        except IngestError as exc:
                            accounting.append(
                                {
                                    "file_index": child,
                                    "status": f"skipped:{exc}" if str(exc) == "member_too_large" else f"error:{exc}",
                                }
                            )
                            continue
                        visit(data, member.filename, child, depth + 1)
                    entry.update(status="extracted" if count else "skipped:empty_archive", members=count)
                return
            if row.get("ingest") == "pdf_text_only" and extension != ".pdf":
                entry["status"] = "skipped:pdf_text_only"
                return
            if extension in {".mp3", ".m4b", ".wav", ".m4a", ".apkg"}:
                entry["status"] = "skipped:audio_or_deck"
                return
            extracted, pages, status = extract(
                path.read_bytes() if path is not None else payload, extension, file_accounting=entry
            )
            entry.update(status=status, pages=pages)
            normalised = " ".join(unicodedata.normalize("NFC", "\n".join(text for _, text in extracted)).split())
            if normalised and status == "extracted":
                digest = hashlib.sha256(normalised.encode("utf-8")).hexdigest()
                entry["text_sha256"] = digest
                exact_donor = digests.get(digest)
                unit_texts = {" ".join(unicodedata.normalize("NFC", text).split()) for _, text in extracted}
                unit_texts.discard("")
                donor = next(
                    (
                        i
                        for i, text, donor_units in retained
                        if i == exact_donor or normalised in text or (unit_texts and unit_texts <= donor_units)
                    ),
                    None,
                )
                if donor is not None:
                    entry["status"] = f"duplicate_of:f{donor}"
                    return
                retained.append((index, normalised, unit_texts))
                digests[digest] = index
            units.extend((index, page, text) for page, text in extracted)
        except IngestError as exc:
            entry["status"] = f"skipped:{exc}" if str(exc) == "member_too_large" else f"error:{exc}"
        except Exception:
            entry["status"] = "error:corrupt"

    for index, path in enumerate(files, 1):
        visit(None, path.name, str(index), 0, path)
    return units, accounting


def matched_files(row: dict, root: Path) -> tuple[list[Path], list[dict]]:
    """Expand terminal ** to recursive files regardless of Python glob version."""
    found, missing = set(), []
    for index, pattern in enumerate(row["files"], 1):
        file_pattern = pattern + "/*" if pattern.endswith("/**") or pattern == "**" else pattern
        members = [p for p in root.glob(file_pattern) if p.is_file()]
        if not members:
            missing.append({"file_index": f"pattern-{index}", "status": "error:missing_file"})
        for path in members:
            if not path.resolve().is_relative_to(root.resolve()):
                raise IngestError("input_outside_root")
            found.add(path)
    return sorted(found), missing


def input_digest(row: dict, files: list[Path], root: Path) -> str:
    """Hash content, relative identities and extraction policy; expose only digest."""
    engine = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    digest = hashlib.sha256(json.dumps({"engine": engine, "row": row}, sort_keys=True).encode())
    for path in files:
        member_digest = hashlib.sha256()
        with path.open("rb") as stream:
            while data := stream.read(1024 * 1024):
                member_digest.update(data)
        digest.update(json.dumps([str(path.relative_to(root)), member_digest.hexdigest()]).encode())
    return digest.hexdigest()


def chunks(row: dict, units: list[tuple[str, int, str]]) -> list[dict]:
    """Bound chunks without dropping text; stable ids use numeric source locators."""
    title, author, author_uk = metadata(row)
    slug = source_identities(row)[0]
    result = []
    for file_index, page, text in units:
        for part, start in enumerate(range(0, len(text), CHUNK_SIZE), 1):
            content = text[start : start + CHUNK_SIZE]
            result.append(
                {
                    "chunk_id": f"{slug}_f{file_index}_p{page:04d}_c{part:04d}",
                    "source_file": slug,
                    "title": title,
                    "author": author,
                    "author_uk": author_uk,
                    "subject": "owned_reference",
                    "grade": "",
                    "text": content,
                    "char_count": len(content),
                }
            )
    return result


def replace_work(conn: sqlite3.Connection, slug: str, records: list[dict]) -> None:
    """Replace one work transactionally, including insert-only FTS and sections."""
    ensure_section_schema(conn)
    if "subject" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}:
        conn.execute("ALTER TABLE textbooks ADD COLUMN subject TEXT")
    # The production schema has only an AFTER INSERT FTS trigger. Issue a
    # delete command ourselves unless a schema also maintains deletes.
    deletes = conn.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND tbl_name='textbooks'").fetchall()
    if not any("AFTER DELETE" in sql.upper() and "textbooks_fts" in sql for (sql,) in deletes):
        conn.execute(
            """INSERT INTO textbooks_fts(textbooks_fts,rowid,title,text)
                        SELECT 'delete',id,title,text FROM textbooks WHERE source_file=?""",
            (slug,),
        )
    conn.execute("DELETE FROM textbooks WHERE source_file=?", (slug,))
    conn.execute("DELETE FROM textbook_sections WHERE source_file=?", (slug,))
    for row in records:
        conn.execute(
            """INSERT INTO textbooks (chunk_id,source_file,title,author,author_uk,subject,grade,text,char_count)
                        VALUES (:chunk_id,:source_file,:title,:author,:author_uk,:subject,:grade,:text,:char_count)""",
            row,
        )
    link_lesson_sections(
        conn,
        source_file=slug,
        sections=[LessonSection(r["chunk_id"], f"Reference {i}", str(i), r["text"]) for i, r in enumerate(records, 1)],
    )


def retrieval_proof(conn: sqlite3.Connection, slug: str) -> dict:
    """Choose a distinctive long token, prove its FTS hit and section binding."""
    candidates = conn.execute(
        "SELECT id,chunk_id,text,parent_section_id FROM textbooks WHERE source_file=? ORDER BY chunk_id", (slug,)
    ).fetchall()
    for rowid, chunk_id, text, section in candidates:
        tokens = sorted(
            set(re.findall(r"[^\W\d_]{5,}", unicodedata.normalize("NFC", text).replace("\u0301", ""))),
            key=lambda token: (-len(token), token),
        )
        for token in tokens:
            hit = conn.execute(
                "SELECT rowid FROM textbooks_fts WHERE textbooks_fts MATCH ? AND rowid=?", (f'"{token}"', rowid)
            ).fetchone()
            linked = conn.execute(
                "SELECT 1 FROM textbook_sections WHERE section_id=? AND source_file=?", (section, slug)
            ).fetchone()
            if hit and linked:
                return {"token": token, "chunk_id": chunk_id}
    raise IngestError("retrieval_unverified")


def verify_saved(conn: sqlite3.Connection, slug: str, records: list[dict]) -> bool:
    """Check exact stored content and metadata plus section linkage, not counts alone."""
    keys = ("chunk_id", "source_file", "title", "author", "author_uk", "subject", "grade", "text", "char_count")
    stored = conn.execute(
        f"SELECT {','.join('t.' + k for k in keys)} FROM textbooks t JOIN textbook_sections s ON t.parent_section_id=s.section_id AND t.source_file=s.source_file AND t.text=s.full_text WHERE t.source_file=? ORDER BY t.chunk_id",
        (slug,),
    ).fetchall()
    expected = sorted(tuple(r[k] for k in keys) for r in records)
    total = conn.execute("SELECT count(*) FROM textbooks WHERE source_file=?", (slug,)).fetchone()[0]
    return stored == expected and total == len(records)


def atomic_write(path: Path, content: str) -> None:
    """Write private artifacts with restrictive permissions and atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            temporary.chmod(0o600)
            stream.write(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def process_work(
    conn: sqlite3.Connection, row: dict, root: Path, out_dir: Path, *, check: bool, dry_run: bool, force: bool
) -> dict:
    """Reconcile one whole inventory row and its private receipt without hidden drops."""
    report = {"id": row["id"], "status": "error:unexplained_row", "files": []}
    state = row.get("ingest")
    if state is not None and state not in STATES:
        report["status"] = "error:unknown_ingest"
        return report
    if state in SKIPS:
        files, _ = matched_files(row, root)
        report.update(
            status=f"skipped:{state}",
            files=[{"file_index": str(i), "status": f"skipped:{state}"} for i, _ in enumerate(files, 1)],
        )
        return report
    files, missing = matched_files(row, root)
    if state == "already_ingested":
        try:
            rights = load_owned_rights()
        except ValueError:
            raise IngestError("owned_rights_unreadable") from None
        if any(rights.get(identity, {}).get("rights") != row["rights"] for identity in source_identities(row)):
            raise IngestError("existing_source_rights_missing")
        sources = [
            {
                "source_file": identity,
                "rights": row["rights"],
                "chunks": conn.execute("SELECT count(*) FROM textbooks WHERE source_file=?", (identity,)).fetchone()[0],
            }
            for identity in source_identities(row)
        ]
        report.update(
            status="already_ingested" if all(s["chunks"] for s in sources) else "error:existing_source_missing",
            chunks=sum(s["chunks"] for s in sources),
            sources=sources,
            files=[
                {"file_index": str(i), "status": "duplicate_of:" + ",".join(source_identities(row))}
                for i, _ in enumerate(files, 1)
            ]
            + missing,
        )
        if missing:
            report["status"] = "error:missing_file"
        return report
    slug = source_identities(row)[0]
    try:
        rights = load_owned_rights()
    except ValueError:
        raise IngestError("owned_rights_unreadable") from None
    if slug not in rights:
        raise IngestError("owned_source_rights_missing")
    if rights[slug]["rights"] != row["rights"]:
        raise IngestError("owned_source_rights_mismatch")
    digest = input_digest(row, files, root)
    receipt_path, jsonl = out_dir / f"{slug}.manifest.json", out_dir / f"{slug}.jsonl"
    saved = None
    if receipt_path.exists():
        try:
            saved = json.loads(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict) or not isinstance(saved.get("report"), dict):
                raise IngestError("invalid_receipt")
        except (OSError, ValueError):
            raise IngestError("invalid_receipt") from None
    if saved is not None and saved.get("input_digest") != digest and not force:
        report["status"] = "error:stale_input"
        report["files"] = [
            {"file_index": str(i), "status": "error:stale_input"} for i, _ in enumerate(files, 1)
        ] + missing
        return report
    if saved is not None and saved.get("input_digest") == digest and not force:
        try:
            content = jsonl.read_text(encoding="utf-8")
            records = [json.loads(line) for line in content.splitlines()]
            artifact_valid = hashlib.sha256(content.encode()).hexdigest() == saved.get("jsonl_digest")
            existing = conn.execute("SELECT count(*) FROM textbooks WHERE source_file=?", (slug,)).fetchone()[0]
            # Rehearsal JSONL can populate a different database without forcing
            # a re-extraction or rewriting private artifacts. Existing differing
            # rows still require an explicit replacement.
            if artifact_valid and records and not existing and not check:
                report = saved["report"]
                if not dry_run:
                    with conn:
                        replace_work(conn, slug, records)
                        report["retrieval"] = retrieval_proof(conn, slug)
                else:
                    report.pop("retrieval", None)
                return report
            valid = artifact_valid and verify_saved(conn, slug, records)
        except (OSError, ValueError, TypeError, KeyError):
            valid = False
        report = saved["report"]
        if not valid:
            report["status"] = "error:artifact_mismatch"
        elif records:
            report["retrieval"] = retrieval_proof(conn, slug)
        return report
    units, accounting = collect(row, files)
    report["files"] = accounting + missing
    records = chunks(row, units)
    failures = any(f["status"].startswith("error:") for f in report["files"])
    if failures:
        report["status"] = "error:missing_file" if missing else "error:file_failure"
    elif not report["files"]:
        report["status"] = "error:unexplained_row"
    elif records:
        report["status"] = "ingested"
    else:
        report["status"] = "typed-skip"
    report["chunks"] = len(records)
    for status in ("garbled_text_layer", "page_no_text"):
        report[status] = sum(p["status"] == status for f in accounting for p in f.get("pages", []))
    if check:
        if records and not failures:
            report["status"] = "error:not_ingested"
        return report
    if dry_run:
        return report
    if failures and not records:
        return report
    # Refuse legacy unreceipted rows unless replacement was explicitly selected.
    if not force and conn.execute("SELECT 1 FROM textbooks WHERE source_file=? LIMIT 1", (slug,)).fetchone():
        report["status"] = "error:untracked_existing_rows"
        return report
    content = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    out_dir.mkdir(parents=True, exist_ok=True)
    with conn:
        replace_work(conn, slug, records)
        if records:
            report["retrieval"] = retrieval_proof(conn, slug)
        atomic_write(jsonl, content)
        receipt = {
            "input_digest": digest,
            "jsonl_digest": hashlib.sha256(content.encode()).hexdigest(),
            "report": report,
        }
        atomic_write(receipt_path, json.dumps(receipt, ensure_ascii=False))
    return report


class PrivateParser(argparse.ArgumentParser):
    """Argparse errors must not echo private arguments or paths."""

    def error(self, message: str) -> None:
        self.exit(2, "error:invalid_arguments\n")


def parser() -> argparse.ArgumentParser:
    """Expose the operational contract and typed exits through --help."""
    result = PrivateParser(
        description="Extract owned reference books into private JSONL and local corpus tables.\nUse for private grounding, never for publication or audio transcription.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  <shared-project-python> -m scripts.ingest.owned_books_ingest --inventory <private>/INVENTORY.yaml --out-dir <private>/jsonl --db <local>/sources-copy.db
  <shared-project-python> -m scripts.ingest.owned_books_ingest --inventory <private>/INVENTORY.yaml --out-dir <private>/jsonl --db <local>/sources-copy.db --check
Outputs: private per-work JSONL and digest receipts; local textbook/FTS/section rows;
  stdout contains metadata-only JSON accounting. --check and --dry-run write nothing.
Exit codes: 0 = all selected rows explained; 1 = a row/file/retrieval failure;
  2 = invalid arguments. --force replaces one work, never legacy source identities.
Related: docs/corpus-inventory.md; registry/sources/owned-rights.yaml; #9581.""",
    )
    result.add_argument(
        "--inventory",
        type=Path,
        required=True,
        help="Private inventory YAML; expects works rows and sibling drive-ukrainian/ files.",
    )
    result.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Private JSONL destination outside all repository checkouts, e.g. <private>/jsonl.",
    )
    result.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Existing local SQLite corpus, e.g. <local>/sources-copy.db; network paths refused.",
    )
    mode = result.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and account without writes (default: false); no installed-state proof.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Verify digests, exact DB rows, FTS and sections without writes (default: false).",
    )
    result.add_argument("--only", help="Select one exact inventory id, e.g. oho-a1-workbook (default: all).")
    result.add_argument(
        "--force",
        action="store_true",
        help="Replace selected work rows and JSONL on changed input (default: false); never overrides --check.",
    )
    return result


def validate_paths(out_dir: Path, db: Path) -> None:
    """Refuse private artifacts in any checkout and SQLite on network storage."""
    output = out_dir.resolve()
    if any((p / ".git").exists() for p in (output, *output.parents)) or output.is_relative_to(REPOSITORY):
        raise IngestError("output_inside_repository")
    if is_network_filesystem_path(db):
        raise IngestError("network_database_refused")
    if not db.is_file():
        raise IngestError("database_missing")


def run(args: argparse.Namespace) -> tuple[dict, int]:
    """Open a local DB in read-only mode for check/dry-run and process all rows."""
    validate_paths(args.out_dir, args.db)
    rows = load_inventory(args.inventory)
    if args.only:
        rows = [r for r in rows if r["id"] == args.only]
        if not rows:
            raise IngestError("unknown_id")
    reports = []
    with contextlib.closing(
        sqlite3.connect(
            args.db.resolve().as_uri() + ("?mode=ro" if args.check or args.dry_run else "?mode=rw"), uri=True
        )
    ) as conn:
        for row in rows:
            try:
                reports.append(
                    process_work(
                        conn,
                        row,
                        args.inventory.parent / "drive-ukrainian",
                        args.out_dir,
                        check=args.check,
                        dry_run=args.dry_run,
                        force=args.force and not args.check,
                    )
                )
            except IngestError as exc:
                reports.append({"id": row["id"], "status": f"error:{exc}", "files": []})
            except Exception:
                reports.append({"id": row["id"], "status": "error:processing_failure", "files": []})
    failures = sum(
        r["status"].startswith("error:") or any(f["status"].startswith("error:") for f in r["files"]) for r in reports
    )
    return {"rows": reports, "denominator": len(rows), "errors": failures}, int(bool(failures))


def main(argv: list[str] | None = None) -> int:
    """Print only sanitized accounting, including top-level failure codes."""
    args = parser().parse_args(argv)
    try:
        report, code = run(args)
    except IngestError as exc:
        report, code = {"status": f"error:{exc}"}, 1
    except Exception:
        report, code = {"status": "error:processing_failure"}, 1
    # Token proof belongs in the private rehearsal report, not diagnostics.
    for row in report.get("rows", []):
        if "retrieval" in row:
            row["retrieval"] = {"verified": True}
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
