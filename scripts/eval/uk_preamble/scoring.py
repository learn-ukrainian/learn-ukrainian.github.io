"""Deterministic span-level scoring of review answers, writing metrics and judge tallies.

Review rules (Protocol v2, #9623). The answer's ``corrected_text`` is the
evidence of what the model changed; the ``corrections`` list is what it claims.

- Changes are the token-level difference between the original paragraph and
  ``corrected_text`` (words, single punctuation marks and whitespace runs;
  apostrophe variants and whitespace amounts compare equal; whitespace-only
  changes are ignored). They depend only on the two texts, never on how the
  corrections were grouped, and unchanged words inside a changed stretch stay
  unchanged.
- A seeded error is a hit when ``corrected_text`` realises one of its
  accepted corrections: changes that reach errors are grouped with them, and
  the model's text over that window is compared with the original after
  applying accepted corrections (each error fixed by an accepted form or left);
  the assignment with the most fixed errors and the least other change wins,
  and an error counts only when no remaining difference touches it. A logged
  correction that ``corrected_text`` does not apply is not a hit; an unlogged
  change counts like a logged one.
- False alarms are counted in units that do not depend on packaging: each
  protected span that is changed or accused, and each other correct word
  (or insertion point) that is changed or accused. An accusation is a logged
  correction's own token-level difference, so quoted context is never
  accused. Corrections that cannot be anchored are unsupported accusations,
  counted one each. A remaining difference on an error span is a wrong
  correction (a miss), not a false alarm.
- Diagnostics: changed units that no correction claims (unlogged) and claimed
  units that ``corrected_text`` does not change (unapplied).
- Style suggestions are tallied separately and never count as hits or false
  alarms. A failed item (no answer, malformed answer, or a task that was not
  run or not accepted) keeps its errors in the denominator as misses.
"""

from __future__ import annotations

import bisect
import difflib
import itertools
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .common import CEFR_LEVELS, ResultsDir, cyrillic_words, fold_apostrophes, latin_words
from .dataset import EvalSet, ReviewItem, Span, WritingTask
from .prompts import JUDGE_CRITERIA, validate_response
from .runner import Slot, TaskSpec, load_raw, valid_entries

MAX_COMBINATIONS = 4096
_TOKEN = re.compile(r"\s+|\w+(?:['-]\w+)*|[^\w\s]")


@dataclass(frozen=True)
class Token:
    start: int
    end: int
    key: str


def tokenize(text: str) -> list[Token]:
    """Words, single punctuation marks and whitespace runs; keys fold apostrophes and whitespace amounts."""
    return [
        Token(m.start(), m.end(), " " if m.group().isspace() else m.group())
        for m in _TOKEN.finditer(fold_apostrophes(text))
    ]


def _whitespace_only(a: Sequence[Token], b: Sequence[Token]) -> bool:
    return all(t.key == " " for t in (*a, *b))


def _opcodes(a: Sequence[Token], b: Sequence[Token]) -> list[tuple[str, int, int, int, int]]:
    matcher = difflib.SequenceMatcher(None, [t.key for t in a], [t.key for t in b], autojunk=False)
    return matcher.get_opcodes()


def _char_range(tokens: Sequence[Token], i1: int, i2: int, length: int) -> tuple[int, int]:
    if i1 < i2:
        return tokens[i1].start, tokens[i2 - 1].end
    pos = tokens[i1].start if i1 < len(tokens) else length
    return pos, pos


@dataclass(frozen=True)
class Change:
    """One non-whitespace difference: source tokens [i1, i2) became target tokens [j1, j2)."""

    i1: int
    i2: int
    j1: int
    j2: int
    start: int  # source characters
    end: int


