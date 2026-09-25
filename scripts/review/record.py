"""Record a review attempt (#8430 r4, R2b-A): validate a return, then write everything that follows from it.

``python -m scripts.review.record <review.yaml> --manifest ... --lesson ... --ledger ...
--task-id ...`` runs the active validator in-process (``validate_review``; nothing of its
rejections is re-implemented), then:

1. copies the raw return to ``lesson-<n>.review.<attempt_id>.yaml`` (a plan review:
   ``plan-review.<attempt_id>.yaml``) in the module's ``_state`` directory. ``record`` owns that file;
2. **accepted** — writes the verdict file the landing reads (``lesson-<n>.verdict.yaml``, a plan:
   ``plan-review.yaml``, holding ``verdict``, ``attempt_id``, ``manifest_sha256``, ``validated_at``),
   the ``attempts`` row and one ``findings`` row per finding, one settle item per active
   ``unsupported_by_source`` finding, and counts a REVISE round;
3. **rejected** — writes the saved return and an ``attempts`` row (``verdict: REJECTED`` with the
   validator's codes), nothing else. Count it as a failed review with ``--failure``;
4. ``--failure <reason>`` records a review that returned nothing (or a rejected return): an
   ``attempts`` row and one more ``budgets.review_failures``.

Identities are trusted, not self-reported: the reviewer's model and harness come from the dispatch
record (``batch_state/tasks/<task-id>.json``), its family from the closeout resolver
(``scripts.review.reviewer_resolver.resolve_author_family``), the writer's family from
``lesson-<n>.writer.yaml`` through the same resolver. An unknown model or family fails closed.

A lesson attempt is also refused as **stale** when any file its manifest pins (found structurally,
``scripts.build.fresh.manifest.changed_inputs``) has changed since the manifest was written.
An attempt recorded with ``--seed-id`` (a seeded lesson, R3) is kept apart: it never writes a verdict
file, a budget or a settle item, and the fix loop never reads it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh import plan_manifest as pm
from scripts.build.fresh.manifest import changed_inputs
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lock
from scripts.review import findings_db, fixloop, second_seat
from scripts.review.validate.validate import validate_review

REPO_ROOT = Path(__file__).resolve().parents[2]
TREE = "curriculum/l2-uk-en"
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")

# record's own rejection codes, beside the validator's (scripts/review/validate/codes.py).
MANIFEST_INPUTS_STALE = "manifest_inputs_stale"
ATTEMPT_IDENTITY_MISMATCH = "attempt_identity_mismatch"


class RecordError(Exception):
    """Nothing could be recorded (unknown identity, unusable manifest, an attempt recorded twice)."""


@dataclass
class Outcome:
    accepted: bool
    verdict: str
    review_id: str
    attempt_id: str
    kind: str
    findings: int = 0
    rejection_codes: list[str] = field(default_factory=list)
    settle_items: list[int] = field(default_factory=list)
    agreement: dict[str, Any] | None = None
    verdict_file: str | None = None
    saved_return: str | None = None
    terminal: list[dict[str, Any]] = field(default_factory=list)
    replay: bool = False
    seed_id: str | None = None
    next: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if value not in (None, [], False) or key in ("accepted", "findings")
        }


# --- identity ---------------------------------------------------------------------------


def resolve_reviewer_identity(task_id: str, tasks_dir: Path) -> dict[str, str]:
    """The reviewer's ``model``, ``harness`` and ``family`` from the dispatch record; RecordError when unknown."""
    if not TOKEN_RE.fullmatch(task_id):
        raise RecordError(f"task id {task_id!r} is not a task token")
    path = Path(tasks_dir) / f"{task_id}.json"
    try:
        task = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RecordError(
            f"the dispatch record {path} is unreadable ({error}); the reviewer's identity is unknown"
        ) from error
    if not isinstance(task, dict):
        raise RecordError(f"the dispatch record {path} is not an object")
    harness = task.get("agent")
    if not isinstance(harness, str) or not harness.strip():
        raise RecordError(f"the dispatch record {task_id} names no harness")
    if harness == "cursor":  # a multi-model harness: only a concrete, attested model counts
        model = task.get("resolved_model") if task.get("resolved_model_known") is True else None
        identifier = f"cursor:{model}" if model else None
    else:
        model = task.get("model")
        identifier = model
    if not isinstance(model, str) or not model.strip() or identifier is None:
        raise RecordError(f"the dispatch record {task_id} names no attested model")
    try:
        family = second_seat.concrete_family(identifier, what=f"dispatch record {task_id}")
    except second_seat.IdentityError as error:
        raise RecordError(str(error)) from error
    return {"model": model.strip(), "harness": harness.strip(), "family": family}


