"""Build module evidence packs from request files.

Input is a request file of locators and ids; every Ukrainian string in the pack
is a byte-for-byte copy of a source row. The builder copies; it never writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.verification import stress

from . import codes, lock, sources

REPO_ROOT = Path(__file__).resolve().parents[3]


def get_mcp_commit(repo_root: Path = REPO_ROOT) -> str:
    """Retrieve the 40-hex commit hash of HEAD for built_with."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and len(proc.stdout.strip()) == 40:
            return proc.stdout.strip()
    except Exception:
        pass
    return "0000000000000000000000000000000000000000"


def load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = REPO_ROOT / "schemas" / schema_name
    return json.loads(schema_path.read_text(encoding="utf-8"))


def collapse_with_indices(text: str) -> tuple[str, list[int]]:
    """Collapse runs of whitespace and record mapping back to original text character indices."""
    norm = sources.normalize_spelling(text)
    collapsed_chars: list[str] = []
    orig_indices: list[int] = []
    i = 0
    n = len(norm)
    while i < n and norm[i].isspace():
        i += 1
    while i < n:
        if norm[i].isspace():
            ws_start = i
            while i < n and norm[i].isspace():
                i += 1
            if i < n:
                collapsed_chars.append(" ")
                orig_indices.append(ws_start)
        else:
            collapsed_chars.append(norm[i])
            orig_indices.append(i)
            i += 1
    return "".join(collapsed_chars), orig_indices


def extract_span(chunk_text: str, first_words: str, last_words: str, record_id: str, chunk_id: str | int) -> str:
    """Extract substring from original chunk text between first_words and last_words inclusive."""
    norm_first = " ".join(sources.normalize_spelling(first_words).split())
    norm_last = " ".join(sources.normalize_spelling(last_words).split())
    collapsed, orig_indices = collapse_with_indices(chunk_text)

    # 1. Find occurrences of first_words
    first_matches: list[int] = []
    start = 0
    while True:
        pos = collapsed.find(norm_first, start)
        if pos == -1:
            break
        first_matches.append(pos)
        start = pos + 1

    if len(first_matches) == 0:
        raise ValueError(
            f"{codes.SPAN_MISMATCH}: id {record_id} chunk {chunk_id}: first_words matched 0 times: {first_words!r}"
        )
    if len(first_matches) > 1:
        raise ValueError(
            f"{codes.SPAN_MISMATCH}: id {record_id} chunk {chunk_id}: first_words matched {len(first_matches)} times: {first_words!r}"
        )

    first_pos = first_matches[0]

    # 2. Find occurrences of last_words after first_words
    last_matches: list[int] = []
    if norm_first == norm_last:
        last_matches.append(first_pos)
    else:
        start = first_pos + 1
        while True:
            pos = collapsed.find(norm_last, start)
            if pos == -1:
                break
            if pos + len(norm_last) >= first_pos + len(norm_first):
                last_matches.append(pos)
            start = pos + 1

    if len(last_matches) == 0:
        raise ValueError(
            f"{codes.SPAN_MISMATCH}: id {record_id} chunk {chunk_id}: last_words matched 0 times after first_words: {last_words!r}"
        )
    if len(last_matches) > 1:
        raise ValueError(
            f"{codes.SPAN_MISMATCH}: id {record_id} chunk {chunk_id}: last_words matched {len(last_matches)} times after first_words: {last_words!r}"
        )

    last_pos = last_matches[0]
    orig_start = orig_indices[first_pos]
    orig_end = orig_indices[last_pos + len(norm_last) - 1]
    return chunk_text[orig_start : orig_end + 1]