def changes_between(source: str, a: Sequence[Token], b: Sequence[Token]) -> tuple[list[Change], list[tuple]]:
    """Non-whitespace changes, and every opcode (whitespace-only ones tagged ``"space"``)."""
    ops = []
    out = []
    for tag, i1, i2, j1, j2 in _opcodes(a, b):
        if tag != "equal" and _whitespace_only(a[i1:i2], b[j1:j2]):
            tag = "space"
        ops.append((tag, i1, i2, j1, j2))
        if tag not in {"equal", "space"}:
            out.append(Change(i1, i2, j1, j2, *_char_range(a, i1, i2, len(source))))
    return out, ops


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


def _reaches(start: int, end: int, span: Span) -> bool:
    """A change over source characters [start, end) addresses ``span`` (insertions at its edges included)."""
    if start == end:
        return span.start <= start <= span.end
    if span.start == span.end:
        return start <= span.start <= end
    return start < span.end and span.start < end


def _overlaps(start: int, end: int, span: Span) -> bool:
    """Characters [start, end) lie inside ``span`` (an insertion only when strictly inside)."""
    if start == end:
        return span.start < start < span.end or span.start == span.end == start
    if span.start == span.end:
        return start < span.start < end
    return start < span.end and span.start < end


@dataclass
class Units:
    """Packaging-independent units a difference affects."""

    errors: set[str] = field(default_factory=set)
    protected: set[str] = field(default_factory=set)
    other: set[tuple[str, int]] = field(default_factory=set)

    def update(self, other: Units) -> None:
        self.errors |= other.errors
        self.protected |= other.protected
        self.other |= other.other

    def keys(self) -> set[tuple[str, Any]]:
        return {("e", e) for e in self.errors} | {("p", p) for p in self.protected} | {("o", o) for o in self.other}


class _Paragraph:
    """The original paragraph with its spans, and the classifier mapping differences to units."""

    def __init__(self, item: ReviewItem) -> None:
        self.item = item
        self.text = item.text
        self.tokens = tokenize(item.text)
        self.starts = [t.start for t in self.tokens]

    def token_at(self, pos: int) -> int:
        return bisect.bisect_right(self.starts, pos) - 1

    def token_range(self, start: int, end: int) -> tuple[int, int]:
        """Source tokens covering characters [start, end); an insertion point inside a word covers that word."""
        if start == end:
            k = bisect.bisect_left(self.starts, start)
            if 0 < k <= len(self.tokens) and self.tokens[k - 1].start < start < self.tokens[k - 1].end:
                return k - 1, k
            return k, k
        return self.token_at(start), self.token_at(end - 1) + 1

    def classify(
        self,
        rewritten: str,
        origin: Sequence[tuple[str, Any]],
        model: str,
        unchosen: Sequence[Span],
        boundary: tuple[int, int],
    ) -> Units:
        """Units touched by the difference between ``rewritten`` (chars tagged with ``origin``) and ``model``."""
        units = Units()
        a, b = tokenize(rewritten), tokenize(model)
        for change in changes_between(rewritten, a, b)[0]:
            if change.start < change.end:
                for kind, value in origin[change.start : change.end]:
                    if kind == "e":
                        units.errors.add(value)
                    else:
                        self._source_char(value, unchosen, units)
                continue
            q = change.start
            left = origin[q - 1] if q > 0 else None
            right = origin[q] if q < len(origin) else None
            if left and right and left[0] == right[0] == "e" and left[1] == right[1]:
                units.errors.add(left[1])
                continue
            if right is not None and right[0] == "s":
                pos = right[1]
            elif left is not None and left[0] == "s":
                pos = left[1] + 1
            else:
                pos = boundary[1] if q > 0 else boundary[0]
            self._source_point(pos, unchosen, units)
        return units

    def _source_char(self, pos: int, unchosen: Sequence[Span], units: Units) -> None:
        for err in unchosen:
            if err.start <= pos < err.end:
                units.errors.add(err.id)
                return
        for prot in self.item.protected:
            if prot.start <= pos < prot.end:
                units.protected.add(prot.id)
                return
        token = self.tokens[self.token_at(pos)]
        if token.key != " ":
            units.other.add(("tok", self.token_at(pos)))

    def _source_point(self, pos: int, unchosen: Sequence[Span], units: Units) -> None:
        for err in unchosen:
            if _overlaps(pos, pos, err):
                units.errors.add(err.id)
                return
        for prot in self.item.protected:
            if prot.start < pos < prot.end:
                units.protected.add(prot.id)
                return
        units.other.add(("ins", pos))

    def rewrite(self, lo: int, hi: int, chosen: Sequence[tuple[Span, str]]) -> tuple[str, list[tuple[str, Any]]]:
        """The original [lo, hi) with ``chosen`` corrections applied, each character tagged with its origin."""
        parts: list[str] = []
        origin: list[tuple[str, Any]] = []
        cursor = lo
        for err, replacement in sorted(chosen, key=lambda c: (c[0].start, c[0].end)):
            parts.append(self.text[cursor : err.start])
            origin += [("s", i) for i in range(cursor, err.start)]
            parts.append(replacement)
            origin += [("e", err.id)] * len(replacement)
            cursor = err.end
        parts.append(self.text[cursor:hi])
        origin += [("s", i) for i in range(cursor, hi)]
        return "".join(parts), origin


