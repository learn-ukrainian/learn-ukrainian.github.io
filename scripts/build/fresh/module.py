"""Ordered fresh module build, prompt freshness, and bounded regeneration.

Only writer-layer check failures can trigger another writer attempt. Cross-run paid
calls are bounded by stable input/seat/effort/attempt IDs in the durable task store:
with identical inputs and a readable result, dispatch reuses a ``done`` attempt.
A fresh per-run state directory therefore needs no persisted regeneration ledger
to avoid paying again for those completed attempts. Harness recovery has its own
bounded sidecar; unreadable results and terminal non-done tasks can require retries.
See ``docs/runbooks/fresh-build-writer-harness.md`` for safe harness recovery.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.closure import compute_closure
from scripts.build.fresh.draft_schema import DraftValidationError
from scripts.build.fresh.immersion import lesson_immersion_payload
from scripts.build.fresh.manifest import unlink_current
from scripts.build.fresh.path_guard import checked_existing_path, public_diagnostic
from scripts.build.fresh.preflight import preflight_lesson
from scripts.build.fresh.prompt import (
    BAND_CARD_MAP,
    check_rendered_prompt,
    grammar_points,
    render_lesson_prompt,
    render_recap_prompt,
)
from scripts.build.fresh.regeneration import (
    HARNESS_EXHAUSTED,
    load_harness,
    load_ledger,
    record_failure,
    record_harness_failure,
    record_writer_call,
    writer_inputs,
)
from scripts.build.fresh.runner import run_lesson
from scripts.build.fresh.writer import WriterCallError, WriterHarnessError, dispatch_writer
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.planned import planned_state

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "module-build-report-v1.schema.json"


def draft_is_current(ledger: dict[str, Any], draft_path: Path, current_hashes: dict[str, str]) -> bool:
    """A draft is reusable only after a completed check-12 attempt on identical bytes."""
    if ledger.get("terminal_layer") is not None or not draft_path.is_file():
        return False
    snapshot = ledger.get("last_success") or {}
    return snapshot.get("through_check") == 12 and snapshot.get("inputs") == {
        **current_hashes,
        "draft_sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest(),
    }


def draft_matches_writer(draft_path: Path, writer_seat: str, effort: str | None = None) -> bool:
    """A completed draft cannot bypass seat binding before dispatch gets called."""
    agent, _, model = writer_seat.partition(":")
    meta_path = draft_path.with_name(draft_path.name.replace(".draft.yaml", ".writer.yaml"))
    try:
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return False
    return (
        isinstance(meta, dict)
        and meta.get("writer") == agent
        and meta.get("model") == model
        and (effort is None or meta.get("effort") == effort)
    )


def _stop(n: int, reason: str, *, check: int = 0, layer: str = "driver") -> dict[str, Any]:
    return {
        "n": n,
        "passed": False,
        "passed_through": check,
        "manifest_sha256": None,
        "stopping_check": check,
        "reason": reason,
        "regenerations": 0,
        "terminal_layer": None,
        "layer": layer,
    }


def build_module(
    level: str,
    slug: str,
    *,
    repo_root: Path,
    lesson_n: int | None = None,
    writer_seat: str | None = None,
    question_seat: str | None = None,
    writer_dispatch: Callable[..., Any] = dispatch_writer,
    runner: Callable[..., dict[str, Any]] = run_lesson,
    runner_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build lessons in plan order and leave an atomic, deterministic module report."""
    from scripts.build.fresh.cli import (
        _compute_input_hashes,
        _load_cited_records,
        _load_lesson_data,
        _load_recap_built_lessons,
    )

    plan, _, _, _, paths = _load_lesson_data(level, slug, lesson_n or 1, repo_root=repo_root)
    state_dir = checked_existing_path(repo_root, paths["state_dir"] / slug, "curriculum/l2-uk-en/evidence")
    state_dir.mkdir(parents=True, exist_ok=True)
    lessons = list(plan["lessons"])
    if lesson_n is not None:
        lessons = [next(item for item in lessons if item["n"] == lesson_n)]
    else:
        lessons.sort(key=lambda item: (item.get("kind") == "recap", item["n"]))
    results = []
    coverage_by_lesson = {}
    pack, words = {}, {}
    for entry in lessons:
        n = entry["n"]
        unlink_current(state_dir, n)
        try:
            plan, entry, pack, words, paths = _load_lesson_data(level, slug, n, repo_root=repo_root)
            position = plan.get("arc_ref", {}).get("position", 1)
            learner = planned_state(
                level,
                position,
                n,
                allow_missing_prior=True,
                plans_dir=paths["plan"].parent,
                evidence_dir=paths["words"].parent,
            )
            expected = _compute_input_hashes(paths, n, learner)
            card_name = BAND_CARD_MAP.get(level.lower().split("-")[0], "b1plus")
            card_path = checked_existing_path(
                repo_root, repo_root / "docs/style-cards" / f"{card_name}.md", "docs/style-cards"
            )
            card_sha = hashlib.sha256(card_path.read_bytes()).hexdigest()
            expected["style_card_sha256"] = card_sha
            built = (
                _load_recap_built_lessons(paths["state_dir"], level, slug, n, repo_root)
                if entry.get("kind") == "recap"
                else []
            )
            state_sources = dict(
                word_store=words, grammar_registry=grammar_points(paths["plan"].parent / "_grammar.yaml", level)
            )
            common = dict(
                cited_records=_load_cited_records(entry, pack, words),
                learner_state=learner,
                **state_sources,
                immersion=lesson_immersion_payload(level, position, n, learner),
                level=level,
                slug=slug,
                lesson_n=n,
                style_card_path=card_path,
                **{
                    key: expected[key]
                    for key in (
                        "plan_sha256",
                        "pack_lock",
                        "words_lock",
                        "lesson_lock_entry_sha256",
                        "learner_state_sha256",
                    )
                },
            )
            if entry.get("kind") == "recap":
                prompt = render_recap_prompt(entry, built_lessons=built, **common)
            else:
                prompt = render_lesson_prompt(entry, **common)
            checked = check_rendered_prompt(
                prompt,
                entry,
                card_path,
                is_recap=entry.get("kind") == "recap",
                built_lessons=built,
                learner_state=learner,
                **state_sources,
            )
            if not checked.passed:
                raise ValueError(f"rendered_prompt_invalid: {checked.errors}")
            prompt_path = checked_existing_path(
                repo_root, state_dir / f"lesson-{n}.prompt.md", "curriculum/l2-uk-en/evidence"
            )
            prompt_bytes = prompt.encode("utf-8")
            lock.atomic_write(prompt_path, prompt_bytes)
            prompt_sha = hashlib.sha256(prompt_bytes).hexdigest()
            lock.atomic_write(
                checked_existing_path(
                    repo_root, state_dir / f"lesson-{n}.prompt.sha256", "curriculum/l2-uk-en/evidence"
                ),
                f"{prompt_sha}\n".encode("ascii"),
            )
            expected["prompt_sha256"] = prompt_sha
            draft_path = checked_existing_path(
                repo_root, state_dir / f"lesson-{n}.draft.yaml", "curriculum/l2-uk-en/evidence"
            )
            ledger_path = checked_existing_path(
                repo_root, state_dir / f"lesson-{n}.regeneration.yaml", "curriculum/l2-uk-en/evidence"
            )
            current = writer_inputs(expected, card_sha, prompt_sha)
            ledger = load_ledger(ledger_path, slug, n, current)
            fresh = draft_is_current(ledger, draft_path, current)
            if fresh and writer_seat:
                effort = writer_dispatch.keywords.get("effort") if isinstance(writer_dispatch, partial) else None
                fresh = draft_matches_writer(draft_path, writer_seat, effort)
            if ledger["terminal_layer"] is not None:
                last = ledger["attempts"][-1] if ledger["attempts"] else {}
                result = _stop(
                    n,
                    public_diagnostic(last.get("reason", "regeneration_terminal"), repo_root),
                    check=last.get("failed_check", 0),
                    layer=ledger["terminal_layer"],
                )
                result["regenerations"] = ledger["regenerations"]
                result["terminal_layer"] = ledger["terminal_layer"]
                results.append(result)
                break
            while True:
                # Evidence is scoped to this attempt, including pre-runner stops.
                coverage_by_lesson.pop(n, None)
                harness = load_harness(ledger_path, slug, n)
                if harness["terminal_state"] is not None:
                    stopped = _stop(n, HARNESS_EXHAUSTED, check=1, layer="engine" if not fresh else "harness")
                    stopped.update(regenerations=ledger["regenerations"], terminal_layer="driver")
                    results.append(stopped)
                    break
                if not fresh:
                    if not writer_seat:
                        results.append(_stop(n, "writer_seat_required"))
                        break
                    agent, sep, model = writer_seat.partition(":")
                    if not sep or not agent or not model:
                        results.append(_stop(n, "writer_seat_invalid"))
                        break
                    preflight = preflight_lesson(
                        entry,
                        pack=pack,
                        word_store=words,
                        pack_path=paths["pack"],
                        words_path=paths["words"],
                        level=level,
                        slug=slug,
                        gap_report_path=state_dir / f"lesson-{n}.gaps.yaml",
                        learner_state=learner,
                        repo_root=repo_root,
                        plans_dir=paths["plan"].parent,
                        evidence_dir=paths["words"].parent,
                    )
                    if not preflight.passed:
                        results.append(_stop(n, "preflight_failed"))
                        break
                    try:
                        writer_dispatch(
                            writer=agent,
                            model=model,
                            level=level,
                            slug=slug,
                            lesson_n=n,
                            prompt_file=prompt_path,
                            prompt_sha256=prompt_sha,
                            output_dir=state_dir,
                            preflight_result=preflight,
                            attempt=1 if ledger.get("last_success") else len(ledger["attempts"]) + 1,
                            inputs=current,
                            plan_activity_types={a["id"]: a["type"] for a in entry.get("activities") or []},
                            repo_root=repo_root,
                        )
                    except (OSError, ValueError, KeyError, TypeError, WriterCallError) as err:
                        error_reason = public_diagnostic(str(err), repo_root)
                        content_error = isinstance(err, (DraftValidationError, WriterCallError)) and not isinstance(
                            err, WriterHarnessError
                        )
                        if content_error:
                            ledger = record_failure(
                                ledger_path, slug, n, {"check": 1, "layer": "writer", "reason": error_reason}, current
                            )
                        else:
                            if not getattr(err, "harness_recorded", False) and getattr(err, "harness_chargeable", True):
                                ledger = record_harness_failure(ledger_path, slug, n, error_reason, current)
                            if load_harness(ledger_path, slug, n)["terminal_state"] is not None:
                                ledger["terminal_layer"] = "driver"
                        reason = (
                            HARNESS_EXHAUSTED
                            if not content_error and ledger["terminal_layer"] == "driver"
                            else error_reason
                        )
                        stopped = _stop(n, reason, check=1, layer="writer" if content_error else "engine")
                        stopped.update(regenerations=ledger["regenerations"], terminal_layer=ledger["terminal_layer"])
                        results.append(stopped)
                        break
                    # Only a delivered reply can spend the content-regeneration budget.
                    ledger = record_writer_call(ledger_path, slug, n, current)
                draft = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
                harness_failures_before = len(load_harness(ledger_path, slug, n)["failures"])
                report = runner(
                    level,
                    slug,
                    n,
                    draft=draft,
                    plan=plan,
                    pack=pack,
                    words=words,
                    state_dir=state_dir,
                    repo_root=repo_root,
                    plans_dir=paths["plan"].parent,
                    evidence_dir=paths["words"].parent,
                    question_seat=question_seat,
                    site_dir=checked_existing_path(
                        repo_root, repo_root / "site/src/content/docs" / level / slug, "site/src/content/docs"
                    ),
                    expected_inputs=expected,
                    **(runner_kwargs or {}),
                )
                coverage_by_lesson[n] = next(
                    (row["details"]["writer_sources"] for row in report.get("checks", [])
                     if "writer_sources" in row.get("details", {})), None
                )
                ledger = load_ledger(ledger_path, slug, n)
                if report["passed"] and report.get("manifest_sha256"):
                    results.append(
                        {
                            "n": n,
                            "passed": True,
                            "passed_through": 12,
                            "manifest_sha256": report["manifest_sha256"],
                            "stopping_check": None,
                            "reason": None,
                            "regenerations": ledger["regenerations"],
                            "terminal_layer": None,
                            "layer": None,
                        }
                    )
                    break
                bad = next((row for row in report.get("checks", []) if row["status"] == "failed"), None)
                check = report.get("stopping_check") or (bad["check"] if bad else report.get("passed_through", 0))
                reason = public_diagnostic(report.get("reason") or (bad["reason"] if bad else "build_failed"), repo_root)
                layer = bad["layer"] if bad else (report.get("layer") or "engine")
                if layer == "harness":
                    # The real runner records its failure. Report-only runners need
                    # accounting here, but the same failure must never count twice.
                    harness = load_harness(ledger_path, slug, n)
                    if len(harness["failures"]) == harness_failures_before:
                        record_harness_failure(ledger_path, slug, n, reason, current)
                        harness = load_harness(ledger_path, slug, n)
                    exhausted = harness["terminal_state"] is not None
                    stopped = _stop(n, HARNESS_EXHAUSTED if exhausted else reason, check=check, layer="harness")
                    stopped.update(
                        regenerations=ledger["regenerations"],
                        terminal_layer="driver" if exhausted else ledger["terminal_layer"],
                    )
                    results.append(stopped)
                    break
                if layer != "writer" and ledger["terminal_layer"] is None:
                    # The real runner records failures itself. Injected runners and
                    # check-12 reports without a failed gate row must stop as well.
                    ledger = record_failure(
                        ledger_path, slug, n, {"check": check, "layer": layer, "reason": reason}, current
                    )
                if ledger["terminal_layer"] is not None:
                    stopped = _stop(n, reason, check=check, layer=layer)
                    stopped["regenerations"] = ledger["regenerations"]
                    stopped["terminal_layer"] = ledger["terminal_layer"]
                    results.append(stopped)
                    break
                fresh = False
            if not results[-1]["passed"]:
                break
        except (OSError, ValueError, KeyError, TypeError) as err:
            reason = public_diagnostic(str(err), repo_root)
            stopped = _stop(n, "recap_inputs_not_built" if "recap_inputs_not_built" in reason else reason)
            ledger = load_ledger(state_dir / f"lesson-{n}.regeneration.yaml", slug, n)
            stopped.update(regenerations=ledger["regenerations"], terminal_layer=ledger["terminal_layer"])
            results.append(stopped)
            break
    # Every exit (including preflight/seat failures on resume) reports the persisted call count.
    for result in results:
        ledger = load_ledger(state_dir / f"lesson-{result['n']}.regeneration.yaml", slug, result["n"])
        result.update(regenerations=ledger["regenerations"])
        if result["reason"] != HARNESS_EXHAUSTED:
            result["terminal_layer"] = ledger["terminal_layer"]
    from scripts.build.fresh.assemble import AssemblerError
    from scripts.build.fresh.source_coverage import coverage_summary, obligations

    for result in results:
        coverage = coverage_by_lesson.get(result["n"])
        if coverage is None:
            try:
                # Cited obligations exist even when the writer produced no draft.
                forms, evidence, pinned, report_only = obligations(
                    {}, plan, pack, words, level, slug, result["n"], provenance={"spans": []}
                )
            except (OSError, ValueError, KeyError, TypeError, AssemblerError):
                # Even the cited obligations are unavailable. Zero would lie.
                coverage = None
            else:
                try:
                    stopped_draft = yaml.safe_load((state_dir / f"lesson-{result['n']}.draft.yaml").read_text())
                    forms, evidence, pinned, report_only = obligations(
                        stopped_draft, plan, pack, words, level, slug, result["n"]
                    )
                except (OSError, ValueError, KeyError, TypeError, AssemblerError):
                    # Keep the cited subset when draft-derived obligations fail.
                    pass
                coverage = coverage_summary(
                    forms, evidence, set(), code=None, pinned=pinned, report_only=report_only, evaluated=False
                )
        result["writer_sources"] = coverage
    report = {
        "level": level,
        "slug": slug,
        "complete": len(results) == len(lessons) and all(
            row["passed"] and row["manifest_sha256"] and row["writer_sources"] is not None
            and row["writer_sources"]["code"] is None
            and all(
                row["writer_sources"][group][field] is not None
                for group in ("forms", "evidence")
                for field in ("covered", "missing", "covered_sha256", "missing_sha256")
            )
            and row["writer_sources"]["noncredited_calls"] is not None
            for row in results
        ),
        "lessons": [
            {
                key: row[key]
                for key in (
                    "n",
                    "passed",
                    "passed_through",
                    "manifest_sha256",
                    "stopping_check",
                    "reason",
                    "regenerations",
                    "terminal_layer",
                    "layer",
                    "writer_sources",
                )
            }
            for row in results
        ],
    }
    Draft202012Validator(
        json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
    ).validate(report)
    lock.atomic_write(
        checked_existing_path(repo_root, state_dir / "module.build.yaml", "curriculum/l2-uk-en/evidence"),
        lock.yaml_bytes(report),
    )
    if lesson_n is None:
        compute_closure(level, slug, list(plan["lessons"]), repo_root=repo_root, state_dir=state_dir)
    return report
