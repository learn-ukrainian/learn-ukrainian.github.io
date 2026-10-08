#!/usr/bin/env python3
"""Foreground slovnyk.me builder: validated resume, atomic state, visible progress."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import signal
import time
from contextlib import ExitStack
from pathlib import Path

from scripts.lexicon import enrich_manifest as enrichment
from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_LOOKUP_SLUGS,
    MANIFEST,
    _atomic_slovnyk_json,
    _load_current_slovnyk_cache_file,
    _resolved_slovnyk_lookup,
    _reusable_slovnyk_cache,
    _slovnyk_cache,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
    _SlovnykCacheCollision,
)


def _cache_state(lemma: str) -> tuple[set[str], str | None]:
    """Validate published data every startup; a checkpoint alone proves nothing."""
    cache = _load_current_slovnyk_cache_file(_slovnyk_cache_path(lemma))
    lookup_word = _slovnyk_lookup_word(lemma)
    if not _reusable_slovnyk_cache(cache, lemma, lookup_word):
        return set(), None
    resolved = {slug for slug in _SLOVNYK_LOOKUP_SLUGS if _resolved_slovnyk_lookup(cache, slug, lookup_word)}
    digest = hashlib.sha256(json.dumps(cache, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return resolved, digest if len(resolved) == len(_SLOVNYK_LOOKUP_SLUGS) else None


def _is_fully_cached(lemma: str) -> bool:
    return _cache_state(lemma)[1] is not None


def _manifest_lemmas(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    if not isinstance(entries, list):
        raise ValueError("invalid entries")
    lemmas = []
    seen = set()
    for entry in entries:
        lemma = entry.get("lemma")
        if lemma is None or lemma == "":
            continue
        if not isinstance(lemma, str) or not lemma.strip():
            raise ValueError("invalid lemma")
        if lemma not in seen:
            seen.add(lemma)
            lemmas.append(lemma)
    return lemmas


def _read_checkpoint(path: Path, fingerprint: str, emit) -> dict[str, str]:
    """Reject unsupported/corrupt state; input drift requires fresh validation."""
    if not path.exists():
        emit("checkpoint=absent adoption=validate-cache")
        return {}
    state = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(state, dict)
        or state.get("version") != 1
        or not isinstance(state.get("completed"), dict)
        or not isinstance(state.get("fingerprint"), str)
        or any(not isinstance(k, str) or not isinstance(v, str) for k, v in state["completed"].items())
    ):
        raise ValueError("invalid checkpoint")
    if state["fingerprint"] != fingerprint:
        emit("checkpoint=input-changed adoption=validate-cache")
        return {}
    emit(f"checkpoint=loaded recorded_complete={len(state['completed'])} validation=required")
    return state["completed"]


def _interrupt(_signum, _frame) -> None:
    raise KeyboardInterrupt


def _run_mirror(args, checkpoint: Path, cache_dir: Path, emit) -> int:
    counts = dict.fromkeys(("fetched", "reused", "misses", "errors", "pending"), 0)
    lemmas = []
    completed = {}
    resolved = {}
    accounted = {}
    attempted = scanned = 0
    denominator = 0
    fingerprint = None
    status = "error"
    phase = "startup"
    in_flight_lemma = None
    interrupted_lemma = None
    start = time.monotonic()

    def progress(done, total):
        elapsed = time.monotonic() - start
        rate = done / elapsed if elapsed > 0 else 0.0
        remaining = total - done
        eta = f"{remaining / rate:.1f}s" if rate > 0 else ("0.0s" if remaining == 0 else "unknown")
        partial = sum(bool(rows) and lemma not in completed for lemma, rows in resolved.items())
        emit(
            f"phase={phase} [{done}/{total}] verified_complete={len(completed)}/{len(lemmas)} "
            f"attempted={attempted} partial={partial} "
            + " ".join(f"{key}={value}" for key, value in counts.items())
            + f" denominator={denominator} rate={rate:.3f}/s ETA={eta}"
        )

    def save():
        _atomic_slovnyk_json(checkpoint, {"version": 1, "fingerprint": fingerprint, "completed": completed})

    try:
        emit("phase=startup validation=starting total=unknown rate=unknown ETA=unknown")
        lemmas = _manifest_lemmas(args.manifest)
        denominator = len(lemmas) * len(_SLOVNYK_LOOKUP_SLUGS)
        counts["pending"] = denominator
        identities = {}
        for lemma in lemmas:
            path, identity = _slovnyk_cache_path(lemma), _slovnyk_lookup_word(lemma)
            if path in identities and identities[path] != identity:
                raise _SlovnykCacheCollision("cache filename collision between distinct lookup identities")
            identities[path] = identity
        selected = lemmas if args.limit is None else lemmas[: args.limit]
        fingerprint = hashlib.sha256(
            json.dumps(
                [lemmas, _SLOVNYK_LOOKUP_SLUGS, enrichment._SLOVNYK_CACHE_SCHEMA_VERSION, str(cache_dir)]
            ).encode()
        ).hexdigest()
        previous = _read_checkpoint(checkpoint, fingerprint, emit)
        emit(f"manifest lemmas={len(lemmas)} denominator={denominator} selected={len(selected)}")
        progress(0, len(lemmas))
        for scanned, lemma in enumerate(lemmas, 1):
            rows, digest = _cache_state(lemma)
            resolved[lemma] = rows
            counts["reused"] += len(rows)
            counts["pending"] -= len(rows)
            accounted.update({(lemma, slug): "reused" for slug in rows})
            if digest is not None:
                completed[lemma] = digest
            if lemma in previous and previous[lemma] != digest:
                emit(f"checkpoint=cache-changed index={scanned} required=retry-or-revalidate")
            if scanned % args.progress_every == 0 or scanned == len(lemmas):
                progress(scanned, len(lemmas))
        save()
        phase = "fetch"
        start = time.monotonic()
        todo = [lemma for lemma in selected if lemma not in completed]
        progress(0, len(todo))
        for lemma in todo:
            attempted += 1
            outcomes = {}
            missing = [slug for slug in _SLOVNYK_LOOKUP_SLUGS if slug not in resolved[lemma]]
            pre_call_rows, _ = _cache_state(lemma)
            in_flight_lemma = lemma
            _slovnyk_cache(lemma, outcomes=outcomes, slugs=missing)
            rows, digest = _cache_state(lemma)
            terminal = False
            for slug in missing:
                outcome = outcomes.get(slug)
                if outcome is None or outcome.status == "pending":
                    continue
                key = {"positive": "fetched", "reused": "reused", "not_found": "misses"}.get(outcome.status, "errors")
                unpublished = key != "errors" and slug not in rows
                if unpublished:
                    key = "errors"
                counts[key] += 1
                accounted[lemma, slug] = key
                counts["pending"] -= 1
                if outcome.status in {"blocked", "parse_error", "error"} or unpublished:
                    terminal = True
                    emit(f"STOP {outcome.status} HTTP={outcome.http_status}")
            resolved[lemma] = rows
            if digest is not None:
                completed[lemma] = digest
            if attempted % args.progress_every == 0 or attempted == len(todo) or terminal:
                # Data is already durable; absent checkpoint entries are safely adopted.
                save()
                progress(attempted, len(todo))
            in_flight_lemma = None
            if terminal:
                break
        status = (
            "complete"
            if len(completed) == len(lemmas) and not counts["errors"] and not counts["pending"]
            else "incomplete"
        )
        if status == "incomplete" and args.limit is not None and len(selected) < len(lemmas):
            status = "limited"
    except KeyboardInterrupt:
        interrupted_lemma = in_flight_lemma
        status = "interrupted"
    except _SlovnykCacheCollision:
        emit("ERROR reason=cache-filename-collision action=resolve-distinct-lookup-identities-before-retry")
        status = "error"
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        emit("ERROR invalid input/checkpoint or storage/publication failure")
        status = "error"
    finally:
        # Never publish a partly scanned completion map over an existing checkpoint.
        if fingerprint is not None and scanned == len(lemmas) and phase == "fetch":
            try:
                completed.clear()
                for lemma in lemmas:
                    rows, digest = _cache_state(lemma)
                    for slug in rows:
                        key = accounted.get((lemma, slug), "pending")
                        if key in {"pending", "errors"}:
                            outcome = outcomes.get(slug) if lemma == interrupted_lemma else None
                            outcome_status = getattr(outcome, "status", None)
                            if (
                                outcome_status is None
                                and lemma == interrupted_lemma
                                and slug in missing
                                and slug not in pre_call_rows
                            ):
                                cache = _load_current_slovnyk_cache_file(_slovnyk_cache_path(lemma))
                                lookup_word = _slovnyk_lookup_word(lemma)
                                if _reusable_slovnyk_cache(cache, lemma, lookup_word) and _resolved_slovnyk_lookup(
                                    cache, slug, lookup_word
                                ):
                                    outcome_status = "not_found" if slug in cache.get("not_found", {}) else "positive"
                            key = {
                                "positive": "fetched",
                                "reused": "reused",
                                "not_found": "misses",
                            }.get(outcome_status, "reused")
                            accounted_key = accounted.get((lemma, slug), "pending")
                            counts[accounted_key] -= 1
                            counts[key] += 1
                            accounted[lemma, slug] = key
                    for slug in resolved[lemma] - rows:
                        key = accounted.get((lemma, slug), "pending")
                        if key != "errors":
                            counts[key] -= 1
                            counts["errors"] += 1
                            accounted[lemma, slug] = "errors"
                    resolved[lemma] = rows
                    if digest is not None:
                        completed[lemma] = digest
                if status == "complete" and (len(completed) != len(lemmas) or counts["errors"]):
                    status = "incomplete"
                elif status in {"incomplete", "limited"} and len(completed) == len(lemmas) and not counts["errors"]:
                    status = "complete"
                save()
            except (OSError, ValueError, TypeError):
                emit("ERROR checkpoint publication failed; published cache remains resumable")
                status = "error"
        emit(
            "RESULT "
            + " ".join(f"{key}={value}" for key, value in counts.items())
            + f" denominator={denominator} status={status} verified_complete={len(completed)}/{len(lemmas)} "
            + f"attempted={attempted} scanned={scanned} elapsed={time.monotonic() - start:.1f}s"
        )
    return 130 if status == "interrupted" else (0 if status == "complete" else 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Populate the foreground per-lemma slovnyk.me cache with validated resume.\n"
        "Use for the single shared-cache writer; isolated dictionary jobs use dictionary_acquisition.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json --limit 5
  .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json
Outputs: per-lookup JSON and non-JSON-named .mirror-checkpoint in LEXICON_SLOVNYK_CACHE;
flushed stdout plus repo-root batch_state/slovnyk-mirror/<target-digest>.log (default).
Exit codes: 0 verified complete (including empty); 1 incomplete/limited/storage/access/parse failure;
2 usage error; 130 interrupted. First access or parse stop preserves partial results.
Legacy nulls are retried; observed 404 evidence and current validated positives resume durably.
Same-cache or same-checkpoint concurrent mirror writers are refused; lock files must remain in place.
Related: docs/runbooks/slovnyk-mirror.md; scripts.ingest.dictionary_acquisition; #10131.
""",
    )
    parser.add_argument(
        "--manifest", type=Path, default=MANIFEST, help="Manifest JSON, e.g. manifest.json (default: Atlas manifest)."
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap selected lemmas, e.g. 5 (default: all); remainder stays pending."
    )
    parser.add_argument(
        "--progress-every", type=int, default=25, help="Validation/fetch log cadence in lemmas (default: 25), e.g. 10."
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="State JSON, e.g. state.json (default: cache/.mirror-checkpoint, outside *.json glob).",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Append progress log, e.g. mirror.log (default: repo-root batch_state/slovnyk-mirror/<target-digest>.log).",
    )
    args = parser.parse_args(argv)
    if args.progress_every < 1 or (args.limit is not None and args.limit < 0):
        parser.error("limit must be nonnegative and progress-every positive")
    cache_dir = _slovnyk_cache_path("mirror-target").parent.resolve()
    checkpoint = (args.checkpoint or cache_dir / ".mirror-checkpoint").resolve()
    target = hashlib.sha256(str(cache_dir).encode()).hexdigest()[:16]
    log_path = args.log_file or enrichment.ROOT / "batch_state/slovnyk-mirror" / f"{target}.log"
    lock_paths = {cache_dir / ".mirror.lock", checkpoint.with_suffix(checkpoint.suffix + ".lock")}
    if log_path.resolve() in {args.manifest.resolve(), checkpoint, *lock_paths} or checkpoint in {
        args.manifest.resolve(),
        cache_dir / ".mirror.lock",
    }:
        parser.error("manifest, checkpoint, log and lock destinations must differ")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log, ExitStack() as stack:

            def emit(line):
                print(line, flush=True)
                log.write(line + "\n")
                log.flush()
                os.fsync(log.fileno())

            for lock_path in sorted(lock_paths):
                lock_path.parent.mkdir(parents=True, exist_ok=True)
                handle = stack.enter_context(lock_path.open("a"))
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    emit("RESULT status=refused reason=active-writer verified_complete=unknown")
                    return 1
            previous_signal = signal.signal(signal.SIGTERM, _interrupt)
            try:
                return _run_mirror(args, checkpoint, cache_dir, emit)
            finally:
                signal.signal(signal.SIGTERM, previous_signal)
    except (OSError, ValueError):
        print("RESULT status=error reason=log-or-lock-storage-failure verified_complete=unknown", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
