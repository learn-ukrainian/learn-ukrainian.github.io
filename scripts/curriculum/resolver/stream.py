"""resolve(expanded, allowlist, sources) -> ResolutionStream.

For every token: its class, its candidate records, what deterministic
narrowing left, and the features all candidates share. Nothing is guessed.
A token gets a `selected` record only through narrowing to one record here,
or later through a recorded answer (receipts.py). Two runs over the same
document, allowlist and sources give byte-identical streams.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lock, tags
from scripts.verification import stress

from . import ambiguity, codes
from .classify import Classified, classify_unit, is_proper_noun
from .inputs import Allowlist, ExpandedDocument, ResolverError
from .narrow import FormIndex, common_features, lookup_keys

PROGRESS_EVERY = 500
REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class ResolutionStream:
    lesson: dict[str, Any]
    inputs: dict[str, str]
    tokens: list[dict[str, Any]]
    failures: list[dict[str, Any]] = field(default_factory=list)
    reports: list[dict[str, Any]] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for token in self.tokens:
            counts[token["class"]] = counts.get(token["class"], 0) + 1
        return dict(sorted(counts.items()))

    def open_tokens(self) -> list[dict[str, Any]]:
        return [t for t in self.tokens if t["class"] in codes.OPEN_CLASSES]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stream_schema": 1,
            "lesson": self.lesson,
            "inputs": self.inputs,
            "counts": self.counts(),
            "tokens": self.tokens,
            "failures": self.failures,
            "reports": self.reports,
        }

    def to_bytes(self) -> bytes:
        return lock.yaml_bytes(self.to_dict())


def source_inputs(expanded: ExpandedDocument, allowlist: Allowlist, sources: Any) -> dict[str, str]:
    vesum_digest, _metadata = sources._vesum_identity()
    return {
        "expanded_sha256": expanded.sha256,
        "allowlist_sha256": allowlist.sha256,
        "words_lock": allowlist.words_lock,
        "vesum": vesum_digest,
        "trie_digest": stress.source_info()["digest"],
    }


def _entry(item: Classified) -> dict[str, Any]:
    return {
        "unit": item.unit.locator(),
        "unit_index": item.unit.index,
        "role": item.unit.role,
        "offset": item.token.start,
        "token": item.token.text,
        "lookup": item.token.lookup,
        "surface": item.surface,
        "class": None,
        "candidates": [],
        "readings": [],
        "features": [],
        "selected": None,
        "provenance": "deterministic",
    }


def resolve(
    expanded: ExpandedDocument,
    allowlist: Allowlist,
    sources: Any,
    *,
    report: Callable[[str], None] | None = None,
) -> ResolutionStream:
    inputs = source_inputs(expanded, allowlist, sources)
    index = FormIndex(allowlist)
    mapper = tags.TagMapper(report=report)
    cross_check = ambiguity.StressCrossCheck(sources)
    classified = [item for unit in expanded.units for item in classify_unit(unit, allowlist)]

    tokens: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    outside: list[tuple[dict[str, Any], Classified]] = []
    total = len(classified)
    for position, item in enumerate(classified, 1):
        entry = _entry(item)
        if not item.needs_lookup:
            entry["class"] = item.final
            if item.surface == codes.GLOSS_REF:
                entry["candidates"] = [item.token.lookup] if item.final == codes.RESOLVED else []
                if item.final == codes.RESOLVED:
                    entry["selected"] = {"record": item.token.lookup, "forms": [], "stressed": None}
            if item.message:
                entry["message"] = item.message
        else:
            candidates = index.candidates(item.token)
            name_match = any(c.record_id in allowlist.name_ids for c in candidates)
            if is_proper_noun(
                item.token, capitalised_record_match=index.capitalised_match(item.token), name_match=name_match
            ):
                entry["surface"] = codes.PROPER_NOUN
            if not candidates:
                entry["class"] = codes.LEMMA_OUTSIDE_STATE
                marked = index.marked_candidates(item.token)
                if marked:
                    entry["marked"] = [
                        {"record": c.record_id, "tags": c.form["tags"], "markers": c.form.get("markers") or []}
                        for c in marked
                    ]
                outside.append((entry, item))
            else:
                decision = ambiguity.decide(candidates, label=allowlist.label, spelling=item.token.lookup)
                entry["class"] = decision.klass
                entry["candidates"] = decision.record_ids
                entry["readings"] = [r.to_dict() for r in decision.readings]
                entry["features"] = common_features(candidates, mapper)
                entry["selected"] = decision.selected
                if decision.klass in codes.OPEN_CLASSES:
                    entry["provenance"] = None
                if decision.message:
                    entry["message"] = decision.message
                for found in cross_check(candidates):
                    reports.append({**found, "unit": entry["unit"], "offset": entry["offset"], "token": entry["token"]})
        tokens.append(entry)
        if report and (position % PROGRESS_EVERY == 0 or position == total):
            report(f"tokens: {position}/{total}")

    if outside:
        keys = sorted({key for _entry_, item in outside for key in lookup_keys(item.token)})
        analyses = sources.verify_words(keys).raw
        for entry, item in outside:
            found = {key: analyses.get(key, []) for key in lookup_keys(item.token)}
            entry["analyses"] = found
            described = "; ".join(
                f"{key}: {', '.join(sorted({f'{a["lemma"]} ({a["pos"]})' for a in rows})) or 'none'}"
                for key, rows in found.items()
            )
            marked_note = (
                " (only marked, non-learner forms of allowlist records spell it)" if entry.get("marked") else ""
            )
            entry["message"] = (
                f"no learner-usable form of an allowlist record spells {item.token.text!r}{marked_note}; "
                f"VESUM analyses by lookup spelling (hyphenated parts included): {described}"
            )

    failures = [
        {
            "code": entry["class"],
            "unit": entry["unit"],
            "offset": entry["offset"],
            "token": entry["token"],
            "text": expanded.units[item.unit.index].text,
            "message": entry.get("message", ""),
        }
        for entry, item in zip(tokens, classified, strict=True)
        if entry["class"] in codes.FAILURE_CLASSES
    ]
    return ResolutionStream(dict(expanded.lesson), inputs, tokens, failures, reports)


# --- Files and CLI ---------------------------------------------------------------


def lesson_paths(level: str, slug: str, n: int, *, evidence_dir: Path | None = None) -> dict[str, Path]:
    root = Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}"
    state = root / "_state" / slug
    return {
        "words": root / "_words.yaml",
        "expanded": state / f"lesson-{n}.expanded.yaml",
        "questions": state / f"lesson-{n}.questions.yaml",
        "resolutions": state / f"lesson-{n}.resolutions.yaml",
    }


def load_allowlist(
    level: str,
    slug: str,
    n: int,
    *,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
    allow_missing_prior: bool = False,
) -> Allowlist:
    """Planned learner state (#8414) ∪ this lesson's core ∪ incidental, by record."""
    from scripts.curriculum.learner_state import PlannedStateError, planned_state
    from scripts.curriculum.validate.loader import PlanError, load_plan

    plans_root = Path(plans_dir) if plans_dir is not None else REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_root = (
        Path(evidence_dir) if evidence_dir is not None else REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}"
    )
    try:
        plan = load_plan(plans_root / f"{slug}.yaml")
        position = (plan.get("arc_ref") or {}).get("position")
        if not isinstance(position, int):
            raise ResolverError(codes.INVALID_INPUT, f"plan {slug} has no arc_ref.position")
        state = planned_state(
            level,
            position,
            n,
            plans_dir=plans_root,
            evidence_dir=evidence_root,
            allow_missing_prior=allow_missing_prior,
        )
    except (PlanError, PlannedStateError) as error:
        raise ResolverError(error.code, error.message) from error
    lesson = next(item for item in plan["lessons"] if isinstance(item, dict) and item.get("n") == n)
    inventory = lesson.get("inventory") or {}
    vocabulary = inventory.get("vocabulary") or {}
    lesson_ids = {
        item["evidence"]
        for key in ("core", "incidental")
        for item in vocabulary.get(key) or []
        if isinstance(item, dict) and isinstance(item.get("evidence"), str)
    }
    words_path = lesson_paths(level, slug, n, evidence_dir=evidence_root)["words"]
    if not lock.check(words_path):
        raise ResolverError(codes.LOCK_MISMATCH, f"word store {str(words_path)!r} is absent or disagrees with its lock")
    store = yaml.safe_load(words_path.read_text(encoding="utf-8"))
    letters = set(state.letters) | set((inventory.get("phonetics") or {}).get("letters") or [])
    return Allowlist.from_store(
        store,
        set(state.all_allowed_ids) | lesson_ids,
        words_lock=Path(f"{words_path}.lock").read_text(encoding="ascii").strip(),
        gloss_ids=frozenset(lesson_ids),
        name_ids=frozenset(state.name_ids),
        letters=frozenset(letters),
        label=f"plan {level}/{slug} lesson {n}",
    )