def _disjoint(chosen: Sequence[tuple[Span, str]]) -> bool:
    spans = sorted((c[0].start, c[0].end) for c in chosen)
    return all(a[1] <= b[0] and not (a[0] == a[1] == b[0] == b[1]) for a, b in itertools.pairwise(spans))


def _eq_map(ops: Sequence[tuple], k: int) -> int | None:
    """Target token index for source boundary ``k`` inside an equal (or whitespace-only) block."""
    for tag, i1, i2, j1, j2 in ops:
        if tag in {"equal", "space"} and i1 <= k <= i2:
            return j1 + min(k - i1, j2 - j1)
    return None


def _window_score(para: _Paragraph, errors: Sequence[Span], lo: int, hi: int, model: str) -> tuple[set[str], Units]:
    """Best assignment of accepted corrections over [lo, hi): (hit error ids, units of the remaining difference)."""
    options = [[None, *((err, form) for form in err.accepted)] for err in errors]
    best: tuple[tuple[int, int, int], set[str], Units] | None = None
    for count, combo in enumerate(itertools.product(*options)):
        if count >= MAX_COMBINATIONS:
            break
        chosen = [choice for choice in combo if choice is not None]
        if not _disjoint(chosen):
            continue
        rewritten, origin = para.rewrite(lo, hi, chosen)
        chosen_ids = {err.id for err, _ in chosen}
        unchosen = [err for err in errors if err.id not in chosen_ids]
        units = para.classify(rewritten, origin, model, unchosen, (lo, hi))
        hits = chosen_ids - units.errors
        rank = (len(hits), -(len(units.protected) + len(units.other)), -len(units.errors))
        if best is None or rank > best[0]:
            best = (rank, hits, units)
    assert best is not None  # the empty assignment is always disjoint
    return best[1], best[2]


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
        "unlogged_change_units": 0,
        "unapplied_logged_units": 0,
        "new_invalid_forms": [],
    }


