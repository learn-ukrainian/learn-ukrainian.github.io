"""
Check for valid content review files across all tiers.

Four review tiers with different standards:
  Tier 1 (Beginner): A1, A2 — v5/v6 review phase + tier-1-beginner
  Tier 2 (Core):     B1, B2, B2-PRO — v5/v6 review phase + tier-2-core
  Tier 3 (Seminar):  HIST, ISTORIO, BIO, LIT, OES, RUTH — v5/v6 review phase + tier-3-seminar
  Tier 4 (Advanced): C1, C1-PRO, C2 — v5/v6 review phase + tier-4-advanced

Detection heuristics:
  - Missing review file
  - Too short for tier
  - Missing required headers for tier
  - Unreplaced template placeholders
  - All-perfect scores without cited evidence
  - Empty "Issues Found" section
  - No Ukrainian text citations
  - Fabricated citations (quoted text not found in source .md)
"""

import contextlib
import re
import sys
from pathlib import Path

import yaml

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from audit.config import get_naturalness_min_score
from common.thresholds import REVIEW_PASS_FLOOR, STYLE_REVIEW_DIMENSION_FLOOR
from slug_utils import review_path as _review_path
from slug_utils import to_bare_slug

# --- Tier Configuration ---

TIER_3_TRACKS = {'bio', 'hist', 'istorio', 'lit', 'oes', 'ruth'}

# Regex patterns for required review sections.
# Accept natural variations: numbered prefixes (## 1. ...), synonyms, modifiers.
# Examples that must match:
#   "## Scores Breakdown", "## 2. Detailed Assessment", "## Evaluation"
#   "## Issues Found", "## 3. "Brutal" Critique", "## Problems"
#   "## Verification Summary", "## 1. Executive Summary", "## Summary"
#   "## Recommendation", "## 4. Final Recommendation", "## Verdict"
_NUM = r'(\d+\.\s*)?'  # optional numbered prefix: "3. "
_HEADER_SCORES = (
    rf'## {_NUM}(Scores( Breakdown)?|Detailed Assessment|Assessment|Evaluation)',
    'Scores/Assessment',
)
_HEADER_ISSUES = (
    rf'## {_NUM}("?Brutal"?\s+)?((Critical )?Issues( Found)?|Critique|Problems|Concerns)',
    'Issues/Critique',
)
_HEADER_VERIFICATION = (
    rf'## {_NUM}((Executive |Verification )?Summary|Verification)',
    'Summary/Verification',
)
_HEADER_RECOMMENDATION = (
    rf'## {_NUM}(Final )?(Recommendation|Verdict|Conclusion)',
    'Recommendation/Verdict',
)

TIER_CONFIG = {
    1: {
        'name': 'Beginner',
        'levels': {'A1', 'A2'},
        'tracks': set(),
        'review_cmd': 'the matching v5/v6 review phase (tier-1-beginner)',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-1-beginner.md',
        'min_chars': 400,
        'min_dimensions': 7,
        'required_headers': [
            _HEADER_SCORES,
            _HEADER_ISSUES,
            _HEADER_RECOMMENDATION,
        ],
        'require_ukr_citations': False,  # A1/A2 modules are mixed-language
    },
    2: {
        'name': 'Core',
        'levels': {'B1', 'B2'},
        'tracks': {'b2-pro'},
        'review_cmd': 'the matching v5/v6 review phase',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-2-core.md',
        'min_chars': 800,
        'min_dimensions': 8,
        'required_headers': [
            _HEADER_SCORES,
            _HEADER_ISSUES,
            _HEADER_VERIFICATION,
            _HEADER_RECOMMENDATION,
        ],
        'require_ukr_citations': True,
    },
    3: {
        'name': 'Seminar',
        'levels': set(),
        'tracks': TIER_3_TRACKS,
        'review_cmd': 'the matching v5/v6 review phase',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-3-seminar.md',
        'min_chars': 1500,
        'min_dimensions': 10,
        'required_headers': [
            _HEADER_SCORES,
            _HEADER_ISSUES,
            _HEADER_VERIFICATION,
            _HEADER_RECOMMENDATION,
        ],
        'require_ukr_citations': True,
    },
    4: {
        'name': 'Advanced',
        'levels': {'C1', 'C2'},
        'tracks': {'c1-pro', 'c2-pro'},
        'review_cmd': 'the matching v5/v6 review phase',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-4-advanced.md',
        'min_chars': 800,
        'min_dimensions': 8,
        'required_headers': [
            _HEADER_SCORES,
            _HEADER_ISSUES,
            _HEADER_VERIFICATION,
            _HEADER_RECOMMENDATION,
        ],
        'require_ukr_citations': True,
    },
}


