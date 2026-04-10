"""Post-build analysis of Gemini writer sessions.

Given a dispatched writer call, parse the matching Gemini session file
and produce three artifacts:

1. **Prompt size breakdown** — what fraction of the prompt was plan,
   wiki, skeleton, checklist, tools description, etc. Flags any section
   that exceeds 40% of the total (rule of thumb: likely drowning out
   the rest).

2. **Section compliance** — for chunked writes, the skeleton declares
   per-paragraph topics. We check whether the response's section has
   enough words and covers the declared topics (keyword overlap).

3. **Directive compliance** — "MUST" / "REQUIRED" directives from the
   prompt are extracted and lightly checked against the response. A
   miss doesn't mean the writer definitely ignored the directive (the
   check is keyword-based), but a consistent pattern of misses across
   modules is a real signal.

Output: YAML written to ``orchestration/{slug}/session-analysis.yaml``.
Designed to be non-blocking and best-effort — any failure is logged
and ignored so it never breaks a build.

Issue: #1174
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# -----------------------------------------------------------------------------
# Prompt section detection
# -----------------------------------------------------------------------------

# Known section markers observed in v6 writer prompts. Each tuple is
# ``(name, pattern)`` where the pattern is a regex matching the section
# header line. Order matters — we walk the prompt in source order and
# attribute each character to the last-started section.
#
# Keep this list in sync with ``scripts/build/phases/v6-write*.md``
# templates. If a new section is introduced there, add it here so we
# don't silently dump its bytes into the previous bucket.
_SECTION_MARKERS: list[tuple[str, re.Pattern[str]]] = [
    ("header",        re.compile(r"^# Section-by-Section Generation", re.MULTILINE)),
    ("header",        re.compile(r"^# Full Module Write", re.MULTILINE)),
    ("skeleton",      re.compile(r"^## Section Skeleton", re.MULTILINE)),
    ("skeleton",      re.compile(r"^## Skeleton", re.MULTILINE)),
    ("plan",          re.compile(r"^## Full Plan", re.MULTILINE)),
    ("plan",          re.compile(r"^## Plan", re.MULTILINE)),
    ("wiki",          re.compile(r"^## (?:Wiki|Knowledge Packet|Research)", re.MULTILINE)),
    ("prior_summary", re.compile(r"^## (?:Previous Sections|Prior Context|Rolling Context)", re.MULTILINE)),
    ("rules",         re.compile(r"^## (?:Writing Rules|Content Rules|Style Rules)", re.MULTILINE)),
    ("checklist",     re.compile(r"^## (?:Checklist|Requirements|Must[- ]Have)", re.MULTILINE)),
    ("output_spec",   re.compile(r"^## Output", re.MULTILINE)),
]


@dataclass
class SectionSize:
    name: str
    start: int          # byte offset in the prompt
    length: int         # characters
    fraction: float     # length / total_prompt_length

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "length": self.length,
            "fraction": round(self.fraction, 4),
        }


def analyze_prompt_sections(prompt: str) -> list[SectionSize]:
    """Split a prompt into recognized sections and measure each.

    Characters before the first recognized section are attributed to
    a synthetic ``"preamble"`` section. Characters after the last
    recognized marker are attributed to the last started section (no
    synthetic trailer — the output spec is usually last and captures
    anything that follows).

    Empty prompt returns an empty list.
    """
    if not prompt:
        return []

    # Collect all match positions across all markers.
    hits: list[tuple[int, str]] = []
    for name, pattern in _SECTION_MARKERS:
        for match in pattern.finditer(prompt):
            hits.append((match.start(), name))
    hits.sort(key=lambda x: x[0])

    # If nothing matched, the whole prompt is one unknown blob.
    if not hits:
        return [SectionSize(name="unknown", start=0, length=len(prompt), fraction=1.0)]

    sections: list[SectionSize] = []
    total = len(prompt)

    # Preamble before the first marker.
    if hits[0][0] > 0:
        sections.append(
            SectionSize(
                name="preamble",
                start=0,
                length=hits[0][0],
                fraction=hits[0][0] / total,
            )
        )

    # One section per marker, spanning from the marker to the next one.
    for i, (start, name) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else total
        length = end - start
        if length <= 0:
            continue
        sections.append(
            SectionSize(
                name=name,
                start=start,
                length=length,
                fraction=length / total if total else 0.0,
            )
        )

    # If the same section name appears multiple times (e.g. two markers
    # both mapped to "skeleton"), merge them so the output YAML is
    # deduplicated and easy to diff across builds.
    merged: dict[str, SectionSize] = {}
    for s in sections:
        if s.name in merged:
            existing = merged[s.name]
            merged[s.name] = SectionSize(
                name=s.name,
                start=min(existing.start, s.start),
                length=existing.length + s.length,
                fraction=existing.fraction + s.fraction,
            )
        else:
            merged[s.name] = s
    return sorted(merged.values(), key=lambda s: s.start)


# -----------------------------------------------------------------------------
# Directive extraction ("MUST" / "REQUIRED" / explicit [ ] checklists)
# -----------------------------------------------------------------------------

# Matches a Markdown checklist item: "- [ ] thing" or "- [x] thing".
_CHECKLIST_ITEM = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s+(.+?)\s*$", re.MULTILINE)

# Matches a bullet or sentence containing MUST / REQUIRED / MANDATORY.
# We capture the sentence (up to terminal punctuation) so the directive
# is human-readable in the report.
_MUST_DIRECTIVE = re.compile(
    r"(?:^|[.\n])\s*([^.\n]*\b(?:MUST|REQUIRED|MANDATORY)\b[^.\n]{0,200}[.!?])",
    re.IGNORECASE,
)

# Matches paragraph-level skeleton bullets used in chunked write prompts:
# "- P1 (~120 words): [Dialogue: ...]"
_SKELETON_PARA = re.compile(
    r"^\s*-\s*P(\d+)\s*\(~?(\d+)\s*words\)\s*:\s*\[([^\]]+)\]",
    re.MULTILINE,
)

# Matches an INJECT_ACTIVITY marker declaration in the skeleton.
# The body can contain hyphens (e.g. "fill-in") so we can't use a
# simple negated character class — we terminate on the literal
# "-->" sequence instead via a lookahead.
_INJECT_ACTIVITY = re.compile(
    r"<!--\s*INJECT_ACTIVITY:\s*((?:(?!-->).)+?)\s*-->",
    re.DOTALL,
)

# Template placeholder text in v6-write*.md prompts that looks like a
# real INJECT_ACTIVITY marker but is actually example schema text. We
# filter these so they don't pollute the directive coverage report.
# Pattern: any marker whose first comma-separated part matches one of
# these literal placeholders (case-insensitive).
_INJECT_PLACEHOLDER_FIRST_PARTS = frozenset({
    "type", "activity-type", "type-slug", "activity_type",
})


@dataclass
class Directive:
    kind: str           # "checklist" | "must" | "skeleton_para" | "inject_activity"
    text: str           # The directive as written in the prompt
    covered: bool = False
    coverage_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_directives(prompt: str) -> list[Directive]:
    """Pull out every directive we can recognize from the prompt."""
    directives: list[Directive] = []

    for match in _CHECKLIST_ITEM.finditer(prompt):
        directives.append(Directive(kind="checklist", text=match.group(1).strip()))

    for match in _MUST_DIRECTIVE.finditer(prompt):
        text = match.group(1).strip()
        # Collapse whitespace so the directive is one line in YAML.
        text = " ".join(text.split())
        if text:
            directives.append(Directive(kind="must", text=text))

    for match in _SKELETON_PARA.finditer(prompt):
        num, words, topic = match.group(1), match.group(2), match.group(3).strip()
        directives.append(
            Directive(
                kind="skeleton_para",
                text=f"P{num} ({words}w): {topic}",
            )
        )

    for match in _INJECT_ACTIVITY.finditer(prompt):
        text = match.group(1).strip()
        first_part = text.split(",", 1)[0].strip().lower()
        if first_part in _INJECT_PLACEHOLDER_FIRST_PARTS:
            # Template example, not a real directive
            continue
        directives.append(Directive(kind="inject_activity", text=text))

    return directives


# -----------------------------------------------------------------------------
# Coverage check against the response
# -----------------------------------------------------------------------------

# Words we strip before computing keyword overlap. Minimal list —
# fancier stemming would need a Ukrainian corpus and isn't worth it
# for this level of heuristic.
_STOPWORDS_UK = frozenset({
    "і", "й", "та", "а", "але", "або", "що", "як", "це", "цей", "ця",
    "в", "у", "на", "до", "від", "з", "зі", "із", "по", "за", "про",
    "не", "ні", "ж", "же", "бо", "тож", "так", "теж", "також",
    "the", "a", "an", "of", "to", "in", "and", "or", "with", "for",
})

# Characters treated as token separators when building the keyword set.
_TOKEN_RE = re.compile(r"[\wа-щА-ЩьюяЬЮЯіІїЇєЄґҐ'ʼ’]+", re.UNICODE)


def _tokenize(text: str) -> set[str]:
    """Return a set of lowercase tokens from ``text``, minus stopwords."""
    tokens = {t.lower() for t in _TOKEN_RE.findall(text)}
    return tokens - _STOPWORDS_UK


def _topic_keywords(directive_text: str) -> set[str]:
    """Extract content keywords from a directive's natural-language text.

    Filters out very short tokens (<3 chars), pure numbers, and
    stopwords. The remaining set is small but highly specific to the
    topic, which is what we want for a cheap "did the writer mention
    this?" check.
    """
    tokens = _tokenize(directive_text)
    return {t for t in tokens if len(t) >= 3 and not t.isdigit()}


def check_directive_coverage(
    directives: list[Directive], response: str,
) -> list[Directive]:
    """Mark each directive as covered or not, based on keyword overlap.

    Rules per kind:

    * ``skeleton_para``: we require at least 40% of the topic keywords
      to appear somewhere in the response. The skeleton's topic blobs
      are dense and specific (e.g. "Dialogue: Arrival at a Kyiv
      language school. Nominative, Accusative, Locative, Vocative").
      40% is permissive enough to tolerate paraphrasing but tight
      enough to flag a paragraph that skipped the assigned topic.

    * ``inject_activity``: exact-substring match on the declared
      activity name or ID in the response (the writer is instructed
      to leave the marker in place).

    * ``checklist`` / ``must``: 40% keyword overlap, same logic as
      skeleton_para.

    The returned list is the same objects, mutated in place for
    convenience — we're building a report, not a pure pipeline.
    """
    if not response:
        for d in directives:
            d.covered = False
            d.coverage_note = "empty response"
        return directives

    response_tokens = _tokenize(response)

    for d in directives:
        if d.kind == "inject_activity":
            # The activity name/id from the marker should survive verbatim
            # in the written content. Strip commas to tolerate minor
            # formatting drift ("fill-in, Case Drill, 8 items" is the
            # marker; we look for "fill-in" OR "Case Drill").
            parts = [p.strip() for p in d.text.split(",") if p.strip()]
            hit = any(p.lower() in response.lower() for p in parts)
            d.covered = hit
            d.coverage_note = (
                "activity marker preserved" if hit else "marker missing"
            )
            continue

        topic = _topic_keywords(d.text)
        if not topic:
            d.covered = True
            d.coverage_note = "no keywords to check"
            continue

        hits = topic & response_tokens
        ratio = len(hits) / len(topic)
        d.covered = ratio >= 0.4
        d.coverage_note = (
            f"{len(hits)}/{len(topic)} keywords ({ratio:.0%})"
        )

    return directives


# -----------------------------------------------------------------------------
# Top-level report builder
# -----------------------------------------------------------------------------

@dataclass
class SessionReport:
    session_path: str
    phase: str
    prompt_chars: int
    response_chars: int
    prompt_words: int
    response_words: int
    sections: list[dict[str, Any]] = field(default_factory=list)
    large_sections: list[str] = field(default_factory=list)  # > 40% share
    directives_total: int = 0
    directives_covered: int = 0
    directives_missed: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_path": self.session_path,
            "phase": self.phase,
            "prompt_chars": self.prompt_chars,
            "response_chars": self.response_chars,
            "prompt_words": self.prompt_words,
            "response_words": self.response_words,
            "sections": self.sections,
            "large_sections": self.large_sections,
            "directives_total": self.directives_total,
            "directives_covered": self.directives_covered,
            "directives_missed": self.directives_missed,
        }


# Threshold above which a prompt section is flagged as "possibly
# drowning out everything else". Matches issue #1174 spec.
_LARGE_SECTION_THRESHOLD = 0.40


def build_report(
    prompt: str, response: str, *, phase: str, session_path: str | Path,
) -> SessionReport:
    """Build a ``SessionReport`` from a parsed prompt+response pair.

    Safe against empty inputs — all analysis functions tolerate
    emptiness and the returned report will just have zero counts.
    """
    sections = analyze_prompt_sections(prompt)
    large = [
        s.name for s in sections if s.fraction > _LARGE_SECTION_THRESHOLD
    ]

    directives = extract_directives(prompt)
    directives = check_directive_coverage(directives, response)

    covered_count = sum(1 for d in directives if d.covered)
    missed = [d.to_dict() for d in directives if not d.covered]

    return SessionReport(
        session_path=str(session_path),
        phase=phase,
        prompt_chars=len(prompt),
        response_chars=len(response),
        prompt_words=len(prompt.split()),
        response_words=len(response.split()),
        sections=[s.to_dict() for s in sections],
        large_sections=large,
        directives_total=len(directives),
        directives_covered=covered_count,
        directives_missed=missed,
    )


def write_report_yaml(report: SessionReport, out_path: Path) -> None:
    """Write a report as YAML.

    Uses PyYAML (already a project dependency via batch_gemini_config,
    activity_schema, etc.) for correctness — an earlier hand-rolled
    emitter had subtle indentation bugs with lists-of-dicts that broke
    round-tripping. Going through PyYAML eliminates the class of bug.
    """
    import yaml
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            report.to_dict(),
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def _dict_to_yaml(obj: Any) -> str:
    """Thin wrapper kept for backwards-compat with existing callers/tests.

    Delegates to PyYAML. See ``write_report_yaml`` for rationale.
    """
    import yaml
    return yaml.safe_dump(
        obj, allow_unicode=True, sort_keys=False, default_flow_style=False,
    ).rstrip("\n")
