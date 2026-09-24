"""Assembler for fresh build engine Part E3a (issue #8397, #8431 r3).

Pure functions for:
- Check 5: draft -> expanded document (plain forms only, step ids on units, provenance)
- Check 9: apply stress -> lesson-<n>.stressed.yaml, Slovnyk, Resursy, locks, frontmatter, render MDX
- Check 11: verify_shippable --fresh

Rule 3 compliance: Zero Cyrillic string literals in this module. All Ukrainian text
comes from records (pack, word store) or the writer's resolved draft.
Rule 4 (R-11) compliance: No forbidden paths.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.evidence.sources import Sources
from scripts.curriculum.learner_state.immersion import compute_lesson_immersion_band
from scripts.curriculum.learner_state.planned import PlannedStateError, planned_state
from scripts.curriculum.resolver import codes as resolver_codes
from scripts.curriculum.resolver.classify import GLOSS_ID_RE
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.stream import resolve
from scripts.generate_mdx.atlas_links import atlas_href_for
from scripts.generate_mdx.core import generate_mdx

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPANDED_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-expanded-v1.schema.json"

_CACHED_EXPANDED_VALIDATOR: Draft202012Validator | None = None

# Failure codes
EXAMPLE_NOT_FOUND = "example_not_found"
TEXT_NOT_FOUND = "text_not_found"
PARADIGM_NOT_FOUND = "paradigm_not_found"
WORD_NOT_FOUND = "word_not_found"
FORM_NOT_FOUND = "form_not_found"
VIDEO_NOT_FOUND = "video_not_found"
ACTIVITY_NOT_FOUND = "activity_not_found"
DRAFT_STATUS_NOT_OK = "draft_status_not_ok"
PRIOR_PLANS_MISSING = "prior_plans_missing"
LOCK_CHECK_FAILED = "lock_check_failed"
LESSON_LOCK_ENTRY_MISSING = "lesson_lock_entry_missing"
LESSON_LOCK_MISMATCH = "lesson_lock_mismatch"
IMMERSION_BAND_FAILED = "immersion_band_failed"
STREAM_BLOCKED = "stream_blocked"


class AssemblerError(Exception):
    """Failure during lesson assembly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def get_expanded_validator(schema_path: Path | None = None) -> Draft202012Validator:
    global _CACHED_EXPANDED_VALIDATOR
    if _CACHED_EXPANDED_VALIDATOR is None:
        path = schema_path or checked_existing_path(REPO_ROOT, EXPANDED_SCHEMA_PATH, "schemas")
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _CACHED_EXPANDED_VALIDATOR = Draft202012Validator(schema)
    return _CACHED_EXPANDED_VALIDATOR


def strip_accents(text: str) -> str:
    """Strip combining grave (U+0300) and combining acute (U+0301) accents."""
    return text.replace("\u0300", "").replace("\u0301", "")


@dataclass(frozen=True)
class CheckResult:
    check: int
    passed: bool
    step: str | None = None
    activity: str | None = None
    token: str | None = None
    reason: str | None = None
    layer: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"check": self.check, "passed": self.passed}
        if self.step is not None:
            result["step"] = self.step
        if self.activity is not None:
            result["activity"] = self.activity
        if self.token is not None:
            result["token"] = self.token
        if self.reason is not None:
            result["reason"] = self.reason
        if self.layer is not None:
            result["layer"] = self.layer
        return result


def _split_inline_spans(text: str, default_role: str) -> list[tuple[str, str]]:
    """Split text with inline markup into (role, text) spans.

    Matches {{uk:...}} as quoted_term and {{gloss:W-...}} as gloss_ref.
    All other text receives default_role.
    """
    pattern = re.compile(r"(\{\{uk:[^{}\u0300\u0301]+\}\}|\{\{gloss:W-[0-9]+\}\})")
    parts = pattern.split(text)
    spans: list[tuple[str, str]] = []
    uk_re = re.compile(r"^\{\{uk:([^{}\u0300\u0301]+)\}\}$")
    gloss_re = re.compile(r"^\{\{gloss:(W-[0-9]+)\}\}$")

    for part in parts:
        if not part:
            continue
        uk_match = uk_re.match(part)
        if uk_match:
            spans.append(("quoted_term", strip_accents(uk_match.group(1))))
            continue
        gloss_match = gloss_re.match(part)
        if gloss_match:
            spans.append(("gloss_ref", strip_accents(part)))
            continue
        spans.append((default_role, part))

    return spans


