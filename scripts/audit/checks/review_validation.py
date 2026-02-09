"""
Check for valid content review files across all tiers.

Four review tiers with different standards:
  Tier 1 (Beginner): A1, A2 — /review-content-core-a + tier-1-beginner
  Tier 2 (Core):     B1, B2, B2-PRO — /review-content-v4 + tier-2-core
  Tier 3 (Seminar):  B2-HIST, C1-HIST, C1-BIO, LIT, OES, RUTH — /review-content-v4 + tier-3-seminar
  Tier 4 (Advanced): C1, C1-PRO, C2 — /review-content-v4 + tier-4-advanced

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

import re
from pathlib import Path


# --- Tier Configuration ---

TIER_3_TRACKS = {'c1-bio', 'b2-hist', 'c1-hist', 'lit', 'oes', 'ruth'}

TIER_CONFIG = {
    1: {
        'name': 'Beginner',
        'levels': {'A1', 'A2'},
        'tracks': set(),
        'review_cmd': '/review-content-core-a',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-1-beginner.md',
        'min_chars': 400,
        'min_dimensions': 5,
        'required_headers': [
            ('## Scores Breakdown', 'Scores Breakdown'),
            ('## Issues Found', 'Issues Found'),
            ('## Recommendation', 'Recommendation'),
        ],
        'require_ukr_citations': False,  # A1/A2 modules are mixed-language
    },
    2: {
        'name': 'Core',
        'levels': {'B1', 'B2'},
        'tracks': {'b2-pro'},
        'review_cmd': '/review-content-v4',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-2-core.md',
        'min_chars': 800,
        'min_dimensions': 8,
        'required_headers': [
            ('## Scores Breakdown', 'Scores Breakdown'),
            ('## Issues Found', 'Issues Found'),
            ('## Verification Summary', 'Verification Summary'),
            ('## Recommendation', 'Recommendation'),
        ],
        'require_ukr_citations': True,
    },
    3: {
        'name': 'Seminar',
        'levels': set(),
        'tracks': TIER_3_TRACKS,
        'review_cmd': '/review-content-v4',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-3-seminar.md',
        'min_chars': 1500,
        'min_dimensions': 10,
        'required_headers': [
            ('## Scores Breakdown', 'Scores Breakdown'),
            ('## Issues Found', 'Issues Found'),
            ('## Verification Summary', 'Verification Summary'),
            ('## Recommendation', 'Recommendation'),
        ],
        'require_ukr_citations': True,
    },
    4: {
        'name': 'Advanced',
        'levels': {'C1', 'C2'},
        'tracks': {'c1-pro', 'c2-pro'},
        'review_cmd': '/review-content-v4',
        'tier_ref': 'claude_extensions/commands/review-tiers/tier-4-advanced.md',
        'min_chars': 800,
        'min_dimensions': 8,
        'required_headers': [
            ('## Scores Breakdown', 'Scores Breakdown'),
            ('## Issues Found', 'Issues Found'),
            ('## Verification Summary', 'Verification Summary'),
            ('## Recommendation', 'Recommendation'),
        ],
        'require_ukr_citations': True,
    },
}


def _detect_tier(file_path: str, level_code: str) -> int | None:
    """Detect which review tier this module belongs to. Returns tier number or None."""
    path_lower = file_path.lower()

    # Check track-based tiers first (more specific)
    for tier_num, cfg in TIER_CONFIG.items():
        for track in cfg['tracks']:
            if track in path_lower:
                return tier_num

    # Then check level-based tiers
    level_upper = level_code.upper() if level_code else ''
    for tier_num, cfg in TIER_CONFIG.items():
        if level_upper in cfg['levels']:
            # Exclude levels that are actually seminar tracks
            # e.g., C1 level but c1-bio track → tier 3, not tier 4
            if tier_num == 4 and any(t in path_lower for t in TIER_3_TRACKS):
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
            "(3) verify every Ukrainian sentence + IPA transcription, "
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
    """Extract quoted Ukrainian text from the review."""
    citations = []
    # «...» angular quotes
    for match in re.findall(r'«([^»]{10,})»', content):
        if re.search(r'[а-яіїєґ]', match):
            citations.append(match)
    # "..." straight quotes containing Cyrillic
    for match in re.findall(r'"([^"]{10,})"', content):
        if re.search(r'[а-яіїєґ]', match):
            citations.append(match)
    # `...` inline code with Ukrainian
    for match in re.findall(r'`([^`]{10,})`', content):
        if re.search(r'[а-яіїєґ]', match):
            citations.append(match)
    return citations


def _verify_citations_against_source(citations: list[str], source_path: Path) -> tuple[int, int]:
    """
    Check how many cited Ukrainian sentences actually exist in the source .md file.
    Returns (verified_count, total_count).
    """
    if not source_path.exists() or not citations:
        return 0, len(citations)

    try:
        source_text = source_path.read_text(encoding='utf-8').lower()
    except Exception:
        return 0, len(citations)

    verified = 0
    for citation in citations:
        # Normalize: lowercase, collapse whitespace
        normalized = re.sub(r'\s+', ' ', citation.lower().strip())
        # Check if a substantial substring (first 30 chars) appears in source
        # This handles minor formatting differences
        check_str = normalized[:min(30, len(normalized))]
        if check_str in source_text:
            verified += 1

    return verified, len(citations)


def check_review_validity(file_path: str, level_code: str, module_slug: str) -> list[dict]:
    """
    Validate the existence and quality of the review file.

    Applies tier-appropriate checks and returns violations with
    actionable REDO prompts that tell the LLM to regenerate from scratch.
    Also verifies that cited Ukrainian text actually exists in the source module.
    """
    violations = []

    # Detect tier
    tier_num = _detect_tier(file_path, level_code)
    if tier_num is None:
        return []

    cfg = TIER_CONFIG[tier_num]
    fix_prompt = _build_fix_prompt(tier_num)

    # Construct review path — check both audit/ and review/ directories
    module_path = Path(file_path)
    base_dir = module_path.parent
    audit_review = base_dir / 'audit' / f"{module_slug}-review.md"
    review_review = base_dir / 'review' / f"{module_slug}-review.md"

    # Prefer audit/ (canonical per AGENTS.md), fall back to review/
    if audit_review.exists():
        review_file = audit_review
    elif review_review.exists():
        review_file = review_review
    else:
        review_file = None

    # 1. Existence Check
    if review_file is None:
        try:
            rel_path = audit_review.relative_to(base_dir.parent.parent)
        except ValueError:
            rel_path = audit_review
        return [{
            'type': 'MISSING_REVIEW',
            'severity': 'critical',
            'message': f"No Tier {tier_num} ({cfg['name']}) review file at {rel_path}. {fix_prompt}"
        }]

    try:
        content = review_file.read_text(encoding='utf-8')

        # 2. Length Check (tier-specific minimum)
        if len(content) < cfg['min_chars']:
            violations.append({
                'type': 'FAKE_REVIEW_TOO_SHORT',
                'severity': 'critical',
                'message': (
                    f"Review is only {len(content)} chars — Tier {tier_num} ({cfg['name']}) "
                    f"requires {cfg['min_chars']}+ chars. {fix_prompt}"
                )
            })
            return violations  # No point checking structure of a stub

        # 3. Structure Check (tier-specific required headers)
        missing = [name for pattern, name in cfg['required_headers']
                   if not re.search(pattern, content)]
        if missing:
            violations.append({
                'type': 'FAKE_REVIEW_STRUCTURE',
                'severity': 'critical',
                'message': f"Review missing required sections: {', '.join(missing)}. {fix_prompt}"
            })

        # 4. Template Placeholder Check
        placeholders = [
            (r'\{slug\}', '{slug}'),
            (r'\{level\}', '{level}'),
            (r'\{num\}', '{num}'),
            (r'\{X\.X\}', '{X.X}'),
            (r'\{what you found\}', '{what you found}'),
        ]
        found_placeholders = [name for pattern, name in placeholders
                              if re.search(pattern, content)]
        if found_placeholders:
            violations.append({
                'type': 'FAKE_REVIEW_TEMPLATE',
                'severity': 'critical',
                'message': (
                    f"Review has unreplaced placeholders: {', '.join(found_placeholders)}. "
                    f"The template was not filled in. {fix_prompt}"
                )
            })

        # Extract citations once — used by checks 5, 7, and 8
        citations = _extract_ukrainian_citations(content)
        has_citations = len(citations) >= 2

        # 5. Rubber-stamp Detection: All perfect scores with no evidence
        perfect, total = _count_perfect_scores(content)
        if total >= cfg['min_dimensions'] and perfect == total:
            if not has_citations:
                violations.append({
                    'type': 'RUBBER_STAMP_REVIEW',
                    'severity': 'critical',
                    'message': (
                        f"Review scores {perfect}/{total} dimensions as 10/10 but cites ZERO "
                        f"Ukrainian sentences as evidence. A perfect score requires justification "
                        f"— quote the specific text that earns each 10. {fix_prompt}"
                    )
                })

        # 6. Empty "Issues Found" section
        issues_match = re.search(
            r'## Issues Found[^\n]*\n(.*?)(?=\n## |\Z)', content, re.DOTALL
        )
        if issues_match:
            issue_text = issues_match.group(1).strip()
            if (not issue_text
                    or len(issue_text) < 30
                    or re.match(r'^(None|No issues|N/A|—|-)\s*$', issue_text, re.IGNORECASE)):
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

        # 7. No Ukrainian citations (tier 2+ only — tier 1 is mixed-language)
        if cfg['require_ukr_citations'] and not has_citations:
            # Only add if not already flagged as rubber-stamp
            if not any(v['type'] == 'RUBBER_STAMP_REVIEW' for v in violations):
                violations.append({
                    'type': 'NO_EVIDENCE_REVIEW',
                    'severity': 'warning',
                    'message': (
                        "Review contains no quoted Ukrainian text. A real review cites specific "
                        "sentences from the module (e.g., «Він пішов до хати» — wrong aspect). "
                        f"{fix_prompt}"
                    )
                })

        # 8. Citation verification — check quoted text exists in the source .md
        if cfg['require_ukr_citations'] and len(citations) >= 2:
            source_md = module_path  # The .md file being reviewed
            verified, total_cit = _verify_citations_against_source(citations, source_md)
            unverified = total_cit - verified
            if total_cit >= 3 and verified == 0:
                # No citations match the source at all — likely fabricated
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
                # Less than half match — suspicious
                violations.append({
                    'type': 'UNVERIFIED_CITATIONS',
                    'severity': 'warning',
                    'message': (
                        f"Only {verified}/{total_cit} Ukrainian citations in the review "
                        f"were found in the source module. The reviewer may be quoting "
                        f"from memory rather than from the actual content. {fix_prompt}"
                    )
                })

    except Exception as e:
        violations.append({
            'type': 'REVIEW_READ_ERROR',
            'severity': 'critical',
            'message': f"Could not read review file: {e}"
        })

    return violations