# --- files ------------------------------------------------------------------------------


def _load_yaml_bytes(data: bytes) -> Any:
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError:
        return None


def _guarded(root: Path, path: Path) -> Path:
    return checked_existing_path(root, path, f"{TREE}/evidence")


def _save_return(root: Path, directory: Path, name: str, data: bytes) -> Path:
    """Copy the raw return (0o644); a different return already saved under this attempt id is refused."""
    target = _guarded(root, directory / name)
    if target.exists():
        if target.read_bytes() != data:
            raise RecordError(f"{name} already holds a different return for this attempt")
        return target
    lock.atomic_write(target, data)
    return target


def _write_verdict_file(
    root: Path, directory: Path, name: str, verdict: str, attempt_id: str, manifest: str, validated_at: str
) -> Path:
    document = {"verdict": verdict, "attempt_id": attempt_id, "manifest_sha256": manifest, "validated_at": validated_at}
    target = _guarded(root, directory / name)
    lock.atomic_write(target, lock.yaml_bytes(document))
    return target


# --- the manifest -----------------------------------------------------------------------


def _load_manifest(manifest_path: Path) -> tuple[dict[str, Any], str]:
    try:
        data = Path(manifest_path).read_bytes()
    except OSError as error:
        raise RecordError(f"the manifest {manifest_path} is unreadable: {error}") from error
    manifest = _load_yaml_bytes(data)
    if not isinstance(manifest, dict) or manifest.get("kind") not in ("plan", "lesson"):
        raise RecordError(f"{manifest_path} is not a plan or lesson review manifest")
    if not isinstance(manifest.get("level"), str) or not isinstance(manifest.get("slug"), str):
        raise RecordError(f"{manifest_path} names no level and slug")
    if manifest["kind"] == "lesson" and not isinstance(manifest.get("lesson"), int):
        raise RecordError(f"{manifest_path} names no lesson number")
    return manifest, hashlib.sha256(data).hexdigest()


def _stale_message(root: Path, manifest: dict[str, Any]) -> str | None:
    """A lesson manifest's changed pins, as one message; None when every pinned file is unchanged."""
    changed = changed_inputs(manifest, root)
    if not changed:
        return None
    return "; ".join(
        f"{item['input']} ({item['entry']['path']}) {'is gone' if item['current_sha256'] is None else 'changed'}"
        for item in changed
    )


# --- recording --------------------------------------------------------------------------


