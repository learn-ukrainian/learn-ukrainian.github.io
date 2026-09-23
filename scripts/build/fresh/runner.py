"""Ordered, fail-closed checks 1-9 for one fresh lesson."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.assemble import check_5_assembly, check_9_stress_and_render
from scripts.build.fresh.draft_schema import validate_draft
from scripts.build.fresh.regeneration import invalidate_lesson_resolution, load_ledger, record_failure
from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state.inventory_gate import check_lesson
from scripts.curriculum.learner_state.observed import write_observed
from scripts.curriculum.resolver import codes, questions, receipts
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.stream import resolve
from scripts.curriculum.resolver.tokenize import tokenize

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "fresh-lesson-gates-v1.schema.json"
QuestionDispatch = Callable[[dict[str, Any], str], dict[str, Any]]


def failure(check: int, reason: str, layer: str, *, code: str | None = None, step: str | None = None,
            activity: str | None = None, token: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"check": check, "status": "failed", "code": code or str(check), "reason": reason, "layer": layer}
    for key, value in (("step", step), ("activity", activity), ("token", token)):
        if value is not None:
            row[key] = str(value)
    return row


def _pass(number: int, details: dict[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"check": number, "status": "passed"}
    if details is not None:
        row["details"] = details
    return row


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
    expected_consolidation = [a["id"] for a in lesson.get("activities") or [] if a.get("placement") == "consolidation"]
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
    allowed.update(v["id"] for v in lesson.get("videos") or [] if isinstance(v, dict) and "id" in v)
    if used - allowed:
        return failure(3, f"evidence_not_in_plan: {sorted(used - allowed)}", "writer")
    return _pass(3)


def _forms(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["form"]: f for f in record.get("forms") or [] if f.get("learner") is True}


def check_4_activities(draft: dict[str, Any], lesson: dict[str, Any], words: dict[str, Any],
                       pack: dict[str, Any]) -> tuple[dict[str, Any], dict[tuple[str, int], list[dict[str, Any]]]]:
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
                answer_form = next((f for f in record.get("forms") or [] if f.get("tags") == item.get("answer_tags")), None) if record else None
                if (len(options) != len(set(options)) or any(f is None for f in selected)
                        or answer_form is None or answer_form.get("form") not in options
                        or item.get("answer") != answer_form.get("form")):
                    return failure(4, "form_choice_options_invalid", "writer", activity=aid, token=str(idx)), {}
                form_options[(aid, idx)] = selected
            if (typ == "fill-in" and item.get("options") and item.get("mode") != "form-choice"
                    and item.get("answer") not in item["options"]):
                return failure(4, "answer_not_in_options", "writer", activity=aid, token=str(idx)), {}
            if typ == "error-correction":
                er = errors.get(item.get("error_ref"))
                if (er is None or er.get("incorrect") not in item.get("sentence", "")
                        or er.get("correct") != item.get("correction", item.get("answer"))):
                    return failure(4, "error_ref_mismatch", "writer", activity=aid, token=str(idx)), {}
            if (typ in {"quiz", "multiple-choice"} and "correct" in item and isinstance(item["correct"], int)
                    and not 0 <= item["correct"] < len(item.get("options") or [])):
                return failure(4, "answer_index_out_of_range", "writer", activity=aid, token=str(idx)), {}
            if "answers" in item and "options" in item and not set(item["answers"]) <= set(item["options"]):
                return failure(4, "answers_not_subset", "writer", activity=aid, token=str(idx)), {}
    return _pass(4), form_options


def check_6_count(expanded: dict[str, Any], target: int) -> dict[str, Any]:
    uk = total = 0
    for unit in expanded["units"]:
        if unit["tab"] != "urok":
            continue
        for token in tokenize(unit["text"]):
            total += 1
            if token.kind == "cyrillic" and unit["role"] != "vesum_exempt":
                uk += 1
    details = {"urok_tokens": total, "ukrainian_tokens": uk,
               "ukrainian_share": round(uk / total, 6) if total else 0,
               "word_target": target, "not_checked": ["word_target_not_calibrated",
                                                      "lesson_structural_minimums_not_calibrated"]}
    if total < target:
        return {**failure(6, "word_target_below_minimum", "writer"), "details": details}
    return _pass(6, details)


def check_7_deterministic(stream: Any, lesson: dict[str, Any]) -> dict[str, Any]:
    if stream.failures:
        first = stream.failures[0]
        layer = "pack" if first["code"] in {codes.LEMMA_OUTSIDE_STATE, codes.UNKNOWN_WORD_ID} else "writer"
        return failure(7, first.get("message") or first["code"], layer, code=first["code"],
                       step=first["unit"].get("step"), activity=first["unit"].get("activity"), token=first["token"])
    vocab = (lesson.get("inventory") or {}).get("vocabulary") or {}
    for group in ("core", "recycled"):
        for item in vocab.get(group) or []:
            rid = item["evidence"] if isinstance(item, dict) else item
            if not any(rid in t.get("candidates", []) for t in stream.tokens):
                return failure(7, f"{group}_record_absent", "writer", token=rid)
    for item in vocab.get("core") or []:
        for tag in item.get("forms") or []:
            if not any(item["evidence"] in t.get("candidates", [])
                       and any(tag in r.get("forms", []) for r in t.get("readings", []))
                       and (t["unit"].get("step") is not None or t["unit"].get("activity") is not None)
                       for t in stream.tokens):
                return failure(7, "taught_form_not_in_teaching_position", "writer", token=f"{item['evidence']}:{tag}")
    return _pass(7, {"tokens": len(stream.tokens), "open_questions": len(stream.open_tokens())})


def dispatch_questions(batch: dict[str, Any], seat: str, *, repo_root: Path) -> dict[str, Any]:
    """Dispatch a bounded language-seat question batch, await, and parse answers."""
    agent, separator, model = seat.partition(":")
    if not separator or not agent or not model:
        raise ValueError("question seat must be agent:model")
    state = repo_root / "batch_state" / "tasks"
    state.mkdir(parents=True, exist_ok=True)
    task_id = f"questions-{batch['lesson']['level']}-{batch['lesson']['slug']}-{batch['lesson']['n']}"
    prompt = state / f"{task_id}.prompt.yaml"
    lock.atomic_write(prompt, lock.yaml_bytes(batch))
    cmd = [sys.executable, str(repo_root / "scripts" / "delegate.py"), "dispatch", "--agent", agent,
           "--model", model, "--mode", "read-only", "--worktree", "--task-id", task_id,
           "--prompt-file", str(prompt), "--research-role", "writer"]
    sent = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if sent.returncode:
        raise RuntimeError(f"question dispatch failed: {sent.stderr.strip()}")
    done = subprocess.run([sys.executable, str(repo_root / "scripts" / "delegate.py"), "wait", task_id],
                          capture_output=True, text=True, timeout=1800, check=False)
    if done.returncode:
        raise RuntimeError(f"question wait failed: {done.stderr.strip()}")
    result = json.loads(done.stdout)
    return yaml.safe_load(Path(result["result_file"]).read_text(encoding="utf-8"))


def _printable_form_draft(draft: dict[str, Any], choices: dict[tuple[str, int], list[dict[str, Any]]]) -> dict[str, Any]:
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


def run_lesson(level: str, slug: str, n: int, *, draft: dict[str, Any], plan: dict[str, Any],
               pack: dict[str, Any], words: dict[str, Any], state_dir: Path, repo_root: Path,
               plans_dir: Path, evidence_dir: Path, question_seat: str | None = None,
               question_dispatch: QuestionDispatch | None = None, sources: Any = None,
               allowlist: Allowlist | None = None, site_dir: Path | None = None,
               expected_inputs: dict[str, str] | None = None, inventory_gate: Callable[..., Any] = check_lesson,
               observed_writer: Callable[..., Any] = write_observed) -> dict[str, Any]:
    """Stop at the first failed check; write a schema-valid gate report each run."""
    from scripts.curriculum.evidence.sources import Sources
    from scripts.curriculum.resolver.stream import load_allowlist

    state_dir.mkdir(parents=True, exist_ok=True)
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
        rows.extend({"check": number, "status": "not_checked", "reason": "e3b2_pending"} for number in (10, 11, 12))
        doc = {"level": level, "slug": slug, "n": n,
               "passed": all(r["status"] != "failed" for r in rows), "checks": rows}
        Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(doc)
        lock.write(gate_path, lock.yaml_bytes(doc))
        bad = next((r for r in rows if r["status"] == "failed"), None)
        if bad is not None:
            record_failure(ledger_path, slug, n, bad, ledger_inputs)
        return doc

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
        return finish(failure(5, assembled.reason or "assembly_failed", assembled.layer or "engine",
                              step=assembled.step, activity=assembled.activity, token=assembled.token))
    expanded = assembled.artifacts["expanded_doc"]
    rows.append(_pass(5))
    row = check_6_count(expanded, lesson["word_target"])
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
    row = check_7_deterministic(stream, lesson)
    if row["status"] == "failed":
        return finish(row)
    rows.append(row)
    batch = questions.build_questions(stream, expanded_obj, selected_allowlist)
    if batch["questions"] and not question_seat:
        return finish(failure(8, "question_seat_required", "driver"))
    try:
        questions.write_questions(state_dir / f"lesson-{n}.questions.yaml", batch)
        if batch["questions"]:
            answer_doc = (question_dispatch or (lambda b, s: dispatch_questions(b, s, repo_root=repo_root)))(batch, question_seat)
            selections = receipts.apply_answers(batch, answer_doc, question_seat.replace(":", "@"))
            if len(selections) != len(batch["questions"]):
                raise ResolverError(codes.TOKEN_UNRESOLVED, "every question must be answered before inventory and rendering")
        else:
            selections = {}
        receipt_doc = receipts.build_receipts(stream, batch, selections,
                                              question_seat.replace(":", "@") if question_seat else None)
        receipt_path = state_dir / f"lesson-{n}.resolutions.yaml"
        receipt_sha = receipts.write_receipts(receipt_path, receipt_doc)
        for token, receipt in zip(stream.tokens, receipt_doc["tokens"], strict=True):
            token["selected"] = receipt["selected"]
            token["provenance"] = receipt["provenance"]
        stream.inputs["receipts_sha256"] = receipt_sha
    except (ResolverError, ValueError, RuntimeError, OSError) as err:
        return finish(failure(8, str(err), "writer" if isinstance(err, ResolverError) else "driver",
                              code=getattr(err, "code", None)))
    rows.append(_pass(8, {"questions": len(batch["questions"]), "answered": len(selections)}))
    gate = inventory_gate(level, slug, n, stream, plans_dir=plans_dir, evidence_dir=evidence_dir,
                          expanded=expanded_obj, resolutions_path=receipt_path)
    if not gate.ok:
        first = gate.failures[0]
        return finish(failure(7, first.message, "pack" if first.code in {codes.UNKNOWN_WORD_ID, codes.LEMMA_OUTSIDE_STATE} else "writer",
                              code=first.code, token=first.token))
    observed_writer(level, slug, n, resolutions_doc=receipt_doc, plans_dir=plans_dir,
                    evidence_dir=evidence_dir, expanded=expanded_obj, state_dir=state_dir)
    print_draft = _printable_form_draft(draft, form_options)
    rendered = check_9_stress_and_render(expanded, print_draft, plan, pack, words, stream, level, slug, n,
                                         repo_root=repo_root, output_dir=state_dir, site_dir=site_dir,
                                         plans_dir=plans_dir, evidence_dir=evidence_dir)
    if not rendered.passed:
        layer = rendered.layer or "engine"
        return finish(failure(9, rendered.reason or "stress_or_render_failed", layer,
                              step=rendered.step, activity=rendered.activity, token=rendered.token))
    rows.append(_pass(9))
    return finish()