def _detect_tier(file_path: str, level_code: str) -> int | None:
    """Detect which review tier this module belongs to. Returns tier number or None."""
    path_parts = [p.lower() for p in Path(file_path).parts]

    # Check track-based tiers first (more specific)
    for tier_num, cfg in TIER_CONFIG.items():
        for track in cfg['tracks']:
            if track in path_parts:
                return tier_num

    # Then check level-based tiers
    level_upper = level_code.upper() if level_code else ''
    for tier_num, cfg in TIER_CONFIG.items():
        if level_upper in cfg['levels']:
            # Exclude levels that are actually seminar tracks
            # e.g., C1 level but bio track → tier 3, not tier 4
            if tier_num == 4 and any(t in path_parts for t in TIER_3_TRACKS):
                continue
            return tier_num

    return None


def _build_fix_prompt(tier_num: int) -> str:
    """Build tier-specific actionable fix prompt for the LLM."""
    cfg = TIER_CONFIG[tier_num]
    cmd = cfg['review_cmd']
    tier_ref = cfg['tier_ref']

    base = (
        f"REDO: DELETE the existing review file and regenerate from scratch. "
        f"Run {cmd} using {tier_ref}. Do NOT patch the existing review — start fresh. "
    )

    if tier_num == 1:
        return base + (
            "You MUST: (1) read every line of the .md and activities .yaml, "
            "(2) check every English explanation is B1-readable and encouraging, "
            "(3) verify every Ukrainian sentence and stress mark, "
            "(4) apply the 'Would I Continue?' test from the tier-1 guide, "
            "(5) score each dimension honestly and list at least 1 real issue."
        )
    elif tier_num == 2:
        return base + (
            "You MUST: (1) read every line of the .md and activities .yaml, "
            "(2) cite specific Ukrainian sentences with issues (quote them with «»), "
            "(3) apply the 'Did I Learn?' test from the tier-2 guide, "
            "(4) score each dimension honestly — justify any 10/10 with evidence, "
            "(5) list at least 1 real issue (no module is perfect)."
        )
    elif tier_num == 3:
        return base + (
            "You MUST: (1) read every line of the .md and activities .yaml, "
            "(2) cite specific Ukrainian sentences with issues (quote them with «»), "
            "(3) apply the 'Would I Stay?' test from the tier-3 seminar guide, "
            "(4) score each of 12 dimensions honestly — if giving 10/10, "
            "justify with a specific quote from the content, "
            "(5) list at least 1 real issue (no module is perfect), "
            "(6) check decolonization perspective and primary sources."
        )
    else:  # tier 4
        return base + (
            "You MUST: (1) read every line of the .md and activities .yaml, "
            "(2) cite specific Ukrainian sentences with issues (quote them with «»), "
            "(3) apply the 'Did This Stretch Me?' test from the tier-4 guide, "
            "(4) verify linguistic analysis is sophisticated (not B1/B2 level), "
            "(5) score each dimension honestly and list at least 1 real issue."
        )


def _count_perfect_scores(content: str) -> tuple[int, int]:
    """Count how many dimension scores are 10/10 vs total scored dimensions."""
    score_pattern = re.findall(r'\|\s*\w[^|]*\|\s*(\d+(?:\.\d+)?)/10\s*\|', content)
    total = len(score_pattern)
    perfect = sum(1 for s in score_pattern if float(s) == 10.0)
    return perfect, total