def record_return(
    review_path: Path | None,
    *,
    manifest_path: Path,
    ledger_path: Path | None = None,
    task_id: str,
    document_path: Path | None = None,
    previous_ledger_path: Path | None = None,
    repo_root: Path | None = None,
    db_path: Path | None = None,
    tasks_dir: Path | None = None,
    review_id: str | None = None,
    attempt_id: str | None = None,
    seed_id: str | None = None,
    second: bool = False,
    failure: str | None = None,
    now: str | None = None,
) -> Outcome:
    """Record one attempt (a return, or with ``failure`` a review that returned none). See the module docstring."""
    root = Path(repo_root if repo_root is not None else REPO_ROOT).resolve()
    manifest, manifest_sha = _load_manifest(manifest_path)
    kind, level, slug = manifest["kind"], manifest["level"], manifest["slug"]
    lesson_n = manifest["lesson"] if kind == "lesson" else None
    directory = fixloop.state_dir(root, level, slug)
    moment = now or findings_db.now_iso()

    data = b""
    echoed: dict[str, Any] = {}
    if failure is None:
        if review_path is None or ledger_path is None:
            raise RecordError("a review return needs the review file and --ledger")
        data = Path(review_path).read_bytes()
        loaded = _load_yaml_bytes(data)
        attempt_block = loaded.get("attempt") if isinstance(loaded, dict) else None
        echoed = attempt_block if isinstance(attempt_block, dict) else {}
    ids = {"review_id": review_id or echoed.get("review_id"), "attempt_id": attempt_id or echoed.get("attempt_id")}
    for name, value in ids.items():
        if not isinstance(value, str) or not TOKEN_RE.fullmatch(value):
            raise RecordError(f"{name} is missing or not a safe token: pass --{name.replace('_', '-')}")
    review_id, attempt_id = ids["review_id"], ids["attempt_id"]

    saved: Path | None = None
    if failure is None:
        name = f"lesson-{lesson_n}.review.{attempt_id}.yaml" if kind == "lesson" else f"plan-review.{attempt_id}.yaml"
        saved = _save_return(root, directory, name, data)

    identity = resolve_reviewer_identity(
        task_id, Path(tasks_dir) if tasks_dir else findings_db.batch_root(root) / "batch_state" / "tasks"
    )
    params = findings_db.load_parameters()
    conn = findings_db.connect(db_path or findings_db.db_path(level, root))
    try:
        existing = findings_db.get_attempt(conn, review_id, attempt_id)
        if failure is not None:
            return _record_failure(
                conn,
                existing,
                review_id,
                attempt_id,
                kind,
                level,
                slug,
                lesson_n,
                manifest_sha,
                identity,
                task_id,
                failure,
                params,
                seed_id,
                second,
                moment,
            )
        return_sha = hashlib.sha256(data).hexdigest()
        if existing is not None:
            return _replay(root, directory, existing, return_sha, saved, kind, lesson_n)
        writer = None
        first = None
        if second:
            if kind != "lesson":
                raise RecordError("a second seat reviews lessons, not plans")
            try:
                writer = second_seat.writer_family(directory, lesson_n)
                first = second_seat.check_eligible(
                    conn,
                    level=level,
                    slug=slug,
                    lesson_n=lesson_n,
                    manifest_sha256=manifest_sha,
                    first_attempt=None,
                    second_family=identity["family"],
                    writer=writer,
                    params=params,
                )
            except (second_seat.SecondSeatError, second_seat.IdentityError) as error:
                raise RecordError(str(error)) from error
        elif kind == "lesson" and seed_id is None:
            try:
                writer = second_seat.writer_family(directory, lesson_n)
            except second_seat.IdentityError:
                writer = None  # the writer's family is recorded when it resolves; only a second seat needs it
        codes = _rejection_codes(
            root,
            manifest,
            manifest_sha,
            kind,
            saved,
            manifest_path,
            document_path,
            ledger_path,
            previous_ledger_path,
            echoed,
            ids,
        )
        review = _load_yaml_bytes(data)
        verdict = "REJECTED" if codes else review_verdict(review)
        row = {
            "review_id": review_id,
            "attempt_id": attempt_id,
            "kind": kind,
            "level": level,
            "slug": slug,
            "lesson_n": lesson_n,
            "manifest_sha256": manifest_sha,
            "reviewer_model": identity["model"],
            "reviewer_family": identity["family"],
            "harness": identity["harness"],
            "prompt_sha256": (review.get("reviewer") or {}).get("prompt_sha256")
            if isinstance(review, dict) and not codes
            else None,
            "verdict": verdict,
            "validated_at": moment,
            "rejection_codes_json": findings_db.dumps(codes) if codes else None,
            "task_id": task_id,
            "role": "second" if second else "first",
            "seed_id": seed_id,
            "writer_family": writer,
            "return_sha256": return_sha,
        }
        if codes:
            with findings_db.transaction(conn):
                findings_db.insert_attempt(conn, row)
            return Outcome(
                False,
                "REJECTED",
                review_id,
                attempt_id,
                kind,
                rejection_codes=codes,
                saved_return=_rel(root, saved),
                seed_id=seed_id,
                next=f"count it as a failed review: record --failure rejected_return --review-id {review_id} --attempt-id {attempt_id}",
            )
        outcome = _persist_accepted(conn, root, directory, review, row, params, seed_id, second, first, moment)
        outcome.saved_return = _rel(root, saved)
        return outcome
    finally:
        conn.close()


def review_verdict(review: Any) -> str:
    """The verdict of an accepted return, recomputed from its findings exactly as the validator does."""
    from scripts.review.validate.validate import _verdict

    return _verdict(review["findings"])[0]


