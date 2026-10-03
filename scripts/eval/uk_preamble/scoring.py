"""Deterministic span-level scoring of review answers, writing metrics and judge tallies.

Review rules (Protocol v2, #9623):
- Each correction is anchored to the original paragraph: its offsets are used
  when ``text[start:end]`` equals ``span`` (apostrophe-insensitive); otherwise
  the span is relocated to its occurrence nearest ``start``. A correction that
  cannot be anchored is an unsupported accusation (a false alarm).
- A correction's effective edit is its span minus the prefix and suffix it
  leaves unchanged; an edit that changes nothing after normalisation is a no-op.
- A seeded error is a hit when an edit reaches its span and the text the
  model produced over the affected region equals the original with that
  error's accepted correction applied (other seeded errors in the region may be
  corrected by any accepted form or left as they were). Comparison is
  normalised for whitespace and apostrophe variants.
- A false alarm is an edit that reaches no seeded error, an unanchored
  correction, or any edit that changes a protected span. Style suggestions are
  tallied separately and never count as hits or false alarms.
- A failed item (no answer, malformed answer, conflicting corrections, or an
  unattributable task) keeps its errors in the denominator as misses.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .common import CEFR_LEVELS, fold_apostrophes, normalise
from .dataset import EvalSet, ReviewItem, Span, WritingTask
from .prompts import JUDGE_CRITERIA, validate_response
from .runner import Slot, load_raw, valid_entries

MAX_COMBINATIONS = 4096


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: str
    eff_start: int
    eff_end: int


def resolve_span(text: str, span: str, start: Any, end: Any) -> tuple[int, int] | None:
    """Anchor a model-reported span in the original text, or None."""
    folded_text, folded_span = fold_apostrophes(text), fold_apostrophes(span)
    if (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start <= end <= len(text)
        and folded_text[start:end] == folded_span
    ):
        return start, end
    if not span:
        return None
    hits = [m.start() for m in re.finditer(re.escape(folded_span), folded_text)]
    if not hits:
        return None
    anchor = start if isinstance(start, int) else 0
    best = min(hits, key=lambda pos: (abs(pos - anchor), pos))
    return best, best + len(span)


def _effective(text: str, start: int, end: int, replacement: str) -> Edit | None:
    original = text[start:end]
    a, b = fold_apostrophes(original), fold_apostrophes(replacement)
    prefix = 0
    while prefix < min(len(a), len(b)) and a[prefix] == b[prefix]:
        prefix += 1
    suffix = 0
    while suffix < min(len(a), len(b)) - prefix and a[len(a) - 1 - suffix] == b[len(b) - 1 - suffix]:
        suffix += 1
    if normalise(original) == normalise(replacement):
        return None
    return Edit(start, end, replacement, start + prefix, end - suffix)


def touches(edit_start: int, edit_end: int, span: Span) -> bool:
    """The edit changes text inside the span (insertions at its boundary do not)."""
    if edit_start == edit_end:
        return span.start < edit_start < span.end or span.start == span.end == edit_start
    if span.start == span.end:
        return edit_start < span.start < edit_end
    return edit_start < span.end and span.start < edit_end


def reaches(edit: Edit, error: Span) -> bool:
    """The edit addresses the error span (boundaries inclusive for insertions)."""
    if edit.eff_start == edit.eff_end:
        return error.start <= edit.eff_start <= error.end
    if error.start == error.end:
        return edit.eff_start <= error.start <= edit.eff_end
    return edit.eff_start < error.end and error.start < edit.eff_end


def _apply(text: str, lo: int, hi: int, edits: Sequence[tuple[int, int, str]]) -> str:
    out, cursor = [], lo
    for start, end, replacement in sorted(edits):
        out.append(text[cursor:start])
        out.append(replacement)
        cursor = end
    out.append(text[cursor:hi])
    return "".join(out)


def _disjoint(spans: Sequence[tuple[int, int, str]]) -> bool:
    ordered = sorted(spans)
    return all(a[1] <= b[0] and not (a[0] == a[1] == b[0] == b[1]) for a, b in itertools.pairwise(ordered))


def _error_hit(text: str, target: Span, others: Sequence[Span], candidate: str, lo: int, hi: int) -> bool:
    options: list[list[tuple[int, int, str] | None]] = [[(target.start, target.end, a) for a in target.accepted]]
    for other in others:
        options.append([None, *((other.start, other.end, a) for a in other.accepted)])
    wanted = normalise(candidate)
    for count, combo in enumerate(itertools.product(*options)):
        if count >= MAX_COMBINATIONS:
            break
        chosen = [choice for choice in combo if choice is not None]
        if _disjoint(chosen) and normalise(_apply(text, lo, hi, chosen)) == wanted:
            return True
    return False


def _failed_review(item: ReviewItem, reason: str) -> dict[str, Any]:
    return {
        "item_id": item.id,
        "failed": True,
        "reason": reason,
        "errors": [{"id": e.id, "type": e.kind, "hit": False} for e in item.errors],
        "protected_count": len(item.protected),
        "hits": 0,
        "fa_protected": 0,
        "fa_other": 0,
        "fa_unanchored": 0,
        "false_alarms": 0,
        "wrong_corrections": 0,
        "noop_corrections": 0,
        "protected_touched": [],
        "style": {"total": 0, "on_protected": 0, "on_error": 0, "unanchored": 0},
        "unlogged_changes": False,
        "new_invalid_forms": [],
    }


class SourcesClient(Protocol):
    def invalid_forms(self, text: str) -> set[str]:
        """Word forms of ``text`` that VESUM does not attest."""

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        """Calque/Russianism, VESUM, CEFR and English-intrusion metrics for one text."""


def score_review_item(
    item: ReviewItem,
    entry: dict[str, Any] | None,
    failure: str | None = None,
    sources: SourcesClient | None = None,
) -> dict[str, Any]:
    if entry is None:
        return _failed_review(item, failure or "no answer")
    text = item.text
    edits: dict[tuple[int, int, str], Edit] = {}
    unanchored = noop = 0
    for correction in entry["corrections"]:
        anchored = resolve_span(text, correction["span"], correction["start"], correction["end"])
        if anchored is None:
            unanchored += 1
            continue
        edit = _effective(text, *anchored, correction["correction"])
        if edit is None:
            noop += 1
            continue
        edits.setdefault((edit.start, edit.end, edit.replacement), edit)
    edit_list = sorted(edits.values(), key=lambda e: (e.start, e.end))
    if not _disjoint([(e.start, e.end, e.replacement) for e in edit_list]):
        return _failed_review(item, "conflicting corrections: overlapping spans")

    links = {i: [j for j, err in enumerate(item.errors) if reaches(edit, err)] for i, edit in enumerate(edit_list)}
    # Connected components of errors joined through shared edits.
    parent = list(range(len(item.errors)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for linked in links.values():
        for a, b in itertools.pairwise(linked):
            parent[find(a)] = find(b)
    hit_ids: set[str] = set()
    for j, err in enumerate(item.errors):
        comp = [k for k in range(len(item.errors)) if find(k) == find(j)]
        comp_edits = [edit_list[i] for i, linked in links.items() if set(linked) & set(comp)]
        if not comp_edits:
            continue
        spans = [(item.errors[k].start, item.errors[k].end) for k in comp] + [(e.start, e.end) for e in comp_edits]
        lo, hi = min(s for s, _ in spans), max(e for _, e in spans)
        candidate = _apply(text, lo, hi, [(e.start, e.end, e.replacement) for e in comp_edits])
        others = [item.errors[k] for k in comp if k != j]
        if _error_hit(text, err, others, candidate, lo, hi):
            hit_ids.add(err.id)

    fa_protected = fa_other = wrong = 0
    touched: set[str] = set()
    for i, edit in enumerate(edit_list):
        on_protected = [p.id for p in item.protected if touches(edit.eff_start, edit.eff_end, p)]
        touched.update(on_protected)
        if on_protected:
            fa_protected += 1
        elif not links[i]:
            fa_other += 1
        elif not any(item.errors[j].id in hit_ids for j in links[i]):
            wrong += 1

    style = {"total": 0, "on_protected": 0, "on_error": 0, "unanchored": 0}
    for suggestion in entry["style_suggestions"]:
        style["total"] += 1
        anchored = resolve_span(text, suggestion["span"], suggestion["start"], suggestion["end"])
        if anchored is None:
            style["unanchored"] += 1
            continue
        probe = Edit(*anchored, suggestion["suggestion"], *anchored)
        if any(touches(probe.eff_start, probe.eff_end, p) for p in item.protected):
            style["on_protected"] += 1
        if any(reaches(probe, err) for err in item.errors):
            style["on_error"] += 1

    expected = _apply(text, 0, len(text), [(e.start, e.end, e.replacement) for e in edit_list])
    new_invalid: list[str] = []
    if sources is not None:
        new_invalid = sorted(sources.invalid_forms(entry["corrected_text"]) - sources.invalid_forms(text))
    false_alarms = fa_protected + fa_other + unanchored
    return {
        "item_id": item.id,
        "failed": False,
        "reason": None,
        "errors": [{"id": e.id, "type": e.kind, "hit": e.id in hit_ids} for e in item.errors],
        "protected_count": len(item.protected),
        "hits": len(hit_ids),
        "fa_protected": fa_protected,
        "fa_other": fa_other,
        "fa_unanchored": unanchored,
        "false_alarms": false_alarms,
        "wrong_corrections": wrong,
        "noop_corrections": noop,
        "protected_touched": sorted(touched),
        "style": style,
        "unlogged_changes": normalise(entry["corrected_text"]) != normalise(expected),
        "new_invalid_forms": new_invalid,
    }


# --------------------------------------------------------------------------- writing

_CYRILLIC_WORD = re.compile(r"[А-Яа-яІіЇїЄєҐґ]+(?:['’ʼ-][А-Яа-яІіЇїЄєҐґ]+)*")
_LATIN_WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
_CALQUE_CHECKS = frozenset({"russian_shadow", "ua_gec"})


class LocalSources:
    """The ``sources`` tool implementations, called in-process on the local databases."""

    def __init__(self) -> None:
        from scripts.verification.check_text import check_text
        from scripts.verification.vesum import verify_words
        from scripts.wiki.sources_db import query_cefr_levels

        self._check_text = check_text
        self._verify_words = verify_words
        self._cefr = query_cefr_levels

    def _check(self, text: str, checks: list[str]) -> dict[str, Any]:
        result = self._check_text(text=text, checks=checks, max_findings=100_000)
        if result.get("status") == "error":
            raise RuntimeError(f"check_text failed: {result.get('error')}")
        return result

    def invalid_forms(self, text: str) -> set[str]:
        return {p["form"] for p in self._check(text, ["vesum"])["problems"] if p["check"] == "vesum"}

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        result = self._check(text, ["vesum", "russian_shadow", "ua_gec"])
        tokens = int(result["summary"]["tokens"])
        # Verdict tier only (curated Russian shadows grounded in Антоненко-Давидович and other
        # sources, multi-token UA-GEC calques); check_text labels the rest "suspicion, not a verdict".
        calques = [
            {"form": f["form"], "check": f["check"], "occurrences": len(f["locations"])}
            for f in result["problems"]
            if f["check"] in _CALQUE_CHECKS
        ]
        suspicions = [
            {"form": f["form"], "check": f["check"], "occurrences": len(f["locations"])}
            for f in result["suspicions"]
            if f["check"] in _CALQUE_CHECKS
        ]
        calque_hits = sum(c["occurrences"] for c in calques)
        suspicion_hits = sum(c["occurrences"] for c in suspicions)
        invalid = sorted({p["form"] for p in result["problems"] if p["check"] == "vesum"})
        cyrillic = _CYRILLIC_WORD.findall(text)
        latin = _LATIN_WORD.findall(text)
        forms = sorted({word.lower() for word in cyrillic})
        lemmas_by_form = self._verify_words(forms) if forms else {}
        lemmas = sorted({m["lemma"] for matches in lemmas_by_form.values() for m in matches})
        levels = self._cefr(lemmas) if lemmas else {}
        target = CEFR_LEVELS.index(level)
        known = above = 0
        above_words: list[str] = []
        for form in forms:
            ranks = [
                CEFR_LEVELS.index(hit["level"])
                for match in lemmas_by_form.get(form, [])
                for hit in levels.get(match["lemma"], [])
                if hit.get("level") in CEFR_LEVELS
            ]
            if ranks:
                known += 1
                if min(ranks) > target:
                    above += 1
                    above_words.append(form)
        words = len(cyrillic) + len(latin)
        return {
            "tokens": tokens,
            "words": words,
            "calque_hits": calque_hits,
            "calque_density": 100.0 * calque_hits / tokens if tokens else 0.0,
            "calques": calques,
            "calque_suspicion_hits": suspicion_hits,
            "calque_suspicion_density": 100.0 * suspicion_hits / tokens if tokens else 0.0,
            "calque_suspicions": suspicions,
            "vesum_invalid": len(invalid),
            "vesum_invalid_forms": invalid,
            "cefr_known_forms": known,
            "cefr_above_level": above,
            "cefr_above_level_forms": above_words,
            "level_adherence": 1.0 - above / known if known else None,
            "english_words": len(latin),
            "english_intrusion": len(latin) / words if words else 0.0,
        }


def score_writing_item(
    task: WritingTask, entry: dict[str, Any] | None, failure: str | None, sources: SourcesClient
) -> dict[str, Any]:
    if entry is None:
        return {
            "item_id": task.id,
            "level": task.level,
            "failed": True,
            "reason": failure or "no answer",
            "metrics": None,
        }
    metrics = sources.writing_metrics(entry["text"], task.level)
    words = metrics.get("words", 0)
    metrics["within_word_range"] = (task.min_words is None or words >= task.min_words) and (
        task.max_words is None or words <= task.max_words
    )
    return {"item_id": task.id, "level": task.level, "failed": False, "reason": None, "metrics": metrics}


# --------------------------------------------------------------------------- whole run


def _item_results(raw: dict[str, Any] | None, kind: str, item_ids: Sequence[str]) -> dict[str, tuple[Any, str | None]]:
    if raw is None:
        return {item_id: (None, "task not run") for item_id in item_ids}
    if not raw.get("accepted"):
        reason = raw.get("identity_problem") or f"task status {raw.get('status')}"
        return {item_id: (None, reason) for item_id in item_ids}
    return {r.item_id: (r.entry, r.error) for r in validate_response(kind, raw.get("response_text"), item_ids)}


def score_candidates(
    results_dir: Path, eval_set: EvalSet, slots: Sequence[Slot], sources: SourcesClient | None
) -> dict[str, list[dict[str, Any]]]:
    """Score every planned slot; unrun or failed tasks score as failed items, never dropped."""
    reviews, writings = eval_set.review_by_id(), eval_set.writing_by_id()
    scored: dict[str, list[dict[str, Any]]] = {"review": [], "writing": []}
    for slot in slots:
        raw = load_raw(results_dir, slot.task_id)
        cell = {"seat": slot.seat.seat_id, "variant": slot.variant, "repeat": slot.repeat, "task_id": slot.task_id}
        for item_id, (entry, failure) in _item_results(raw, slot.kind, slot.item_ids).items():
            if slot.kind == "review":
                record = score_review_item(reviews[item_id], entry, failure, sources)
            else:
                if sources is None:
                    raise RuntimeError("writing metrics need the sources tools")
                record = score_writing_item(writings[item_id], entry, failure, sources)
            scored[slot.kind].append({**cell, **record})
    return scored


def score_judgements(results_dir: Path, judge_task_ids: Sequence[str]) -> list[dict[str, Any]]:
    """Map each blind verdict back to variant labels; failed judgements are kept as failed."""
    records = []
    for task_id in judge_task_ids:
        raw = load_raw(results_dir, task_id)
        if raw is None:
            continue
        order = raw["meta"]["order"]
        entries = valid_entries(raw, "judge")
        failures = {}
        if raw.get("accepted"):
            failures = {r.item_id: r.error for r in validate_response("judge", raw["response_text"], raw["item_ids"])}
        for item_id in raw["item_ids"]:
            mapping = order[item_id]
            record = {
                "task_id": task_id,
                "judge_seat": raw["seat"],
                "candidate_seat": raw["meta"]["candidate_seat"],
                "pair": raw["meta"]["pair"],
                "repeat": raw["repeat"],
                "item_id": item_id,
            }
            entry = entries.get(item_id)
            if entry is None:
                reason = failures.get(item_id) or raw.get("identity_problem") or f"task status {raw.get('status')}"
                records.append({**record, "failed": True, "reason": reason, "winner": None, "scores": None})
                continue
            winner = "tie" if entry["winner"] == "tie" else mapping[entry["winner"]]
            scores = {mapping[side]: {c: entry["scores"][side][c] for c in JUDGE_CRITERIA} for side in ("A", "B")}
            records.append({**record, "failed": False, "reason": None, "winner": winner, "scores": scores})
    return records