def build_pack(
    level: str,
    slug: str,
    request_path: Path,
    *,
    evidence_dir: Path | None = None,
    plans_dir: Path | None = None,
    sources_instance: sources.Sources | None = None,
    standard_path: Path | None = None,
    offline: bool = False,
    dry_run: bool = False,
    stamp: bool = False,
    report: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Build a module evidence pack from a request YAML."""
    request_path = Path(request_path)
    if not request_path.is_file():
        raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: request file not found at {request_path}")

    try:
        request_raw = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{codes.INVALID_REQUEST}: failed to parse request YAML: {exc}") from exc

    if not isinstance(request_raw, dict):
        raise ValueError(f"{codes.INVALID_REQUEST}: request must be a mapping, got {type(request_raw).__name__}")

    # Validate against request schema
    req_schema = load_schema("evidence-pack-request-v1.schema.json")
    req_validator = Draft202012Validator(req_schema)
    errors = list(req_validator.iter_errors(request_raw))
    if errors:
        details = "; ".join(e.message for e in errors)
        raise ValueError(f"{codes.INVALID_REQUEST}: request schema validation failed: {details}")

    expected_module = f"{level}/{slug}"
    actual_module = request_raw.get("module")
    if actual_module != expected_module:
        raise ValueError(
            f"{codes.INVALID_REQUEST}: request module {actual_module!r} does not match target {expected_module!r}"
        )

    evidence_base = (
        Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / "curriculum/l2-uk-en/evidence" / level
    )
    pack_path = evidence_base / f"{slug}.yaml"

    # Rule 7: Check previous build for dropped unsupported records
    if pack_path.is_file():
        try:
            prev_doc = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
            if isinstance(prev_doc, dict):
                prev_u_ids = {u["id"] for u in prev_doc.get("unsupported", []) if isinstance(u, dict) and "id" in u}
                new_u_ids = {u["id"] for u in request_raw.get("unsupported", []) if isinstance(u, dict) and "id" in u}
                dropped = prev_u_ids - new_u_ids
                if dropped:
                    raise ValueError(
                        f"{codes.UNSUPPORTED_DROPPED}: unsupported ids dropped from previous build: {sorted(dropped)}"
                    )
        except (ValueError, FileNotFoundError):
            raise
        except Exception:
            pass

    owns_sources = False
    if sources_instance is None:
        sources_instance = sources.Sources(standard_path=standard_path, report=report)
        owns_sources = True

    try:
        # 1. Texts
        texts_out: list[dict[str, Any]] = []
        raw_texts = request_raw.get("texts", [])
        for idx, t in enumerate(raw_texts, 1):
            chunk_id = t["source"]["chunk_id"]
            chunk = sources_instance.get_textbook_chunk(chunk_id)
            if chunk is None:
                raise ValueError(
                    f"{codes.SOURCE_UNAVAILABLE}: textbook chunk {chunk_id!r} not found for text {t['id']}"
                )
            quote = extract_span(chunk["text"], t["span"]["first_words"], t["span"]["last_words"], t["id"], chunk_id)
            sha256 = hashlib.sha256(quote.encode("utf-8")).hexdigest()
            texts_out.append(
                {
                    "id": t["id"],
                    "source": {
                        "kind": "textbook",
                        "file": chunk["source_file"],
                        "grade": chunk.get("grade"),
                        "author": chunk.get("author"),
                        "section_id": chunk.get("parent_section_id"),
                        "page": chunk.get("page"),
                        "chunk_id": chunk["chunk_id"],
                    },
                    "quote": quote,
                    "sha256": sha256,
                    "supports": t["supports"],
                }
            )
            if report:
                report(f"texts: {idx}/{len(raw_texts)}")

        # 2. Exercises
        exercises_out: list[dict[str, Any]] = []
        raw_exercises = request_raw.get("exercises", [])
        for idx, x in enumerate(raw_exercises, 1):
            chunk_id = x["source"]["chunk_id"]
            chunk = sources_instance.get_textbook_chunk(chunk_id)
            if chunk is None:
                raise ValueError(
                    f"{codes.SOURCE_UNAVAILABLE}: textbook chunk {chunk_id!r} not found for exercise {x['id']}"
                )
            quote = extract_span(chunk["text"], x["span"]["first_words"], x["span"]["last_words"], x["id"], chunk_id)
            sha256 = hashlib.sha256(quote.encode("utf-8")).hexdigest()
            exercises_out.append(
                {
                    "id": x["id"],
                    "source": {
                        "kind": "textbook",
                        "file": chunk["source_file"],
                        "grade": chunk.get("grade"),
                        "author": chunk.get("author"),
                        "section_id": chunk.get("parent_section_id"),
                        "page": chunk.get("page"),
                        "chunk_id": chunk["chunk_id"],
                    },
                    "quote": quote,
                    "sha256": sha256,
                    "pattern": x["pattern"],
                    "items_sample": [quote],
                }
            )
            if report:
                report(f"exercises: {idx}/{len(raw_exercises)}")

        # 3. Examples
        examples_out: list[dict[str, Any]] = []
        raw_examples = request_raw.get("examples", [])
        if raw_examples:
            # Word store check: load _words.yaml
            words_store_path = evidence_base / "_words.yaml"
            if not words_store_path.is_file():
                raise ValueError(
                    f"{codes.SOURCE_UNAVAILABLE}: level word store missing at {words_store_path} for examples"
                )
            words_store = yaml.safe_load(words_store_path.read_text(encoding="utf-8"))
            known_word_ids = {w["id"] for w in words_store.get("words", []) if isinstance(w, dict) and "id" in w}

            for idx, ex in enumerate(raw_examples, 1):
                chunk_id = ex["source"]["chunk_id"]
                table = ex["source"]["table"]
                if table == "textbooks":
                    chunk = sources_instance.get_textbook_chunk(chunk_id)
                    if chunk is None:
                        raise ValueError(
                            f"{codes.SOURCE_UNAVAILABLE}: textbook chunk {chunk_id!r} not found for example {ex['id']}"
                        )
                    source_dict = {
                        "kind": "textbook",
                        "file": chunk["source_file"],
                        "grade": chunk.get("grade"),
                        "author": chunk.get("author"),
                        "section_id": chunk.get("parent_section_id"),
                        "page": chunk.get("page"),
                        "chunk_id": chunk["chunk_id"],
                    }
                elif table == "literary_texts":
                    chunk = sources_instance.get_literary_chunk(chunk_id)
                    if chunk is None:
                        raise ValueError(
                            f"{codes.SOURCE_UNAVAILABLE}: literary chunk {chunk_id!r} not found for example {ex['id']}"
                        )
                    source_dict = {
                        "kind": "literary",
                        "file": chunk["source_file"],
                        "author": chunk.get("author"),
                        "work": chunk.get("work"),
                        "year": chunk.get("year"),
                        "page": None,
                        "chunk_id": chunk["chunk_id"],
                    }
                else:
                    raise ValueError(
                        f"{codes.INVALID_REQUEST}: unexpected source table {table!r} in example {ex['id']}"
                    )

                quote = extract_span(
                    chunk["text"], ex["span"]["first_words"], ex["span"]["last_words"], ex["id"], chunk_id
                )
                sha256 = hashlib.sha256(quote.encode("utf-8")).hexdigest()

                # Verify each word id exists in the level word store
                for wid in ex["words"]:
                    if wid not in known_word_ids:
                        raise ValueError(
                            f"{codes.UNRESOLVED_CITED}: word id {wid!r} cited in example {ex['id']} not in word store"
                        )

                rec = {
                    "id": ex["id"],
                    "source": source_dict,
                    "text": quote,
                    "sha256": sha256,
                    "sentence_ref": {"words": list(ex["words"])},
                }
                examples_out.append(rec)
                if report:
                    report(f"examples: {idx}/{len(raw_examples)}")

        # 4. Errors
        errors_out: list[dict[str, Any]] = []
        raw_errors = request_raw.get("errors", [])
        for idx, err_req in enumerate(raw_errors, 1):
            src_req = err_req["source"]
            matches = sources_instance.find_ua_gec_error(src_req["error"], src_req["correct"])
            if len(matches) == 0:
                raise ValueError(
                    f"{codes.INVALID_REQUEST}: error pair not found in ua_gec_errors for {err_req['id']}: error={src_req['error']!r}, correct={src_req['correct']!r}"
                )
            if len(matches) > 1:
                raise ValueError(
                    f"{codes.INVALID_REQUEST}: error pair matched {len(matches)} rows in ua_gec_errors for {err_req['id']}: error={src_req['error']!r}, correct={src_req['correct']!r}"
                )
            row = matches[0]
            errors_out.append(
                {
                    "id": err_req["id"],
                    "source": {"table": "ua_gec_errors", "id": row["id"]},
                    "incorrect": row["error"],
                    "correct": row["correct"],
                    "error_type": row["error_type"],
                    "pattern": err_req["pattern"],
                }
            )
            if report:
                report(f"errors: {idx}/{len(raw_errors)}")

        # 4b. Notes
        notes_out: list[dict[str, Any]] = []
        raw_notes = request_raw.get("notes", [])
        for idx, n in enumerate(raw_notes, 1):
            note_id = n["source"]["id"]
            row = sources_instance.get_style_guide_entry(note_id)
            if row is None:
                raise ValueError(
                    f"{codes.SOURCE_UNAVAILABLE}: style_guide entry id {note_id} not found for note {n['id']}"
                )
            notes_out.append(
                {
                    "id": n["id"],
                    "source": {"table": "style_guide", "id": row["id"]},
                    "word": row["word"],
                    "section": row.get("section"),
                    "text": row["text"],
                    "excerpt_full": row.get("excerpt_full") or None,
                    "russianism_pattern": row.get("russianism_pattern") or None,
                }
            )
            if report:
                report(f"notes: {idx}/{len(raw_notes)}")

        # 5. Videos
        videos_out: list[dict[str, Any]] = []
        raw_videos = request_raw.get("videos", [])
        for idx, v in enumerate(raw_videos, 1):
            checked = None
            if not offline:
                checked = sources_instance.check_url(v["url"], timeout=10.0)
            videos_out.append(
                {
                    "id": v["id"],
                    "url": v["url"],
                    "channel": v["channel"],
                    "use": v["use"],
                    "checked": checked,
                }
            )
            if report:
                report(f"videos: {idx}/{len(raw_videos)}")

        # 6. Standard
        standard_out: list[dict[str, Any]] = []
        raw_standard = request_raw.get("standard", [])
        for idx, s in enumerate(raw_standard, 1):
            lines_str = s["lines"]
            start_str, end_str = lines_str.split("-")
            start_line = int(start_str)
            end_line = int(end_str)
            text, file_sha256 = sources_instance.get_standard_lines(start_line, end_line)
            standard_out.append(
                {
                    "id": s["id"],
                    "lines": lines_str,
                    "text": text,
                    "file_sha256": file_sha256,
                }
            )
            if report:
                report(f"standard: {idx}/{len(raw_standard)}")

        # 7. Unsupported
        unsupported_out: list[dict[str, Any]] = []
        raw_unsupported = request_raw.get("unsupported", [])
        for idx, u in enumerate(raw_unsupported, 1):
            rec = {
                "id": u["id"],
                "claim": u["claim"],
                "searches": u["searches"],
                "status": "resolved" if "resolved_by" in u else "open",
            }
            if "resolved_by" in u:
                rec["resolved_by"] = u["resolved_by"]
            unsupported_out.append(rec)
            if report:
                report(f"unsupported: {idx}/{len(raw_unsupported)}")

        # 8. built_with
        sources_db_hash = sources_instance._fingerprint(sources_instance.sources_db)[0]
        vesum_hash = sources_instance._vesum_identity()[0]
        commit_sha = get_mcp_commit()
        trie_hash = stress.source_info()["digest"]
        try:
            standard_sha = sources_instance.get_standard_file_hash()
        except Exception:
            standard_sha = "0" * 64

        built_with: dict[str, Any] = {
            "mcp_commit": commit_sha,
            "sources_db": sources_db_hash,
            "vesum": vesum_hash,
            "trie": trie_hash,
            "ulif_forms": "pending",
            "standard_sha256": standard_sha,
        }
        if stress.STRESS_OVERRIDES_PATH.exists():
            built_with["overrides_sha256"] = sources._file_hash(stress.STRESS_OVERRIDES_PATH)
        else:
            built_with["overrides_sha256"] = None

        ru_batch = sources_instance.russian_patterns([])
        built_with["russian_patterns"] = ru_batch.content_hash

        if stamp:
            built_with["built_at"] = datetime.now(UTC).isoformat()

        # Assemble pack document
        pack_doc: dict[str, Any] = {
            "evidence_schema": 1,
            "module": expected_module,
            "built_with": built_with,
        }
        if texts_out:
            pack_doc["texts"] = texts_out
        if exercises_out:
            pack_doc["exercises"] = exercises_out
        if examples_out:
            pack_doc["examples"] = examples_out
        if errors_out:
            pack_doc["errors"] = errors_out
        if notes_out:
            pack_doc["notes"] = notes_out
        if videos_out:
            pack_doc["videos"] = videos_out
        if standard_out:
            pack_doc["standard"] = standard_out
        if unsupported_out:
            pack_doc["unsupported"] = unsupported_out

        # Validate pack against schema
        pack_schema = load_schema("evidence-pack-v1.schema.json")
        validator = Draft202012Validator(pack_schema)
        val_errors = list(validator.iter_errors(pack_doc))
        if val_errors:
            details = "; ".join(e.message for e in val_errors)
            raise ValueError(f"{codes.FORM_MISMATCH}: built pack failed schema validation: {details}")

        # Check for forbidden words field (rule 8)
        if "words" in pack_doc:
            raise ValueError(f"{codes.WORDS_FIELD_FORBIDDEN}: pack contains forbidden 'words' field")

        pack_lock_digest = ""
        if not dry_run:
            pack_lock_digest = lock.write(pack_path, lock.yaml_bytes(pack_doc))

        open_unsupported_count = sum(1 for u in unsupported_out if u.get("status") == "open")

        return {
            "status": "ok",
            "level": level,
            "slug": slug,
            "module": expected_module,
            "dry_run": dry_run,
            "offline": offline,
            "pack_path": str(pack_path),
            "pack_lock": pack_lock_digest,
            "texts_count": len(texts_out),
            "exercises_count": len(exercises_out),
            "examples_count": len(examples_out),
            "errors_count": len(errors_out),
            "notes_count": len(notes_out),
            "videos_count": len(videos_out),
            "standard_count": len(standard_out),
            "unsupported_open_count": open_unsupported_count,
            "unsupported_resolved_count": len(unsupported_out) - open_unsupported_count,
            "pack": pack_doc,
        }
    finally:
        if owns_sources:
            sources_instance.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.evidence build-pack",
        description=(
            "Build a module evidence pack (<slug>.yaml) from a request YAML.\n"
            "Grounds all module texts, exercises, examples, errors, videos, and standard lines in sources."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-pack a1 alphabet --request req.yaml\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-pack a1 alphabet --request req.yaml --offline\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-pack a1 alphabet --request req.yaml --dry-run\n"
            "  .venv/bin/python -m scripts.curriculum.evidence build-pack a1 alphabet --request req.yaml --json\n\n"
            "Outputs:\n"
            "  curriculum/l2-uk-en/evidence/<level>/<slug>.yaml (+ .lock)\n\n"
            "Exit codes:\n"
            "  0: Build succeeded or dry-run complete without error\n"
            "  1: Request invalid, schema validation failed, or source unavailable\n\n"
            "Outcome Codes:\n"
            f"{codes.help_text()}\n"
        ),
    )
    parser.add_argument("level", help="Target curriculum level slug (e.g. 'a1', 'a2')")
    parser.add_argument("slug", help="Target module slug (e.g. 'alphabet', 'introductions')")
    parser.add_argument("--request", required=True, type=Path, help="Path to input request YAML file")
    parser.add_argument("--offline", action="store_true", help="Do not check video URLs over network")
    parser.add_argument("--dry-run", action="store_true", help="Compute evidence pack without writing files")
    parser.add_argument(
        "--stamp", action="store_true", help="Include built_at timestamp in built_with (breaks build determinism)"
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result to stdout")
    parser.add_argument("--evidence-dir", type=Path, default=None, help="Override evidence output directory")
    parser.add_argument("--plans-dir", type=Path, default=None, help="Override lesson plans directory")
    parser.add_argument(
        "--sources-db", type=Path, default=None, help="Override sources database path (default: data/sources.db)"
    )
    parser.add_argument("--vesum-db", type=Path, default=None, help="Override VESUM database path")
    parser.add_argument("--standard-path", type=Path, default=None, help="Override State Standard file path")

    args = parser.parse_args(argv)

    report = lambda msg: print(f"progress: {msg}", file=sys.stderr)  # noqa: E731
    explicit_sources = None
    if args.sources_db is not None or args.vesum_db is not None or args.standard_path is not None:
        explicit_sources = sources.Sources(
            sources_db=args.sources_db,
            vesum_db=args.vesum_db,
            standard_path=args.standard_path,
            report=report,
        )

    try:
        result = build_pack(
            args.level,
            args.slug,
            args.request,
            evidence_dir=args.evidence_dir,
            plans_dir=args.plans_dir,
            sources_instance=explicit_sources,
            standard_path=args.standard_path,
            offline=args.offline,
            dry_run=args.dry_run,
            stamp=args.stamp,
            report=report,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if explicit_sources is not None:
            explicit_sources.close()

    if args.json:
        output = dict(result)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"Evidence Pack Build: module={result['module']} (dry-run: {result['dry_run']})")
        print(
            f"Counts: texts={result['texts_count']}, exercises={result['exercises_count']}, "
            f"examples={result['examples_count']}, errors={result['errors_count']}, "
            f"notes={result['notes_count']}, videos={result['videos_count']}, "
            f"standard={result['standard_count']}"
        )
        print(f"Unsupported: {result['unsupported_open_count']} open, {result['unsupported_resolved_count']} resolved")
        if not result["dry_run"]:
            print(f"Pack written: {result['pack_path']} (lock: {result['pack_lock'][:16]}...)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
