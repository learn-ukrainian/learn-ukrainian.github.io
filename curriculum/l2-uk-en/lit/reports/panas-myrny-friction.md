# Friction Report: Module panas-myrny-intro

**Date**: 2026-02-12
**Task**: Fresh Narrative Engine v2.4 Build (Target: 5000 words)

## Critical Friction Points

### 1. Tool Failure: `web_fetch`
- **Issue**: The tool failed to retrieve content from `litopys.org.ua` and `ukrlib.com.ua`. It seems to have issues with specific redirects or simulated browser headers for these sites.
- **Impact**: "Turn 1" (Data Mine) had to be simulated using `google_web_search` snippets and internal knowledge rather than direct text extraction. This risks minor quoting inaccuracies (though checked).
- **Recommendation**: Update `web_fetch` to handle Cyrillic encoding and redirects better, or allow a "raw HTML" dump mode.

### 2. Workflow: Word Count Estimation
- **Issue**: The "Writer Persona" tends to underestimate the volume required for 5000 words. A "dense" 2500-word draft feels complete but fails the specific volume audit.
- **Impact**: Required 3 iterations of "Narrative Hydration" (Turn 3b) to reach the target.
- **Recommendation**: The skill should explicitly mandate a "Section Word Count Budget" (e.g., "Intro must be 800 words") rather than a total target, to force expansion during the drafting phase.

### 3. Tool Sensitivity: `replace`
- **Issue**: The `replace` tool failed on multi-paragraph context matches due to likely whitespace/newline mismatches in the `old_string`.
- **Impact**: Required manual `tail` and copy-paste to ensure exact string matching.
- **Recommendation**: Use unique anchor tags in future templates (e.g., `<!-- SECTION_END -->`) to make insertion easier.

## Success Metrics
- **Final Word Count**: ~5100 words.
- **Richness**: High (5 quotes, deep analysis, intertextuality).
- **Audit**: Expected PASS.