def _extract_ukrainian_citations(content: str) -> list[str]:
    """Extract quoted Ukrainian text from the review.

    IMPORTANT: Match ALL quote pairs first, then filter by length.
    Using {10,} inside the regex causes it to skip short matches like "scary",
    making the closing quote become the opening of a huge cross-line match.

    Deduplicates citations and strips markdown formatting before returning.
    """
    raw_citations = []
    min_len = 10
    # 「...」 CJK corner brackets (preferred — no collision with Ukrainian «» quotes)
    for match in re.findall(r'「([^」]*)」', content):
        if len(match) >= min_len and re.search(r'[а-яіїєґ]', match):
            raw_citations.append(match)
    # «...» angular quotes (legacy — kept for backward compatibility with older reviews)
    for match in re.findall(r'«([^»]*)»', content):
        if len(match) >= min_len and re.search(r'[а-яіїєґ]', match):
            raw_citations.append(match)
    # "..." straight quotes containing Cyrillic
    for match in re.findall(r'"([^"]*)"', content):
        if len(match) >= min_len and re.search(r'[а-яіїєґ]', match):
            raw_citations.append(match)
    # `...` inline code with Ukrainian (skip multi-line matches from code fences)
    for match in re.findall(r'`([^`]*)`', content):
        if len(match) >= min_len and '\n' not in match and re.search(r'[а-яіїєґ]', match):
            raw_citations.append(match)

    # Strip markdown bold/italic markers before dedup and verification
    cleaned = []
    seen = set()
    for c in raw_citations:
        stripped = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', c)
        norm_key = re.sub(r'\s+', ' ', stripped.lower().strip())
        if norm_key not in seen:
            seen.add(norm_key)
            cleaned.append(stripped)
    return cleaned


def _verify_citations_against_source(citations: list[str], source_path: Path) -> tuple[int, int]:
    """
    Check how many cited Ukrainian sentences actually exist in the source module files.
    Searches: content .md, activities YAML, and vocabulary YAML.
    Returns (verified_count, total_count).
    """
    if not source_path.exists() or not citations:
        return 0, len(citations)

    # Build combined source text from all module files
    source_parts = []
    try:
        source_parts.append(source_path.read_text(encoding='utf-8').lower())
    except Exception:
        return 0, len(citations)

    # Also search activities and vocabulary YAML
    base_dir = source_path.parent
    slug = source_path.stem
    for subdir in ('activities', 'vocabulary'):
        yaml_path = base_dir / subdir / f"{slug}.yaml"
        if yaml_path.exists():
            with contextlib.suppress(Exception):
                source_parts.append(yaml_path.read_text(encoding='utf-8').lower())

    source_text = '\n'.join(source_parts)
    # Strip markdown formatting from source too (bold, italic, links)
    source_text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', source_text)

    verified = 0
    for citation in citations:
        # Normalize: lowercase, collapse whitespace
        normalized = re.sub(r'\s+', ' ', citation.lower().strip())
        # Primary check: first 30 chars (handles exact copies)
        check_str = normalized[:min(30, len(normalized))]
        if check_str in source_text:
            verified += 1
            continue
        # Fallback: check sliding windows of 20 chars through the citation
        # This catches cases where the start is slightly paraphrased but
        # the core text is verbatim (e.g., added article or reordered intro)
        found = False
        if len(normalized) >= 20:
            for start in range(0, min(len(normalized) - 19, 40), 5):
                window = normalized[start:start + 20]
                if window in source_text:
                    found = True
                    break
        if found:
            verified += 1

    return verified, len(citations)


