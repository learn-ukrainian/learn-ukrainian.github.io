"""Ordered fresh module build, prompt freshness, and bounded regeneration."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.closure import compute_closure
from scripts.build.fresh.immersion import lesson_immersion_payload
from scripts.build.fresh.manifest import unlink_current
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.build.fresh.preflight import preflight_lesson
from scripts.build.fresh.prompt import BAND_CARD_MAP, check_rendered_prompt, render_lesson_prompt, render_recap_prompt
from scripts.build.fresh.regeneration import load_ledger
from scripts.build.fresh.runner import run_lesson
from scripts.build.fresh.writer import dispatch_writer
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.planned import planned_state

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "module-build-report-v1.schema.json"


def draft_is_current(ledger: dict[str, Any], draft_path: Path, current_hashes: dict[str, str]) -> bool:
    """A draft is reusable only after a completed check-12 attempt on identical bytes."""
    if ledger.get("terminal_layer") is not None or not draft_path.is_file():
        return False
    snapshot = ledger.get("last_success") or {}
    return (snapshot.get("through_check") == 12 and snapshot.get("inputs") == {
        **current_hashes, "draft_sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest()})


def _stop(n: int, reason: str, *, check: int = 0, layer: str = "driver") -> dict[str, Any]:
    return {"n": n, "passed": False, "passed_through": check, "manifest_sha256": None,
            "stopping_check": check, "reason": reason, "regenerations": 0,
            "terminal_layer": None, "layer": layer}


def build_module(level: str, slug: str, *, repo_root: Path, lesson_n: int | None = None,
                 writer_seat: str | None = None, question_seat: str | None = None,
                 writer_dispatch: Callable[..., Any] = dispatch_writer,
                 runner: Callable[..., dict[str, Any]] = run_lesson,
                 runner_kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
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
    for entry in lessons:
        n = entry["n"]
        unlink_current(state_dir, n)
        try:
            plan, entry, pack, words, paths = _load_lesson_data(level, slug, n, repo_root=repo_root)
            position = plan.get("arc_ref", {}).get("position", 1)
            learner = planned_state(level, position, n, allow_missing_prior=True,
                                    plans_dir=paths["plan"].parent, evidence_dir=paths["words"].parent)
            expected = _compute_input_hashes(paths, n, learner)
            card_name = BAND_CARD_MAP.get(level.lower().split("-")[0], "b1plus")
            card_path = checked_existing_path(repo_root, repo_root / "docs/style-cards" / f"{card_name}.md",
                                              "docs/style-cards")
            card_sha = hashlib.sha256(card_path.read_bytes()).hexdigest()
            expected["style_card_sha256"] = card_sha
            built = (_load_recap_built_lessons(paths["state_dir"], level, slug, n, repo_root)
                     if entry.get("kind") == "recap" else [])
            common = dict(cited_records=_load_cited_records(entry, pack, words), learner_state=learner,
                          immersion=lesson_immersion_payload(level, position, n, learner),
                          level=level, slug=slug, lesson_n=n, style_card_path=card_path,
                          **{key: expected[key] for key in ("plan_sha256", "pack_lock", "words_lock",
                                                             "lesson_lock_entry_sha256", "learner_state_sha256")})
            if entry.get("kind") == "recap":
                prompt = render_recap_prompt(entry, built_lessons=built, **common)
            else:
                prompt = render_lesson_prompt(entry, **common)
            checked = check_rendered_prompt(prompt, entry, card_path,
                                             is_recap=entry.get("kind") == "recap", built_lessons=built)
            if not checked.passed:
                raise ValueError(f"rendered_prompt_invalid: {checked.errors}")
            prompt_path = checked_existing_path(repo_root, state_dir / f"lesson-{n}.prompt.md",
                                                "curriculum/l2-uk-en/evidence")
            prompt_bytes = prompt.encode("utf-8")
            lock.atomic_write(prompt_path, prompt_bytes)
            prompt_sha = hashlib.sha256(prompt_bytes).hexdigest()
            lock.atomic_write(checked_existing_path(repo_root, state_dir / f"lesson-{n}.prompt.sha256",
                                                    "curriculum/l2-uk-en/evidence"), f"{prompt_sha}\n".encode("ascii"))
            expected["prompt_sha256"] = prompt_sha
            draft_path = checked_existing_path(repo_root, state_dir / f"lesson-{n}.draft.yaml",
                                               "curriculum/l2-uk-en/evidence")
            ledger_path = checked_existing_path(repo_root, state_dir / f"lesson-{n}.regeneration.yaml",
                                                "curriculum/l2-uk-en/evidence")
            ledger = load_ledger(ledger_path, slug, n)
            current = {"plan_sha256": expected["plan_sha256"], "pack_lock": expected["pack_lock"],
                       "words_lock": expected["words_lock"], "card_sha256": card_sha,
                       "prompt_sha256": prompt_sha}
            fresh = draft_is_current(ledger, draft_path, current)
            if ledger["terminal_layer"] is not None:
                result = _stop(n, "regeneration_terminal", check=ledger["attempts"][-1]["failed_check"],
                               layer=ledger["terminal_layer"])
                result["regenerations"] = ledger["regenerations"]
                result["terminal_layer"] = ledger["terminal_layer"]
                results.append(result)
                break
            while True:
                if not fresh:
                    if not writer_seat:
                        results.append(_stop(n, "writer_seat_required"))
                        break
                    agent, sep, model = writer_seat.partition(":")
                    if not sep or not agent or not model:
                        results.append(_stop(n, "writer_seat_invalid"))
                        break
                    preflight = preflight_lesson(entry, pack=pack, word_store=words, pack_path=paths["pack"],
                                                words_path=paths["words"], level=level, slug=slug,
                                                gap_report_path=state_dir / f"lesson-{n}.gaps.yaml",
                                                learner_state=learner, repo_root=repo_root,
                                                plans_dir=paths["plan"].parent, evidence_dir=paths["words"].parent)
                    if not preflight.passed:
                        results.append(_stop(n, "preflight_failed"))
                        break
                    writer_dispatch(writer=agent, model=model, level=level, slug=slug, lesson_n=n,
                                    prompt_file=prompt_path, prompt_sha256=prompt_sha, output_dir=state_dir,
                                    preflight_result=preflight, attempt=len(ledger["attempts"]) + 1,
                                    plan_activity_types={a["id"]: a["type"] for a in entry.get("activities") or []},
                                    repo_root=repo_root)
                draft = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
                report = runner(level, slug, n, draft=draft, plan=plan, pack=pack, words=words,
                                state_dir=state_dir, repo_root=repo_root, plans_dir=paths["plan"].parent,
                                evidence_dir=paths["words"].parent, question_seat=question_seat,
                                site_dir=checked_existing_path(repo_root,
                                                               repo_root / "site/src/content/docs" / level / slug,
                                                               "site/src/content/docs"),
                                expected_inputs=expected, **(runner_kwargs or {}))
                ledger = load_ledger(ledger_path, slug, n)
                if report["passed"] and report.get("manifest_sha256"):
                    results.append({"n": n, "passed": True, "passed_through": 12,
                                    "manifest_sha256": report["manifest_sha256"], "stopping_check": None,
                                    "reason": None, "regenerations": ledger["regenerations"],
                                    "terminal_layer": None, "layer": None})
                    break
                bad = next((row for row in report.get("checks", []) if row["status"] == "failed"), None)
                check = report.get("stopping_check") or (bad["check"] if bad else report.get("passed_through", 0))
                reason = report.get("reason") or (bad["reason"] if bad else "build_failed")
                if ledger["terminal_layer"] is not None:
                    stopped = _stop(n, reason, check=check, layer=bad["layer"] if bad else "engine")
                    stopped["regenerations"] = ledger["regenerations"]
                    stopped["terminal_layer"] = ledger["terminal_layer"]
                    results.append(stopped)
                    break
                fresh = False
            if not results[-1]["passed"]:
                break
        except (OSError, ValueError, KeyError, TypeError) as err:
            reason = str(err)
            results.append(_stop(n, "recap_inputs_not_built" if "recap_inputs_not_built" in reason else reason))
            break
    report = {"level": level, "slug": slug, "complete": len(results) == len(lessons) and all(
        row["passed"] and row["manifest_sha256"] for row in results),
              "lessons": [{key: row[key] for key in ("n", "passed", "passed_through", "manifest_sha256",
                                                    "stopping_check", "reason", "regenerations", "terminal_layer", "layer")}
                          for row in results]}
    Draft202012Validator(json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(
        encoding="utf-8"))).validate(report)
    lock.atomic_write(checked_existing_path(repo_root, state_dir / "module.build.yaml",
                                            "curriculum/l2-uk-en/evidence"), lock.yaml_bytes(report))
    if lesson_n is None:
        compute_closure(level, slug, list(plan["lessons"]), repo_root=repo_root, state_dir=state_dir)
    return report
