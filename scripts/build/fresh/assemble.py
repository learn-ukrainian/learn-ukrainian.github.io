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

from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.evidence.sources import Sources
from scripts.curriculum.learner_state.immersion import compute_lesson_immersion_band
from scripts.curriculum.resolver.classify import GLOSS_ID_RE
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument, ResolverError
from scripts.curriculum.resolver.stream import resolve
from scripts.generate_mdx.atlas_links import atlas_href_for
from scripts.generate_mdx.core import generate_mdx

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPANDED_SCHEMA_PATH = REPO_ROOT / "schemas" / "lesson-expanded-v1.schema.json"

_CACHED_EXPANDED_VALIDATOR: Draft202012Validator | None = None


def get_expanded_validator(schema_path: Path | None = None) -> Draft202012Validator:
    global _CACHED_EXPANDED_VALIDATOR
    if _CACHED_EXPANDED_VALIDATOR is None:
        path = schema_path or EXPANDED_SCHEMA_PATH
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
    """
    lesson_entry: dict[str, Any] = {}
    for entry in plan.get("lessons", []):
        if isinstance(entry, dict) and entry.get("n") == lesson_n:
            lesson_entry = entry
            break

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
                ex_rec = None
                for ex in pack.get("examples", []):
                    if isinstance(ex, dict) and ex.get("id") == ref_id:
                        ex_rec = ex
                        break
                ex_text = ""
                if ex_rec:
                    ex_text = str(ex_rec.get("uk") or ex_rec.get("text") or "")
                add_unit("urok", step_id, None, None, block_idx, "record_print", ex_text, source="record", ref=ref_id)

            elif kind == "quote":
                ref_id = block.get("ref", "")
                chunk_rec = None
                for chk in pack.get("textbook_chunks", []):
                    if isinstance(chk, dict) and chk.get("id") == ref_id:
                        chunk_rec = chk
                        break
                quote_text = ""
                if chunk_rec:
                    quote_text = str(chunk_rec.get("text") or chunk_rec.get("content") or "")
                add_unit("urok", step_id, None, None, block_idx, "record_print", quote_text, source="record", ref=ref_id)

            elif kind == "paradigm":
                ref_id = block.get("ref", "")
                p_text = ""
                for p_item in pack.get("paradigms", []):
                    if isinstance(p_item, dict) and p_item.get("id") == ref_id:
                        p_text = str(p_item.get("text") or p_item.get("form") or "")
                        break
                add_unit("urok", step_id, None, None, block_idx, "record_print", p_text, source="record", ref=ref_id)

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
                        add_unit("urok", step_id, None, None, f"bilingual_{block_idx}_{line_idx}", role, span_text, source="writer_prose")

            elif kind in ("culture", "tip", "summary", "callout"):
                txt = block.get("text", "")
                for role, span_text in _split_inline_spans(txt, "narration"):
                    add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

            elif kind == "video":
                v_lead = block.get("lead_in")
                if v_lead:
                    for role, span_text in _split_inline_spans(v_lead, "narration"):
                        add_unit("urok", step_id, None, None, block_idx, role, span_text, source="writer_prose")

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

    # Consolidation lead-in
    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        for role, span_text in _split_inline_spans(consol_lead, "narration"):
            add_unit("urok", None, None, None, "consolidation_lead_in", role, span_text, source="writer_prose")

    # 2. Tab: vpravy (Activities)
    for act in draft.get("activities", []):
        if not isinstance(act, dict):
            continue
        act_id = act.get("id")
        title = act.get("title")
        if title:
            add_unit("vpravy", None, act_id, None, "title", "instruction", str(title), source="writer_prose")
        instr = act.get("instruction")
        if instr:
            add_unit("vpravy", None, act_id, None, "instruction", "instruction", str(instr), source="writer_prose")

        for item_idx, item in enumerate(act.get("items", [])):
            if not isinstance(item, dict):
                continue

            prompt = item.get("prompt") or item.get("sentence") or item.get("question") or item.get("cue")
            if prompt:
                add_unit("vpravy", None, act_id, item_idx, "prompt", "item_prompt", str(prompt), source="writer_prose")

            answer = item.get("answer") or item.get("correct") or item.get("target")
            if answer:
                add_unit("vpravy", None, act_id, item_idx, "answer", "item_answer", str(answer), source="writer_prose")

            opts = item.get("options") or item.get("choices") or item.get("distractors") or []
            for opt_idx, opt in enumerate(opts):
                add_unit("vpravy", None, act_id, item_idx, f"opt_{opt_idx}", "item_option", str(opt), source="writer_prose")

            err_txt = item.get("error") or item.get("incorrect")
            if err_txt:
                add_unit("vpravy", None, act_id, item_idx, "error", "error_text", str(err_txt), source="writer_prose")

            pairs = item.get("pairs") or []
            for p_idx, pair in enumerate(pairs):
                if isinstance(pair, dict):
                    left = pair.get("left") or pair.get("prompt")
                    right = pair.get("right") or pair.get("answer")
                    if left:
                        add_unit("vpravy", None, act_id, item_idx, f"pair_l_{p_idx}", "item_prompt", str(left), source="writer_prose")
                    if right:
                        add_unit("vpravy", None, act_id, item_idx, f"pair_r_{p_idx}", "item_answer", str(right), source="writer_prose")

    # 3. Tab: slovnyk (Vocabulary)
    vocab_inv = lesson_entry.get("inventory", {}).get("vocabulary", {})
    core_items = vocab_inv.get("core", [])
    incidental_items = vocab_inv.get("incidental", [])

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    for c in core_items:
        if isinstance(c, dict):
            wid = c.get("evidence")
            if wid and wid in words_by_id:
                w_rec = words_by_id[wid]
                lemma = str(w_rec.get("lemma", ""))
                add_unit("slovnyk", None, None, None, f"core_{wid}", "record_print", lemma, source="record", ref=wid)

    for inc in incidental_items:
        wid = inc.get("evidence") if isinstance(inc, dict) else inc
        if isinstance(wid, str) and wid in words_by_id:
            w_rec = words_by_id[wid]
            lemma = str(w_rec.get("lemma", ""))
            add_unit("slovnyk", None, None, None, f"inc_{wid}", "record_print", lemma, source="record", ref=wid)

    # 4. Tab: resursy (Resources)
    for chk in pack.get("textbook_chunks", []):
        if isinstance(chk, dict):
            cid = chk.get("id")
            title = str(chk.get("title") or "")
            if cid and title:
                add_unit("resursy", None, None, None, f"res_{cid}", "record_print", title, source="record", ref=cid)

    for vid in pack.get("videos", []):
        if isinstance(vid, dict):
            vid_id = vid.get("id")
            v_title = str(vid.get("title") or "")
            if vid_id and v_title:
                add_unit("resursy", None, None, None, f"res_{vid_id}", "record_print", v_title, source="record", ref=vid_id)

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
    """Write expanded document with lock sidecar, and provenance document."""
    output_dir.mkdir(parents=True, exist_ok=True)
    exp_path = output_dir / f"lesson-{lesson_n}.expanded.yaml"
    prov_path = output_dir / f"lesson-{lesson_n}.provenance.yaml"

    content_bytes = lock.yaml_bytes(expanded_doc)
    lock.write(exp_path, content_bytes)

    prov_bytes = yaml.safe_dump(provenance_doc, allow_unicode=True, sort_keys=False).encode("utf-8")
    prov_path.write_bytes(prov_bytes)

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
        expanded_doc, provenance_doc = assemble_expanded_document(
            draft, plan, pack, words_store, level, slug, lesson_n
        )
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
    """Apply stress from stream tokens to expanded document units."""
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
                txt = txt[:start] + stressed_val + txt[start + length:]
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
                sense = sel.get("gloss") or sel.get("sense")
                if rec and sense:
                    selected_senses[rec] = str(sense)

    vocab_items: list[dict[str, Any]] = []

    def process_item(wid: str, forms_list: list[str]) -> None:
        if wid not in words_by_id:
            return
        w_rec = words_by_id[wid]
        lemma = str(w_rec.get("lemma", ""))
        stressed_lemma = lemma
        for f in w_rec.get("forms", []):
            if (
                isinstance(f, dict)
                and f.get("stressed")
                and (f.get("form") == lemma or f.get("learner") is True)
            ):
                stressed_lemma = str(f["stressed"])
                break

        gloss = selected_senses.get(wid) or str(w_rec.get("gloss", ""))
        item_entry: dict[str, Any] = {
            "lemma": stressed_lemma,
            "translation": gloss,
            "pos": str(w_rec.get("pos", "")),
            "gender": str(w_rec.get("gender", "")),
            "atlas_href": atlas_href_for(lemma),
        }
        if forms_list:
            item_entry["forms"] = forms_list
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
    """Build Resursy external resources dictionary from pack and plan."""
    books: list[dict[str, Any]] = []
    youtube: list[dict[str, Any]] = []

    for chk in pack.get("textbook_chunks", []):
        if isinstance(chk, dict):
            books.append(
                {
                    "title": str(chk.get("title") or "Textbook"),
                    "author": str(chk.get("author") or ""),
                    "pages": chk.get("pages") or chk.get("page") or "",
                    "url": str(chk.get("url") or ""),
                    "source": str(chk.get("id") or ""),
                    "description": str(chk.get("attribution") or ""),
                }
            )

    plan_video_uses: dict[str, str] = {}
    for st in lesson_plan.get("steps", []):
        if isinstance(st, dict):
            for v_need in st.get("needs", []):
                if isinstance(v_need, str) and v_need.startswith("V-"):
                    plan_video_uses[v_need] = str(st.get("use") or st.get("teach") or "")

    for vid in pack.get("videos", []):
        if isinstance(vid, dict):
            vid_id = str(vid.get("id") or "")
            youtube.append(
                {
                    "title": str(vid.get("title") or "Video"),
                    "url": str(vid.get("url") or ""),
                    "channel": str(vid.get("channel") or ""),
                    "description": plan_video_uses.get(vid_id) or str(vid.get("description") or ""),
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
    """Render Tab 1 (Urok) markdown from draft and stressed units."""
    stressed_units_by_key: dict[tuple[str, str | None, int | str], str] = {}
    for u in stressed_doc.get("units", []):
        if u.get("tab") == "urok":
            key = (u["tab"], u.get("step"), u.get("block"))
            stressed_units_by_key[key] = u.get("text", "")

    words_by_id: dict[str, dict[str, Any]] = {}
    for w in words_store.get("words", []):
        if isinstance(w, dict) and "id" in w:
            words_by_id[w["id"]] = w

    def replace_gloss(match: re.Match[str]) -> str:
        wid = match.group(1)
        w_rec = words_by_id.get(wid)
        if w_rec:
            lem = w_rec.get("lemma", "")
            gl = w_rec.get("gloss", "")
            return f"{lem} ({gl})" if gl else lem
        return wid

    def format_text(raw: str, step_id: str | None, block_key: int | str) -> str:
        val = stressed_units_by_key.get(("urok", step_id, block_key), raw)
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
            lines.append(format_text(lead_in, step_id, "lead_in"))
            lines.append("")

        for block_idx, block in enumerate(step.get("blocks", [])):
            if not isinstance(block, dict):
                continue
            kind = block.get("kind")

            if kind == "prose":
                txt = block.get("text", "")
                lines.append(format_text(txt, step_id, block_idx))
                lines.append("")

            elif kind == "example":
                ref_id = block.get("ref", "")
                ex_rec = None
                for ex in pack.get("examples", []):
                    if isinstance(ex, dict) and ex.get("id") == ref_id:
                        ex_rec = ex
                        break
                if ex_rec:
                    uk = format_text(str(ex_rec.get("uk") or ex_rec.get("text") or ""), step_id, block_idx)
                    en = str(ex_rec.get("en") or ex_rec.get("translation") or "")
                    lines.append(f"> {uk}")
                    if en:
                        lines.append(f">\n> *{en}*")
                    lines.append("")

            elif kind == "quote":
                ref_id = block.get("ref", "")
                chunk_rec = None
                for chk in pack.get("textbook_chunks", []):
                    if isinstance(chk, dict) and chk.get("id") == ref_id:
                        chunk_rec = chk
                        break
                if chunk_rec:
                    q_text = format_text(str(chunk_rec.get("text") or chunk_rec.get("content") or ""), step_id, block_idx)
                    attr = str(chunk_rec.get("attribution") or chunk_rec.get("author") or "")
                    lines.append(f"> {q_text}")
                    if attr:
                        lines.append(f">\n> — *{attr}*")
                    lines.append("")

            elif kind == "paradigm":
                ref_id = block.get("ref", "")
                lines.append(f"<!-- paradigm: {ref_id} -->")
                lines.append("")

            elif kind == "table":
                rows = block.get("rows", [])
                if rows:
                    header = rows[0]
                    lines.append("| " + " | ".join(str(c) for c in header) + " |")
                    lines.append("| " + " | ".join("---" for _ in header) + " |")
                    for row in rows[1:]:
                        lines.append("| " + " | ".join(str(c) for c in row) + " |")
                    lines.append("")

            elif kind == "pronunciation":
                txt = block.get("text", "")
                lines.append(format_text(txt, step_id, block_idx))
                lines.append("")

            elif kind == "bilingual":
                uk_lines = block.get("uk", [])
                en_lines = block.get("en", [])
                lines.append("| Ukrainian | English |")
                lines.append("| --- | --- |")
                for u_line, e_line in zip(uk_lines, en_lines, strict=False):
                    lines.append(f"| {u_line} | {e_line} |")
                lines.append("")

            elif kind == "culture":
                txt = block.get("text", "")
                lines.append(f"> [!note]\n> {format_text(txt, step_id, block_idx)}")
                lines.append("")

            elif kind == "tip":
                txt = block.get("text", "")
                lines.append(f"> [!tip]\n> {format_text(txt, step_id, block_idx)}")
                lines.append("")

            elif kind == "summary":
                txt = block.get("text", "")
                lines.append(f"> [!summary]\n> {format_text(txt, step_id, block_idx)}")
                lines.append("")

            elif kind == "callout":
                txt = block.get("text", "")
                lines.append(f"> [!note]\n> {format_text(txt, step_id, block_idx)}")
                lines.append("")

            elif kind == "video":
                v_lead = block.get("lead_in")
                if v_lead:
                    lines.append(format_text(v_lead, step_id, block_idx))
                    lines.append("")
                ref_id = block.get("ref", "")
                lines.append(f"<!-- video: {ref_id} -->")
                lines.append("")

            elif kind == "dialogue":
                dial = draft.get("dialogue") or {}
                for line_idx, line in enumerate(dial.get("lines", [])):
                    if isinstance(line, dict):
                        spk = line.get("speaker", "")
                        l_txt = format_text(line.get("text", ""), step_id, f"dialogue_{line_idx}")
                        lines.append(f"> **{spk}:** {l_txt}")
                lines.append("")

            elif kind == "activity":
                ref_id = block.get("ref", "")
                lines.append(f"<!-- activity: {ref_id} -->")
                lines.append("")

    consol_lead = draft.get("consolidation", {}).get("lead_in")
    if consol_lead:
        lines.append(format_text(consol_lead, None, "consolidation_lead_in"))
        lines.append("")

    return "\n".join(lines).strip()


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
) -> CheckResult:
    """Check 9: Apply stress, build Slovnyk and Resursy, verify locks, render MDX."""
    try:
        stressed_doc = apply_stress(expanded_doc, stream)
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"stress application raised: {exc}", layer="writer")

    tokens = getattr(stream, "tokens", None) or (stream.get("tokens") if isinstance(stream, dict) else [])
    for tok in tokens:
        if isinstance(tok, dict):
            sel = tok.get("selected")
            if isinstance(sel, dict) and sel.get("stressed") == "pending":
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

    vocab_items = build_slovnyk_tab(lesson_entry, words_store, stream)
    external_resources = build_resursy_tab(lesson_entry, pack)

    try:
        lock_doc = lesson_lock.compute_lesson_lock(
            level,
            slug,
            plan_dict=plan,
            pack_dict=pack,
            words_dict=words_store,
            repo_root=repo_root,
        )
        lessons_lock_sha256 = hashlib.sha256(lock.yaml_bytes(lock_doc)).hexdigest()
        lesson_entry_sha256 = ""
        for l_item in lock_doc.get("lessons", []):
            if l_item.get("n") == lesson_n:
                lesson_entry_sha256 = l_item.get("entry_sha256", "")
                break
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"lesson lock calculation failed: {exc}", layer="pack")

    try:
        band = compute_lesson_immersion_band(
            track="standard",
            level=level,
            module_slug=slug,
            lesson_n=lesson_n,
            cumulative_core_count=10,
            repo_root=repo_root,
        )
        immersion_band_key = band.band_key
    except Exception:
        immersion_band_key = f"{level}_start"

    lesson_job = str(lesson_entry.get("job") or "")

    meta_data = {
        "title": str(lesson_entry.get("title") or "Lesson"),
        "subtitle": str(lesson_entry.get("rationale") or ""),
        "evidence": {
            "lessons_lock_sha256": lessons_lock_sha256,
            "lesson_entry_sha256": lesson_entry_sha256,
        },
        "immersion": immersion_band_key,
        "job": lesson_job,
    }

    urok_md = _render_urok_markdown(draft, stressed_doc, pack, words_store)

    try:
        mdx_content = generate_mdx(
            md_content=urok_md,
            module_num=lesson_n,
            yaml_activities=draft.get("activities", []),
            meta_data=meta_data,
            vocab_items=vocab_items,
            external_resources=external_resources,
            level=level,
            pipeline_version="v7",
            build_status="draft",
        )
    except Exception as exc:
        return CheckResult(check=9, passed=False, reason=f"MDX rendering failed: {exc}", layer="writer")

    if output_dir is not None:
        write_stressed_document(stressed_doc, output_dir, lesson_n)

    if site_dir is not None:
        site_dir.mkdir(parents=True, exist_ok=True)
        mdx_file = site_dir / f"lesson-{lesson_n}.mdx"
        mdx_file.write_text(mdx_content, encoding="utf-8")

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
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    astro_build: bool = False,
) -> dict[str, Any]:
    """End-to-end assembly pipeline for one lesson (checks 5, 9, 11)."""
    root = repo_root or REPO_ROOT

    paths = lesson_lock.resolve_paths(level, slug, repo_root=root)
    state_dir = output_dir or (paths["evidence_dir"] / "_state" / slug)
    target_site_dir = site_dir or (root / "site" / "src" / "content" / "docs" / level / slug)

    plan = yaml.safe_load(paths["plan"].read_text(encoding="utf-8"))
    pack = yaml.safe_load(paths["pack"].read_text(encoding="utf-8"))
    words_store = yaml.safe_load(paths["words"].read_text(encoding="utf-8"))

    if draft_dict is None:
        draft_file = state_dir / f"lesson-{lesson_n}.draft.yaml"
        if not draft_file.is_file():
            raise FileNotFoundError(f"Draft file not found: {draft_file}")
        draft = yaml.safe_load(draft_file.read_text(encoding="utf-8"))
    else:
        draft = draft_dict

    # Check 5: Assembly
    c5 = check_5_assembly(draft, plan, pack, words_store, level, slug, lesson_n, output_dir=state_dir)
    if not c5.passed:
        return {"ok": False, "failure": c5.to_dict()}

    expanded_doc = c5.artifacts["expanded_doc"]

    # Resolver resolution
    allowlist = Allowlist.load(root / f"curriculum/l2-uk-en/evidence/{level}")
    sources = Sources()
    stream = resolve(ExpandedDocument.from_data(expanded_doc), allowlist, sources)

    # Check 9: Stress and render
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
