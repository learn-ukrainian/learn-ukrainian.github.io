"""Ordered, fail-closed checks 1-12 for one fresh lesson."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.assemble import check_5_assembly, check_9_stress_and_render, check_11_render
from scripts.build.fresh.draft_schema import validate_draft
from scripts.build.fresh.manifest import unlink_current, write_manifest, write_manifest_error
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.build.fresh.regeneration import invalidate_lesson_resolution, load_ledger, record_failure, record_success
from scripts.build.fresh.writer import strip_markdown_fence
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes as learner_codes
from scripts.curriculum.learner_state.inventory_gate import check_lesson
from scripts.curriculum.learner_state.observed import ObservedError, write_observed
from scripts.curriculum.resolver import codes, questions, receipts
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.stream import resolve
from scripts.curriculum.resolver.tokenize import tokenize
from scripts.review.digest.error import DigestError

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "fresh-lesson-gates-v1.schema.json"
QuestionDispatch = Callable[[dict[str, Any], str], dict[str, Any]]


def failure(
    check: int,
    reason: str,
    layer: str,
    *,
    code: str | None = None,
    step: str | None = None,
    activity: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "check": check,
        "status": "failed",
        "code": code or str(check),
        "reason": reason,
        "layer": layer,
    }
    for key, value in (("step", step), ("activity", activity), ("token", token)):
        if value is not None:
            row[key] = str(value)
    return row


def _pass(number: int, details: dict[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"check": number, "status": "passed"}
    if details is not None:
        row["details"] = details
    return row


def _inventory_layer(code: str) -> str:
    if code in {
        learner_codes.PLAN_NOT_FOUND,
        learner_codes.PLAN_YAML_INVALID,
        learner_codes.PRIOR_PLANS_MISSING,
        learner_codes.POSITION_NOT_FOUND,
        learner_codes.LESSON_NOT_FOUND,
        learner_codes.LEMMA_OUTSIDE_STATE,
    }:
        return "plan"
    if code in {
        learner_codes.BASE_LAYER_MISSING,
        learner_codes.BASE_LAYER_UNRESOLVED,
        learner_codes.PENDING_STRESS,
        learner_codes.LOCK_MISMATCH,
    }:
        return "pack"
    if code in {
        learner_codes.EXPANDED_DOCUMENT_MISSING,
        learner_codes.EXPANDED_DOCUMENT_MISMATCH,
        learner_codes.RESOLUTIONS_NOT_FOUND,
        learner_codes.RESOLUTIONS_INVALID,
        learner_codes.UNKNOWN_TAB,
    }:
        return "engine"
    return "writer"


def _lesson(plan: dict[str, Any], n: int) -> dict[str, Any]:
    return next(item for item in plan["lessons"] if item["n"] == n)


def check_3_structure(draft: dict[str, Any], lesson: dict[str, Any]) -> dict[str, Any]:
    steps = lesson.get("steps") or []
    dsteps = draft.get("steps") or []
    if [s["id"] for s in dsteps] != [s["id"] for s in steps]:
        return failure(3, "step_ids_or_order", "writer")
    plan_acts = {a["id"]: a for a in lesson.get("activities") or []}
    if [a["id"] for a in draft.get("activities") or []] != list(plan_acts):
        return failure(3, "activity_ids_or_order", "writer")
    expected_consolidation = lesson.get("consolidation") or []
    if draft["consolidation"]["activities"] != expected_consolidation:
        return failure(3, "consolidation_activities", "writer")
    used: set[str] = set()
    for planned, actual in zip(steps, dsteps, strict=True):
        sid = planned["id"]
        blocks = actual.get("blocks") or []
        refs = [b.get("ref") for b in blocks if b["kind"] == "activity"]
        if refs != (planned.get("practice") or []):
            return failure(3, "step_practice_order", "writer", step=sid)
        host = (lesson.get("dialogue") or {}).get("step")
        if sum(b["kind"] == "dialogue" for b in blocks) != int(host == sid):
            return failure(3, "dialogue_placement", "writer", step=sid)
        expected = set(planned.get("evidence") or [])
        cited = set()
        text_seen = False
        for block in blocks:
            kind = block["kind"]
            if kind in {"dialogue", "quote"}:
                text_seen = True
            if kind == "activity":
                aid = block["ref"]
                if plan_acts.get(aid, {}).get("type") == "true-false" and not text_seen:
                    return failure(3, "true_false_before_text", "writer", step=sid, activity=aid)
                continue
            cited.update(block.get("explains") or [])
            if block.get("ref"):
                cited.add(block["ref"])
        if not expected <= cited:
            return failure(3, f"evidence_missing: {sorted(expected - cited)}", "writer", step=sid)
        used |= cited
    allowed = {e for s in steps for e in s.get("evidence") or []}
    allowed.update(v["evidence"] for v in lesson.get("videos") or [] if isinstance(v, dict) and "evidence" in v)
    if used - allowed:
        return failure(3, f"evidence_not_in_plan: {sorted(used - allowed)}", "writer")
    return _pass(3)


def _forms(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["form"]: f for f in record.get("forms") or [] if f.get("learner") is True}


def check_4_activities(
    draft: dict[str, Any], lesson: dict[str, Any], words: dict[str, Any], pack: dict[str, Any]
) -> tuple[dict[str, Any], dict[tuple[str, int], list[dict[str, Any]]]]:
    records = {w["id"]: w for w in words.get("words") or []}
    errors = {e["id"]: e for e in pack.get("errors") or []}
    planned = {a["id"]: a for a in lesson.get("activities") or []}
    form_options: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for activity in draft.get("activities") or []:
        aid = activity["id"]
        typ = planned[aid]["type"]
        for idx, item in enumerate(activity.get("items") or []):
            if typ == "fill-in" and item.get("mode") == "form-choice":
                record = records.get(item.get("record"))
                forms = _forms(record) if record else {}
                options = item.get("options") or []
                selected = [forms.get(opt) for opt in options]
                answer_form = (
                    next((f for f in record.get("forms") or [] if f.get("tags") == item.get("answer_tags")), None)
                    if record
                    else None
                )
                if (
                    len(options) != len(set(options))
                    or any(f is None for f in selected)
                    or answer_form is None
                    or answer_form.get("form") not in options
                    or item.get("answer") != answer_form.get("form")
                ):
                    return failure(4, "form_choice_options_invalid", "writer", activity=aid, token=str(idx)), {}
                form_options[(aid, idx)] = selected
            if (
                typ == "fill-in"
                and item.get("options")
                and item.get("mode") != "form-choice"
                and item.get("answer") not in item["options"]
            ):
                return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
            if typ == "error-correction":
                er = errors.get(item.get("error_ref"))
                if (
                    er is None
                    or item.get("error_ref") not in (planned[aid].get("error_refs") or [])
                    or er.get("incorrect") not in item.get("sentence", "")
                    or er.get("correct") != item.get("correction", item.get("answer"))
                ):
                    return failure(4, "error_ref_mismatch", "writer", activity=aid, token=str(idx)), {}
            if (
                typ in {"quiz", "multiple-choice"}
                and "correct" in item
                and isinstance(item["correct"], int)
                and not 0 <= item["correct"] < len(item.get("options") or [])
            ):
                return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(idx)), {}
            if "answers" in item and "options" in item and not set(item["answers"]) <= set(item["options"]):
                return failure(4, "answers_not_subset", "writer", activity=aid, token=str(idx)), {}
            if typ == "select":
                correct_count = sum(option.get("correct") is True for option in item.get("options") or [])
                if correct_count < max(2, item.get("min_correct", 2)):
                    return failure(4, "select_correct_set_invalid", "writer", activity=aid, token=str(idx)), {}
            if typ == "quiz" and isinstance(item.get("answer"), str):
                offered = [
                    option.get("text") if isinstance(option, dict) else option for option in item.get("options") or []
                ]
                if item["answer"] not in offered:
                    return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
    return _pass(4), form_options


def check_6_count(expanded: dict[str, Any], target: int, words: dict[str, Any] | None = None) -> dict[str, Any]:
    uk = total = 0
    records = {w["id"]: w for w in (words or {}).get("words") or []}
    for unit in expanded["units"]:
        if unit["tab"] != "urok":
            continue
        if unit["role"] == "gloss_ref":
            match = re.fullmatch(r"\{\{gloss:(W-[0-9]+)\}\}", unit["text"])
            record = records.get(match.group(1)) if match else None
            if record is None:
                return failure(6, "gloss_record_missing", "pack", token=unit["text"])
            lemma_count = len(tokenize(record["lemma"]))
            gloss_count = len(tokenize(record.get("sense_gloss") or record.get("gloss_en") or ""))
            uk += lemma_count
            total += lemma_count + gloss_count
            continue
        for token in tokenize(unit["text"]):
            total += 1
            if token.kind == "cyrillic" and unit["role"] != "vesum_exempt":
                uk += 1
    details = {
        "urok_tokens": total,
        "ukrainian_tokens": uk,
        "ukrainian_share": round(uk / total, 6) if total else 0,
        "word_target": target,
        "not_checked": ["word_target_not_calibrated", "lesson_structural_minimums_not_calibrated"],
    }
    if total < target:
        return {**failure(6, "word_target_below_minimum", "writer"), "details": details}
    return _pass(6, details)


def check_7_deterministic(
    stream: Any,
    lesson: dict[str, Any],
    draft: dict[str, Any] | None = None,
    form_options: dict[tuple[str, int], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    for forms in (form_options or {}).values():
        for form in forms:
            if form.get("stress_source") == "pending" or not form.get("stressed"):
                return failure(7, "pending_stress", "pack", token=form.get("form"))
    if stream.failures:
        first = stream.failures[0]
        layer = (
            "pack"
            if first["code"] in {codes.LEMMA_OUTSIDE_STATE, codes.UNKNOWN_WORD_ID, codes.PENDING_STRESS}
            else "writer"
        )
        return failure(
            7,
            first.get("message") or first["code"],
            layer,
            code=first["code"],
            step=first["unit"].get("step"),
            activity=first["unit"].get("activity"),
            token=first["token"],
        )
    vocab = (lesson.get("inventory") or {}).get("vocabulary") or {}
    drilled_forms = {
        (item["record"], form["tags"])
        for act in (draft or {}).get("activities") or []
        for idx, item in enumerate(act.get("items") or [])
        for form in (form_options or {}).get((act["id"], idx), [])
    }
    for group in ("core", "recycled"):
        for item in vocab.get(group) or []:
            rid = item["evidence"] if isinstance(item, dict) else item
            if not any(
                t["unit"].get("tab") in {"urok", "vpravy"} and rid in t.get("candidates", []) for t in stream.tokens
            ):
                return failure(7, f"{group}_record_absent", "writer", token=rid)
    for item in vocab.get("core") or []:
        for tag in item.get("forms") or []:
            if (item["evidence"], tag) in drilled_forms:
                continue
            if not any(
                item["evidence"] in t.get("candidates", [])
                and any(tag in r.get("forms", []) for r in t.get("readings", []))
                and (t["unit"].get("step") is not None or t["unit"].get("activity") is not None)
                for t in stream.tokens
            ):
                return failure(7, "taught_form_not_in_teaching_position", "writer", token=f"{item['evidence']}:{tag}")
    return _pass(7, {"tokens": len(stream.tokens), "open_questions": len(stream.open_tokens())})


def dispatch_questions(batch: dict[str, Any], seat: str, *, repo_root: Path) -> dict[str, Any]:
    """Dispatch a bounded language-seat question batch, await, and parse answers."""
    agent, separator, model = seat.partition(":")
    if not separator or not agent or not model:
        raise ValueError("question seat must be agent:model")
    state = repo_root / "batch_state" / "tasks"
    state.mkdir(parents=True, exist_ok=True)
    task_id = (
        f"questions-{batch['lesson']['level']}-{batch['lesson']['slug']}-{batch['lesson']['n']}-{uuid.uuid4().hex[:8]}"
    )
    prompt = state / f"{task_id}.prompt.md"
    instruction = (
        "Choose exactly one offered candidate for every question using its sentence. "
        "Return only YAML with an answers list; each entry has id and record, "
        "and stressed when a record has multiple offered readings. "
        "Use only offered record identifiers and stressed spellings.\n\n"
    )
    lock.atomic_write(prompt, instruction.encode("utf-8") + lock.yaml_bytes(batch))
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "delegate.py"),
        "dispatch",
        "--agent",
        agent,
        "--model",
        model,
        "--mode",
        "read-only",
        "--worktree",
        "--task-id",
        task_id,
        "--prompt-file",
        str(prompt),
        "--research-role",
        "writer",
        "--research-task-family",
        "constrained-resolution",
        "--research-track",
        batch["lesson"]["level"],
        "--research-owned-path",
        f"curriculum/l2-uk-en/evidence/{batch['lesson']['level']}/_state/"
        f"{batch['lesson']['slug']}/lesson-{batch['lesson']['n']}.questions.yaml",
    ]
    sent = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if sent.returncode:
        raise RuntimeError(f"question dispatch failed: {sent.stderr.strip()}")
    done = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "delegate.py"), "wait", task_id, "--timeout", "1800"],
        capture_output=True,
        text=True,
        timeout=1830,
        check=False,
    )
    if done.returncode:
        raise RuntimeError(f"question wait failed: {done.stderr.strip()}")
    result = json.loads(done.stdout)
    if result.get("status") != "done" or not result.get("result_file"):
        raise RuntimeError("question dispatch did not finish with an answer file")
    return yaml.safe_load(strip_markdown_fence(Path(result["result_file"]).read_text(encoding="utf-8")))


def _printable_form_draft(
    draft: dict[str, Any], choices: dict[tuple[str, int], list[dict[str, Any]]]
) -> dict[str, Any]:
    rendered = copy.deepcopy(draft)
    for act in rendered.get("activities") or []:
        for idx, item in enumerate(act.get("items") or []):
            forms = choices.get((act["id"], idx))
            if forms is None:
                continue
            item["options"] = [f["stressed"] for f in forms]
            answer = next(f for f in forms if f["tags"] == item["answer_tags"])
            item["answer"] = answer["stressed"]
    return rendered


def _printable_form_expanded(
    expanded: dict[str, Any], choices: dict[tuple[str, int], list[dict[str, Any]]]
) -> dict[str, Any]:
    rendered = copy.deepcopy(expanded)
    for unit in rendered["units"]:
        if unit["tab"] != "vpravy" or not isinstance(unit["item"], int):
            continue
        forms = choices.get((unit["activity"], unit["item"]))
        block = unit["block"]
        if forms is not None and isinstance(block, str) and block.startswith("opt_"):
            index = int(block[4:])
            unit["text"] = forms[index]["stressed"]
    return rendered


def run_lesson(
    level: str,
    slug: str,
    n: int,
    *,
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words: dict[str, Any],
    state_dir: Path,
    repo_root: Path,
    plans_dir: Path,
    evidence_dir: Path,
    question_seat: str | None = None,
    question_dispatch: QuestionDispatch | None = None,
    sources: Any = None,
    allowlist: Allowlist | None = None,
    site_dir: Path | None = None,
    expected_inputs: dict[str, str] | None = None,
    inventory_gate: Callable[..., Any] = check_lesson,
    observed_writer: Callable[..., Any] = write_observed,
    render_check: Callable[..., Any] = check_11_render,
) -> dict[str, Any]:
    """Stop at the first failed check; write a schema-valid gate report each run."""
    from scripts.curriculum.evidence.sources import Sources
    from scripts.curriculum.resolver.stream import load_allowlist

    state_dir.mkdir(parents=True, exist_ok=True)
    unlink_current(state_dir, n)
    rows: list[dict[str, Any]] = []
    inputs = expected_inputs or {}
    ledger_inputs = {
        "plan_sha256": inputs.get("plan_sha256") or hashlib.sha256(lock.yaml_bytes(plan)).hexdigest(),
        "pack_lock": inputs.get("pack_lock") or hashlib.sha256(lock.yaml_bytes(pack)).hexdigest(),
        "words_lock": inputs.get("words_lock") or hashlib.sha256(lock.yaml_bytes(words)).hexdigest(),
        "card_sha256": inputs.get("style_card_sha256") or "0" * 64,
        "prompt_sha256": inputs.get("prompt_sha256") or "0" * 64,
    }
    gate_path = state_dir / f"lesson-{n}.gates.yaml"
    ledger_path = state_dir / f"lesson-{n}.regeneration.yaml"

    def finish(row: dict[str, Any] | None = None) -> dict[str, Any]:
        if row is not None:
            rows[:] = [prior for prior in rows if prior["check"] != row["check"]]
            rows.append(row)
        existing = {prior["check"] for prior in rows}
        for number in range(1, 10):
            if number not in existing:
                rows.append({"check": number, "status": "not_checked", "reason": "prior_check_failed"})
        rows.sort(key=lambda prior: prior["check"])
        for number in (10, 11):
            if number not in {r["check"] for r in rows}:
                rows.append({"check": number, "status": "not_checked", "reason": "prior_check_failed"})
        rows.sort(key=lambda prior: prior["check"])
        doc = {
            "level": level,
            "slug": slug,
            "n": n,
            "passed": all(r["status"] != "failed" for r in rows),
            "checks": rows,
        }
        Draft202012Validator(
            json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(encoding="utf-8"))
        ).validate(doc)
        lock.write(gate_path, lock.yaml_bytes(doc))
        bad = next((r for r in rows if r["status"] == "failed"), None)
        if bad is not None:
            record_failure(ledger_path, slug, n, bad, ledger_inputs)
        return {**doc, "passed_through": bad["check"] if bad else 11, "manifest_sha256": None}

    previous = load_ledger(ledger_path, slug, n)
    if previous["terminal_layer"] is not None:
        return finish(failure(1, "regeneration_terminal", previous["terminal_layer"]))
    if previous["attempts"]:
        invalidate_lesson_resolution(state_dir, n)

    lesson = _lesson(plan, n)
    activity_types = {a["id"]: a["type"] for a in lesson.get("activities") or []}
    errors = validate_draft(draft, level, activity_types=activity_types)
    if errors:
        err = errors[0]
        return finish(failure(1, f"{err.check}: {err.reason}", "writer", token=err.path))
    if draft["lesson"] != {"module": f"{level}/{slug}", "n": n}:
        return finish(failure(1, "lesson_identity_mismatch", "writer"))
    for key, value in inputs.items():
        if key in draft["inputs"] and draft["inputs"][key] != value:
            return finish(failure(1, f"input_hash_mismatch: {key}", "writer"))
    rows.append(_pass(1))
    if draft["status"] == "evidence_gap":
        gap = draft["gaps"][0]
        return finish(failure(2, gap.get("detail") or "evidence_gap", "pack", step=gap.get("step")))
    rows.append(_pass(2))
    row = check_3_structure(draft, lesson)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    row, form_options = check_4_activities(draft, lesson, words, pack)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    assembled = check_5_assembly(draft, plan, pack, words, level, slug, n, output_dir=state_dir)
    if not assembled.passed:
        return finish(
            failure(
                5,
                assembled.reason or "assembly_failed",
                assembled.layer or "engine",
                step=assembled.step,
                activity=assembled.activity,
                token=assembled.token,
            )
        )
    expanded = assembled.artifacts["expanded_doc"]
    rows.append(_pass(5))
    row = check_6_count(expanded, lesson["word_target"], words)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    try:
        expanded_obj = ExpandedDocument.from_data(expanded)
        selected_allowlist = allowlist or load_allowlist(level, slug, n, plans_dir=plans_dir, evidence_dir=evidence_dir)
        if sources is None:
            with Sources() as source_client:
                stream = resolve(expanded_obj, selected_allowlist, source_client)
        else:
            stream = resolve(expanded_obj, selected_allowlist, sources)
    except ResolverError as err:
        layer = "pack" if err.code in {codes.UNKNOWN_WORD_ID, codes.LOCK_MISMATCH} else "engine"
        return finish(failure(7, err.message, layer, code=err.code))
    except (OSError, ValueError) as err:
        return finish(failure(7, f"resolver_input_unavailable: {err}", "pack"))
    except Exception as err:
        return finish(failure(7, f"resolver_error: {err}", "engine"))
    row = check_7_deterministic(stream, lesson, draft, form_options)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    # Questions omit step, while receipts retain it for digest provenance.
    token_steps = [token["unit"].pop("step", None) for token in stream.tokens]
    batch = questions.build_questions(stream, expanded_obj, selected_allowlist)
    try:
        questions.write_questions(state_dir / f"lesson-{n}.questions.yaml", batch)
    except (ResolverError, OSError) as err:
        return finish(failure(8, f"question_batch_invalid: {err}", "engine", code=getattr(err, "code", None)))
    if batch["questions"] and not question_seat:
        return finish(failure(8, "question_seat_required", "driver"))
    if batch["questions"] and (question_seat.count(":") != 1 or not all(question_seat.split(":"))):
        return finish(failure(8, "question_seat_invalid", "driver"))
    try:
        if batch["questions"]:
            answer_doc = (question_dispatch or (lambda b, s: dispatch_questions(b, s, repo_root=repo_root)))(
                batch, question_seat
            )
            selections = receipts.apply_answers(batch, answer_doc, question_seat.replace(":", "@"))
            if len(selections) != len(batch["questions"]):
                raise ResolverError(
                    codes.TOKEN_UNRESOLVED, "every question must be answered before inventory and rendering"
                )
        else:
            selections = {}
        receipt_doc = receipts.build_receipts(
            stream, batch, selections, question_seat.replace(":", "@") if question_seat else None
        )
        for receipt, step in zip(receipt_doc["tokens"], token_steps, strict=True):
            if step is not None:
                receipt["unit"]["step"] = step
        receipt_path = state_dir / f"lesson-{n}.resolutions.yaml"
        receipt_sha = receipts.write_receipts(receipt_path, receipt_doc)
        for token, receipt in zip(stream.tokens, receipt_doc["tokens"], strict=True):
            token["selected"] = receipt["selected"]
            token["provenance"] = receipt["provenance"]
        for token, step in zip(stream.tokens, token_steps, strict=True):
            if step is not None:
                token["unit"] = {**token["unit"], "step": step}
        stream.inputs["receipts_sha256"] = receipt_sha
    except (ResolverError, ValueError, RuntimeError, OSError) as err:
        return finish(
            failure(
                8, str(err), "writer" if isinstance(err, ResolverError) else "driver", code=getattr(err, "code", None)
            )
        )
    rows.append(_pass(8, {"questions": len(batch["questions"]), "answered": len(selections)}))
    try:
        gate = inventory_gate(
            level,
            slug,
            n,
            stream,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            expanded=expanded_obj,
            resolutions_path=receipt_path,
        )
    except Exception as err:
        return finish(failure(7, f"inventory_gate_error: {err}", "engine"))
    if not gate.ok:
        first = gate.failures[0]
        return finish(failure(7, first.message, _inventory_layer(first.code), code=first.code, token=first.token))
    try:
        observed_writer(
            level,
            slug,
            n,
            resolutions_doc=receipt_doc,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            expanded=expanded_obj,
            state_dir=state_dir,
        )
    except ObservedError as err:
        return finish(failure(7, err.message, _inventory_layer(err.code), code=err.code))
    except Exception as err:
        return finish(failure(7, f"observed_index_error: {err}", "engine"))
    print_draft = _printable_form_draft(draft, form_options)
    print_expanded = _printable_form_expanded(expanded, form_options)
    try:
        rendered = check_9_stress_and_render(
            print_expanded,
            print_draft,
            plan,
            pack,
            words,
            stream,
            level,
            slug,
            n,
            repo_root=repo_root,
            output_dir=state_dir,
            site_dir=site_dir,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
        )
    except Exception as err:
        return finish(failure(9, f"stress_or_render_error: {err}", "engine"))
    if not rendered.passed:
        layer = rendered.layer or "engine"
        return finish(
            failure(
                9,
                rendered.reason or "stress_or_render_failed",
                layer,
                step=rendered.step,
                activity=rendered.activity,
                token=rendered.token,
            )
        )
    rows.append(_pass(9))
    rows.append({"check": 10, "status": "not_checked", "reason": "grammar_checker_undecided"})
    (repo_root / "batch_state" / "verify_shippable").mkdir(parents=True, exist_ok=True)
    try:
        rendered_check = render_check(
            level, slug, astro_build=True, module_dir=site_dir, plan_path=plans_dir / f"{slug}.yaml"
        )
    except Exception as err:
        return finish(failure(11, f"verify_shippable_error: {err}", "engine"))
    if not rendered_check.passed:
        row = failure(11, rendered_check.reason or "verify_shippable_failed", "engine")
        row["details"] = {"verify_shippable": rendered_check.artifacts.get("verify_shippable", {})}
        return finish(row)
    rows.append(_pass(11, {"verify_shippable": rendered_check.artifacts.get("verify_shippable", {})}))
    gate = finish()
    try:
        manifest, digest = write_manifest(
            level,
            slug,
            n,
            lesson_kind="recap" if lesson.get("kind") == "recap" else "lesson",
            state_dir=state_dir,
            repo_root=repo_root,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
            position=plan.get("arc_ref", {}).get("position", 1),
            site_dir=site_dir,
        )
    except Exception as err:
        reason = f"digest_error:{err.code}: {err.message}" if isinstance(err, DigestError) else str(err)
        path = getattr(err, "path", None) or (err.filename if isinstance(err, OSError) and err.filename else reason)
        write_manifest_error(state_dir, n, reason, str(path), datetime.now(UTC).isoformat().replace("+00:00", "Z"))
        bad = failure(12, reason, "engine")
        record_failure(ledger_path, slug, n, bad, ledger_inputs)
        return {
            **gate,
            "passed": False,
            "passed_through": 12,
            "stopping_check": 12,
            "reason": reason,
            "manifest_sha256": None,
        }
    draft_path = state_dir / f"lesson-{n}.draft.yaml"
    success_inputs = {**ledger_inputs, "draft_sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest()}
    record_success(ledger_path, slug, n, success_inputs)
    return {**gate, "passed_through": 12, "manifest_sha256": digest, "manifest": manifest}