def _find_review_file(file_path: str, module_slug: str) -> tuple[Path | None, Path]:
    """Locate the review file (canonical, content-review, or legacy path).

    Returns (review_file_path_or_None, canonical_path).
    """
    module_path = Path(file_path)
    base_dir = module_path.parent
    canonical = _review_path(base_dir, module_slug)

    bare = to_bare_slug(module_slug)
    if canonical.exists():
        return canonical, canonical

    content_review = base_dir / "audit" / f"{bare}-content-review.md"
    if content_review.exists():
        return content_review, canonical

    legacy = base_dir / "audit" / f"{bare}-review.md"
    if legacy.exists():
        return legacy, canonical

    return None, canonical


def _check_content_review_format(content: str, fix_prompt: str) -> list[dict]:
    """Validate content-review specific format (Grade A/B/C/F)."""
    violations = []
    grade_match = re.search(r'\*\*Verdict:\*\*\s*([ABCF])\b', content[:2000])
    if grade_match and grade_match.group(1) == 'F':
        violations.append({
            'type': 'REVIEW_VERDICT_FAIL',
            'severity': 'critical',
            'message': (
                "Content review grades this module F — critical issues found. "
                "Rebuild the module to fix identified problems."
            )
        })
    cr_required = [
        (r'## (Issues Found|CRITICAL|HIGH)', 'Issues Found'),
        (r'## Grade Justification', 'Grade Justification'),
    ]
    missing = [name for pattern, name in cr_required if not re.search(pattern, content)]
    if missing:
        violations.append({
            'type': 'FAKE_REVIEW_STRUCTURE',
            'severity': 'critical',
            'message': f"Content review missing required sections: {', '.join(missing)}. Rerun /content-review."
        })
    return violations


def _check_pipeline_review_format(content: str, cfg: dict, fix_prompt: str) -> list[dict]:
    """Validate standard pipeline review format (PASS/FAIL + required headers)."""
    violations = []
    # Review verdict is NO LONGER an audit gate (#980 Phase 1)
    # Audit = deterministic checks (code). Review = LLM quality (score).
    # They are separate systems. The review score blocks via the dashboard
    # (shippable = audit PASS + review >= 8.0), not via the audit gates.
    # This prevents the circular dependency where review FAIL → audit FAIL
    # → fix loop can't fix → module stuck forever.
    missing = [name for pattern, name in cfg['required_headers'] if not re.search(pattern, content)]
    if missing:
        violations.append({
            'type': 'FAKE_REVIEW_STRUCTURE',
            'severity': 'critical',
            'message': f"Review missing required sections: {', '.join(missing)}. {fix_prompt}"
        })
    return violations


def _check_template_placeholders(content: str, fix_prompt: str) -> list[dict]:
    """Check for unreplaced template placeholders."""
    placeholders = [
        (r'\{slug\}', '{slug}'),
        (r'\{level\}', '{level}'),
        (r'\{num\}', '{num}'),
        (r'\{X\.X\}', '{X.X}'),
        (r'\{what you found\}', '{what you found}'),
    ]
    found = [name for pattern, name in placeholders if re.search(pattern, content)]
    if found:
        return [{
            'type': 'FAKE_REVIEW_TEMPLATE',
            'severity': 'critical',
            'message': (
                f"Review has unreplaced placeholders: {', '.join(found)}. "
                f"The template was not filled in. {fix_prompt}"
            )
        }]
    return []


def _check_citation_verification(citations: list[str], source_path: Path, fix_prompt: str) -> list[dict]:
    """Verify cited Ukrainian text actually exists in the source module."""
    violations = []
    if len(citations) < 2:
        return violations

    verified, total_cit = _verify_citations_against_source(citations, source_path)
    unverified = total_cit - verified

    if total_cit >= 3 and verified == 0:
        violations.append({
            'type': 'FABRICATED_CITATIONS',
            'severity': 'critical',
            'message': (
                f"Review quotes {total_cit} Ukrainian sentences but NONE were found "
                f"in the source module. The reviewer likely fabricated citations "
                f"instead of reading the actual content. {fix_prompt}"
            )
        })
    elif total_cit >= 3 and (verified / total_cit) < 0.5:
        is_conclusive = total_cit >= 5 and unverified >= 5
        severity = 'critical' if is_conclusive else 'warning'
        violations.append({
            'type': 'UNVERIFIED_CITATIONS',
            'severity': severity,
            'message': (
                f"Only {verified}/{total_cit} Ukrainian citations in the review "
                f"were found in the source module. The reviewer may be quoting "
                f"from memory rather than from the actual content. {fix_prompt}"
            )
        })

    return violations