def _rejection_codes(
    root: Path,
    manifest: dict[str, Any],
    manifest_sha: str,
    kind: str,
    saved: Path,
    manifest_path: Path,
    document_path: Path | None,
    ledger_path: Path,
    previous_ledger_path: Path | None,
    echoed: dict[str, Any],
    ids: dict[str, Any],
) -> list[str]:
    codes: list[str] = []
    for name in ("review_id", "attempt_id"):
        if echoed.get(name) not in (None, ids[name]):
            codes.append(ATTEMPT_IDENTITY_MISMATCH)
    if kind == "lesson" and _stale_message(root, manifest) is not None:
        codes.append(MANIFEST_INPUTS_STALE)
    result = validate_review(
        saved,
        manifest_path=Path(manifest_path),
        document_path=document_path,
        ledger_path=Path(ledger_path),
        previous_ledger_path=previous_ledger_path,
        repo_root=root,
    )
    codes += [item.code for item in result.rejections]
    return list(dict.fromkeys(codes))


def _persist_accepted(
    conn: Any,
    root: Path,
    directory: Path,
    review: dict[str, Any],
    row: dict[str, Any],
    params: dict[str, Any],
    seed_id: str | None,
    second: bool,
    first: Any,
    moment: str,
) -> Outcome:
    kind, level, slug, lesson_n = row["kind"], row["level"], row["slug"], row["lesson_n"]
    findings = review["findings"]
    provenance = None
    if kind == "lesson" and seed_id is None:
        try:
            provenance = fixloop.load_provenance(directory, lesson_n)
        except fixloop.ProvenanceError:
            provenance = None
    opened: list[int] = []
    agreement = None
    with findings_db.transaction(conn):
        findings_db.insert_attempt(conn, row)
        for finding in findings:
            layer = None if seed_id is not None else fixloop.layer_for_finding(finding, provenance, kind=kind)
            findings_db.insert_finding(conn, row["review_id"], row["attempt_id"], finding, layer=layer, seed_id=seed_id)
            if seed_id is None and finding["status"] == "active" and "unsupported_by_source" in finding:
                opened.append(
                    findings_db.open_settle_item(
                        conn,
                        ref=findings_db.finding_ref(row["review_id"], row["attempt_id"], finding["id"]),
                        kind="unsupported_by_source",
                        level=level,
                        slug=slug,
                        lesson_n=lesson_n,
                        manifest_sha256=row["manifest_sha256"],
                        opened_at=moment,
                    )
                )
        stored = findings_db.count_findings(conn, row["review_id"], row["attempt_id"])
        if stored != len(findings):  # no finding may be dropped between the validator and the database
            raise RecordError(f"{len(findings)} findings validated but {stored} stored; nothing was recorded")
        if seed_id is None and not second and kind == "lesson" and row["verdict"] == "REVISE":
            findings_db.bump_budget(conn, level, slug, lesson_n, "revise_rounds")
        if second:
            agreement = second_seat.record_agreement(
                conn, first, findings_db.get_attempt(conn, row["review_id"], row["attempt_id"]), opened_at=moment
            )
            opened += agreement.pop("settle_items")
    outcome = Outcome(
        True,
        row["verdict"],
        row["review_id"],
        row["attempt_id"],
        kind,
        findings=len(findings),
        settle_items=opened,
        agreement=agreement,
        seed_id=seed_id,
    )
    if seed_id is None and not second:
        name = f"lesson-{lesson_n}.verdict.yaml" if kind == "lesson" else pm.REVIEW_NAME
        outcome.verdict_file = _rel(
            root,
            _write_verdict_file(
                root, directory, name, row["verdict"], row["attempt_id"], row["manifest_sha256"], row["validated_at"]
            ),
        )
        outcome.terminal = _terminal_now(conn, level, slug, lesson_n, params)
    return outcome