def actual_changes(item: ReviewItem, corrected_text: str) -> tuple[set[str], set[str], Units]:
    """(hit error ids, error ids changed but not fixed, units changed) from the text difference alone."""
    para = _Paragraph(item)
    target = unicodedata.normalize("NFC", corrected_text)
    target_tokens = tokenize(target)
    changes, ops = changes_between(item.text, para.tokens, target_tokens)
    # Group errors and the changes that reach them (union-find over errors and changes).
    nodes = [("e", i) for i in range(len(item.errors))] + [("c", i) for i in range(len(changes))]
    parent = {node: node for node in nodes}

    def find(node: tuple[str, int]) -> tuple[str, int]:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for ci, change in enumerate(changes):
        for ei, err in enumerate(item.errors):
            if _reaches(change.start, change.end, err):
                parent[find(("c", ci))] = find(("e", ei))
    groups: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for node in nodes:
        groups.setdefault(find(node), []).append(node)

    hits: set[str] = set()
    units = Units()
    for members in groups.values():
        comp_changes = [changes[i] for kind, i in members if kind == "c"]
        if not comp_changes:
            continue  # errors nobody changed: misses
        comp_errors = [item.errors[i] for kind, i in members if kind == "e"]
        ranges = [(c.i1, c.i2) for c in comp_changes]
        ranges += [para.token_range(err.start, err.end) for err in comp_errors]
        ti, tj = min(r[0] for r in ranges), max(r[1] for r in ranges)
        lo, hi = _char_range(para.tokens, ti, tj, len(item.text))
        mapped_lo, mapped_hi = _eq_map(ops, ti), _eq_map(ops, tj)
        cj = min([c.j1 for c in comp_changes] + ([mapped_lo] if mapped_lo is not None else []))
        ck = max([c.j2 for c in comp_changes] + ([mapped_hi] if mapped_hi is not None else []))
        model = target[target_tokens[cj].start : target_tokens[ck - 1].end] if ck > cj else ""
        comp_hits, comp_units = _window_score(para, comp_errors, lo, hi, model)
        hits |= comp_hits
        units.update(comp_units)
    return hits, units.errors - hits, units


def _accused(para: _Paragraph, start: int, end: int, replacement: str) -> Units:
    """Units a logged correction claims: its own token-level difference, mapped to the original."""
    rewritten, origin = para.rewrite(start, end, [])
    return para.classify(
        rewritten, origin, unicodedata.normalize("NFC", replacement), list(para.item.errors), (start, end)
    )


def score_review_item(
    item: ReviewItem,
    entry: dict[str, Any] | None,
    failure: str | None = None,
    sources: SourcesClient | None = None,
) -> dict[str, Any]:
    if entry is None:
        return _failed_review(item, failure or "no answer")
    text = item.text
    para = _Paragraph(item)
    hits, wrong, changed = actual_changes(item, entry["corrected_text"])

    claimed = Units()
    unanchored = noop = 0
    for correction in entry["corrections"]:
        anchored = resolve_span(text, correction["span"], correction["start"], correction["end"])
        if anchored is None:
            unanchored += 1
            continue
        units = _accused(para, *anchored, correction["correction"])
        if not units.keys():
            noop += 1
        claimed.update(units)

    protected = changed.protected | claimed.protected
    other = changed.other | claimed.other
    changed_keys = changed.keys() | {("e", e) for e in hits}
    claimed_keys = claimed.keys()

    style = {"total": 0, "on_protected": 0, "on_error": 0, "unanchored": 0}
    for suggestion in entry["style_suggestions"]:
        style["total"] += 1
        anchored = resolve_span(text, suggestion["span"], suggestion["start"], suggestion["end"])
        if anchored is None:
            style["unanchored"] += 1
            continue
        if any(_overlaps(*anchored, p) for p in item.protected):
            style["on_protected"] += 1
        if any(_reaches(*anchored, err) for err in item.errors):
            style["on_error"] += 1

    new_invalid: list[str] = []
    if sources is not None:
        new_invalid = sorted(sources.invalid_forms(entry["corrected_text"]) - sources.invalid_forms(text))
    return {
        "item_id": item.id,
        "failed": False,
        "reason": None,
        "errors": [{"id": e.id, "type": e.kind, "hit": e.id in hits} for e in item.errors],
        "protected_count": len(item.protected),
        "hits": len(hits),
        "fa_protected": len(protected),
        "fa_other": len(other),
        "fa_unanchored": unanchored,
        "false_alarms": len(protected) + len(other) + unanchored,
        "wrong_corrections": len(wrong),
        "noop_corrections": noop,
        "protected_touched": sorted(protected),
        "style": style,
        "unlogged_change_units": len(changed_keys - claimed_keys),
        "unapplied_logged_units": len(claimed_keys - changed_keys),
        "new_invalid_forms": new_invalid,
    }