def _check_gaming_language(content: str, fix_prompt: str) -> list[dict]:
    """Detect meta-language that reveals intent to pass audit."""
    gaming_phrases = [
        r'ensur(e|es|ing)\s+(a\s+)?high\s+(overall\s+)?score',
        r'clean\s+audit',
        r'designed?\s+to\s+pass',
        r'ensuring?\s+.*pass(es|ing)?',
        r'reflect(s|ing)?\s+the\s+fix(es)?',
        r'accurately\s+citing',  # "accurately reflect" removed — legitimate in fact-checking (#969)
        r'this\s+fresh\s+review\s+will',
        r'will\s+ensure\s+.*compli(ance|ant)',
        r'crafted?\s+to\s+(meet|satisfy|ensure)',
        r'tailored?\s+to\s+(pass|satisfy)',
    ]
    found_gaming = []
    content_lower = content.lower()
    for pattern in gaming_phrases:
        match = re.search(pattern, content_lower)
        if match:
            found_gaming.append(match.group(0))
    if found_gaming:
        return [{
            'type': 'GAMING_LANGUAGE_DETECTED',
            'severity': 'critical',
            'message': (
                f"Review contains audit-gaming language: "
                f"{', '.join(repr(g) for g in found_gaming[:3])}. "
                f"Reviews must HONESTLY evaluate content, not be written to "
                f"'ensure a high score'. {fix_prompt}"
            )
        }]
    return []


def _check_score_credibility(content: str, cfg: dict, issue_text: str | None,
                              issues_match, fix_prompt: str) -> list[dict]:
    """Check for suspiciously uniform high scores and praise-only citations."""
    violations = []
    _perfect, total = _count_perfect_scores(content)

    if total < cfg['min_dimensions']:
        return violations

    scores = [float(s) for s in re.findall(
        r'\|\s*\w[^|]*\|\s*(\d+(?:\.\d+)?)/10\s*\|', content
    )]
    if not scores:
        return violations

    avg_score = sum(scores) / len(scores)
    min_score = min(scores)
    has_real_issues = (issues_match and issue_text
                      and len(issue_text) >= 50
                      and not re.match(
                          r'^(None|No issues|N/A|—|-)\s*$',
                          issue_text, re.IGNORECASE))
    if min_score >= 9.0 and not has_real_issues:
        violations.append({
            'type': 'SUSPICIOUSLY_HIGH_SCORES',
            'severity': 'warning',
            'message': (
                f"All {len(scores)} dimensions scored ≥ 9/10 "
                f"(avg {avg_score:.1f}) but no substantive issues found. "
                f"No module is perfect — a credible review identifies at least "
                f"1 concrete improvement. {fix_prompt}"
            )
        })

    return violations


def _check_praise_only_citations(content: str, citations: list[str], fix_prompt: str) -> list[dict]:
    """Check if all citations are used for praise, none for criticism."""
    if len(citations) < 3:
        return []

    negative_markers = re.compile(
        r'(issue|problem|incorrect|помилк|неприродн|awkward|wrong|error|'
        r'should\s+be|could\s+be\s+(improved|better)|missing|lacks?|weak|'
        r'unclear|confusing|inaccurat|fix|❌|⚠️)', re.IGNORECASE
    )
    for cit in citations:
        cit_escaped = re.escape(cit[:30])
        ctx_match = re.search(
            rf'.{{0,100}}{cit_escaped}.{{0,100}}',
            content, re.DOTALL
        )
        if ctx_match and negative_markers.search(ctx_match.group(0)):
            return []  # Found at least one critical citation

    return [{
        'type': 'PRAISE_ONLY_CITATIONS',
        'severity': 'warning',
        'message': (
            f"Review cites {len(citations)} Ukrainian passages but ALL are used "
            f"positively — none highlight problems. A credible review uses citations "
            f"to show both strengths AND weaknesses. {fix_prompt}"
        )
    }]


