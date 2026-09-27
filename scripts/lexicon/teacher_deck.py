"""``teacher-deck refresh``: rebuild the teacher-table practice deck from the master DOCX (#8843).

One command: ingest the lesson texts into ``sources.db`` (existing
``private_teacher_lessons_ingest``, no duplicate rows), sync the vocabulary
table, rebuild the shard and cloze, validate them (generator gate plus the
independent checker), and only then replace the local published set together.
With ``--publish`` the set is uploaded as one versioned GitHub Release asset and
the committed pointer is rewritten; the site build downloads and re-validates it
(``site/scripts/hydrate-teacher-deck.mjs``), exactly like the CEFR practice deck.
Unchanged inputs reproduce byte-identical artifacts.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from scripts.ingest.private_teacher_lessons_ingest import ingest_lessons, parse_docx
from scripts.lexicon import teacher_deck_shard as shard
from scripts.lexicon.sync_teacher_table_deck import (
    DEFAULT_SITE_DATA_PATH,
    HEADING,
    TeacherTableSyncError,
    build_deck_entries,
    extract_teacher_rows,
    frozen_keys_payload,
    normalize_uk_key,
    site_data_bytes,
)
from scripts.practice_deck import publish as release

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = PROJECT_ROOT / "data/lexicon/teacher-deck"
DEFAULT_POINTER = PROJECT_ROOT / "site/src/data/lexicon-teacher-deck.pointer.json"
DEFAULT_FROZEN_KEYS = PROJECT_ROOT / "site/src/data/lexicon-teacher-deck-frozen-keys.json"
CHECKER = PROJECT_ROOT / "scripts/audit/check_teacher_deck.py"
RELEASE_TAG = "atlas-teacher-deck"
RELEASE_TITLE = "Teacher-table practice deck"
RELEASE_NOTES = "Versioned release assets for the teacher-table practice deck (#8843); pinned by the site pointer."
PACKAGE_SCHEMA = "atlas-practice-teacher-package"
PACKAGE_FILES = (
    shard.MANIFEST_FILE,
    shard.FROZEN_KEYS_FILE,
    shard.DECK_FILE,
    shard.CLOZE_FILE,
    shard.COVERAGE_FILE,
)


class RefreshError(RuntimeError):
    """The refresh stopped before replacing the published set."""


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest(docx: Path, sources_db: Path) -> str:
    """Load the dated lessons into *sources_db*; replace the source only when it changed."""

    lessons = parse_docx(docx).lessons
    conn = sqlite3.connect(sources_db.resolve().as_uri() + "?mode=rw", uri=True, timeout=30)
    try:
        try:
            inserted, skipped = ingest_lessons(conn, lessons, force=False)
            mode = "incremental"
        except ValueError as exc:
            if "Source changed" not in str(exc):
                raise
            inserted, skipped = ingest_lessons(conn, lessons, force=True)
            mode = "replaced (existing lesson text changed)"
    finally:
        conn.close()
    return f"lessons: {len(lessons)} units, inserted {inserted}, unchanged {skipped} [{mode}]"


# ----------------------------------------------------------------------------- release package


def asset_name(deck_version: str) -> str:
    return f"lexicon-teacher-deck-{deck_version}.json.gz"


def build_package(files: dict[str, bytes], deck_version: str) -> tuple[bytes, bytes]:
    """Deterministic package JSON and its gzip (mtime 0), like the CEFR practice deck."""

    package = {
        "schema": PACKAGE_SCHEMA,
        "schemaVersion": shard.SCHEMA_VERSION,
        "deckVersion": deck_version,
        "files": [{"path": name, "content": files[name].decode("utf-8")} for name in PACKAGE_FILES],
    }
    package_bytes = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return package_bytes, gzip.compress(package_bytes, compresslevel=9, mtime=0)


def build_pointer(files: dict[str, bytes], package_bytes: bytes, gzip_bytes: bytes, repo: str) -> dict[str, Any]:
    manifest = json.loads(files[shard.MANIFEST_FILE])
    deck_version = str(manifest["deckVersion"])
    return {
        "asset_url": release._asset_url(repo, RELEASE_TAG, asset_name(deck_version)),
        "release_tag": RELEASE_TAG,
        "deck_version": deck_version,
        "package_schema_version": shard.SCHEMA_VERSION,
        "gz_sha256": _sha256(gzip_bytes),
        "package_sha256": _sha256(package_bytes),
        "gz_bytes": len(gzip_bytes),
        "package_bytes": len(package_bytes),
        "docx_sha256": manifest["docxSha256"],
        "file_count": len(manifest["files"]),
        "files": manifest["files"],
        "counts": manifest["counts"],
        "inputs": manifest["inputs"],
        "note": (
            "Pins the teacher-table deck release asset (#8843). Built by `teacher-deck refresh --publish`; "
            "the site build downloads it and re-checks hashes, schema versions and budgets."
        ),
    }


def unpack(gzip_bytes: bytes, pointer: dict[str, Any]) -> dict[str, bytes]:
    if _sha256(gzip_bytes) != pointer.get("gz_sha256"):
        raise RefreshError("published teacher deck asset does not match its pointer")
    package = json.loads(gzip.decompress(gzip_bytes))
    if package.get("schema") != PACKAGE_SCHEMA:
        raise RefreshError("published teacher deck asset has an unknown schema")
    return {str(item["path"]): str(item["content"]).encode("utf-8") for item in package["files"]}


def download_published(pointer: dict[str, Any], repo: str) -> dict[str, bytes]:
    data = release._download_release_asset(
        asset_name(str(pointer["deck_version"])), release_tag=str(pointer["release_tag"]), repo=repo
    )
    return unpack(data, pointer)


def publish(files: dict[str, bytes], repo: str) -> tuple[dict[str, Any], str]:
    """Create the release when missing, upload the versioned asset (verify instead when it
    already exists) and return the pointer to commit; the caller writes it."""

    manifest = json.loads(files[shard.MANIFEST_FILE])
    package_bytes, gzip_bytes = build_package(files, str(manifest["deckVersion"]))
    pointer = build_pointer(files, package_bytes, gzip_bytes, repo)
    name = asset_name(pointer["deck_version"])
    release.ensure_release(RELEASE_TAG, repo, title=RELEASE_TITLE, notes=RELEASE_NOTES)
    if name in release._release_asset_names(release_tag=RELEASE_TAG, repo=repo):
        release.verify_existing_release_asset(name, expected_gz_bytes=gzip_bytes, release_tag=RELEASE_TAG, repo=repo)
        action = f"asset {name} already published (verified identical)"
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            gzip_path = Path(temp_dir) / name
            gzip_path.write_bytes(gzip_bytes)
            release.upload_release_asset(gzip_path, asset_name=name, release_tag=RELEASE_TAG, repo=repo, clobber=False)
        action = f"uploaded {name} ({len(gzip_bytes)} B) to release {RELEASE_TAG}"
    return pointer, action


# ----------------------------------------------------------------------------- refresh


def previous_published_set(out_dir: Path, pointer_path: Path, repo: str) -> tuple[dict[str, bytes], str]:
    """The last built set: local copy first, else the published asset, else nothing (first sync)."""

    if (out_dir / shard.DECK_FILE).exists():
        return {path.name: path.read_bytes() for path in out_dir.iterdir() if path.is_file()}, f"local set {out_dir}"
    pointer = _read_json(pointer_path)
    if pointer:
        return download_published(pointer, repo), f"published asset {pointer['deck_version']}"
    return {}, "none (first sync)"


def _aspect_value(entry: dict[str, Any]) -> str | None:
    aspect = entry.get("aspect")
    return aspect.get("value") if isinstance(aspect, dict) else None


def entry_delta(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, list[str]]:
    before = {str(entry["entryId"]): entry for entry in previous}
    after = {str(entry["entryId"]): entry for entry in current}
    changed = []
    for entry_id in sorted(before.keys() & after.keys(), key=lambda key: after[key]["firstSeen"]):
        old, new = before[entry_id], after[entry_id]
        old_view = {"uk": old.get("uk"), "en": old.get("teacherEn", old.get("en")), "aspect": _aspect_value(old)}
        new_view = {"uk": new["uk"], "en": new["teacherEn"], "aspect": _aspect_value(new)}
        notes = [
            f"{field}: {old_view[field]!r} -> {new_view[field]!r}"
            for field in new_view
            if old_view[field] != new_view[field]
        ]
        if notes:
            changed.append(f"{new['uk']}: " + "; ".join(notes))
    added = sorted(after.keys() - before.keys(), key=lambda key: after[key]["firstSeen"])
    return {
        "added": [f"{after[key]['uk']} = {after[key]['en']}" for key in added],
        "removed": [f"{before[key]['uk']} = {before[key]['en']}" for key in sorted(before.keys() - after.keys())],
        "changed": changed,
    }


def key_delta(previous_keys: list[str], current: list[dict[str, Any]]) -> dict[str, list[str]]:
    """First-sync delta against the lemma-only deck, which has no meanings to compare."""

    before = {normalize_uk_key(key) for key in previous_keys}
    after = {str(entry["key"]) for entry in current}
    return {
        "added": [f"{entry['uk']} = {entry['en']}" for entry in current if entry["key"] not in before],
        "removed": [key for key in previous_keys if normalize_uk_key(key) not in after],
        "changed": [],
    }


def _public_lesson_sentences(cloze_bytes: bytes | None) -> set[str]:
    if not cloze_bytes:
        return set()
    return {
        str(item["sentence"]).replace(shard.BLANK, str(item["form"]), 1)
        for item in json.loads(cloze_bytes).get("cloze", [])
        if item.get("source") == "teacher-lesson"
    }


def aspect_summary(entries: list[dict[str, Any]], counts: dict[str, Any]) -> list[str]:
    """Source-derived verb aspect: the teacher's marker set, counts by basis, and every
    entry whose marker disagrees with the sources or whose aspect stays unknown."""

    markers: dict[str, int] = {}
    for entry in entries:
        for marker in shard.ASPECT_MARKER_RE.findall(str(entry["teacherEn"])):
            markers[marker.strip()] = markers.get(marker.strip(), 0) + 1
    lines = [
        "teacher aspect markers in the English (stripped, never the authority): "
        + (", ".join(f"{marker} x{n}" for marker, n in sorted(markers.items())) or "none")
    ]
    for shape, table in counts["verbAspect"].items():
        cells = "; ".join(
            f"{basis}: " + ", ".join(f"{v} {n}" for v, n in values.items()) for basis, values in table.items()
        )
        lines.append(f"verb aspect ({shape}): {cells or 'none'}")
    lines.append(
        "EN->UK production cards: "
        + ", ".join(f"{n} {shape}" for shape, n in counts["entriesByMode"]["production-flashcard"].items())
        + f"; entries without: "
        f"{counts['withoutProduction']}; entries with an aspect partner (not an overlap): {counts['aspectPartnerEntries']}"
    )
    for title, keep in (
        ("teacher marker disagrees with the sources", lambda a: a["markerAgrees"] is False),
        ("aspect unknown", lambda a: a["value"] == "unknown"),
    ):
        rows = [entry for entry in entries if entry.get("aspect") and keep(entry["aspect"])]
        lines.append(f"{title}: {len(rows)}")
        lines.extend(
            f"  {entry['uk']} = {entry['teacherEn']} | sources {entry['aspect']['value']} ({entry['aspect']['basis']}; "
            f"VESUM {'/'.join(entry['aspect']['vesum']) or '-'}, ULIF {'/'.join(entry['aspect']['ulif']) or '-'}"
            f"{', lemma ' + entry['aspect']['lemma'] if entry['multiword'] and entry['aspect']['lemma'] else ''})"
            for entry in rows
        )
    return lines


def run_checker(staging: Path, args: argparse.Namespace, expected_keys: int) -> str:
    command = [
        sys.executable,
        str(CHECKER),
        "--deck-dir",
        str(staging),
        "--docx",
        str(args.docx),
        "--heading",
        args.heading,
        "--expect-keys",
        str(expected_keys),
        "--vesum-db",
        str(args.vesum_db),
        "--sources-db",
        str(args.sources_db),
        "--atlas-db",
        str(args.atlas_db),
        "--withheld",
        str(args.withheld),
        "--limit",
        "20",
    ]
    # The checker re-reads the DOCX and queries VESUM/sources.db for every cloze item.
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=1800)
    if result.returncode != 0:
        raise RefreshError(
            "independent checker failed; published set left unchanged:\n" + result.stdout + result.stderr
        )
    return result.stdout


class PublishedSetSwap:
    """A swapped-in local published set whose old copy is kept until the run commits."""

    def __init__(self, out_dir: Path, backup: Path | None) -> None:
        self.out_dir = out_dir
        self.backup = backup  # the old set (None: there was none)

    def finish(self) -> None:
        if self.backup is not None:
            shutil.rmtree(self.backup)

    def undo(self) -> None:
        shutil.rmtree(self.out_dir)
        if self.backup is not None:
            self.backup.rename(self.out_dir)


def swap_published_set(files: dict[str, bytes], out_dir: Path) -> PublishedSetSwap | None:
    """Swap the whole directory at once, keeping the old set as ``.<name>.previous``
    until ``finish()`` or ``undo()``; return None when nothing changed.

    If the second rename fails the old set is moved back, so *out_dir* is never lost.
    A ``.previous`` left behind by an interrupted run is restored (or, when the new set
    is in place, discarded) before anything else.
    """

    staging = out_dir.with_name(f".{out_dir.name}.next")
    backup = out_dir.with_name(f".{out_dir.name}.previous")
    if backup.exists():
        if out_dir.exists():
            shutil.rmtree(backup)
        else:
            backup.rename(out_dir)
    unchanged = out_dir.exists() and {path.name for path in out_dir.iterdir()} == set(files)
    if unchanged and all((out_dir / name).read_bytes() == data for name, data in files.items()):
        return None
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for name, data in files.items():
        (staging / name).write_bytes(data)
    had_previous = out_dir.exists()
    if had_previous:
        out_dir.rename(backup)
    try:
        staging.rename(out_dir)
    except OSError:
        if had_previous:
            backup.rename(out_dir)
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return PublishedSetSwap(out_dir, backup if had_previous else None)


def replace_published_set(files: dict[str, bytes], out_dir: Path) -> bool:
    """Swap the whole directory at once; return False when nothing changed."""

    swap = swap_published_set(files, out_dir)
    if swap is None:
        return False
    swap.finish()
    return True


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _restore_file(target: Path, original: bytes | None) -> None:
    if original is None:
        target.unlink(missing_ok=True)
        return
    temp = target.with_name(f".{target.name}.previous")
    temp.write_bytes(original)
    temp.replace(target)


def commit_outputs(local_files: dict[str, bytes], out_dir: Path, committed: dict[Path, bytes]) -> bool:
    """Write the run's outputs only after every step (checker, publish) succeeded,
    all together or not at all.

    Committed files (table deck, frozen keys, pointer) are staged next to their targets
    and their current bytes kept; the local set is swapped (its old copy kept); then each
    staged file replaces its target (``os.replace``). A failure at any step undoes every
    step already taken: replaced files get their old bytes back (or are removed when they
    did not exist) and the old local set is swapped back. Only then are the backups
    discarded. (A killed process can still stop mid-way; the committed files then show in
    ``git status``.)
    """

    originals = {target: target.read_bytes() if target.exists() else None for target in committed}
    staged: list[tuple[Path, Path]] = []
    replaced: list[Path] = []
    swap: PublishedSetSwap | None = None
    try:
        for target, data in committed.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(f".{target.name}.next")
            temp.write_bytes(data)
            staged.append((temp, target))
        swap = swap_published_set(local_files, out_dir)
        for temp, target in staged:
            temp.replace(target)
            replaced.append(target)
    except BaseException:
        for target in reversed(replaced):
            _restore_file(target, originals[target])
        if swap is not None:
            swap.undo()
        for temp, _target in staged:
            temp.unlink(missing_ok=True)
        raise
    if swap is None:
        return False
    swap.finish()
    return True


def refresh(args: argparse.Namespace) -> int:
    out_dir: Path = args.out_dir
    lines: list[str] = []
    docx_sha, rows = extract_teacher_rows(args.docx, args.heading)
    if not args.skip_ingest:
        lines.append(ingest(args.docx, args.sources_db))

    previous_files, previous_basis = previous_published_set(out_dir, args.pointer, args.repo)
    previous_deck = json.loads(previous_files[shard.DECK_FILE]) if shard.DECK_FILE in previous_files else {}
    previous_entries = previous_deck.get("entries") or []
    build = build_deck_entries(rows, previous_entries)
    lemma_keys = [str(entry["uk"]) for entry in build.entries]

    previous_keys = (_read_json(args.table_deck) or {}).get("lemma_keys") or []
    if not args.allow_shrink:
        current = {normalize_uk_key(key) for key in lemma_keys}
        dropped = [key for key in previous_keys if normalize_uk_key(key) not in current]
        if dropped:
            raise RefreshError(
                f"refusing to drop {len(dropped)} published keys (first: {dropped[:3]}); pass --allow-shrink"
            )

    inputs = shard.TeacherDeckInputs(
        args.atlas_db, args.sources_db, args.vesum_db, args.synonym_verdicts, args.withheld
    )
    deck_build = shard.build_teacher_deck(build.entries, inputs)
    errors = shard.validate_teacher_deck(deck_build.deck, deck_build.cloze)
    if errors:
        raise RefreshError("generator validation failed:\n  " + "\n  ".join(errors[:20]))
    frozen = frozen_keys_payload(docx_sha, build, args.heading)
    files = shard.render_published_set(deck_build, frozen)

    review = shard.lesson_sentence_review(deck_build, args.vesum_db)
    local_files = {**files, shard.REVIEW_FILE: shard.render_json(review, list_keys=("sentences",))}
    pending = review["counts"]
    if args.publish and pending["sentences"]:
        raise RefreshError(
            f"refusing to publish: {pending['sentences']} served teacher-lesson cloze items "
            f"({pending['distinctSentences']} distinct sentences) have no language-review record in "
            f"{args.withheld}; nothing was replaced or uploaded. Run without --publish to write the queue to "
            f"{out_dir / shard.REVIEW_FILE}, record the review with `teacher-deck record-review`, then rerun "
            "with --publish."
        )

    check_dir = out_dir.with_name(f".{out_dir.name}.check")
    if check_dir.exists():
        shutil.rmtree(check_dir)
    check_dir.mkdir(parents=True)
    try:
        for name, data in files.items():
            (check_dir / name).write_bytes(data)
        checker_output = run_checker(check_dir, args, len(build.source_keys))
    finally:
        shutil.rmtree(check_dir, ignore_errors=True)

    previous_public = _public_lesson_sentences(previous_files.get(shard.CLOZE_FILE))
    committed = {args.table_deck: site_data_bytes(lemma_keys), args.frozen_keys: files[shard.FROZEN_KEYS_FILE]}
    if args.publish:
        # Upload first (a versioned, content-addressed asset); the pointer is written
        # with the other committed files only once the whole run has succeeded.
        pointer, action = publish(files, args.repo)
        committed[args.pointer] = _json_bytes(pointer)
        publish_line = f"publish: {action}; pointer {args.pointer} -> {pointer['deck_version']}"
    else:
        current_pointer = _read_json(args.pointer) or {}
        state = "up to date" if current_pointer.get("deck_version") == deck_build.deck["deckVersion"] else "NOT updated"
        publish_line = f"publish: skipped (pointer {state}); rerun with --publish after the review queue is empty"
    replaced = commit_outputs(local_files, out_dir, committed)

    if previous_entries:
        delta = entry_delta(previous_entries, deck_build.deck["entries"])
    else:
        delta = key_delta(previous_keys, deck_build.deck["entries"])
    counts = deck_build.deck["counts"]
    lines += [
        f"document: sha256 {docx_sha}",
        f"table: {build.raw_data_rows} rows, {len(build.source_keys)} distinct source keys, "
        f"{len(build.entries)} entries, {len(build.merges)} merged "
        f"({sum(1 for m in build.merges if m['differentEnglish'])} with different English)",
        f"previous deck: {previous_basis}",
        f"deck version: {deck_build.deck['deckVersion']} "
        f"({'local published set replaced' if replaced else 'no-op: artifacts unchanged'}; {out_dir})",
        f"entries: {counts['entries']} ({counts['singleWord']} single-word, {counts['multiword']} multiword, "
        f"{counts['atlasJoined']} joined to the Atlas)",
        f"items: {json.dumps(counts['items'])}",
        f"inputs: {json.dumps(deck_build.input_versions, sort_keys=True)}",
    ]
    for name in ("added", "removed", "changed"):
        lines.append(f"{name} entries: {len(delta[name])}")
        lines.extend(f"  {row}" for row in delta[name])
    for merge in build.merges:
        lines.append(
            f"merged: {merge['uk']} rows {merge['rows']} spellings {merge['spellings']} meanings {merge['meanings']}"
        )
    public = deck_build.public_lesson_sentences
    new_public = [row for row in public if row["sentence"] not in previous_public]
    lines.append(
        f"teacher-lesson sentences public in the cloze file: {len(public)}, newly public: {len(new_public)} "
        "(scan for names/private details before --publish; NEW marks sentences not built before)"
    )
    lines.extend(f"  {'NEW ' if row in new_public else ''}[{row['lesson']}] {row['sentence']}" for row in public)
    review_counts = review["counts"]
    flagged = review_counts["flaggedSentences"]
    screen = deck_build.coverage["lessonSentenceScreen"]
    lines.append(
        "lesson sentences screened out before selection: fragment rule "
        + (", ".join(f"{rule} {n}" for rule, n in screen["fragmentRule"].items()) or "none")
        + "; withheld by review "
        + (", ".join(f"{code} {n}" for code, n in screen["withheldCode"].items()) or "none")
        + f" (ledger: {len(deck_build.reviews.withheld)} withheld, {len(deck_build.reviews.kept)} kept)"
    )
    lines.append(
        f"lesson-sentence review queue: {review_counts['sentences']} of {review_counts['servedLessonItems']} served "
        f"lesson cloze items ({review_counts['distinctSentences']} of {review_counts['servedLessonSentences']} "
        f"distinct sentences) have no review record -> {out_dir / shard.REVIEW_FILE} (local only, never "
        "published); queued items flagged: " + ", ".join(f"{flag} {flagged[flag]}" for flag in shard.REVIEW_FLAGS)
    )
    lines.extend(aspect_summary(deck_build.deck["entries"], counts))
    lines.append(checker_output.rstrip())
    lines.append(publish_line)
    print("\n".join(lines))
    if args.report:
        args.report.write_text(
            json.dumps(
                {
                    "delta": delta,
                    "counts": counts,
                    "inputs": deck_build.input_versions,
                    "publicLessonSentences": public,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0


# ----------------------------------------------------------------------------- review ledger

CODE_PRIORITY = ("PRIV", "ERR", "AMBIG", "FRAG")  # one sentence reviewed twice keeps the gravest code


def _restored_sentences(cloze_path: Path) -> dict[str, str]:
    return {
        str(item["clozeId"]): str(item["sentence"]).replace(shard.BLANK, str(item["form"]), 1)
        for item in json.loads(cloze_path.read_text(encoding="utf-8"))["cloze"]
    }


def _position_range(text: str | None, size: int) -> range:
    if not text:
        return range(size)
    start, _, end = text.partition("-")
    return range(int(start), int(end or start) + 1)


def record_review(args: argparse.Namespace) -> int:
    """Fold one language-review result into the committed ledger (hashes only, never text).

    Every queue item at --positions is recorded: withheld with its code when the results
    TSV lists its cloze id, otherwise kept. Existing records stay; withheld beats kept.
    """

    queue = json.loads(args.queue.read_text(encoding="utf-8"))["sentences"]
    positions = _position_range(args.positions, len(queue))
    if positions.start < 0 or positions.stop > len(queue) or not positions:
        raise RefreshError(f"--positions {args.positions} outside the queue (0-{len(queue) - 1})")
    restored = _restored_sentences(args.cloze)
    reviewed_ids: dict[str, str] = {}
    for index in positions:
        item = queue[index]
        cloze_id = str(item["clozeId"])
        if restored.get(cloze_id) != item["sentence"]:
            raise RefreshError(f"{cloze_id}: the queue sentence is not the cloze file's sentence")
        reviewed_ids[cloze_id] = item["sentence"]
    verdicts: dict[str, str] = {}
    for line_number, line in enumerate(args.results.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        cloze_id, _, code = (part.strip() for part in line.partition("\t"))
        if code not in shard.WITHHELD_CODES:
            raise RefreshError(f"{args.results}:{line_number}: unknown code {code!r}")
        if cloze_id not in reviewed_ids:
            raise RefreshError(f"{args.results}:{line_number}: {cloze_id} is not a queue item at --positions")
        digest = shard.sentence_sha256(reviewed_ids[cloze_id])
        verdicts[digest] = min(verdicts.get(digest, code), code, key=CODE_PRIORITY.index)

    ledger = _read_json(args.ledger) or {}
    withheld = {row["sentenceSha256"]: row for row in ledger.get("withheld", [])}
    kept = {row["sentenceSha256"]: row for row in ledger.get("kept", [])}
    stamp = {"reviewer": args.reviewer, "reviewedAt": args.reviewed_at}
    added = {"withheld": 0, "kept": 0}
    for sentence in dict.fromkeys(reviewed_ids.values()):
        digest = shard.sentence_sha256(sentence)
        code = verdicts.get(digest)
        if code:
            previous = withheld.get(digest)
            if previous is None or CODE_PRIORITY.index(code) < CODE_PRIORITY.index(previous["code"]):
                withheld[digest] = {"sentenceSha256": digest, "code": code, **stamp}
                added["withheld"] += previous is None
            kept.pop(digest, None)
        elif digest not in withheld and digest not in kept:
            kept[digest] = {"sentenceSha256": digest, **stamp}
            added["kept"] += 1
    payload = {
        "schema": shard.WITHHELD_SCHEMA,
        "schemaVersion": shard.SCHEMA_VERSION,
        "note": (
            "Language-review ledger for teacher-lesson cloze sentences (#8843), keyed by sentenceSha256 = "
            "SHA-256 of the NFC-normalised sentence with whitespace collapsed; no sentence text. Withheld "
            "sentences are never served (ERR incorrect Ukrainian, AMBIG more than one option fits, FRAG not a "
            "usable sentence, PRIV private detail); kept sentences need no further review. Update with "
            "`teacher-deck record-review`."
        ),
        "withheld": [withheld[key] for key in sorted(withheld)],
        "kept": [kept[key] for key in sorted(kept)],
    }
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    temp = args.ledger.with_name(f".{args.ledger.name}.next")
    temp.write_bytes(shard.render_json(payload, list_keys=("withheld", "kept")))
    temp.replace(args.ledger)
    by_code = {code: sum(1 for row in withheld.values() if row["code"] == code) for code in shard.WITHHELD_CODES}
    print(
        f"record-review: {len(reviewed_ids)} queue items at positions {positions.start}-{positions.stop - 1} "
        f"({len(set(reviewed_ids.values()))} distinct sentences), {len(verdicts)} withheld in this result; "
        f"ledger now {len(withheld)} withheld ({', '.join(f'{c} {n}' for c, n in by_code.items())}), "
        f"{len(kept)} kept; new records: {added['withheld']} withheld, {added['kept']} kept -> {args.ledger}"
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    examples = """Examples:
  .venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx "/path/to/master.docx"
  .venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx "/path/to/master.docx" --publish
  .venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx /private/master.docx \\
      --sources-db /tmp/sources-copy.db --out-dir /tmp/teacher-deck --table-deck /tmp/table-deck.json \\
      --frozen-keys /tmp/frozen-keys.json --pointer /tmp/pointer.json