class SourcesClient(Protocol):
    def invalid_forms(self, text: str) -> set[str]:
        """Word forms of ``text`` that VESUM does not attest."""

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        """Calque/Russianism, VESUM, CEFR and English-intrusion metrics for one text."""


# --------------------------------------------------------------------------- writing

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
        cyrillic = cyrillic_words(text)
        latin = latin_words(text)
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


def task_state(raw: dict[str, Any] | None) -> str:
    """accepted, not_accepted (ran but failed or unattributable) or not_run."""
    if raw is None:
        return "not_run"
    return "accepted" if raw.get("accepted") else "not_accepted"


def _item_results(raw: dict[str, Any] | None, kind: str, item_ids: Sequence[str]) -> dict[str, tuple[Any, str | None]]:
    if raw is None:
        return {item_id: (None, "task not run") for item_id in item_ids}
    if not raw.get("accepted"):
        reason = raw.get("identity_problem") or raw.get("condition_problem") or f"task status {raw.get('status')}"
        return {item_id: (None, reason) for item_id in item_ids}
    return {r.item_id: (r.entry, r.error) for r in validate_response(kind, raw.get("response_text"), item_ids)}


def score_candidates(
    results: ResultsDir, eval_set: EvalSet, slots: Sequence[Slot], sources: SourcesClient | None
) -> dict[str, list[dict[str, Any]]]:
    """Score every planned slot; unrun or failed tasks score as failed items, never dropped."""
    reviews, writings = eval_set.review_by_id(), eval_set.writing_by_id()
    scored: dict[str, list[dict[str, Any]]] = {"review": [], "writing": []}
    for slot in slots:
        raw = load_raw(results, slot.task_id)
        cell = {
            "seat": slot.seat.seat_id,
            "variant": slot.variant,
            "repeat": slot.repeat,
            "task_id": slot.task_id,
            "task_state": task_state(raw),
        }
        for item_id, (entry, failure) in _item_results(raw, slot.kind, slot.item_ids).items():
            if slot.kind == "review":
                record = score_review_item(reviews[item_id], entry, failure, sources)
            else:
                if sources is None:
                    raise RuntimeError("writing metrics need the sources tools")
                record = score_writing_item(writings[item_id], entry, failure, sources)
            scored[slot.kind].append({**cell, **record})
    return scored


def score_judgements(results: ResultsDir, judge_tasks: Sequence[TaskSpec]) -> list[dict[str, Any]]:
    """Map each blind verdict back to variant labels; failed or unrun judgements are kept as failed."""
    records = []
    for task in judge_tasks:
        raw = load_raw(results, task.task_id)
        entries = valid_entries(raw, "judge")
        failures: dict[str, str | None] = {}
        if raw is not None and raw.get("accepted"):
            failures = {r.item_id: r.error for r in validate_response("judge", raw["response_text"], task.item_ids)}
        for item_id in task.item_ids:
            mapping = task.meta["order"][item_id]
            record = {
                "task_id": task.task_id,
                "judge_seat": task.seat.seat_id,
                "candidate_seat": task.meta["candidate_seat"],
                "pair": task.meta["pair"],
                "repeat": task.repeat,
                "item_id": item_id,
                "words": task.meta["words"][item_id],
            }
            entry = entries.get(item_id)
            if entry is None:
                if raw is None:
                    reason = "task not run"
                else:
                    reason = (
                        failures.get(item_id)
                        or raw.get("identity_problem")
                        or raw.get("condition_problem")
                        or f"task status {raw.get('status')}"
                    )
                records.append({**record, "failed": True, "reason": reason, "winner": None, "scores": None})
                continue
            winner = "tie" if entry["winner"] == "tie" else mapping[entry["winner"]]
            scores = {mapping[side]: {c: entry["scores"][side][c] for c in JUDGE_CRITERIA} for side in ("A", "B")}
            records.append({**record, "failed": False, "reason": None, "winner": winner, "scores": scores})
    return records
