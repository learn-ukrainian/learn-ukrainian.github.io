# Seminar Track Full-Rebuild Workflow

This workflow is the mandatory standard for rebuilding or creating modules in "Seminar" tracks: `b2-hist`, `c1-bio`, `c1-hist`, `lit`, `oes`, and `ruth`. It prioritizes research-driven, decolonized, and linguistically rich content.

## Phase 0: Research-First Mandate
- **Sniper Search**: Use `google_web_search` with `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua` for academic accuracy.
- **Source Filter**: STRICTLY Ukrainian-language sources only; Russian sources are prohibited.
- **Notes**: Capture chronology, primary quotes, and decolonization angles. Save to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`.
- **Engagement Mapping**: Identify at least 5 engagement hooks (`[!myth-buster]`, `[!history-bite]`, `[!context]`, `[!quote]`) from research data.

## Phase 1: Metadata Alignment (`meta/{slug}.yaml`)
- **Plan Sync**: Match the immutable `word_target` from `plans/`.
- **Granular Outline**: Refactor `content_outline` into H2 sections with word allocations summing to the target.
- **Vital Status**: Verify subject's status to ensure correct section naming (e.g., "Legacy" vs. "Impact").

## Phase 2: Content Hydration (`{slug}.md`)
- **Deep Immersion**: Write authentic Ukrainian text targeting word minimums (never reducing them).
- **Callout Integration**: Implement the 5+ mapped engagement callouts into the narrative flow.
- **Production Support**: Include a level-appropriate Model Answer (`> [!model-answer]`).
- **Typography**: Use Ukrainian angular quotes `«...»`.

## Phase 3: Atomic YAML Generation
- **Enriched Vocabulary**: Create `vocabulary/{slug}.yaml` matching the count target defined in the plan/meta. Include IPA and English translations.
- **Pedagogical Activities**: Create `activities/{slug}.yaml` following track-specific schemas (e.g., Seminar style: **Reading Input → Analytical Output**).

## Phase 4: Technical Audit (`scripts/audit_module.py`)
- **Strict Gates**: Run the audit script to verify:
    - **Outline Compliance**: Headers must match the metadata outline exactly.
    - **Word Density**: Every section must meet its allocated target.
    - **Schema Integrity**: Validate activity IDs and field names against `schemas/`.
    - **Richness Score**: Ensure 95%+ richness through vocabulary density and engagement.

## Phase 5: Review-Content-v4 (Deep Quality & Scoring)
**Mandatory: Native-level line-by-line verification.**
- **Linguistic Verification**: Check every sentence for grammar, naturalness, Russianisms, and calques.
- **Activity Verification**: Verify every activity item for factual correctness and schema alignment.
- **12-Dimension Scoring**: Score the module (0-10) across 12 dimensions (Experience, Coherence, Relevance, Educational, Language, Pedagogy, Immersion, Activities, Richness, Humanity, LLM Fingerprint, Linguistic Accuracy).
- **Report Generation**: Save the formal report to `curriculum/l2-uk-en/{level}/review/{slug}-review.md`.
- **Pass Threshold**: 8.5+ overall score; no dimension below its auto-fail threshold.

## Phase 6: Build Pipeline
- **MDX Generation**: Run `npm run generate {level} {num}` to verify the merge of MD and YAML sidecars.
- **Status Check**: Confirm that `status/{slug}.json` reflects a PASS.