"""
    parser = argparse.ArgumentParser(
        prog="teacher-deck",
        description=(
            "Teacher-table practice deck (Dev's example deck) maintenance.\n"
            "Use `refresh` whenever the teacher's master DOCX changes; do not hand-edit the generated files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples
        + "Related: docs/practice/teacher-deck-artifacts.md; scripts/audit/check_teacher_deck.py; #8843.\n",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    refresh_parser = sub.add_parser(
        "refresh",
        help="Ingest lessons, sync the table, rebuild + validate the deck, replace the published set.",
        description=(
            "Rebuild the whole teacher deck from the master DOCX and replace the published set together.\n"
            "Use after every new DOCX; a rerun with unchanged inputs is a byte-identical no-op."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples
        + """Outputs: writes lessons into --sources-db (private-teacher-lessons-a rows only); replaces --out-dir
  (manifest.json, frozen-keys.json, practice-deck.teacher.json, practice-cloze.teacher.json, coverage.json);
  rewrites --table-deck and --frozen-keys. Also writes --out-dir/lesson-sentence-review.json (local only, never
  packaged): every teacher-lesson cloze sentence with proper-noun / VESUM-unknown / digits-or-contact flags.
  --publish uploads lexicon-teacher-deck-<version>.json.gz to the GitHub release `atlas-teacher-deck` (skipped when that version already exists and is identical) and
  rewrites --pointer. Prints the document and input versions, added/removed/changed entries, merges, every
  teacher-lesson sentence that becomes public with the review flag counts, the teacher's aspect markers and the
  source-derived verb aspect counts, and the independent checker's matrix and residual lists.