def _report(message: str) -> None:
    print(f"progress: {message}", file=sys.stderr)


def _load(args: argparse.Namespace) -> tuple[ExpandedDocument, Allowlist, Any]:
    from scripts.curriculum.evidence.sources import Sources

    paths = lesson_paths(args.level, args.slug, args.n, evidence_dir=args.evidence_dir)
    expanded = ExpandedDocument.load(paths["expanded"])
    wanted = {"level": args.level, "slug": args.slug, "n": args.n}
    if expanded.lesson != wanted:
        raise ResolverError(codes.INVALID_INPUT, f"expanded document is for {expanded.lesson}, not {wanted}")
    allowlist = load_allowlist(
        args.level,
        args.slug,
        args.n,
        plans_dir=args.plans_dir,
        evidence_dir=args.evidence_dir,
        allow_missing_prior=args.allow_missing_prior,
    )
    return expanded, allowlist, Sources(vesum_db=args.vesum_db, report=_report)


def _print_failures(stream: ResolutionStream) -> None:
    for failure in stream.failures:
        print(
            f"{failure['code']}: {failure['token']!r} at {failure['unit']} offset {failure['offset']} "
            f"in {failure['text']!r}: {failure['message']}",
            file=sys.stderr,
        )


def _run(args: argparse.Namespace) -> int:
    from . import questions as questions_module
    from . import receipts

    paths = lesson_paths(args.level, args.slug, args.n, evidence_dir=args.evidence_dir)
    if args.command == "check":
        doc = receipts.check_receipts(paths["resolutions"])
        _emit(args, {"status": "ok", "path": str(paths["resolutions"]), "tokens": len(doc["tokens"])})
        return 0
    expanded, allowlist, sources = _load(args)
    with sources:
        stream = resolve(expanded, allowlist, sources, report=_report)
    summary: dict[str, Any] = {
        "lesson": stream.lesson,
        "inputs": stream.inputs,
        "counts": stream.counts(),
        "failures": len(stream.failures),
        "reports": len(stream.reports),
    }
    if args.command == "resolve":
        _print_failures(stream)
        _emit(args, stream.to_dict() if args.json else summary)
        return 1 if stream.failures else 0
    if stream.failures:
        _print_failures(stream)
        _emit(args, {**summary, "status": "failed", "error": "token failures come before any paid question"})
        return 1
    batch = questions_module.build_questions(stream, expanded, allowlist)
    if args.command == "questions":
        written = None
        if not args.dry_run:
            questions_module.write_questions(paths["questions"], batch)
            written = str(paths["questions"])
        blocking = sum(1 for q in batch["questions"] if q["blocking"])
        _emit(
            args,
            batch
            if args.json
            else {**summary, "questions": len(batch["questions"]), "blocking": blocking, "written": written},
        )
        return 0
    # apply
    if batch["questions"]:
        stored = questions_module.load_questions(paths["questions"])
        if stored != batch:
            raise ResolverError(
                codes.STALE_QUESTIONS, f"{paths['questions']} differs from the current inputs; re-emit it"
            )
        if args.answers is None or args.seat is None:
            raise ResolverError(codes.TOKEN_UNRESOLVED, "this lesson has questions: pass the answers file and --seat")
        answers = yaml.safe_load(Path(args.answers).read_text(encoding="utf-8"))
        selections = receipts.apply_answers(batch, answers, args.seat)
    else:
        selections = {}
    doc = receipts.build_receipts(stream, batch, selections, args.seat)
    written = None
    if not args.dry_run:
        receipts.write_receipts(paths["resolutions"], doc)
        written = str(paths["resolutions"])
    _emit(args, doc if args.json else {**summary, "answered": len(selections), "written": written})
    return 0


