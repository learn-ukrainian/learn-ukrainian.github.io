"""
Review Gaming Detection

Deterministic checks that catch LLM review-gaming patterns:
- Score uniformity (all dimensions rated identically high)
- Citation density (too few Ukrainian citations for content length)
- Review section coverage (review ignores sections of the content)
- Score drift (scores significantly above track mean)
- Review boilerplate (copy-pasted issue text across reviews)
- Phantom section references (review cites non-existent content sections)
- Cross-agent enforcement (same LLM reviews its own content)

All checks return list[dict] with 'type', 'severity', 'message' keys
(review-style violations — single regeneration instruction).

Issue: #610
"""

import hashlib
import json
import re
import statistics
import sys
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import contextlib

from slug_utils import review_path as _review_path
from slug_utils import to_bare_slug

# Reuse existing infrastructure from review_validation
from .review_validation import (
    _detect_tier,
    _extract_ukrainian_citations,
)

# =============================================================================
# HELPERS
# =============================================================================

def _find_review_file(file_path: str, module_slug: str) -> Path | None:
    """Find the review file for a given module."""
    md_path = Path(file_path)
    base_dir = md_path.parent
    canonical = _review_path(base_dir, module_slug)
    if canonical.exists():
        return canonical

    # Check legacy audit/ location
    bare = to_bare_slug(module_slug)
    legacy = base_dir / 'audit' / f'{bare}-review.md'
    if legacy.exists():
        return legacy

    # Check review/ with bare slug
    alt = base_dir / 'review' / f'{bare}-review.md'
    if alt.exists():
        return alt

    return None


def _extract_all_scores(content: str) -> list[float]:
    """Extract all dimension scores from a review."""
    scores = []
    for match in re.findall(r'\|\s*\w[^|]*\|\s*(\d+(?:\.\d+)?)/10\s*\|', content):
        with contextlib.suppress(ValueError):
            scores.append(float(match))
    return scores


def _extract_h2_headers(content: str) -> list[str]:
    """Extract H2 header text from markdown content."""
    return re.findall(r'^##\s+(.+)', content, re.MULTILINE)