def _terminal_now(
    conn: Any, level: str, slug: str, lesson_n: int | None, params: dict[str, Any]
) -> list[dict[str, Any]]:
    """The terminal transitions the counters of ``lesson_n`` (or the plan) imply right now."""
    budget = findings_db.module_budgets(conn, level, slug).get(
        lesson_n if lesson_n is not None else findings_db.PLAN_LESSON_N
    )
    if budget is None:
        return []
    where = f"lesson {lesson_n}" if lesson_n is not None else "the plan review"
    found = []
    if budget["revise_rounds"] > params["max_revise_rounds"]:
        found.append(
            {
                "transition": fixloop.TERMINAL,
                "reason": fixloop.REASON_REVISE,
                "detail": f"{where}: REVISE round {budget['revise_rounds']} exceeds {params['max_revise_rounds']}; no further round is allowed",
            }
        )
    if budget["review_failures"] >= params["review_failures_terminal_at"]:
        found.append(
            {
                "transition": fixloop.TERMINAL,
                "reason": fixloop.REASON_REVIEW_FAILURE,
                "detail": f"{where}: {budget['review_failures']} failed reviews",
            }
        )
    return found


def _replay(
    root: Path, directory: Path, existing: Any, return_sha: str, saved: Path, kind: str, lesson_n: int | None
) -> Outcome:
    """The same return recorded again: change nothing but re-publish the verdict file a crash may have left out."""
    if existing["return_sha256"] != return_sha:
        raise RecordError(
            f"attempt {existing['attempt_id']} of review {existing['review_id']} was recorded with a different return"
        )
    outcome = Outcome(
        existing["verdict"] in ("APPROVE", "REVISE"),
        existing["verdict"],
        existing["review_id"],
        existing["attempt_id"],
        kind,
        rejection_codes=json.loads(existing["rejection_codes_json"] or "[]"),
        saved_return=_rel(root, saved),
        replay=True,
        seed_id=existing["seed_id"],
    )
    if outcome.accepted and existing["role"] == "first" and existing["seed_id"] is None:
        name = f"lesson-{lesson_n}.verdict.yaml" if kind == "lesson" else pm.REVIEW_NAME
        outcome.verdict_file = _rel(
            root,
            _write_verdict_file(
                root,
                directory,
                name,
                existing["verdict"],
                existing["attempt_id"],
                existing["manifest_sha256"],
                existing["validated_at"],
            ),
        )
    return outcome


def _record_failure(
    conn: Any,
    existing: Any,
    review_id: str,
    attempt_id: str,
    kind: str,
    level: str,
    slug: str,
    lesson_n: int | None,
    manifest_sha: str,
    identity: dict[str, str],
    task_id: str,
    reason: str,
    params: dict[str, Any],
    seed_id: str | None,
    second: bool,
    moment: str,
) -> Outcome:
    counted = seed_id is None and not second
    budget_n = lesson_n if lesson_n is not None else findings_db.PLAN_LESSON_N
    if existing is not None:
        # a rejected return is counted by a later --failure on its own attempt; anything else is refused
        if existing["failure_reason"] is not None:
            return Outcome(
                False, existing["verdict"], review_id, attempt_id, kind, replay=True, seed_id=existing["seed_id"]
            )
        if existing["verdict"] != "REJECTED" or existing["manifest_sha256"] != manifest_sha:
            raise RecordError(
                f"attempt {attempt_id} of review {review_id} was already recorded as {existing['verdict']}"
            )
        counted = existing["seed_id"] is None and existing["role"] == "first"
        with findings_db.transaction(conn):
            conn.execute(
                "UPDATE attempts SET failure_reason = ? WHERE review_id = ? AND attempt_id = ?",
                (reason, review_id, attempt_id),
            )
            if counted:
                findings_db.bump_budget(conn, level, slug, budget_n, "review_failures")
    else:
        with findings_db.transaction(conn):
            findings_db.insert_attempt(
                conn,
                {
                    "review_id": review_id,
                    "attempt_id": attempt_id,
                    "kind": kind,
                    "level": level,
                    "slug": slug,
                    "lesson_n": lesson_n,
                    "manifest_sha256": manifest_sha,
                    "reviewer_model": identity["model"],
                    "reviewer_family": identity["family"],
                    "harness": identity["harness"],
                    "verdict": "FAILED",
                    "validated_at": moment,
                    "task_id": task_id,
                    "role": "second" if second else "first",
                    "seed_id": seed_id,
                    "failure_reason": reason,
                },
            )
            if counted:
                findings_db.bump_budget(conn, level, slug, budget_n, "review_failures")
    outcome = Outcome(False, "FAILED", review_id, attempt_id, kind, seed_id=seed_id)
    if counted:
        outcome.terminal = _terminal_now(conn, level, slug, lesson_n, params)
    return outcome


