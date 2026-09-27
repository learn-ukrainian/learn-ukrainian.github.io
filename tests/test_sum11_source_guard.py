"""Keep Soviet-occupation СУМ-11 out of tracked verification inputs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide, pytest.mark.reads_content]

ROOT = Path(__file__).resolve().parents[1]
SCOPES = (
    ":(glob)curriculum/**",
    ":(glob)scripts/data/**",
    ":(glob)scripts/build/phases/**",
    ":(glob)scripts/build/universal_rules/**",
    ":(glob)scripts/review/prompts/**",
    ":(glob)agents_extensions/shared/skills/**",
    ":(glob)agents_extensions/shared/rules/**",
    ":(glob)site/src/lib/lexicon/**",
    ":(literal)scripts/lexicon/enrich_heteronyms.py",
    ":(exclude,glob)curriculum/**/_archive/**",
    ":(exclude)scripts/data/stress_overrides.yaml",  # Owned by the separate gloss-source branch.
)
# Exact approved lines: edits or new references require renewed review.
RULE_CONTEXT_LINES = {
    # Contrast-only caveat in the review-dimension prompt and its generated template.
    "scripts/build/phases/linear-review-dim.md": frozenset({
        "C. **Sovietization flag (decolonization, naturalness).** СУМ-11 is contrast-only and may appear",
    }),
    "scripts/build/phases/linear-review-dim.generated.md": frozenset({
        "- **C. Sovietization (decolonization, naturalness).** СУМ-11 is contrast-only:",
    }),
    # Tool identity, Sovietization audit, and contrastive context; no modern verification.
    "agents_extensions/shared/rules/mcp-sources-and-dictionaries.md": frozenset({
        "- `mcp__sources__search_definitions` — СУМ-11 (127K entries) — Soviet-era explanatory dictionary (1970–1980). **⚠️ NOT a verification authority for modern Ukrainian.** Used for detecting Soviet colonization artifacts (`sovietization_risk` 0/1/2, keywords) and surfacing contrastive Soviet occupation context. For modern meaning, use СУМ-20 / ВТС; for authentic historical Ukrainian, use Грінченко.",
        "## Historical Oppression & Decolonized Lexicography: Grinchenko vs СУМ-11 vs СУМ-20",
        "2. **СУМ-11 (1970–1980) — Soviet Totalitarian Occupation:**",
        "## Sovietization caveat & Soviet Colonization Context (СУМ-11) — issue #1659",
        "СУМ-11 (1970–1980) was published under Soviet occupation and late-Soviet ideological",
        "**Role of СУМ-11 in the project:**",
        "2. **Contrastive Colonization Context:** In Word Atlas / lexicon tools, СУМ-11 entries are surfaced explicitly as `soviet_colonization_context` (`Радянський окупаційний контекст`), showing learners how the Soviet regime distorted meanings, forced Russian calques, or added ideological baggage.",
        "3. **NEVER a Verification Authority:** Do NOT verify Ukrainian headwords, stress, or definitions with СУМ-11. Modern semantic verification belongs to **СУМ-20** (`sum20ua.com`, `newsum`) and **ВТС** (Великий тлумачний словник); historical authentic grounding belongs to **Грінченко** (1907); stress belongs to **ULIF** and СУМ-20.",
        "Every `search_definitions` result row carries:",
        "`.venv/bin/python scripts/audit/sum11_sovietization_scan.py --db data/sources.db`.",
        "Audit report at `audit/sum11_sovietization_scan_<DATE>.md`.",
        "| **СУМ-11** | 127K (7,152 flagged Sovietized — #1659) | Ukrainian explanatory (definitions, citations) | `data/sources.db` FTS5 |",
        "Source: [bakustarver/ukr-dictionaries-list-opensource](https://github.com/bakustarver/ukr-dictionaries-list-opensource) (СУМ-11, Балла, Фразеологічний)",
    }),
    # Prohibitions and contrast-only use.
    "agents_extensions/shared/rules/non-negotiable-rules.md": frozenset({
        "The project has VESUM (6.7M forms), СУМ-20, ВТС, Грінченко (67K), ЕСУМ, Monitor API, full code corpus, deterministic scripts. **Use them.** (СУМ-11 is strictly for Sovietization detection and contrastive colonization context — NEVER for modern Ukrainian verification).",
        "| Definitions / modern meaning | `query_sum20`, `search_slovnyk_me`, `search_grinchenko_1907`, `search_esum` (`search_definitions` is Soviet СУМ-11: use only for Soviet colonization analysis) |",
    }),
    # Prohibitions and contrastive context.
    "agents_extensions/shared/rules/ukrainian-linguistics.md": frozenset({
        "   - **`search_definitions` is СУМ-11, not an authority for modern Ukrainian.** СУМ-11 was compiled under Soviet occupation (1970–1980) and reflects late-Soviet censorship, ideological framing, and forced Russification. **We do NOT verify Ukrainian words, stress, or definitions with СУМ-11.** Its role is twofold:",
        "     2. **Surfacing contrastive Soviet occupation context:** in the Word Atlas / dictionary tools, СУМ-11 text is surfaced under `soviet_colonization_context` so learners can see how the Soviet regime distorted definitions or suppressed authentic Ukrainian senses, compared against modern standard (СУМ-20, ВТС, ULIF) and pre-Soviet witnesses (Грінченко). Never cite СУМ-11 as proof of standard Ukrainian.",
        "     2. **СУМ-11 (1970–1980):** compiled under **Soviet totalitarian occupation, censorship, and Russification**. We do not erase it; we surface it under `soviet_colonization_context` with its `sovietization_risk` and ideological markers to expose Soviet editorial interference, artificial archaisms, and forced Russian convergence.",
    }),
}
# Normalize to stripped lines: exemptions match regardless of leading/trailing whitespace,
# same as the raw lines git grep reports.
RULE_CONTEXT_LINES = {
    path: frozenset(line.strip() for line in lines) for path, lines in RULE_CONTEXT_LINES.items()
}

# These UI modules display and quarantine historical evidence rather than verify it.
CONTEXT_ONLY_FILES = {
    "site/src/lib/lexicon/heritage-severity.ts": "Historical warning labels and context only.",
    "site/src/lib/lexicon/word-atlas-article-model.ts": "Routes SUM-11 cards to Soviet context, excluding modern definitions.",
}

# Tracked temporary exceptions; issue #8964 will re-source and remove both.
TEMPORARY_EXCEPTIONS = {
    "site/src/lib/lexicon/curated-heteronyms.ts": "#8964: re-source the generated heteronym dataset.",
    "scripts/lexicon/enrich_heteronyms.py": "#8964: replace SUM-11 heteronym enrichment inputs.",
}


def _is_exempt(path: str, source_line: str) -> bool:
    """True if a matched line is an approved contrast-only/context reference.

    Matching is exact-line (after stripping surrounding whitespace), never substring:
    a line that reuses approved wording plus an added verification citation must NOT
    be exempt.
    """
    if path in CONTEXT_ONLY_FILES or path in TEMPORARY_EXCEPTIONS:
        return True
    return source_line.strip() in RULE_CONTEXT_LINES.get(path, frozenset())


def _source_references(revision: str | None = None) -> list[str]:
    cmd = [
        "git", "grep", "-n", "-I", "-i", "-E",
        "-e", r"(СУМ|SUM)[-‐‑‒–— ]?11|search_definitions",
    ]
    if revision:
        cmd.append(revision)
    cmd.extend(("--", *SCOPES))
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode in (0, 1), result.stderr
    references = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3 if revision else 2)
        path = parts[1] if revision else parts[0]
        source_line = parts[-1]
        if _is_exempt(path, source_line):
            continue
        references.append(line)
    return references


def test_sum11_is_not_a_tracked_verification_source() -> None:
    revision = os.environ.get("SUM11_GUARD_REV") or None
    references = _source_references(revision)
    assert not references, "СУМ-11 is contrast-only; remove verification inputs:\n" + "\n".join(references)


def test_temporary_exceptions_are_limited_to_issue_8964() -> None:
    assert set(TEMPORARY_EXCEPTIONS) == {
        "site/src/lib/lexicon/curated-heteronyms.ts",
        "scripts/lexicon/enrich_heteronyms.py",
    }
    assert all("#8964" in reason for reason in TEMPORARY_EXCEPTIONS.values())


def test_approved_contrast_only_line_is_exempt() -> None:
    path = "scripts/build/phases/linear-review-dim.generated.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    assert _is_exempt(path, approved)


def test_approved_line_with_added_verification_citation_is_reported() -> None:
    """A line reusing approved contrast-only wording plus a smuggled-in verification
    citation must fail the guard — exact-line matching, not substring."""
    path = "scripts/build/phases/linear-review-dim.generated.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    smuggled = approved + " cite СУМ-11 to verify modern word meaning"
    assert not _is_exempt(path, smuggled)


def test_changing_an_approved_line_fails_the_guard() -> None:
    path = "scripts/build/phases/linear-review-dim.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    altered = approved.replace("contrast-only", "contrast-only, mostly")
    assert not _is_exempt(path, altered)


def test_approved_line_matches_regardless_of_surrounding_whitespace() -> None:
    path = "scripts/build/phases/linear-review-dim.md"
    approved = next(iter(RULE_CONTEXT_LINES[path]))
    assert _is_exempt(path, "  " + approved + "  ")