_STYLE_REVIEW_DIMENSION_FLOOR = STYLE_REVIEW_DIMENSION_FLOOR
_V6_REVIEW_MIN_SCORE = REVIEW_PASS_FLOOR
_STYLE_REVIEW_DIMENSIONS = {
    'pragmatic_authenticity': 'Pragmatic authenticity',
    'stylistic_consistency': 'Stylistic consistency',
    'culture_and_register': 'Culture + register',
    'naturalness': 'Naturalness',
}
_VERSIONED_ROUND_RE = re.compile(r'-r(\d+)(?=\.[^.]+$)')


def _normalize_style_review_key(value: str) -> str:
    """Normalize style-review dimension identifiers."""
    normalized = value.strip().lower().replace('&', 'and').replace('+', 'and')
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized).strip('_')
    aliases = {
        'culture_register': 'culture_and_register',
    }
    return aliases.get(normalized, normalized)


def _versioned_round_number(path: Path) -> int:
    """Extract the numeric review round from a versioned artifact filename."""
    match = _VERSIONED_ROUND_RE.search(path.name)
    return int(match.group(1)) if match else -1


def _load_latest_yaml(orch_dir: Path, pattern: str) -> tuple[Path | None, dict | None, str | None]:
    """Load the latest matching YAML file from orchestration dir."""
    matches = list(orch_dir.glob(pattern))
    if not matches:
        return None, None, None

    latest = max(matches, key=lambda path: (_versioned_round_number(path), path.name))
    try:
        data = yaml.safe_load(latest.read_text(encoding='utf-8'))
    except Exception as exc:
        return latest, None, str(exc)
    if not isinstance(data, dict):
        return latest, None, 'YAML root is not a mapping'
    return latest, data, None