def _emit(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for key, value in payload.items():
            print(f"{key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.curriculum.resolver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Token resolver for fresh-build lessons (#8413 Brief B, #8431 r3 §3).\n"
            "Use after the engine writes lesson-<n>.expanded.yaml and before stress is applied;\n"
            "do NOT use on v1 modules or on text that already carries stress marks."
        ),
        epilog=(
            "Commands:\n"
            "  resolve    classify and narrow every token; read-only; exit 1 on token failures\n"
            "  questions  write lesson-<n>.questions.yaml (+ .lock), one constrained question per open token\n"
            "  apply      validate the seat's answers and write lesson-<n>.resolutions.yaml (+ .lock)\n"
            "  check      verify a resolutions file against its lock, its schema and its rules\n\n"
            "Files: curriculum/l2-uk-en/evidence/<level>/_state/<slug>/lesson-<n>.{expanded,questions,resolutions}.yaml\n"
            "Exit codes: 0 = success, 1 = failure.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.resolver resolve a1 sounds-and-letters 1\n"
            "  .venv/bin/python -m scripts.curriculum.resolver questions a1 sounds-and-letters 1 --dry-run --json\n"
            "  .venv/bin/python -m scripts.curriculum.resolver apply a1 sounds-and-letters 1 answers.yaml --seat agy/task-7\n\n"
            "Outcome codes:\n" + codes.help_text()
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("resolve", "Classify and narrow every token of the expanded document (read-only)."),
        ("questions", "Emit the lesson's constrained-questions batch."),
        ("apply", "Apply a seat's answers and write the resolution receipts."),
        ("check", "Check a resolutions file (lock, schema, rules)."),
    ):
        sub = commands.add_parser(name, help=text, description=text)
        sub.add_argument("level", help="level directory, e.g. a1")
        sub.add_argument("slug", help="module slug (lesson-plans/<level>/<slug>.yaml)")
        sub.add_argument("n", type=int, help="lesson number within the module")
        if name == "apply":
            sub.add_argument("answers", nargs="?", type=Path, help="answers YAML {answers: [{id, record}]}")
            sub.add_argument("--seat", help="answering seat identity from the dispatch record, e.g. agy/task-7")
        if name in ("questions", "apply"):
            sub.add_argument("--dry-run", action="store_true", help="compute and print without writing files")
        sub.add_argument("--json", action="store_true", help="machine-readable output on stdout")
        sub.add_argument("--plans-dir", type=Path, default=None, help="override lesson-plans/<level>/")
        sub.add_argument("--evidence-dir", type=Path, default=None, help="override evidence/<level>/")
        sub.add_argument("--vesum-db", type=Path, default=None, help="override the VESUM database path")
        sub.add_argument(
            "--allow-missing-prior", action="store_true", help="waive missing earlier plans (pilot authoring)"
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except (ResolverError, ValueError, FileNotFoundError) as error:
        code = getattr(error, "code", None) or str(error).split(":", 1)[0]
        if getattr(args, "json", False):
            print(json.dumps({"status": "failed", "code": code, "error": str(error)}, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1