def _rel(root: Path, path: Path | None) -> str | None:
    return path.resolve().relative_to(root).as_posix() if path is not None else None


# --- CLI --------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.review.record",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Record one review attempt of the fresh build: validate the return with the active validator, save it,\n"
            "and on acceptance write the verdict file the landing reads plus the attempts and findings rows,\n"
            "settle items and budgets in batch_state/review-findings/<level>.sqlite (#8430).\n"
            "Use once per attempt, after the review seat returns. With --failure, record a review that returned\n"
            "nothing (timeout, crash, no deliverable) or count a rejected return as a failed review.\n"
            "Do NOT use it to judge a review: it re-implements no rejection of scripts.review.validate."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.record review.yaml --manifest lesson-2.manifest.yaml \\\n"
            "    --lesson lesson-2.expanded.yaml --ledger batch_state/review-receipts/R/A.jsonl --task-id review-a1-m-2\n"
            "  .venv/bin/python -m scripts.review.record plan-review.return.yaml --manifest plan-review.manifest.yaml \\\n"
            "    --ledger batch_state/review-receipts/R/A.jsonl --task-id plan-review-a1-m\n"
            "  .venv/bin/python -m scripts.review.record --failure timeout --manifest lesson-2.manifest.yaml \\\n"
            "    --review-id R --attempt-id A --task-id review-a1-m-2\n"
            "\nOutputs: one JSON object on stdout. Writes the saved return, the verdict file (accepted first-seat\n"
            "attempts) and the findings database. Exit codes: 0 accepted or failure recorded; 1 rejected;\n"
            "3 accepted or recorded and a terminal transition (operator) is reached; 2 not recorded (error on stderr)."
        ),
    )
    parser.add_argument("review", type=Path, nargs="?", help="the reviewer's review.yaml (omit with --failure)")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="the attempt manifest (plan-review.manifest.yaml or lesson-<n>.manifest.yaml)",
    )
    parser.add_argument(
        "--document",
        "--lesson",
        dest="document",
        type=Path,
        default=None,
        help="the expanded lesson the quotes are checked in (lesson reviews); for a plan review the plan (default: the manifest's)",
    )
    parser.add_argument("--ledger", type=Path, default=None, help="this attempt's receipt ledger")
    parser.add_argument("--previous-ledger", type=Path, default=None, help="the previous attempt's ledger (re-reviews)")
    parser.add_argument(
        "--task-id",
        required=True,
        help="the dispatch task id: reviewer model and harness are read from batch_state/tasks/<task-id>.json",
    )
    parser.add_argument("--review-id", default=None, help="needed only when the return does not state it (--failure)")
    parser.add_argument("--attempt-id", default=None, help="needed only when the return does not state it (--failure)")
    parser.add_argument(
        "--seed-id",
        default=None,
        help="the attempt reviews a seeded lesson (R3): recorded apart, never enters the fix loop",
    )
    parser.add_argument(
        "--second-seat",
        action="store_true",
        help="the attempt is the second-seat review of a sampled lesson (third family, same manifest)",
    )
    parser.add_argument(
        "--failure",
        metavar="REASON",
        default=None,
        help="record a review that returned nothing (or count a rejected return) and add one review failure",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="repository root (default: this repository)")
    parser.add_argument(
        "--db", type=Path, default=None, help="findings database (default: batch_state/review-findings/<level>.sqlite)"
    )
    parser.add_argument("--tasks-dir", type=Path, default=None, help="dispatch records (default: batch_state/tasks)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        outcome = record_return(
            args.review,
            manifest_path=args.manifest,
            ledger_path=args.ledger,
            task_id=args.task_id,
            document_path=args.document,
            previous_ledger_path=args.previous_ledger,
            repo_root=args.repo_root,
            db_path=args.db,
            tasks_dir=args.tasks_dir,
            review_id=args.review_id,
            attempt_id=args.attempt_id,
            seed_id=args.seed_id,
            second=args.second_seat,
            failure=args.failure,
        )
    except (RecordError, findings_db.FindingsDbError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(outcome.payload(), indent=2, sort_keys=True, ensure_ascii=False))
    if outcome.terminal:
        return 3
    return 0 if outcome.accepted or args.failure is not None else 1


if __name__ == "__main__":
    sys.exit(main())