def assemble_expanded_document(
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    level: str,
    slug: str,
    lesson_n: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assemble lesson draft into expanded document and provenance structures.

    Returns (expanded_doc_dict, provenance_dict).
    Every unit carries 'step' (plan step id, or None for tabs without steps).
    Plain forms only: quotes, examples, paradigms, glosses have accents stripped.
    Fails closed with named AssemblerError codes on missing records.
    """
    status = draft.get("status")
    if status != "ok":
        raise AssemblerError(DRAFT_STATUS_NOT_OK, f"draft status is {status!r}, expected 'ok'")

    lesson_entry: dict[str, Any] = {}
    for entry in plan.get("lessons", []):
        if isinstance(entry, dict) and entry.get("n") == lesson_n:
            lesson_entry = entry
            break
    if not lesson_entry:
        raise AssemblerError("lesson_not_found", f"lesson {lesson_n} not found in plan")

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    examples_by_id: dict[str, dict[str, Any]] = {}
    for ex in pack.get("examples", []):
        if isinstance(ex, dict) and "id" in ex:
            examples_by_id[ex["id"]] = ex

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    paradigms_by_id: dict[str, dict[str, Any]] = {}
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict) and "paradigm" in st and isinstance(st["paradigm"], dict):
            pid = st["paradigm"].get("id")
            if pid:
                paradigms_by_id[pid] = st["paradigm"]

    units: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []

    def add_unit(
        tab: str,
        step: str | None,
        activity: str | None,
        item: int | None,
        block: int | str,
        role: str,
        text: str,
        *,
        source: str = "writer_prose",
        ref: str | None = None,
    ) -> None:
        clean = strip_accents(text) if source != "writer_prose" else text
        units.append(
            {
                "tab": tab,
                "step": step,
                "activity": activity,
                "item": item,
                "block": block,
                "role": role,
                "text": clean,
            }
        )
        spans.append(
            {
                "tab": tab,
                "step": step,
                "activity": activity,
                "item": item,
                "block": block,
                "source": source,
                "ref": ref,
                "text": clean,
            }
        )

    # 1. Tab: urok (Lesson)
    for step in draft.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        lead_in = step.get("lead_in")
        if lead_in:
            for role, span_text in _split_inline_spans(lead_in, "narration"):
                add_unit("urok", step_id, None, None, "lead_in", role, span_text, source="writer_prose")

        blocks = step.get("blocks", [])
        for block_idx, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "prose":
                prose_text = block.get("text", "")
                for role, span_text in _split_inline_spans(prose_text, "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "example":
                ref_id = block.get("ref", "")
                ex_rec = examples_by_id.get(ref_id)
                if ex_rec is None:
                    raise AssemblerError(EXAMPLE_NOT_FOUND, f"example record {ref_id} not found in pack")
                ex_text = str(ex_rec.get("text", ""))
                add_unit("urok", step_id, None, None, block_idx, "record_print", ex_text, source="record", ref=ref_id)

            elif kind == "quote":
                ref_id = block.get("ref", "")
                t_rec = texts_by_id.get(ref_id)
                if t_rec is None:
                    raise AssemblerError(TEXT_NOT_FOUND, f"quote record {ref_id} not found in pack")
                quote_text = str(t_rec.get("quote", ""))
                add_unit(
                    "urok", step_id, None, None, block_idx, "record_print", quote_text, source="record", ref=ref_id
                )

            elif kind == "paradigm":
                ref_id = block.get("ref", "")
                p_info = paradigms_by_id.get(ref_id)
                if p_info is None:
                    raise AssemblerError(PARADIGM_NOT_FOUND, f"paradigm {ref_id} not found in lesson steps")
                wid = p_info.get("word", "")
                w_rec = words_by_id.get(wid)
                if w_rec is None:
                    raise AssemblerError(
                        WORD_NOT_FOUND, f"word record {wid} for paradigm {ref_id} not found in words store"
                    )
                forms_by_tag = {f.get("tags"): f for f in w_rec.get("forms", []) if isinstance(f, dict)}
                for f_idx, ftag in enumerate(p_info.get("forms", [])):
                    form_entry = forms_by_tag.get(ftag)
                    if form_entry is None:
                        raise AssemblerError(
                            FORM_NOT_FOUND, f"form tag {ftag} not found for word {wid} in paradigm {ref_id}"
                        )
                    p_form_text = str(form_entry.get("form") or form_entry.get("stressed") or "")
                    add_unit(
                        "urok",
                        step_id,
                        None,
                        None,
                        f"paradigm_{block_idx}_{f_idx}",
                        "record_print",
                        p_form_text,
                        source="record",
                        ref=wid,
                    )

            elif kind == "table":
                rows = block.get("rows", [])
                for r_idx, row in enumerate(rows):
                    if isinstance(row, list):
                        for c_idx, cell in enumerate(row):
                            c_str = str(cell)
                            for role, span_text in _split_inline_spans(c_str, "narration"):
                                add_unit(
                                    "urok",
                                    step_id,
                                    None,
                                    None,
                                    f"table_{block_idx}_{r_idx}_{c_idx}",
                                    role,
                                    span_text,
                                    source="writer_prose",
                                )

            elif kind == "pronunciation":
                pron_text = block.get("text", "")
                for role, span_text in _split_inline_spans(pron_text, "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "bilingual":
                uk_lines = block.get("uk", [])
                for line_idx, line in enumerate(uk_lines):
                    l_str = str(line)
                    for role, span_text in _split_inline_spans(l_str, "narration"):
                        add_unit(
                            "urok",
                            step_id,
                            None,
                            None,
                            f"bilingual_{block_idx}_{line_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                        )
                for line_idx, line in enumerate(block.get("en", [])):
                    add_unit("urok", step_id, None, None, f"bilingual_en_{block_idx}_{line_idx}",
                             "vesum_exempt", str(line), source="writer_prose")

            elif kind in ("culture", "tip", "summary", "callout"):
                txt = block.get("text", "")
                for role, span_text in _split_inline_spans(txt, "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "video":
                ref_id = block.get("ref", "")
                vid_rec = videos_by_id.get(ref_id)
                if vid_rec is None:
                    raise AssemblerError(VIDEO_NOT_FOUND, f"video record {ref_id} not found in pack")
                v_lead = block.get("lead_in")
                if v_lead:
                    for role, span_text in _split_inline_spans(v_lead, "narration"):
                        add_unit(
                            "urok",
                            step_id,
                            None,
                            None,
                            f"video_lead_{block_idx}",
                            role,
                            span_text,
                            source="writer_prose",
                        )

            elif kind == "dialogue":
                dial = draft.get("dialogue") or {}
                for line_idx, line in enumerate(dial.get("lines", [])):
                    if isinstance(line, dict):
                        l_text = str(line.get("text", ""))
                        for role, span_text in _split_inline_spans(l_text, "dialogue_line"):
                            add_unit(
                                "urok",
                                step_id,
                                None,
                                None,
                                f"dialogue_{line_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )
                for line_idx, line in enumerate(dial.get("translation_en") or []):
                    add_unit("urok", step_id, None, None, f"dialogue_translation_{line_idx}",
                             "vesum_exempt", str(line), source="writer_prose")

    # Consolidation lead-in
    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        for role, span_text in _split_inline_spans(consol_lead, "narration"):
            add_unit("urok", None, None, None, "consolidation_lead_in", role, span_text, source="writer_prose")

    # 2. Tab: vpravy (Activities)
    act_to_step: dict[str, str] = {}
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict):
            st_id = st.get("id")
            if st_id:
                for act_ref in st.get("practice", []):
                    if isinstance(act_ref, str):
                        act_to_step[act_ref] = st_id

    for st in draft.get("steps", []):
        if isinstance(st, dict):
            st_id = st.get("id")
            if st_id:
                for bl in st.get("blocks", []):
                    if isinstance(bl, dict) and bl.get("kind") == "activity":
                        act_ref = bl.get("ref")
                        if isinstance(act_ref, str):
                            act_to_step[act_ref] = st_id

    plan_acts_by_id = {
        act["id"]: act
        for act in lesson_entry.get("activities", [])
        if isinstance(act, dict) and "id" in act
    }

    for act in draft.get("activities", []):
        if not isinstance(act, dict):
            continue
        act_id = act.get("id")
        if not act_id or act_id not in plan_acts_by_id:
            raise AssemblerError(ACTIVITY_NOT_FOUND, f"draft activity {act_id} not found in plan")
        act_step = act_to_step.get(act_id) if act_id else None
        instr = act.get("instruction")
        if instr:
            for role, span_text in _split_inline_spans(str(instr), "instruction"):
                add_unit("vpravy", act_step, act_id, None, "instruction", role, span_text, source="writer_prose")

        for item_idx, item in enumerate(act.get("items", [])):
            if not isinstance(item, dict):
                continue

            prompt = None
            for key in ("prompt", "sentence", "question", "cue", "statement"):
                val = item.get(key)
                if val is not None and not isinstance(val, bool) and str(val).strip():
                    prompt = str(val)
                    break
            if prompt:
                error_text = item.get("error") if plan_acts_by_id[act_id].get("type") == "error-correction" else None
                if isinstance(error_text, str) and error_text and error_text in prompt:
                    before, after = prompt.split(error_text, 1)
                    for role, span_text in _split_inline_spans(before, "item_prompt"):
                        add_unit("vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose")
                    add_unit("vpravy", act_step, act_id, item_idx, "prompt", "error_text", error_text,
                             source="writer_prose")
                    for role, span_text in _split_inline_spans(after, "item_prompt"):
                        add_unit("vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose")
                else:
                    for role, span_text in _split_inline_spans(prompt, "item_prompt"):
                        add_unit("vpravy", act_step, act_id, item_idx, "prompt", role, span_text, source="writer_prose")

            # Answer-like candidate fields: exclude any boolean value (e.g. true/false activities
            # where answer, correct, is_true, isTrue are boolean flags, not text to resolve/stress).
            answer = None
            for key in ("answer", "correction", "target", "correct", "is_true", "isTrue"):
                val = item.get(key)
                if val is not None and not isinstance(val, bool) and str(val).strip():
                    answer = str(val)
                    break
            if answer:
                for role, span_text in _split_inline_spans(answer, "item_answer"):
                    add_unit("vpravy", act_step, act_id, item_idx, "answer", role, span_text, source="writer_prose")

            opts = item.get("options") or item.get("choices") or item.get("distractors") or []
            for opt_idx, opt in enumerate(opts):
                if isinstance(opt, bool):
                    continue
                opt_val = opt.get("text") if isinstance(opt, dict) else opt
                if opt_val is not None and not isinstance(opt_val, bool):
                    opt_str = str(opt_val)
                    for role, span_text in _split_inline_spans(opt_str, "item_option"):
                        add_unit("vpravy", act_step, act_id, item_idx, f"opt_{opt_idx}", role, span_text, source="writer_prose")

            err_txt = None
            for key in ("error", "incorrect"):
                val = item.get(key)
                if val is not None and not isinstance(val, bool) and str(val).strip():
                    err_txt = str(val)
                    break
            if err_txt:
                for role, span_text in _split_inline_spans(err_txt, "error_text"):
                    add_unit("vpravy", act_step, act_id, item_idx, "error", role, span_text, source="writer_prose")

            expl = item.get("explanation")
            if expl and isinstance(expl, str):
                for role, span_text in _split_inline_spans(expl, "instruction"):
                    add_unit("vpravy", act_step, act_id, item_idx, "explanation", role, span_text, source="writer_prose")

            pairs = item.get("pairs") or []
            for p_idx, pair in enumerate(pairs):
                if isinstance(pair, dict):
                    left = pair.get("left") if not isinstance(pair.get("left"), bool) else None
                    if left is None:
                        left = pair.get("prompt") if not isinstance(pair.get("prompt"), bool) else None
                    right = pair.get("right") if not isinstance(pair.get("right"), bool) else None
                    if right is None:
                        right = pair.get("answer") if not isinstance(pair.get("answer"), bool) else None
                    if left:
                        for role, span_text in _split_inline_spans(str(left), "item_prompt"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"pair_l_{p_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )
                    if right:
                        for role, span_text in _split_inline_spans(str(right), "item_answer"):
                            add_unit(
                                "vpravy",
                                act_step,
                                act_id,
                                item_idx,
                                f"pair_r_{p_idx}",
                                role,
                                span_text,
                                source="writer_prose",
                            )

    # 3. Tab: slovnyk (Vocabulary)
    vocab_inv = lesson_entry.get("inventory", {}).get("vocabulary", {})
    core_items = vocab_inv.get("core", [])
    incidental_items = vocab_inv.get("incidental", [])

    for c in core_items:
        if isinstance(c, dict):
            wid = c.get("evidence")
            if wid:
                w_rec = words_by_id.get(wid)
                if not w_rec:
                    raise AssemblerError(WORD_NOT_FOUND, f"core word {wid} not found in words store")
                lemma = str(w_rec.get("lemma", ""))
                add_unit("slovnyk", None, None, None, f"core_{wid}", "record_print", lemma, source="record", ref=wid)

    for inc in incidental_items:
        wid = inc.get("evidence") if isinstance(inc, dict) else inc
        if isinstance(wid, str):
            w_rec = words_by_id.get(wid)
            if not w_rec:
                raise AssemblerError(WORD_NOT_FOUND, f"incidental word {wid} not found in words store")
            lemma = str(w_rec.get("lemma", ""))
            add_unit("slovnyk", None, None, None, f"inc_{wid}", "record_print", lemma, source="record", ref=wid)

    # 4. Tab: resursy (Resources) - CITED ids only
    cited_text_ids: list[str] = []
    cited_video_ids: list[str] = []
    for st in lesson_entry.get("steps", []):
        if isinstance(st, dict):
            for ev in st.get("evidence", []):
                if isinstance(ev, str):
                    if ev.startswith("T-") and ev not in cited_text_ids:
                        cited_text_ids.append(ev)
                    elif ev.startswith("V-") and ev not in cited_video_ids:
                        cited_video_ids.append(ev)
    for v_entry in lesson_entry.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str) and ev not in cited_video_ids:
                cited_video_ids.append(ev)

    for cid in cited_text_ids:
        t_rec = texts_by_id.get(cid)
        if t_rec is None:
            raise AssemblerError(TEXT_NOT_FOUND, f"cited text record {cid} not found in pack")
        src = t_rec.get("source", {})
        title = str(src.get("work") or src.get("file") or src.get("author") or cid)
        add_unit("resursy", None, None, None, f"res_{cid}", "record_print", title, source="record", ref=cid)

    for vid in cited_video_ids:
        v_rec = videos_by_id.get(vid)
        if v_rec is None:
            raise AssemblerError(VIDEO_NOT_FOUND, f"cited video record {vid} not found in pack")
        chan = str(v_rec.get("channel") or vid)
        add_unit("resursy", None, None, None, f"res_{vid}", "record_print", chan, source="record", ref=vid)

    expanded_doc = {
        "expanded_schema": 1,
        "lesson": {
            "level": level,
            "slug": slug,
            "n": lesson_n,
        },
        "units": units,
    }

    provenance_doc = {
        "provenance_schema": 1,
        "lesson": {
            "level": level,
            "slug": slug,
            "n": lesson_n,
        },
        "spans": spans,
    }

    return expanded_doc, provenance_doc


def write_expanded_document(
    expanded_doc: dict[str, Any],
    provenance_doc: dict[str, Any],
    output_dir: Path,
    lesson_n: int,
) -> tuple[Path, Path]:
    """Write expanded document with lock sidecar, and provenance document atomically."""
    output_dir.mkdir(parents=True, exist_ok=True)
    exp_path = output_dir / f"lesson-{lesson_n}.expanded.yaml"
    prov_path = output_dir / f"lesson-{lesson_n}.provenance.yaml"

    content_bytes = lock.yaml_bytes(expanded_doc)
    lock.write(exp_path, content_bytes)

    prov_bytes = yaml.safe_dump(provenance_doc, allow_unicode=True, sort_keys=False).encode("utf-8")
    lock.atomic_write(prov_path, prov_bytes)

    return exp_path, prov_path


def check_5_assembly(
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    level: str,
    slug: str,
    lesson_n: int,
    *,
    output_dir: Path | None = None,
) -> CheckResult:
    """Check 5: Assemble draft to expanded document, validate schema and accent ban."""
    try:
        expanded_doc, provenance_doc = assemble_expanded_document(draft, plan, pack, words_store, level, slug, lesson_n)
    except AssemblerError as exc:
        return CheckResult(check=5, passed=False, reason=f"{exc.code}: {exc.message}", layer="pack")
    except Exception as exc:
        return CheckResult(check=5, passed=False, reason=f"assembly raised: {exc}", layer="writer")

    validator = get_expanded_validator()
    errors = sorted(validator.iter_errors(expanded_doc), key=lambda e: e.path)
    if errors:
        err = errors[0]
        return CheckResult(
            check=5,
            passed=False,
            reason=f"expanded document schema validation failed at {list(err.path)}: {err.message}",
            layer="writer",
        )

    for idx, u in enumerate(expanded_doc.get("units", [])):
        txt = u.get("text", "")
        if "\u0300" in txt or "\u0301" in txt:
            return CheckResult(
                check=5,
                passed=False,
                step=u.get("step"),
                activity=u.get("activity"),
                token=txt,
                reason=f"combining accent in unit {idx}: {txt!r}",
                layer="writer",
            )

    try:
        ExpandedDocument.from_data(expanded_doc)
    except ResolverError as err:
        return CheckResult(check=5, passed=False, reason=f"ExpandedDocument rejected: {err.message}", layer="writer")

    if output_dir is not None:
        write_expanded_document(expanded_doc, provenance_doc, output_dir, lesson_n)

    return CheckResult(
        check=5,
        passed=True,
        artifacts={"expanded_doc": expanded_doc, "provenance": provenance_doc},
    )


def apply_stress(expanded_doc: dict[str, Any], stream: Any) -> dict[str, Any]:
    """Apply stress from stream tokens to expanded document units by unit index."""
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])

    replacements_by_unit: dict[int, list[tuple[int, int, str]]] = {}
    for tok in tokens:
        if not isinstance(tok, dict):
            continue
        selected = tok.get("selected")
        if not isinstance(selected, dict):
            continue
        stressed = selected.get("stressed")
        if not stressed or stressed == "pending":
            continue
        unit_idx = tok.get("unit_index")
        offset = tok.get("offset")
        tok_str = str(tok.get("token", ""))
        if isinstance(unit_idx, int) and isinstance(offset, int) and tok_str:
            replacements_by_unit.setdefault(unit_idx, []).append((offset, len(tok_str), str(stressed)))

    units = copy.deepcopy(expanded_doc.get("units", []))
    for unit_idx, unit in enumerate(units):
        reps = replacements_by_unit.get(unit_idx)
        if not reps:
            continue
        reps.sort(key=lambda item: item[0], reverse=True)
        txt = unit["text"]
        for start, length, stressed_val in reps:
            if start + length <= len(txt):
                txt = txt[:start] + stressed_val + txt[start + length :]
        unit["text"] = txt

    return {
        "stressed_schema": 1,
        "lesson": expanded_doc.get("lesson"),
        "units": units,
    }


def write_stressed_document(stressed_doc: dict[str, Any], output_dir: Path, lesson_n: int) -> Path:
    """Write stressed document with lock sidecar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stressed_path = output_dir / f"lesson-{lesson_n}.stressed.yaml"
    content_bytes = lock.yaml_bytes(stressed_doc)
    lock.write(stressed_path, content_bytes)
    return stressed_path


def build_slovnyk_tab(
    lesson_plan: dict[str, Any],
    words_store: dict[str, Any],
    stream: Any = None,
) -> list[dict[str, Any]]:
    """Build Slovnyk vocabulary items (core and incidental) for this lesson."""
    vocab_inv = lesson_plan.get("inventory", {}).get("vocabulary", {})
    core_items = vocab_inv.get("core", [])
    incidental_items = vocab_inv.get("incidental", [])

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    selected_senses: dict[str, str] = {}
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    for tok in tokens:
        if isinstance(tok, dict):
            sel = tok.get("selected")
            if isinstance(sel, dict):
                rec = sel.get("record")
                if rec and rec in words_by_id:
                    w_rec = words_by_id[rec]
                    gloss = w_rec.get("sense_gloss") or w_rec.get("gloss_en") or ""
                    if gloss:
                        selected_senses[rec] = str(gloss)

    vocab_items: list[dict[str, Any]] = []

    def process_item(wid: str, forms_list: list[str]) -> None:
        if wid not in words_by_id:
            return
        w_rec = words_by_id[wid]
        lemma = str(w_rec.get("lemma", ""))

        # Lemma stress comes from the record's lemma form, never first learner form
        stressed_lemma = lemma
        lemma_form = None
        for f in w_rec.get("forms", []):
            if isinstance(f, dict) and f.get("form") == lemma:
                lemma_form = f
                break

        if lemma_form is not None:
            if lemma_form.get("stress_source") == "pending":
                stressed_lemma = lemma
            elif lemma_form.get("stressed"):
                stressed_lemma = str(lemma_form["stressed"])

        gloss = selected_senses.get(wid) or str(w_rec.get("sense_gloss") or w_rec.get("gloss_en") or "")
        try:
            atlas_href = atlas_href_for(lemma)
        except Exception:
            atlas_href = None

        # Taught forms are the stressed forms of the plan's form tags
        forms_by_tag = {f.get("tags"): f for f in w_rec.get("forms", []) if isinstance(f, dict)}
        taught_forms: list[str] = []
        for ftag in forms_list:
            f_entry = forms_by_tag.get(ftag)
            if f_entry:
                if f_entry.get("stress_source") == "pending" or not f_entry.get("stressed"):
                    taught_forms.append(str(f_entry.get("form", "")))
                else:
                    taught_forms.append(str(f_entry["stressed"]))

        item_entry: dict[str, Any] = {
            "lemma": stressed_lemma,
            "translation": gloss,
            "pos": str(w_rec.get("pos", "")),
            "atlas_href": atlas_href,
        }
        if taught_forms:
            item_entry["forms"] = taught_forms
        vocab_items.append(item_entry)

    for c in core_items:
        if isinstance(c, dict):
            wid = c.get("evidence")
            if wid:
                process_item(wid, c.get("forms", []))

    for inc in incidental_items:
        wid = inc.get("evidence") if isinstance(inc, dict) else inc
        if isinstance(wid, str):
            process_item(wid, [])

    return vocab_items


def build_resursy_tab(
    lesson_plan: dict[str, Any],
    pack: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Build Resursy external resources dictionary from cited pack records only."""
    books: list[dict[str, Any]] = []
    youtube: list[dict[str, Any]] = []

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    cited_text_ids: list[str] = []
    cited_video_ids: list[str] = []
    for st in lesson_plan.get("steps", []):
        if isinstance(st, dict):
            for ev in st.get("evidence", []):
                if isinstance(ev, str):
                    if ev.startswith("T-") and ev not in cited_text_ids:
                        cited_text_ids.append(ev)
                    elif ev.startswith("V-") and ev not in cited_video_ids:
                        cited_video_ids.append(ev)
    for v_entry in lesson_plan.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str) and ev not in cited_video_ids:
                cited_video_ids.append(ev)

    for cid in cited_text_ids:
        t_rec = texts_by_id.get(cid)
        if t_rec:
            src = t_rec.get("source", {})
            title = str(src.get("work") or src.get("file") or src.get("author") or cid)
            author = str(src.get("author") or "")
            page = str(src.get("page") or "")
            books.append(
                {
                    "title": title,
                    "author": author,
                    "pages": page,
                    "url": "",
                    "source": cid,
                    "description": str(t_rec.get("supports") or ""),
                }
            )

    plan_video_uses: dict[str, str] = {}
    for v_entry in lesson_plan.get("videos", []):
        if isinstance(v_entry, dict):
            ev = v_entry.get("evidence")
            if isinstance(ev, str):
                plan_video_uses[ev] = str(v_entry.get("use") or "")

    for vid_id in cited_video_ids:
        vid = videos_by_id.get(vid_id)
        if vid:
            chan = str(vid.get("channel") or vid_id)
            youtube.append(
                {
                    "title": chan,
                    "url": str(vid.get("url") or ""),
                    "channel": chan,
                    "description": plan_video_uses.get(vid_id) or str(vid.get("use") or ""),
                }
            )

    result: dict[str, list[dict[str, Any]]] = {}
    if books:
        result["books"] = books
    if youtube:
        result["youtube"] = youtube
    return result


def _render_urok_markdown(
    draft: dict[str, Any],
    stressed_doc: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
) -> str:
    """Render Tab 1 (Urok) markdown from draft and stressed units.

    Keys stressed text by unit index and reassembles every block from all its spans in order.
    """
    stressed_units = stressed_doc.get("units", [])
    stressed_text_by_unit_idx: dict[int, str] = {i: u["text"] for i, u in enumerate(stressed_units)}

    unit_indices_by_block: dict[tuple[str | None, str | None, int | str], list[int]] = {}
    for i, u in enumerate(stressed_units):
        key = (u.get("tab"), u.get("step"), u.get("block"))
        unit_indices_by_block.setdefault(key, []).append(i)

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    texts_by_id: dict[str, dict[str, Any]] = {}
    for t in pack.get("texts", []):
        if isinstance(t, dict) and "id" in t:
            texts_by_id[t["id"]] = t

    examples_by_id: dict[str, dict[str, Any]] = {}
    for ex in pack.get("examples", []):
        if isinstance(ex, dict) and "id" in ex:
            examples_by_id[ex["id"]] = ex

    videos_by_id: dict[str, dict[str, Any]] = {}
    for v in pack.get("videos", []):
        if isinstance(v, dict) and "id" in v:
            videos_by_id[v["id"]] = v

    def replace_gloss(match: re.Match[str]) -> str:
        wid = match.group(1)
        w_rec = words_by_id.get(wid)
        if w_rec:
            lem = w_rec.get("lemma", "")
            gl = w_rec.get("sense_gloss") or w_rec.get("gloss_en") or ""
            return f"{lem} ({gl})" if gl else lem
        return wid

    def format_block_text(step_id: str | None, block_key: int | str, fallback: str = "") -> str:
        indices = unit_indices_by_block.get(("urok", step_id, block_key))
        val = "".join(stressed_text_by_unit_idx[i] for i in indices) if indices else fallback
        val = re.sub(r"\{\{uk:([^{}\u0300\u0301]+)\}\}", r"\1", val)
        val = GLOSS_ID_RE.sub(replace_gloss, val)
        return val

    lines: list[str] = []

    for step in draft.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")

        lead_in = step.get("lead_in")
        if lead_in:
            lines.append(format_block_text(step_id, "lead_in", lead_in))
            lines.append("")

        for block_idx, block in enumerate(step.get("blocks", [])):
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "prose":
                txt = block.get("text", "")
                lines.append(format_block_text(step_id, block_idx, txt))
                lines.append("")

            elif kind == "example":
                ref_id = block.get("ref", "")
                ex_rec = examples_by_id.get(ref_id)
                if ex_rec:
                    uk = format_block_text(step_id, block_idx, str(ex_rec.get("text", "")))
                    en = str(ex_rec.get("translation_en") or "")
                    lines.append(f"> {uk}")
                    if en:
                        lines.append(f">\n> *{en}*")
                    lines.append("")

            elif kind == "quote":
                ref_id = block.get("ref", "")
                t_rec = texts_by_id.get(ref_id)
                if t_rec:
                    q_text = format_block_text(step_id, block_idx, str(t_rec.get("quote", "")))
                    src = t_rec.get("source", {})
                    author = str(src.get("author") or "")
                    work = str(src.get("work") or "")
                    year = src.get("year")
                    page = src.get("page")
                    attr_parts = [p for p in [author, work, str(year) if year else "", str(page) if page else ""] if p]
                    attr = ", ".join(attr_parts) if attr_parts else str(src.get("file", ""))
                    lines.append(f"> {q_text}")
                    if attr:
                        lines.append(f">\n> — *{attr}*")
                    lines.append("")

            elif kind == "paradigm":
                ref_id = block.get("ref", "")
                indices = [
                    i
                    for i, u in enumerate(stressed_units)
                    if u.get("tab") == "urok"
                    and u.get("step") == step_id
                    and str(u.get("block", "")).startswith(f"paradigm_{block_idx}_")
                ]
                lines.append("| | |")
                lines.append("| --- | --- |")
                for u_idx in indices:
                    u_text = stressed_text_by_unit_idx[u_idx]
                    u_text = re.sub(r"\{\{uk:([^{}\u0300\u0301]+)\}\}", r"\1", u_text)
                    lines.append(f"| {u_text} |")
                lines.append("")

            elif kind == "table":
                rows = block.get("rows", [])
                if rows:
                    header = [
                        format_block_text(step_id, f"table_{block_idx}_0_{c_idx}", str(c))
                        for c_idx, c in enumerate(rows[0])
                    ]
                    lines.append("| " + " | ".join(header) + " |")
                    lines.append("| " + " | ".join("---" for _ in header) + " |")
                    for r_idx, row in enumerate(rows[1:], start=1):
                        cells = [
                            format_block_text(step_id, f"table_{block_idx}_{r_idx}_{c_idx}", str(c))
                            for c_idx, c in enumerate(row)
                        ]
                        lines.append("| " + " | ".join(cells) + " |")
                    lines.append("")

            elif kind == "pronunciation":
                txt = block.get("text", "")
                lines.append(format_block_text(step_id, block_idx, txt))
                lines.append("")

            elif kind == "bilingual":
                uk_lines = block.get("uk", [])
                en_lines = block.get("en", [])
                lines.append("| | |")
                lines.append("| --- | --- |")
                for line_idx, (u_raw, e_raw) in enumerate(zip(uk_lines, en_lines, strict=False)):
                    u_line = format_block_text(step_id, f"bilingual_{block_idx}_{line_idx}", str(u_raw))
                    e_line = str(e_raw)
                    lines.append(f"| {u_line} | {e_line} |")
                lines.append("")

            elif kind == "culture":
                txt = block.get("text", "")
                lines.append(f"> [!note]\n> {format_block_text(step_id, block_idx, txt)}")
                lines.append("")

            elif kind == "tip":
                txt = block.get("text", "")
                lines.append(f"> [!tip]\n> {format_block_text(step_id, block_idx, txt)}")
                lines.append("")

            elif kind == "summary":
                txt = block.get("text", "")
                lines.append(f"> [!summary]\n> {format_block_text(step_id, block_idx, txt)}")
                lines.append("")

            elif kind == "callout":
                txt = block.get("text", "")
                lines.append(f"> [!note]\n> {format_block_text(step_id, block_idx, txt)}")
                lines.append("")

            elif kind == "video":
                v_lead = block.get("lead_in")
                if v_lead:
                    lines.append(format_block_text(step_id, f"video_lead_{block_idx}", v_lead))
                    lines.append("")
                ref_id = block.get("ref", "")
                vid_rec = videos_by_id.get(ref_id)
                if vid_rec:
                    chan = str(vid_rec.get("channel") or "")
                    url = str(vid_rec.get("url") or "")
                    lines.append(f"> [{chan}]({url})")
                    lines.append("")

            elif kind == "dialogue":
                dial = draft.get("dialogue") or {}
                for line_idx, line in enumerate(dial.get("lines", [])):
                    if isinstance(line, dict):
                        spk = line.get("speaker", "")
                        l_txt = format_block_text(step_id, f"dialogue_{line_idx}", line.get("text", ""))
                        lines.append(f"> **{spk}:** {l_txt}")
                lines.append("")

            elif kind == "activity":
                ref_id = block.get("ref", "")
                if ref_id:
                    lines.append(f"<!-- INJECT_ACTIVITY: {ref_id} -->")
                    lines.append("")

    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        lines.append(format_block_text(None, "consolidation_lead_in", consol_lead))
        lines.append("")

    return "\n".join(lines).strip()


def apply_stress_to_activities(
    draft_activities: list[dict[str, Any]],
    stressed_doc: dict[str, Any],
    replace_gloss_fn: Any,
) -> list[dict[str, Any]]:
    """Apply stress from stream/stressed units to draft activity fields."""
    stressed_units = stressed_doc.get("units", [])
    vpravy_indices: dict[tuple[str | None, int | None, int | str], list[int]] = {}
    for i, u in enumerate(stressed_units):
        if u.get("tab") == "vpravy":
            key = (u.get("activity"), u.get("item"), u.get("block"))
            vpravy_indices.setdefault(key, []).append(i)

    def format_act_text(act_id: str | None, item_idx: int | None, block_key: int | str, fallback: str) -> str:
        indices = vpravy_indices.get((act_id, item_idx, block_key))
        val = "".join(stressed_units[i]["text"] for i in indices) if indices else fallback
        val = re.sub(r"\{\{uk:([^{}\u0300\u0301]+)\}\}", r"\1", val)
        val = GLOSS_ID_RE.sub(replace_gloss_fn, val)
        return val

    stressed_activities = copy.deepcopy(draft_activities)
    for act in stressed_activities:
        if not isinstance(act, dict):
            continue
        act_id = act.get("id")
        if "instruction" in act:
            act["instruction"] = format_act_text(act_id, None, "instruction", act["instruction"])
        for item_idx, item in enumerate(act.get("items", [])):
            if not isinstance(item, dict):
                continue
            for prompt_key in ("prompt", "sentence", "question", "cue", "statement"):
                if prompt_key in item and isinstance(item[prompt_key], str):
                    item[prompt_key] = format_act_text(act_id, item_idx, "prompt", item[prompt_key])
            for ans_key in ("answer", "correct", "target", "is_true", "isTrue"):
                if ans_key in item and isinstance(item[ans_key], str):
                    item[ans_key] = format_act_text(act_id, item_idx, "answer", item[ans_key])
            for err_key in ("error", "incorrect"):
                if err_key in item and isinstance(item[err_key], str):
                    item[err_key] = format_act_text(act_id, item_idx, "error", item[err_key])
            if "explanation" in item and isinstance(item["explanation"], str):
                item["explanation"] = format_act_text(act_id, item_idx, "explanation", item["explanation"])
            for opt_key in ("options", "choices", "distractors"):
                if opt_key in item and isinstance(item[opt_key], list):
                    new_opts = []
                    for opt_idx, opt in enumerate(item[opt_key]):
                        if isinstance(opt, dict) and "text" in opt:
                            opt_copy = dict(opt)
                            opt_copy["text"] = format_act_text(act_id, item_idx, f"opt_{opt_idx}", opt["text"])
                            new_opts.append(opt_copy)
                        elif isinstance(opt, str):
                            new_opts.append(format_act_text(act_id, item_idx, f"opt_{opt_idx}", opt))
                        else:
                            new_opts.append(opt)
                    item[opt_key] = new_opts
            if "pairs" in item and isinstance(item["pairs"], list):
                for p_idx, pair in enumerate(item["pairs"]):
                    if isinstance(pair, dict):
                        for left_key in ("left", "prompt"):
                            if left_key in pair:
                                pair[left_key] = format_act_text(act_id, item_idx, f"pair_l_{p_idx}", pair[left_key])
                        for right_key in ("right", "answer"):
                            if right_key in pair:
                                pair[right_key] = format_act_text(act_id, item_idx, f"pair_r_{p_idx}", pair[right_key])
    return stressed_activities


def check_9_stress_and_render(
    expanded_doc: dict[str, Any],
    draft: dict[str, Any],
    plan: dict[str, Any],
    pack: dict[str, Any],
    words_store: dict[str, Any],
    stream: Any,
    level: str,
    slug: str,
    lesson_n: int,
    *,
    repo_root: Path = REPO_ROOT,
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> CheckResult:
    """Check 9: Apply stress, build Slovnyk and Resursy, verify locks, render MDX."""
    try:
        stressed_doc = apply_stress(expanded_doc, stream)
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"stress application raised: {exc}", layer="writer")

    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    for tok in tokens:
        if isinstance(tok, dict):
            klass = str(tok.get("class", ""))
            sel = tok.get("selected")
            if klass == "pending_stress" or (
                isinstance(sel, dict)
                and (sel.get("stressed") is None or sel.get("stressed") == "pending")
                and not klass.startswith("skipped")
            ):
                return CheckResult(
                    check=9,
                    passed=False,
                    token=str(tok.get("token", "")),
                    reason="pending stress in stream",
                    layer="word_store",
                )

    lesson_entry: dict[str, Any] = {}
    for entry in plan.get("lessons", []):
        if isinstance(entry, dict) and entry.get("n") == lesson_n:
            lesson_entry = entry
            break
    if not lesson_entry:
        return CheckResult(check=9, passed=False, reason=f"lesson {lesson_n} not found in plan", layer="plan")

    vocab_items = build_slovnyk_tab(lesson_entry, words_store, stream)
    external_resources = build_resursy_tab(lesson_entry, pack)

    # Check on-disk lesson lock
    lock_ok, lock_diff = lesson_lock.check_lesson_lock(
        level,
        slug,
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=repo_root,
    )
    if not lock_ok:
        return CheckResult(
            check=9,
            passed=False,
            reason=f"lessons.lock.yaml check failed: {lock_diff}",
            layer="pack",
        )

    # Compute lesson lock
    try:
        lock_doc = lesson_lock.compute_lesson_lock(
            level,
            slug,
            plan_dict=plan,
            pack_dict=pack,
            words_dict=words_store,
            repo_root=repo_root,
            evidence_dir=evidence_dir,
            plans_dir=plans_dir,
        )
        lessons_lock_sha256 = hashlib.sha256(lock.yaml_bytes(lock_doc)).hexdigest()
        lesson_entry_sha256 = None
        for l_item in lock_doc.get("lessons", []):
            if l_item.get("n") == lesson_n:
                lesson_entry_sha256 = l_item.get("entry_sha256")
                break
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"lesson lock calculation failed: {exc}", layer="pack")

    if not lesson_entry_sha256:
        return CheckResult(
            check=9, passed=False, reason=f"lesson {lesson_n} lock entry not found in computed lock", layer="plan"
        )

    draft_lock_entry = draft.get("inputs", {}).get("lesson_lock_entry_sha256")
    if not draft_lock_entry:
        return CheckResult(
            check=9, passed=False, reason="draft inputs missing lesson_lock_entry_sha256", layer="writer"
        )
    if draft_lock_entry != lesson_entry_sha256:
        return CheckResult(
            check=9,
            passed=False,
            reason=f"draft lesson_lock_entry_sha256 {draft_lock_entry!r} != computed {lesson_entry_sha256!r}",
            layer="writer",
        )

    # Immersion band computation
    arc_ref = plan.get("arc_ref")
    if not isinstance(arc_ref, dict) or "position" not in arc_ref:
        return CheckResult(check=9, passed=False, reason="plan missing arc_ref.position", layer="plan")
    arc_position = int(arc_ref["position"])

    p_root = plans_dir or (repo_root / f"curriculum/l2-uk-en/lesson-plans/{level}")
    e_root = evidence_dir or (repo_root / f"curriculum/l2-uk-en/evidence/{level}")
    try:
        p_state = planned_state(
            level,
            arc_position,
            lesson_n,
            allow_missing_prior=False,
            plans_dir=p_root,
            evidence_dir=e_root,
        )
        if getattr(p_state, "waiver", None):
            return CheckResult(
                check=9,
                passed=False,
                reason=f"{PRIOR_PLANS_MISSING}: {p_state.waiver}",
                layer="plan",
            )
        cumulative_core_count = p_state.cumulative_core_count
    except PlannedStateError as exc:
        code = getattr(exc, "code", PRIOR_PLANS_MISSING)
        return CheckResult(check=9, passed=False, reason=f"{code}: {exc}", layer="plan")
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"planned state computation failed: {exc}", layer="plan")

    try:
        band = compute_lesson_immersion_band(
            track=level,
            arc_position=arc_position,
            lesson_n=lesson_n,
            cumulative_core_count=cumulative_core_count,
        )
        immersion_band_key = band.band_key
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"immersion band computation failed: {exc}", layer="plan")

    plan_lessons = plan.get("lessons", [])
    offset = next(
        (i for i, l in enumerate(plan_lessons) if isinstance(l, dict) and l.get("n") == lesson_n), lesson_n - 1
    )
    base = f"/{level}/{slug}/"
    previous = base if offset == 0 else f"{base}{lesson_n - 1}/"
    following = f"{base}{lesson_n + 1}/" if offset + 1 < len(plan_lessons) else base

    meta_data = {
        "title": str(lesson_entry.get("title", "")),
        "subtitle": str(lesson_entry.get("rationale") or ""),
        "evidence": {
            "lessons_lock_sha256": lessons_lock_sha256,
            "lesson_entry_sha256": lesson_entry_sha256,
        },
        "immersion": immersion_band_key,
        "job": str(lesson_entry.get("job") or ""),
        "prev": previous,
        "next": following,
        "lesson": lesson_n,
        "module_slug": slug,
    }

    urok_md = _render_urok_markdown(draft, stressed_doc, pack, words_store)

    words_by_id = {w["id"]: w for w in words_store.get("words", []) if isinstance(w, dict) and "id" in w}

    def replace_gloss(match: re.Match[str]) -> str:
        wid = match.group(1)
        w_rec = words_by_id.get(wid)
        if w_rec:
            lem = w_rec.get("lemma", "")
            gl = w_rec.get("sense_gloss") or w_rec.get("gloss_en") or ""
            return f"{lem} ({gl})" if gl else lem
        return wid

    plan_acts_by_id = {
        act["id"]: act
        for act in lesson_entry.get("activities", [])
        if isinstance(act, dict) and "id" in act
    }

    for draft_act in draft.get("activities", []):
        if isinstance(draft_act, dict):
            act_id = draft_act.get("id")
            if not act_id or act_id not in plan_acts_by_id:
                return CheckResult(
                    check=9,
                    passed=False,
                    reason=f"{ACTIVITY_NOT_FOUND}: draft activity {act_id} not found in plan",
                    layer="plan",
                )

    stressed_activities = apply_stress_to_activities(draft.get("activities", []), stressed_doc, replace_gloss)

    from scripts.yaml_activities import ActivityParser

    activity_parser = ActivityParser()
    converted_activities = []
    for act_dict in stressed_activities:
        if not isinstance(act_dict, dict):
            continue
        act_id = act_dict.get("id")
        plan_act = plan_acts_by_id.get(act_id)
        if not plan_act:
            return CheckResult(
                check=9,
                passed=False,
                reason=f"{ACTIVITY_NOT_FOUND}: draft activity {act_id} not found in plan",
                layer="plan",
            )
        act_payload = copy.deepcopy(act_dict)
        act_payload["type"] = plan_act.get("type")
        act_payload["placement"] = plan_act.get("placement")
        if not act_payload.get("title") and plan_act.get("focus"):
            act_payload["title"] = plan_act.get("focus")

        try:
            act_obj = activity_parser._parse_activity(act_payload)
            act_obj.placement = plan_act.get("placement")
            converted_activities.append(act_obj)
        except Exception as exc:
            return CheckResult(
                check=9,
                passed=False,
                reason=f"activity parsing failed for {act_id}: {exc}",
                layer="writer",
            )

    try:
        mdx_content = generate_mdx(
            md_content=urok_md,
            module_num=lesson_n,
            yaml_activities=converted_activities,
            meta_data=meta_data,
            vocab_items=vocab_items,
            external_resources=external_resources,
            level=level,
            pipeline_version="v7",
            build_status="draft",
            fresh=True,
        )
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"MDX rendering failed: {exc}", layer="writer")

    if output_dir is not None:
        write_stressed_document(stressed_doc, output_dir, lesson_n)

    if site_dir is not None:
        site_dir.mkdir(parents=True, exist_ok=True)
        mdx_file = site_dir / f"{lesson_n}.mdx"
        lock.atomic_write(mdx_file, mdx_content.encode("utf-8"))

    return CheckResult(
        check=9,
        passed=True,
        artifacts={
            "stressed_doc": stressed_doc,
            "vocab_items": vocab_items,
            "external_resources": external_resources,
            "mdx": mdx_content,
            "meta_data": meta_data,
        },
    )


def check_11_render(
    level: str,
    slug: str,
    *,
    astro_build: bool = False,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
) -> CheckResult:
    """Check 11: verify_shippable --fresh on assembled site docs."""
    from scripts.build.verify_shippable import verify as vs_verify

    rep = vs_verify(level, slug, module_dir=module_dir, plan_path=plan_path, astro_build=astro_build, fresh=True)
    passed = bool(rep.get("shippable"))
    return CheckResult(
        check=11,
        passed=passed,
        reason=None if passed else "verify_shippable check 11 reported not shippable",
        layer=None if passed else "render",
        artifacts={"verify_shippable": rep},
    )


def assemble_lesson(
    level: str,
    slug: str,
    lesson_n: int,
    *,
    repo_root: Path | None = None,
    draft_dict: dict[str, Any] | None = None,
    plan_dict: dict[str, Any] | None = None,
    pack_dict: dict[str, Any] | None = None,
    words_dict: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    astro_build: bool = False,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """End-to-end assembly pipeline for one lesson (checks 5, 9, 11).

    Refuses site write on failures or open tokens, writing only state files.
    """
    root = repo_root or REPO_ROOT

    paths = lesson_lock.resolve_paths(level, slug, evidence_dir=evidence_dir, plans_dir=plans_dir, repo_root=root)
    state_dir = output_dir or (paths["evidence_dir"] / "_state" / slug)
    target_site_dir = site_dir or (root / "site" / "src" / "content" / "docs" / level / slug)

    plan = plan_dict if plan_dict is not None else yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    pack = pack_dict if pack_dict is not None else yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))
    words_store = words_dict if words_dict is not None else yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    if draft_dict is None:
        draft_file = state_dir / f"lesson-{lesson_n}.draft.yaml"
        if not draft_file.is_file():
            raise FileNotFoundError(f"Draft file not found: {draft_file}")
        draft = yaml.safe_load(draft_file.read_text(encoding="utf-8"))
    else:
        draft = draft_dict

    if draft.get("status") != "ok":
        return {
            "ok": False,
            "failure": {
                "check": 5,
                "passed": False,
                "reason": f"{DRAFT_STATUS_NOT_OK}: draft status is {draft.get('status')!r}, expected 'ok'",
                "layer": "writer",
            },
        }

    # Check 5: Assembly
    c5 = check_5_assembly(draft, plan, pack, words_store, level, slug, lesson_n, output_dir=state_dir)
    if not c5.passed:
        return {"ok": False, "failure": c5.to_dict()}

    expanded_doc = c5.artifacts["expanded_doc"]

    # Resolver resolution
    try:
        from scripts.curriculum.resolver.stream import allowlist_for_lesson

        allowlist = allowlist_for_lesson(level, slug, lesson_n, evidence_dir=evidence_dir, plans_dir=plans_dir)
    except Exception:
        allowlist = Allowlist.from_records(words_store.get("words", []))

    try:
        sources = Sources()
    except Exception:
        sources = None
    stream = resolve(ExpandedDocument.from_data(expanded_doc), allowlist, sources)

    # Major 4: Check if stream has any failures or open tokens
    stream_failures = list(getattr(stream, "failures", []) or [])
    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    blocking_tokens: list[dict[str, Any]] = []
    for tok in tokens:
        if isinstance(tok, dict):
            klass = str(tok.get("class", ""))
            if (
                klass in resolver_codes.FAILURE_CLASSES
                or klass in ("stress_open", "stress_certain_identity_open")
                or klass in resolver_codes.OPEN_CLASSES
                or klass == "pending_stress"
                or (
                    tok.get("selected") is None
                    and not klass.startswith("skipped")
                    and klass != resolver_codes.LETTER_OR_SYLLABLE
                )
            ):
                blocking_tokens.append(tok)

    if stream_failures or blocking_tokens:
        # Refuse site write: write only state files and return report naming blocking tokens
        stressed_doc = apply_stress(expanded_doc, stream)
        write_stressed_document(stressed_doc, state_dir, lesson_n)
        return {
            "ok": False,
            "failure": {
                "check": 9,
                "passed": False,
                "reason": f"stream has {len(blocking_tokens)} blocking token(s) and {len(stream_failures)} failure(s); refusing site write",
                "layer": "stream",
            },
            "check_5": c5.to_dict(),
            "blocking_tokens": [str(t.get("token", "")) for t in blocking_tokens],
            "stream_failures": [str(f) for f in stream_failures],
            "message": f"stream has {len(blocking_tokens)} blocking token(s) and {len(stream_failures)} failure(s); refusing site write",
        }

    # Check 9: Stress and render (clean stream only writes site)
    c9 = check_9_stress_and_render(
        expanded_doc,
        draft,
        plan,
        pack,
        words_store,
        stream,
        level,
        slug,
        lesson_n,
        repo_root=root,
        output_dir=state_dir,
        site_dir=target_site_dir,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
    )
    if not c9.passed:
        return {"ok": False, "failure": c9.to_dict()}

    # Check 11: Render shippable
    c11 = check_11_render(
        level,
        slug,
        astro_build=astro_build,
        module_dir=target_site_dir,
        plan_path=paths["plan"],
    )

    return {
        "ok": c5.passed and c9.passed and c11.passed,
        "check_5": c5.to_dict(),
        "check_9": c9.to_dict(),
        "check_11": c11.to_dict(),
        "mdx": c9.artifacts.get("mdx"),
        "frontmatter": c9.artifacts.get("meta_data"),
    }