Exit codes: 0 success or no-op; 1 validation/checker failure, refused shrink, or --publish refused while a served
  lesson sentence has no review record (nothing replaced);
  2 unreadable inputs or failed download/upload.
Related: docs/practice/teacher-deck-artifacts.md; scripts/audit/check_teacher_deck.py; #8843.
""",
    )
    add = refresh_parser.add_argument
    add("--docx", type=Path, required=True, help="Private master DOCX (e.g. /private/master.docx).")
    add("--heading", default=HEADING, help=f"Exact table heading (default: {HEADING!r}).")
    add(
        "--sources-db",
        type=Path,
        default=PROJECT_ROOT / "data/sources.db",
        help="sources.db receiving the lessons and supplying textbook sentences (default: data/sources.db).",
    )
    add("--skip-ingest", action="store_true", help="Do not write lessons into --sources-db (default: ingest).")
    add(
        "--atlas-db",
        type=Path,
        default=PROJECT_ROOT / "data/atlas.db",
        help="Word Atlas DB, opened read-only (default: data/atlas.db).",
    )
    add("--vesum-db", type=Path, default=PROJECT_ROOT / "data/vesum.db", help="VESUM DB (default: data/vesum.db).")
    add(
        "--withheld",
        type=Path,
        default=shard.DEFAULT_SENTENCE_REVIEWS,
        help=(
            "Language-review ledger of lesson sentences by SHA-256 (withheld with a code, or kept); "
            "withheld sentences are never served (default: site/src/data/lexicon-teacher-deck-withheld.json)."
        ),
    )
    add(
        "--synonym-verdicts",
        type=Path,
        default=PROJECT_ROOT / "registry/lexicon/synonym_pair_verdicts.yaml",
        help="Reviewed synonym/antonym verdicts (default: registry/lexicon/synonym_pair_verdicts.yaml).",
    )
    add(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Local published set directory, untracked (default: data/lexicon/teacher-deck).",
    )
    add(
        "--table-deck",
        type=Path,
        default=DEFAULT_SITE_DATA_PATH,
        help="Lemma-only special set JSON (default: site/src/data/lexicon-teacher-table-deck.json).",
    )
    add(
        "--frozen-keys",
        type=Path,
        default=DEFAULT_FROZEN_KEYS,
        help="Committed frozen key list (default: site/src/data/lexicon-teacher-deck-frozen-keys.json).",
    )
    add(
        "--pointer",
        type=Path,
        default=DEFAULT_POINTER,
        help="Committed release pointer (default: site/src/data/lexicon-teacher-deck.pointer.json).",
    )
    add(
        "--publish",
        action="store_true",
        help=(
            "Upload the set as a release asset and rewrite --pointer; refused while any served lesson sentence "
            "has no review record in --withheld (default: build locally only)."
        ),
    )
    add(
        "--repo",
        default=release.DEFAULT_REPO,
        help=f"GitHub OWNER/REPO for --publish (default: {release.DEFAULT_REPO}).",
    )
    add("--allow-shrink", action="store_true", help="Allow dropping previously published keys (default: refuse).")
    add("--report", type=Path, help="Optional JSON report path (default: none).")

    record = sub.add_parser(
        "record-review",
        help="Record a language review of lesson sentences in the committed ledger (hashes only).",
        description=(
            "Fold one language-review result into the sentence ledger: queue items at --positions are kept\n"
            "unless the results TSV withholds them. Use after reviewing lesson-sentence-review.json; then refresh."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.lexicon.teacher_deck record-review --queue /tmp/deck/lesson-sentence-review.json \\
      --cloze /tmp/deck/practice-cloze.teacher.json --results /tmp/withheld-part1.tsv --positions 0-774 \\
      --reviewer "gemini-3.8-flash-high (review-8843-lang-1)" --reviewed-at 2026-09-27
Inputs: --results is `clozeId<TAB>code` per withheld item (code ERR/AMBIG/FRAG/PRIV).
Outputs: rewrites --ledger (sorted, sentence hashes only) and prints the counts.
Exit codes: 0 recorded; 1 a result or queue item does not match the cloze file; 2 unreadable inputs.
Related: docs/practice/teacher-deck-artifacts.md; #8843.
""",
    )
    add = record.add_argument
    add("--queue", type=Path, required=True, help="Reviewed queue file (lesson-sentence-review.json).")
    add("--cloze", type=Path, required=True, help="The cloze file the queue was built with (resolves cloze ids).")
    add("--results", type=Path, required=True, help="Review result TSV: clozeId<TAB>code per withheld item.")
    add("--positions", help="0-based inclusive queue range the reviewer covered, e.g. 0-774 (default: all).")
    add("--reviewer", required=True, help="Reviewer model and task id, e.g. 'gemini-3.8-flash-high (review-...)'.")
    add("--reviewed-at", required=True, help="Review date, YYYY-MM-DD.")
    add(
        "--ledger",
        type=Path,
        default=shard.DEFAULT_SENTENCE_REVIEWS,
        help="Ledger to update (default: site/src/data/lexicon-teacher-deck-withheld.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return record_review(args) if args.command == "record-review" else refresh(args)
    except (RefreshError, shard.TeacherDeckBuildError, TeacherTableSyncError, release.PracticeDeckPublishError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, sqlite3.Error, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"error: cannot read inputs or reach the release ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