def check_v6_review_validity(file_path: str, level_code: str, module_slug: str) -> list[dict]:
    """Validate the structured linguistic + style review gate for v6 modules."""
    module_dir = Path(file_path).parent
    orch_dir = module_dir / 'orchestration' / module_slug
    review_dir = module_dir / 'review'
    style_threshold = get_naturalness_min_score(level_code)
    violations = []

    review_path = review_dir / f'{module_slug}-review-aggregate.yaml'
    review_data = None
    review_error = None
    if review_path.exists():
        try:
            review_data = yaml.safe_load(review_path.read_text(encoding='utf-8'))
        except Exception as exc:
            review_error = str(exc)
    else:
        versioned = list(review_dir.glob(f'{module_slug}-review-aggregate-r*.yaml'))
        if versioned:
            review_path = max(versioned, key=lambda path: (_versioned_round_number(path), path.name))
            try:
                review_data = yaml.safe_load(review_path.read_text(encoding='utf-8'))
            except Exception as exc:
                review_error = str(exc)
        else:
            review_path, review_data, review_error = _load_latest_yaml(orch_dir, 'review-structured-r*.yaml')

    if review_path is None:
        return [{
            'type': 'MISSING_STRUCTURED_REVIEW',
            'severity': 'critical',
            'message': 'No review aggregate YAML found',
        }]
    if review_error is not None:
        return [{
            'type': 'STRUCTURED_REVIEW_PARSE_ERROR',
            'severity': 'critical',
            'message': f'Failed to parse {review_path.name}: {review_error}',
        }]

    verdict_score_raw = None
    if isinstance(review_data, dict):
        verdict_score_raw = review_data.get('verdict_score', review_data.get('overall_score'))
    if verdict_score_raw is None:
        scores = [d.get('score', 0) for d in review_data.get('scores', []) if isinstance(d, dict)]
        if scores:
            verdict_score_raw = min(scores)
    if verdict_score_raw is None:
        violations.append({
            'type': 'STRUCTURED_REVIEW_NO_SCORES',
            'severity': 'critical',
            'message': f'No scores found in {review_path.name}',
        })
    else:
        try:
            verdict_score = float(verdict_score_raw)
        except (TypeError, ValueError):
            verdict_score = 0.0
        if verdict_score < _V6_REVIEW_MIN_SCORE:
            violations.append({
                'type': 'STRUCTURED_REVIEW_BELOW_THRESHOLD',
                'severity': 'critical',
                'message': (
                    f'Latest review {review_path.name} score is {verdict_score:.1f} < {_V6_REVIEW_MIN_SCORE:.1f}'
                ),
            })

    style_path, style_data, style_error = _load_latest_yaml(orch_dir, 'review-structured-style-r*.yaml')
    if style_path is None:
        violations.append({
            'type': 'MISSING_STYLE_REVIEW',
            'severity': 'critical',
            'message': 'No review-structured-style-r*.yaml found in orchestration dir',
        })
        return violations
    if style_error is not None:
        violations.append({
            'type': 'STYLE_REVIEW_PARSE_ERROR',
            'severity': 'critical',
            'message': f'Failed to parse {style_path.name}: {style_error}',
        })
        return violations

    style_scores = {}
    for item in style_data.get('scores', []):
        if not isinstance(item, dict):
            continue
        key = _normalize_style_review_key(str(item.get('key') or item.get('label') or item.get('name') or ''))
        if key not in _STYLE_REVIEW_DIMENSIONS:
            continue
        try:
            style_scores[key] = float(item.get('score'))
        except (TypeError, ValueError):
            violations.append({
                'type': 'STYLE_REVIEW_PARSE_ERROR',
                'severity': 'critical',
                'message': f'Invalid style-review score in {style_path.name} for {key}',
            })
            return violations

    missing_dimensions = [
        key for key in _STYLE_REVIEW_DIMENSIONS
        if key not in style_scores
    ]
    if missing_dimensions:
        violations.append({
            'type': 'STYLE_REVIEW_MISSING_DIMENSIONS',
            'severity': 'critical',
            'message': (
                f'{style_path.name} missing required dimensions: '
                + ', '.join(missing_dimensions)
            ),
        })
        return violations

    try:
        overall_score = float(style_data.get('overall_score'))
    except (TypeError, ValueError):
        overall_score = sum(style_scores.values()) / len(style_scores)

    if overall_score < style_threshold:
        violations.append({
            'type': 'STYLE_REVIEW_BELOW_THRESHOLD',
            'severity': 'critical',
            'message': (
                f'Latest style review {style_path.name} score is {overall_score:.1f} < {style_threshold:.1f}'
            ),
        })

    low_dimensions = [
        f'{_STYLE_REVIEW_DIMENSIONS[key]}={score:.1f}'
        for key, score in style_scores.items()
        if score < _STYLE_REVIEW_DIMENSION_FLOOR
    ]
    if low_dimensions:
        violations.append({
            'type': 'STYLE_REVIEW_DIMENSION_FLOOR',
            'severity': 'critical',
            'message': (
                f'Latest style review {style_path.name} has dimension(s) below '
                f'{_STYLE_REVIEW_DIMENSION_FLOOR:.1f}: ' + ', '.join(low_dimensions)
            ),
        })

    return violations