def _normalize_for_hash(text: str) -> str:
    """Normalize text for hashing: lowercase, strip, collapse whitespace."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def _get_all_review_files(track_dir: Path) -> list[Path]:
    """Get all review files in a track directory."""
    review_dir = track_dir / 'review'
    if review_dir.is_dir():
        return sorted(review_dir.glob('*-review.md'))
    return []


# =============================================================================
# CHECK 10: DIMENSION SCORE UNIFORMITY
# =============================================================================

def check_score_uniformity(review_content: str) -> list[dict]:
    """
    Flag reviews where all dimension scores are uniformly high.

    If stdev < 0.5 AND mean >= 8.0, the reviewer likely isn't evaluating
    each dimension independently.

    Severity: warning only (genuinely good modules can have uniform scores).
    """
    violations = []

    scores = _extract_all_scores(review_content)
    if len(scores) < 5:
        return []  # Not enough scores to evaluate

    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0

    if stdev < 0.5 and mean >= 8.0:
        violations.append({
            'type': 'UNIFORM_HIGH_SCORES',
            'severity': 'warning',
            'message': (
                f"All {len(scores)} dimension scores are uniformly high "
                f"(mean={mean:.1f}, stdev={stdev:.2f}). "
                "Each dimension should be evaluated independently — "
                "genuinely different aspects rarely score identically."
            ),
        })

    return violations


# =============================================================================
# CHECK 8: CITATION DENSITY
# =============================================================================

def check_citation_density(
    review_content: str,
    content_path: str,
    file_path: str,
    level_code: str,
) -> list[dict]:
    """
    Verify the review has enough Ukrainian citations relative to content length.

    Tier 1 (A1/A2) is skipped — reviews are shorter.
    Tier 2+: <1 citation per 600 words = critical; <1 per 300 = warning.
    """
    violations = []

    tier = _detect_tier(file_path, level_code)
    if tier is None or tier == 1:
        return []

    # Count citations
    citations = _extract_ukrainian_citations(review_content)
    citation_count = len(citations)

    # Get content word count
    content_file = Path(content_path) if content_path else Path(file_path)
    if content_file.exists():
        try:
            content_text = content_file.read_text(encoding='utf-8')
            word_count = len(content_text.split())
        except OSError:
            return []
    else:
        return []

    if word_count < 200:
        return []  # Content too short to meaningfully check

    # Calculate ratio — conservative thresholds to avoid breaking existing reviews
    expected_min = word_count / 600  # At least 1 citation per 600 words (critical)
    expected_warn = word_count / 300  # Ideally 1 per 300 words (warning)

    if citation_count < expected_min:
        violations.append({
            'type': 'LOW_CITATION_DENSITY',
            'severity': 'critical',
            'message': (
                f"Review has only {citation_count} Ukrainian citation(s) for "
                f"{word_count}-word content (need at least {int(expected_min)}). "
                "A proper review must cite specific Ukrainian sentences from the content "
                "to support its assessment. Quote the actual text with «» or \"\"."
            ),
        })
    elif citation_count < expected_warn:
        violations.append({
            'type': 'LOW_CITATION_DENSITY',
            'severity': 'warning',
            'message': (
                f"Review has {citation_count} Ukrainian citation(s) for "
                f"{word_count}-word content (ideally {int(expected_warn)}+). "
                "More citations would strengthen the review's evidence base."
            ),
        })

    return violations


# =============================================================================
# CHECK 9: REVIEW SECTION COVERAGE
# =============================================================================

def check_review_section_coverage(
    review_content: str,
    content: str,
) -> list[dict]:
    """
    Verify the review mentions/covers sections from the content.

    Extracts H2 headers from content, checks if the review text mentions
    each section (fuzzy: section title words appear near each other).

    Skip if content has <3 H2 sections.
    Threshold: <30% = critical; <60% = warning.
    """
    violations = []

    content_headers = _extract_h2_headers(content)
    if len(content_headers) < 3:
        return []

    # Filter out standard non-content headers
    skip_headers = {
        'словник', 'vocabulary', 'лексика', 'бібліографія', 'джерела',
        'література', 'використані джерела', 'самооцінювання',
        'self-assessment', 'самоперевірка',
    }
    content_headers = [
        h for h in content_headers
        if h.strip().lower() not in skip_headers
    ]
    if len(content_headers) < 3:
        return []

    # English equivalents for common Ukrainian section prefixes.
    # Fallback matching when reviews are written in English.
    _SECTION_EN_EQUIVALENTS: dict[str, list[str]] = {
        'вступ': ['introduction', 'intro'],
        'теорія': ['theory'],
        'практика': ['practice'],
        'культурний контекст': ['cultural context', 'culture section'],
        'граматика': ['grammar'],
        'лексика': ['vocabulary', 'lexicon'],
        'читання': ['reading'],
        'підсумок': ['summary', 'conclusion'],
        'фонетика': ['phonetics', 'pronunciation'],
        'діалог': ['dialogue', 'dialog'],
        'письмо': ['writing'],
        'аудіювання': ['listening'],
        'словник': ['glossary', 'word list'],
        'вправи': ['exercises', 'drills'],
        'повторення': ['review', 'revision'],
        'хронологія': ['chronology', 'timeline'],
        'аналіз': ['analysis'],
        'розминка': ['warm-up', 'warmup', 'warm up'],
        'презентація': ['presentation'],
        'біографія': ['biography'],
        'життєпис': ['biography'],
        'діагностика': ['diagnostic'],
        'основні': ['main', 'basic', 'core'],
    }

    review_lower = review_content.lower()
    mentioned = 0

    for header in content_headers:
        header_lower = header.strip().lower()
        # Check if the full header text appears in review
        if header_lower in review_lower:
            mentioned += 1
            continue

        # Check the part before colon (e.g. "Час дієслова" from "Час дієслова: ...")
        pre_colon = header_lower.split(':')[0].strip()
        if len(pre_colon) > 3 and pre_colon in review_lower:
            mentioned += 1
            continue

        # Fuzzy: check if distinctive words from the header appear in review
        # Use len > 2 to catch short Ukrainian words like "Вид", "Час"
        # Use word boundaries to avoid substring matches (час in учасник)
        words = [w for w in re.split(r'[\s:,]+', header_lower) if len(w) > 2]
        if words and all(
            re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', review_lower)
            for w in words
        ):
            mentioned += 1
            continue

        # Partial: if at least 60% of distinctive words match (with word boundaries)
        if len(words) >= 2:
            matches = sum(
                1 for w in words
                if re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', review_lower)
            )
            if matches >= len(words) * 0.6:
                mentioned += 1
                continue

        # English-equivalent fallback: check if the pre-colon Ukrainian label
        # has a known English equivalent that appears in the review
        matched_en = False
        for uk_key, en_list in _SECTION_EN_EQUIVALENTS.items():
            if uk_key in pre_colon or pre_colon in uk_key:
                for en_term in en_list:
                    if en_term in review_lower:
                        matched_en = True
                        break
            if matched_en:
                break
        if matched_en:
            mentioned += 1

    total = len(content_headers)
    coverage = mentioned / total if total > 0 else 1.0

    if coverage < 0.30:
        missed = [h for h in content_headers if h.strip().lower() not in review_lower]
        violations.append({
            'type': 'REVIEW_LOW_SECTION_COVERAGE',
            'severity': 'critical',
            'message': (
                f"Review only covers {mentioned}/{total} ({coverage:.0%}) content sections. "
                f"Missed: {', '.join(missed[:5])}. "
                "A thorough review must address each major section of the content."
            ),
        })
    elif coverage < 0.60:
        violations.append({
            'type': 'REVIEW_LOW_SECTION_COVERAGE',
            'severity': 'warning',
            'message': (
                f"Review covers {mentioned}/{total} ({coverage:.0%}) content sections. "
                "Consider addressing all major sections for a complete review."
            ),
        })

    return violations


# =============================================================================
# CHECK 6: SCORE DRIFT MONITORING
# =============================================================================

def check_score_drift(
    review_content: str,
    file_path: str,
    module_slug: str,
) -> list[dict]:
    """
    Flag reviews whose mean score is a 2-sigma outlier above the track mean.

    Loads all reviews in the same track directory, calculates mean and stdev
    of review means, then flags if current review is anomalously high.

    Fallback if <5 reviews: flag if mean > 9.2.
    Severity: warning.
    """
    violations = []
    md_path = Path(file_path)
    track_dir = md_path.parent

    current_scores = _extract_all_scores(review_content)
    if len(current_scores) < 5:
        return []

    current_mean = statistics.mean(current_scores)

    # Collect means from all reviews in the track
    review_files = _get_all_review_files(track_dir)

    # Exclude current module's review
    bare_slug = to_bare_slug(module_slug)
    other_means = []

    for review_file in review_files:
        if bare_slug in review_file.stem:
            continue
        try:
            text = review_file.read_text(encoding='utf-8')
        except OSError:
            continue
        scores = _extract_all_scores(text)
        if len(scores) >= 5:
            other_means.append(statistics.mean(scores))

    if len(other_means) >= 5:
        track_mean = statistics.mean(other_means)
        track_stdev = statistics.stdev(other_means)

        # Dynamic threshold: 2-sigma above track mean
        # Floor stdev at 0.5 to avoid zero-variance tracks triggering on any deviation
        threshold = track_mean + max(2 * track_stdev, 0.5)
        if current_mean > threshold:
            violations.append({
                'type': 'SCORE_DRIFT_OUTLIER',
                'severity': 'warning',
                'message': (
                    f"Review mean score ({current_mean:.1f}) is a 2σ outlier "
                    f"above track average ({track_mean:.1f} ± {track_stdev:.1f}). "
                    "This may indicate rubber-stamping. Re-examine scores critically."
                ),
            })
    else:
        # Fallback: too few reviews for statistics
        if current_mean > 9.2:
            violations.append({
                'type': 'SCORE_DRIFT_OUTLIER',
                'severity': 'warning',
                'message': (
                    f"Review mean score ({current_mean:.1f}) is very high "
                    "(>9.2 with insufficient track data for statistical comparison). "
                    "Verify each dimension score is justified with specific evidence."
                ),
            })

    return violations


# =============================================================================
# CHECK 7: REVIEW BOILERPLATE DETECTION
# =============================================================================

def check_review_boilerplate(
    review_content: str,
    file_path: str,
    module_slug: str,
) -> list[dict]:
    """
    Detect copy-pasted issue text across reviews.

    Extracts the "Issues" section content, splits into sentences, hashes them,
    and checks overlap with other reviews in the track.

    Threshold: >50% overlap with any single other review = warning; >70% = critical.
    """
    violations = []
    md_path = Path(file_path)
    track_dir = md_path.parent

    # Extract issues section from current review
    issues_match = re.search(
        r'^##\s+.*(?:Issues|Critique|Problems|Concerns|Проблеми|Недоліки|Зауваження|Критика).*?\n(.*?)(?=^##\s|\Z)',
        review_content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not issues_match:
        return []

    current_issues_text = issues_match.group(1).strip()
    if len(current_issues_text) < 50:
        return []  # Too short to meaningfully check

    # Split into sentences and hash
    current_sentences = [
        s.strip() for s in re.split(r'(?<=[.!?])\s+', current_issues_text)
        if len(s.strip()) > 20
    ]
    if len(current_sentences) < 3:
        return []

    current_hashes = {
        hashlib.md5(_normalize_for_hash(s).encode('utf-8')).hexdigest()
        for s in current_sentences
    }

    # Compare against other reviews
    bare_slug = to_bare_slug(module_slug)
    review_files = _get_all_review_files(track_dir)
    max_overlap = 0.0
    max_overlap_file = ''

    for review_file in review_files:
        if bare_slug in review_file.stem:
            continue

        try:
            text = review_file.read_text(encoding='utf-8')
        except OSError:
            continue

        other_issues = re.search(
            r'^##\s+.*(?:Issues|Critique|Problems|Concerns|Проблеми|Недоліки|Зауваження|Критика).*?\n(.*?)(?=^##\s|\Z)',
            text,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if not other_issues:
            continue

        other_text = other_issues.group(1).strip()
        other_sentences = [
            s.strip() for s in re.split(r'(?<=[.!?])\s+', other_text)
            if len(s.strip()) > 20
        ]
        if not other_sentences:
            continue

        other_hashes = {
            hashlib.md5(_normalize_for_hash(s).encode('utf-8')).hexdigest()
            for s in other_sentences
        }

        overlap = len(current_hashes & other_hashes)
        overlap_pct = overlap / len(current_hashes) if current_hashes else 0

        if overlap_pct > max_overlap:
            max_overlap = overlap_pct
            max_overlap_file = review_file.name

    if max_overlap > 0.70:
        violations.append({
            'type': 'REVIEW_BOILERPLATE',
            'severity': 'critical',
            'message': (
                f"Review issues section shares {max_overlap:.0%} of sentences "
                f"with {max_overlap_file}. "
                "This indicates copy-pasted boilerplate. "
                "Each review must contain module-specific feedback."
            ),
        })
    elif max_overlap > 0.50:
        violations.append({
            'type': 'REVIEW_BOILERPLATE',
            'severity': 'warning',
            'message': (
                f"Review issues section shares {max_overlap:.0%} of sentences "
                f"with {max_overlap_file}. "
                "Ensure feedback is specific to this module, not recycled."
            ),
        })

    return violations


# =============================================================================
# CHECK 11: PHANTOM SECTION REFERENCES
# =============================================================================

def check_review_section_references(
    review_content: str,
    content: str,
) -> list[dict]:
    """
    Verify that sections referenced in the review actually exist in content.

    Pattern: 'Section "X"', 'розділ "X"', or direct header references.
    Flag phantom references to non-existent sections.

    Threshold: any phantom reference = warning.
    """
    violations = []

    # Extract section references from review (case-insensitive for Ukrainian)
    patterns = [
        r'[Ss]ection\s+"([^"]+)"',
        r'[Ss]ection\s+«([^»]+)»',
        r'[Рр]озділ\s+["«]([^"»]+)["»]',
        r'[Ss]ection\s+on\s+"([^"]+)"',
    ]

    referenced_sections = []
    for pattern in patterns:
        for match in re.finditer(pattern, review_content, re.IGNORECASE):
            referenced_sections.append(match.group(1))

    if not referenced_sections:
        return []

    # Get actual headers from content
    content_headers = _extract_h2_headers(content)
    # Also include H3 headers
    h3_headers = re.findall(r'^###\s+(.+)', content, re.MULTILINE)
    all_headers = content_headers + h3_headers
    headers_lower = {h.strip().lower() for h in all_headers}

    # Check each reference
    phantom = []
    for ref in referenced_sections:
        ref_lower = ref.strip().lower()

        # Exact match
        if ref_lower in headers_lower:
            continue

        # Fuzzy: check if all key words from ref appear in any header
        ref_words = {w for w in ref_lower.split() if len(w) > 3}
        found = False
        for header in headers_lower:
            header_words = {w for w in header.split() if len(w) > 3}
            if ref_words and ref_words.issubset(header_words):
                found = True
                break

        if not found:
            phantom.append(ref)

    if phantom:
        violations.append({
            'type': 'PHANTOM_SECTION_REFERENCE',
            'severity': 'warning',
            'message': (
                f"Review references {len(phantom)} section(s) not found in content: "
                f"{', '.join(repr(p) for p in phantom[:5])}. "
                "Verify section names match actual content headers."
            ),
        })

    return violations


# =============================================================================
# CHECK 12: CROSS-AGENT ENFORCEMENT
# =============================================================================

def check_cross_agent_review(
    review_content: str,
    file_path: str,
) -> list[dict]:
    """
    Verify that the reviewer is not the same model that built the content.

    Looks for 'Reviewed-By:' in the review and 'builder_model' in state-v3.json.
    Same model family = critical. Missing Reviewed-By = warning.
    """
    violations = []
    md_path = Path(file_path)
    track_dir = md_path.parent

    # Extract Reviewed-By from review
    reviewed_by_match = re.search(
        r'\*?\*?Reviewed-By:\*?\*?\s*(.+)',
        review_content,
        re.IGNORECASE,
    )
    reviewed_by = reviewed_by_match.group(1).strip() if reviewed_by_match else None

    # Get builder model from state-v3.json
    bare_slug = to_bare_slug(md_path.stem)
    orch_dir = track_dir / 'orchestration' / bare_slug
    state_v3 = orch_dir / 'state-v3.json'

    builder_model = None
    if state_v3.exists():
        try:
            with open(state_v3, encoding='utf-8') as f:
                state = json.load(f)
            # Look for builder model in Phase B (prose generation)
            phases = state.get('phases', {})
            phase_b = phases.get('B', phases.get('b', {}))
            builder_model = phase_b.get('model', phase_b.get('builder_model'))
            # Also check Phase A if B is missing
            if not builder_model:
                phase_a = phases.get('A', phases.get('a', {}))
                builder_model = phase_a.get('model', phase_a.get('builder_model'))
        except (json.JSONDecodeError, OSError):
            pass

    if not reviewed_by:
        violations.append({
            'type': 'MISSING_REVIEWER_ID',
            'severity': 'critical',
            'message': (
                "Review is missing 'Reviewed-By:' metadata. "
                "Re-run Phase D to generate a review with proper provenance."
            ),
        })
        return violations

    if builder_model:
        # Normalize model families
        reviewer_family = _model_family(reviewed_by)
        builder_family = _model_family(builder_model)

        if reviewer_family and builder_family and reviewer_family == builder_family:
            violations.append({
                'type': 'SELF_REVIEW_DETECTED',
                'severity': 'critical',
                'message': (
                    f"Same model family reviewed its own content: "
                    f"builder={builder_model}, reviewer={reviewed_by}. "
                    "Reviews MUST be done by a different LLM to prevent bias. "
                    "Regenerate the review using the other agent."
                ),
            })

    return violations


def _model_family(model_id: str) -> str | None:
    """Extract model family from model ID string."""
    model_lower = model_id.lower().strip()

    if any(k in model_lower for k in ['gemini', 'google', 'palm']):
        return 'google'
    if any(k in model_lower for k in ['claude', 'anthropic', 'sonnet', 'opus', 'haiku']):
        return 'anthropic'
    if any(k in model_lower for k in ['gpt', 'openai', 'o1', 'o3']):
        return 'openai'

    return None


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def check_review_gaming(
    review_content: str,
    content: str,
    file_path: str,
    level_code: str,
    module_slug: str,
) -> list[dict]:
    """
    Run all review gaming detection checks.

    Args:
        review_content: The review file text
        content: The content .md file text
        file_path: Path to the content .md file
        level_code: CEFR level code (e.g. 'B1')
        module_slug: Module slug (e.g. 'sentence-structure')

    Returns combined list of violations from all sub-checks.
    """
    violations = []

    # Check 10: Score uniformity (fast — statistics)
    violations.extend(check_score_uniformity(review_content))

    # Check 8: Citation density
    violations.extend(check_citation_density(
        review_content, file_path, file_path, level_code
    ))

    # Check 9: Section coverage
    violations.extend(check_review_section_coverage(review_content, content))

    # Check 6: Score drift (reads other reviews)
    violations.extend(check_score_drift(review_content, file_path, module_slug))

    # Check 7: Boilerplate detection (reads other reviews)
    violations.extend(check_review_boilerplate(review_content, file_path, module_slug))

    # Check 11: Phantom section references
    violations.extend(check_review_section_references(review_content, content))

    # Check 12: Cross-agent enforcement
    violations.extend(check_cross_agent_review(review_content, file_path))

    return violations
