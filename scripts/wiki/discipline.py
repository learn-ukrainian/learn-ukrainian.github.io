#!/usr/bin/env python3
"""Writer + reviewer discipline utilities — citation bounds and canonical anchors.

Two failure classes this module addresses:

1. **Invented citations**: Gemini (and to a lesser extent Opus) writes
   `[S6]`, `[S7]`, etc. in article/module body even when retrieval only
   supplied `[S1]` through `[S5]`. The post-compile resolver then marks
   these as `type: unknown` with the bare chunk ID because no real
   source exists. Prevention beats remediation — the writer prompt
   should carry an explicit numeric bound, and a mechanical post-pass
   strips any `[SX]` where X > N.

2. **Decolonization-critical fact drift**: LLMs leak Russian-imperial
   or Soviet-residual forms into Ukrainian-language output (e.g.
   «блакитний-жовтий» for the flag instead of the canonical
   «синьо-жовтий»). These are known, finite, and high-stakes — the
   registry at `data/canonical_anchors.yaml` lists them. Writers must
   use the canonical form verbatim; reviewers must REJECT any article
   containing a forbidden pattern; mechanical validators can either
   strip-and-flag or block-and-surface.

Consumers:

- `scripts/wiki/compiler.py::_build_prompt` — injects the canonical-
  anchors table and source-count into the writer prompt.
- `scripts/wiki/compile.py::cmd_compile_one` — runs the mechanical
  validators after compile, before index update, and emits a
  structured event on any violation.
- `scripts/build/v6_build.py` — analogous injection for module writer
  and reviewer prompts (shared via `scripts/build/contracts/`).

Design intent:

- All regex patterns are explicit + commented — they're the hot path
  for decolonization correctness, reviewability matters more than
  code golf.
- Zero network calls. Zero LLM calls. Fast enough to run on every
  compile without measurable overhead.
- Returns structured records, never mutates inputs. Callers decide
  whether to strip, warn, or hard-fail.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Repo-root resolution — works when run as module or script.
_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Path to the shared anchors registry. Both wiki + module pipelines use this.
CANONICAL_ANCHORS_PATH = _REPO_ROOT / "data" / "canonical_anchors.yaml"

#: Regex for finding short-form citation IDs like [S12] in article prose.
#: Matches [S1], [S23], [S456]; does NOT match [S1a], [S], [Sabc].
_CITATION_RE = re.compile(r"\[S(\d+)\]")


# ─────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CitationViolation:
    """A single invented-citation issue found in article body."""

    cited_id: str  # e.g. "S6"
    cited_number: int  # e.g. 6
    max_legal: int  # e.g. 5 (source_count)
    context: str  # surrounding text for human review
    kind: str = "invented_citation"


@dataclass(frozen=True)
class AnchorViolation:
    """A single canonical-anchor forbidden-pattern match in article body."""

    anchor_id: str  # e.g. "flag_ukraine"
    topic_uk: str
    matched_pattern: str
    matched_text: str  # the actual string from the article that matched
    context: str  # surrounding text (~60 chars each side)
    reason: str
    correct_form: str
    kind: str = "forbidden_anchor_form"


@dataclass
class DisciplineReport:
    """Combined report from all mechanical validators."""

    citations: list[CitationViolation] = field(default_factory=list)
    anchors: list[AnchorViolation] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.citations and not self.anchors

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "citation_violations": [v.__dict__ for v in self.citations],
            "anchor_violations": [v.__dict__ for v in self.anchors],
            "counts": {
                "citations": len(self.citations),
                "anchors": len(self.anchors),
            },
        }


# ─────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def load_canonical_anchors(path: Path | None = None) -> dict[str, Any]:
    """Load and cache the canonical anchors registry.

    Returns the parsed YAML as a dict. Raises FileNotFoundError if the
    registry file is missing — this is intentional. Running the pipeline
    without the registry = running without the fact-discipline floor,
    which we never want to do silently.
    """
    target = path or CANONICAL_ANCHORS_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"Canonical anchors registry not found at {target}. "
            "This file is load-bearing for decolonization correctness."
        )
    data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if "anchors" not in data:
        raise ValueError(
            f"{target} missing required top-level key 'anchors'"
        )
    return data


def _iter_anchors(path: Path | None = None) -> list[dict[str, Any]]:
    """Return the flat anchor list. Kept separate from load_canonical_anchors
    so callers can pass a test fixture path without polluting the lru_cache."""
    if path is None:
        return list(load_canonical_anchors()["anchors"])
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("anchors", []))


# ─────────────────────────────────────────────────────────────────────
# Mechanical validators
# ─────────────────────────────────────────────────────────────────────


def validate_citation_bound(
    article_text: str, source_count: int
) -> list[CitationViolation]:
    """Flag every [SN] in article where N > source_count.

    These are the invented citations — writer cited a chunk that was
    never retrieved. Post-compile the resolver marks them as
    `type: unknown` with a bare chunk ID; catching them here, before
    the resolver runs, means we can strip-or-flag before the reader
    ever sees a broken citation.

    Returns a list of CitationViolation, one per offending ID (even if
    the same invented ID appears many times — callers can dedupe).
    """
    if source_count < 0:
        raise ValueError(f"source_count must be ≥0, got {source_count}")

    violations: list[CitationViolation] = []
    for match in _CITATION_RE.finditer(article_text):
        cited_num = int(match.group(1))
        if cited_num > source_count:
            start = max(0, match.start() - 40)
            end = min(len(article_text), match.end() + 40)
            context = article_text[start:end].replace("\n", " ")
            violations.append(
                CitationViolation(
                    cited_id=f"S{cited_num}",
                    cited_number=cited_num,
                    max_legal=source_count,
                    context=context,
                )
            )
    return violations


def validate_canonical_anchors(
    article_text: str, anchors_path: Path | None = None
) -> list[AnchorViolation]:
    """Scan article for forbidden patterns listed in the anchors registry.

    For each anchor with a non-empty `forbidden` list, run each
    `pattern` as a regex against the article body. Every match produces
    one AnchorViolation with the matched text, surrounding context,
    and the `reason` text from the registry for downstream reporting.

    Regex flags: case-insensitive for Latin, case-insensitive for
    Cyrillic is implicit since the patterns in the registry are
    typically written case-sensitively for the exact form we're
    forbidding. Callers write the patterns; this function just runs
    them.
    """
    violations: list[AnchorViolation] = []
    for anchor in _iter_anchors(anchors_path):
        forbidden = anchor.get("forbidden") or []
        if not forbidden:
            continue
        for rule in forbidden:
            pattern = rule.get("pattern")
            reason = rule.get("reason", "")
            if not pattern:
                continue
            try:
                rx = re.compile(pattern, flags=re.IGNORECASE)
            except re.error as exc:
                # Registry bug — surface it; don't silently skip.
                violations.append(
                    AnchorViolation(
                        anchor_id=anchor.get("id", "<unknown>"),
                        topic_uk=anchor.get("topic_uk", ""),
                        matched_pattern=pattern,
                        matched_text=f"<regex-error: {exc}>",
                        context="",
                        reason=f"REGISTRY BUG: invalid regex — {exc}",
                        correct_form=anchor.get("correct", ""),
                        kind="registry_error",
                    )
                )
                continue
            for match in rx.finditer(article_text):
                start = max(0, match.start() - 60)
                end = min(len(article_text), match.end() + 60)
                context = article_text[start:end].replace("\n", " ")
                violations.append(
                    AnchorViolation(
                        anchor_id=anchor.get("id", "<unknown>"),
                        topic_uk=anchor.get("topic_uk", ""),
                        matched_pattern=pattern,
                        matched_text=match.group(0),
                        context=context,
                        reason=reason,
                        correct_form=anchor.get("correct", ""),
                    )
                )
    return violations


def run_discipline_checks(
    article_text: str,
    source_count: int,
    anchors_path: Path | None = None,
) -> DisciplineReport:
    """Run both mechanical validators and return a combined report."""
    return DisciplineReport(
        citations=validate_citation_bound(article_text, source_count),
        anchors=validate_canonical_anchors(article_text, anchors_path),
    )


# ─────────────────────────────────────────────────────────────────────
# Repairs
# ─────────────────────────────────────────────────────────────────────


def strip_invented_citations(
    article_text: str, source_count: int
) -> tuple[str, list[str]]:
    """Remove every [SN] where N > source_count from article text.

    Returns (repaired_text, stripped_ids). The stripped citations are
    replaced with an empty string; surrounding punctuation and spaces
    are preserved as-is — we don't try to re-flow the sentence. If a
    paragraph ends up with nothing after `something.  .` the downstream
    enrich/verify phases will catch it; we stay conservative.

    stripped_ids preserves order + duplicates, so the caller can log
    exactly how many invented citations were removed and which chunks
    they claimed to cite.
    """
    stripped: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        cited_num = int(match.group(1))
        if cited_num > source_count:
            stripped.append(f"S{cited_num}")
            return ""
        return match.group(0)

    repaired = _CITATION_RE.sub(_repl, article_text)
    # Clean up left-over `  ` (two spaces) and `[]` wrappers from
    # things like `text [S6] [S7] text` → `text  text`.
    repaired = re.sub(r" {2,}", " ", repaired)
    repaired = re.sub(r"\[\s*\]", "", repaired)
    return repaired, stripped


def flag_anchor_violations(
    article_text: str, violations: list[AnchorViolation]
) -> str:
    """Insert `<!-- VERIFY: ... -->` markers next to forbidden-anchor hits.

    Non-destructive: the original text is preserved, but each violation
    gets a trailing HTML comment that the downstream reviewer will see
    and the published site will ignore. This lets us flag-without-
    breaking when we don't want to auto-strip (e.g. for cases where
    the writer's sentence would collapse if we removed the phrase).

    Deduplicates by (anchor_id, match_start) so repeated hits on the
    same position only get marked once.
    """
    if not violations:
        return article_text

    # Some anchor patterns (like "блакитно-жовт") only match a word stem.
    # Walk forward from match.end() to the next word-boundary character so
    # the VERIFY marker lands AFTER the full word, not mid-word (which
    # would split "блакитно-жовтий" into "блакитно-жовт" + marker + "ий").
    word_boundary_re = re.compile(r"[\s.,;:!?»)]|$")

    positions: list[tuple[int, int, str]] = []
    for v in violations:
        rx = re.compile(v.matched_pattern, flags=re.IGNORECASE)
        for m in rx.finditer(article_text):
            if m.group(0) == v.matched_text:
                marker = (
                    f"<!-- VERIFY: {v.anchor_id} — {v.reason} "
                    f"Canonical form: «{v.correct_form}» -->"
                )
                # Extend insertion point to the next word boundary so we
                # don't slice through a word like "блакитно-жовтий".
                boundary = word_boundary_re.search(article_text, m.end())
                insert_at = boundary.start() if boundary else m.end()
                positions.append((m.start(), insert_at, marker))
                break  # one mark per violation, not every match

    positions.sort(reverse=True)
    out = article_text
    seen_ends: set[int] = set()
    for _, end, marker in positions:
        if end in seen_ends:
            continue
        seen_ends.add(end)
        out = out[:end] + " " + marker + out[end:]
    return out


# ─────────────────────────────────────────────────────────────────────
# Prompt-side rendering
# ─────────────────────────────────────────────────────────────────────


def render_canonical_anchors_for_writer(
    anchors_path: Path | None = None,
) -> str:
    """Render the canonical anchors as a Ukrainian instructional block
    for injection into the writer prompt as `{canonical_anchors}`.

    Output is Ukrainian prose + a single table. The writer reads this
    right before producing output and is expected to comply verbatim.
    """
    anchors = _iter_anchors(anchors_path)
    rendered_rows: list[str] = []
    for anchor in anchors:
        forbidden = anchor.get("forbidden") or []
        if not forbidden:
            continue  # purely affirmative anchors don't go in the writer table
        topic_uk = anchor.get("topic_uk", "")
        correct = anchor.get("correct", "")
        for rule in forbidden:
            pattern = rule.get("pattern", "")
            reason = rule.get("reason", "")
            rendered_rows.append(
                f"| {topic_uk} | **{correct}** | ❌ `{pattern}` | {reason} |"
            )

    header = (
        "## Канонічні формули (ОБОВ'ЯЗКОВО дотримуватися)\n\n"
        "Під час написання тексту ти МАЄШ використовувати канонічні форми "
        "нижче дослівно. Заборонені варіанти — це ВІДОМІ дрейфи LLM у бік "
        "російсько-імперських або радянсько-залишкових формулювань. "
        "Вони автоматично перевіряються після компіляції; порушення = "
        "перезапуск або REJECT на етапі рецензії.\n\n"
        "| Тема | Канонічна форма | Заборонено | Чому |\n"
        "|---|---|---|---|"
    )
    if not rendered_rows:
        return header + "\n| (реєстр порожній — цей рівень не має анкерів) | | | |\n"
    return header + "\n" + "\n".join(rendered_rows) + "\n"


def render_citation_discipline_block(source_count: int) -> str:
    """Render the strict citation-discipline rules for the writer prompt.

    Parameterized by actual retrieval count so the numeric bound is
    unambiguous. Ukrainian, to match the rest of the writer prompt's
    primary language.
    """
    return (
        f"## Дисципліна посилань (строга, не м'яка)\n\n"
        f"Блок джерел вище містить рівно **{source_count}** фрагментів, "
        f"пронумерованих від `[S1]` до `[S{source_count}]`.\n\n"
        f"1. **Цитуй ТІЛЬКИ ідентифікатори з діапазону `[S1]..[S{source_count}]`.** "
        f"Числа вище `{source_count}` НЕ ІСНУЮТЬ і не мають з'являтися в тексті.\n"
        f"2. Якщо твердження не підтверджується жодним із наявних джерел, "
        f"ЛИШИ його без посилання або додай `<!-- VERIFY: причина -->` "
        f"замість вигадування цитати. Нецитоване твердження є методично "
        f"слабшим, але вигадана цитата — фактична брехня.\n"
        f"3. Кожен `[SX]` у твоєму виводі буде механічно перевірено проти "
        f"списку джерел. Вигадані посилання автоматично видаляються "
        f"або змушують перезапуск циклу рецензії.\n"
        f"4. `Ї` у числових діапазонах не використовуй (формат суворий: "
        f"арабські цифри в дужках, `[S1]`, `[S2]`, `[S{source_count}]`, без "
        f"пробілів, без літер).\n"
    )


def render_canonical_anchors_for_reviewer(
    anchors_path: Path | None = None,
) -> str:
    """Render canonical anchors as a REJECTION criterion block for the
    reviewer prompt. Reviewer reads this and REJECTs any article that
    contains a forbidden form."""
    anchors = _iter_anchors(anchors_path)
    rendered: list[str] = []
    for anchor in anchors:
        forbidden = anchor.get("forbidden") or []
        if not forbidden:
            continue
        topic = anchor.get("topic_uk", "")
        correct = anchor.get("correct", "")
        for rule in forbidden:
            pattern = rule.get("pattern", "")
            reason = rule.get("reason", "")
            rendered.append(
                f"- **{topic}** → canonical `{correct}`; REJECT if `{pattern}` matches. Reason: {reason}"
            )

    if not rendered:
        return "## Canonical anchors\n(registry empty)\n"
    return (
        "## Canonical anchors — REJECT triggers\n\n"
        "The article under review must not contain any of the forbidden "
        "patterns below. Every match is an automatic REJECT verdict — "
        "these are decolonization-critical facts with state/dictionary "
        "authority. Emit a `REJECT` verdict, cite the specific matched "
        "text, and produce a `<fixes>` block replacing the forbidden "
        "form with the canonical one.\n\n"
        + "\n".join(rendered)
        + "\n"
    )