def check_review_validity(file_path: str, level_code: str, module_slug: str) -> list[dict]:
    """
    Validate the existence and quality of the review file.

    Applies tier-appropriate checks and returns violations with
    actionable REDO prompts that tell the LLM to regenerate from scratch.
    Also verifies that cited Ukrainian text actually exists in the source module.
    """
    violations = []

    tier_num = _detect_tier(file_path, level_code)
    if tier_num is None:
        return []

    cfg = TIER_CONFIG[tier_num]
    fix_prompt = _build_fix_prompt(tier_num)

    # 1. Find review file
    review_file, canonical = _find_review_file(file_path, module_slug)

    if review_file is None:
        try:
            rel_path = canonical.relative_to(Path(file_path).parent.parent.parent)
        except ValueError:
            rel_path = canonical
        return [{
            'type': 'MISSING_REVIEW',
            'severity': 'critical',
            'message': f"No Tier {tier_num} ({cfg['name']}) review file at {rel_path}. {fix_prompt}"
        }]

    is_content_review = review_file.name.endswith('-content-review.md')

    try:
        content = review_file.read_text(encoding='utf-8')

        # 2. Length Check
        if len(content) < cfg['min_chars']:
            return [{
                'type': 'FAKE_REVIEW_TOO_SHORT',
                'severity': 'critical',
                'message': (
                    f"Review is only {len(content)} chars — Tier {tier_num} ({cfg['name']}) "
                    f"requires {cfg['min_chars']}+ chars. {fix_prompt}"
                )
            }]

        # 3. Format-specific checks (content-review vs pipeline review)
        if is_content_review:
            violations.extend(_check_content_review_format(content, fix_prompt))
        else:
            violations.extend(_check_pipeline_review_format(content, cfg, fix_prompt))

        # 4. Template placeholders
        violations.extend(_check_template_placeholders(content, fix_prompt))

        # 5-8. Citation-based checks
        citations = _extract_ukrainian_citations(content)
        has_citations = len(citations) >= 2

        perfect, total = _count_perfect_scores(content)
        if total >= cfg['min_dimensions'] and perfect == total and not has_citations:
            violations.append({
                'type': 'RUBBER_STAMP_REVIEW',
                'severity': 'critical',
                'message': (
                    f"Review scores {perfect}/{total} dimensions as 10/10 but cites ZERO "
                    f"Ukrainian sentences as evidence. A perfect score requires justification "
                    f"— quote the specific text that earns each 10. {fix_prompt}"
                )
            })

        # 6. Empty issues section
        issues_match = re.search(
            r'## (?:\d+\.\s*)?(?:"?Brutal"?\s+)?(?:(?:Critical )?Issues(?: Found)?|Critique|Problems|Concerns)[^\n]*\n(.*?)(?=\n## |\Z)',
            content, re.DOTALL
        )
        issue_text = issues_match.group(1).strip() if issues_match else None
        if issues_match and (not issue_text or len(issue_text) < 30
                or re.match(r'^(None|No issues|N/A|—|-)\s*$', issue_text or '', re.IGNORECASE)):
            violations.append({
                'type': 'EMPTY_ISSUES_SECTION',
                'severity': 'warning',
                'message': (
                    "Review claims zero issues — no module is perfect. "
                    "At minimum, identify 1 sentence that could be more natural, "
                    "1 activity that could be improved, or 1 vocabulary choice "
                    f"worth discussing. {fix_prompt}"
                )
            })

        # 7. No Ukrainian citations
        if cfg['require_ukr_citations'] and not has_citations and not any(v['type'] == 'RUBBER_STAMP_REVIEW' for v in violations):
            violations.append({
                'type': 'NO_EVIDENCE_REVIEW',
                'severity': 'warning',
                'message': (
                    "Review contains no quoted Ukrainian text. A real review cites specific "
                    "sentences from the module (e.g., «Він пішов до хати» — wrong aspect). "
                    f"{fix_prompt}"
                )
            })

        # 8. Citation verification
        if cfg['require_ukr_citations']:
            violations.extend(_check_citation_verification(citations, Path(file_path), fix_prompt))

        # 9. Gaming language
        violations.extend(_check_gaming_language(content, fix_prompt))

        # 10. Score credibility
        violations.extend(_check_score_credibility(content, cfg, issue_text, issues_match, fix_prompt))

        # 11. Praise-only citations
        if has_citations:
            violations.extend(_check_praise_only_citations(content, citations, fix_prompt))

    except Exception as e:
        violations.append({
            'type': 'REVIEW_READ_ERROR',
            'severity': 'critical',
            'message': f"Could not read review file: {e}"
        })

    return violations
