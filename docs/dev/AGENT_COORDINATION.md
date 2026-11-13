# Agent Coordination Hub

**Last Updated:** 2026-01-03
**Coordinator:** Claude 1 (this session)

## Active Agents

| Code | Agent | Subscription | Current Task | Issue | Status |
|------|-------|--------------|--------------|-------|--------|
| **A** | Gemini 1 | User's | B2 M111 | #349 | ✅ Complete (reviewed) |
| **M** | Gemini 2 | User's | B2 M112 | #349 | ✅ Complete (reviewed) |
| **K** | Gemini 3 | User's | B1 M81-84 | #351 | ✅ Complete (4 modules created) |
| **C1-b** | Claude 1 (other session) | User's | B2 enrichment | #349 | 🔄 Fixing 67 gaps (M82, M100, etc.) |
| **Opus** | Antigravity Opus | Google AI Pro #1 | Grammar validation refactor | #352 | ✅ Complete |
| **Gemini-Flash** | Gemini 3-flash | Google AI Pro #1 | B1 word count fixes (15 modules) | - | ✅ Complete (2,984 words added) |
| **Gemini-ULP** | Gemini | User's | ULP podcast mapping (240 episodes → 623 modules) | - | ✅ Complete (173 mappings, reviewed) |
| **C1-c** | Claude Sonnet | User's Claude Max | Grammar validate testing (#352) | - | ✅ Complete (10/10 tests pass) |
| **C1-d** | Claude Sonnet | User's Claude Max | Resource refactor (#354) | #354 | ✅ Complete (285 files cleaned, YAML architecture) |
| **C1-c** | Claude Sonnet | User's Claude Max | External resources expansion (#338) Phases 1-6 | #338 | ✅ Complete (296 ULP resources integrated) |
| **Gemini-Flash-B2** | Gemini 3-flash | Google AI Pro #1 | B2 word count fixes (8 modules) | - | ✅ Complete |
| **Gemini-Pro-C1** | Gemini Pro | User's | C1 metadata generation + biography adjustments | - | 🔄 IN PROGRESS (generating C1 module metadata) |

## This Session (C1-a: Coordinator)

- **Role:** Review hub, agent coordination, issue management
- **Same Claude, different session:** C1-b is doing B2 migration
- **Tracking:** All agent progress, reviewing completed work

## Context Files

| Agent | Context Document | Model |
|-------|------------------|-------|
| Agent M (Gemini 2) | `docs/dev/GEMINI2_B1_MIGRATION_CONTEXT.md` | gemini-3-flash |
| C1-b (Claude other session) | `docs/dev/CLAUDE_B2_MIGRATION_CONTEXT.md` | Sonnet |
| **C1-c (Claude grammar testing)** | **`docs/dev/CLAUDE_GRAMMAR_TEST_CONTEXT.md`** | **Sonnet** |
| **C1-d (Claude resource refactor)** | **`docs/dev/CLAUDE_RESOURCE_REFACTOR_CONTEXT.md`** | **Sonnet** |
| **C1-c (Claude external resources)** | **`docs/dev/C1C_MAPPING_METHODOLOGY_INSTRUCTIONS.md`** | **Sonnet** |
| **Gemini-Flash-B2 (word count)** | **`docs/dev/B2_WORD_COUNT_FIXES.md`** | **gemini-3-flash** |
| **Gemini (B1 M81-84)** | **`docs/dev/GEMINI_B1_M81-84_CONTEXT.md`** | **gemini-3-flash (pilot on M81)** |
| Agent K (Gemini 3) | TBD - assign when context resets | gemini-3-flash |
| C2 (Claude 2) | TBD - standing by for assignment | Sonnet/Opus |

## Analysis Documents

| Topic | Document | Status | Next Step |
|-------|----------|--------|-----------|
| **Activity Quality Validation** | **`docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md`** | **✅ Complete + Issued** | **See Issue #355** |

## Migration Progress

| Level | Modules | Extraction | Enrichment | Content Quality | Status |
|-------|---------|------------|------------|-----------------|--------|
| A1 | 34 | ✅ Done | ✅ Done | ✅ 34/34 pass | ✅ Complete |
| A2 | 57 | ✅ Done | ✅ Done | ✅ 57/57 pass | ✅ Complete |
| B1 | 91 | ✅ Done | ✅ Done | ✅ 91/91 pass | ✅ Complete |
| B2 | 145 | ✅ Done | 🔄 Fixing 67 gaps | ⚠️ 131/145 pass (0 fail ✅, 14 unbuilt) | 🔄 In progress (90%) |
| C1 | 196 | 🔄 Metadata generation | ⏳ Pending | - | 🔄 Early planning (Gemini Pro) |

## C1-b B2 Enrichment Progress

```
☒ Run B2 vocabulary extraction script
☒ Verify extraction (110 YAML files)
☒ Enrich M01-M03 (passive voice)
☒ Enrich M04-M10 (passive voice remainder)
☒ Enrich vocabulary M11-M30 (syntax, registers)
☒ Enrich vocabulary M31-M70 (idioms, synonyms)
☒ Enrich vocabulary M71-M106 (history modules)
☒ Enrich vocabulary M110-M111 (additional modules)
☒ Run global vocab audit validation
☒ Test pipeline on B2
```

**Status:** 🔄 **Fixing Remaining Gaps** (2026-01-02)

### Audit Findings

**Global vocabulary audit results:**
- 67 modules have vocabulary items missing IPA/translations
- **Main gaps:**
  - M100: 64 items missing enrichment
  - M82: 60 items missing enrichment
  - M87-M91: Partial gaps
  - M96-M99: Partial gaps

**Current work:** C1-b is fixing the 67 remaining vocabulary gaps across all affected modules.

## B2 Module Status

| Range | Count | Content | Vocabulary YAML | Enrichment | Audit Status |
|-------|-------|---------|-----------------|------------|--------------|
| M01-M10 | 10 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M11-M70 | 60 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M71-M110 | 40 | ✅ | ✅ | 🔄 Fixing gaps (M82, M87-91, M96-100) | ✅ Pass |
| M111-M115 | 5 | ✅ | ✅ | ✅ Done (M110-111) | ✅ Pass |
| M116 | 1 | ✅ | ✅ | ✅ Done | ✅ Pass (fixed by Gemini-Flash-B2) |
| M117 | 1 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M118-M120 | 3 | ✅ | ✅ | ✅ Done | ✅ Pass (fixed by Gemini-Flash-B2) |
| M121-M122 | 2 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M123-M124 | 2 | ✅ | ✅ | ✅ Done | ✅ Pass (fixed by Gemini-Flash-B2) |
| M125-M126 | 2 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M127-M128 | 2 | ✅ | ✅ | ✅ Done | ✅ Pass (fixed by Gemini-Flash-B2) |
| M129-M131 | 3 | ✅ | ✅ | ✅ Done | ✅ Pass |
| M132-M145 | 14 | ❌ Need to build | ❌ | ❌ | - |

**Total:** 131/145 modules PASS (90%), 0 FAIL word count ✅, 14 not built

**CRITICAL: B2+ 1750-word target is HARD requirement (not soft warning)**

**All word count issues resolved!** ✅
- M116, M118-120, M123-124, M127-128: Fixed by Gemini-Flash-B2 (2026-01-02)

## Issue Tracking

- **#340** - Epic: Vocabulary YAML Architecture (Agent A - A2) - ✅ CLOSED
- **#334** - Epic: Podcast Data Ingestion and Structuring - 🔄 IN PROGRESS
- **#349** - B2 YAML Migration (C1-b) - 🔄 IN PROGRESS (fixing 67 gaps)
- **#350** - B1 YAML Migration (Agent M) - 🔄 UNBLOCKED (ready for work)
- **#351** - B1.7 Expansion (Agent K) - ✅ CLOSED (M81-M84 complete)
- **#352** - Grammar Validation Refactor (Antigravity Opus) - ✅ CLOSED + TESTED
- **#353** - Phase 3a: Extract External Resources - ✅ CLOSED (247 modules, 602 podcasts)
- **#354** - Refactor: Extract Resources from Markdown - ✅ CLOSED (285 files, YAML architecture)
- **#338** - Ukrainian Lessons Integration - ✅ CLOSED (296 ULP resources, priority sorting)
- **#355** - Activity Quality Validation Expansion - 📋 OPEN (awaiting Claude agent assignment)
- **#356** - LIT Track YAML Conversion - 📋 OPEN (awaiting agent assignment)
- **#358** - Epic: Complete External Content Coverage for All Modules - 📋 OPEN (3-phase external resources plan)

## Issue #352: Grammar Validation System Refactor ✅ COMPLETE + TESTED

**Agent:** Antigravity Opus (Google AI Pro #1)
**Tester:** C1-c (Claude Sonnet)
**Priority:** P0 - BLOCKS ALL CONTENT WORK
**Status:** ✅ Complete (2026-01-02) | ✅ Tested (2026-01-02) | **PRODUCTION READY**

### Implemented Solution

**Phase 1: Remove Queue Generation** ✅
- Removed `grammar_queue` from pipeline default steps
- Deleted 3 scripts (964 lines): `generate_grammar_queue.py`, `generate_grammar_review_queue.py`, `finalize_validation.py`
- Removed `step_grammar_queue()` from `scripts/pipeline.py`
- Commit: 932fda3c

**Phase 2: Implement Direct LLM Validation** ✅
- Added `--validate-grammar` flag to audit script (opt-in)
- Uses Gemini API directly with existing prompt
- Gracefully skips if GEMINI_API_KEY not set
- Commit: 2ef8b996

**Phase 3: Documentation** ✅
- Updated CLAUDE.md: removed queue references, added CLI docs
- Commit: 2ef8b996

**Usage:**
```bash
export GEMINI_API_KEY="your-key"
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md --validate-grammar
```

**Unblocks:** B1 word count fixes (15 modules), B2 word count fixes (8 modules), all content work

### Testing Results ✅

**Tester:** C1-c (Claude Sonnet)
**Date:** 2026-01-02
**Report:** `docs/dev/GRAMMAR_VALIDATE_TEST_REPORT.md`

**Results:** 10/10 tests passed
- ✅ CLI functionality (help, default, graceful degradation)
- ✅ Manual grammar validation (A1/B1/B2 modules - no errors found)
- ✅ Code review (robust error handling, clean implementation)

**Findings:**
- No grammar errors found in curriculum (excellent Ukrainian quality)
- Graceful degradation works perfectly (GEMINI_API_KEY not required)
- Error handling robust, follows project patterns
- **Production ready** - can be used immediately

**Status:** APPROVED FOR PRODUCTION USE

## Issue #353: Extract External Resources ✅ COMPLETE

**Agent:** C1-d (Claude Sonnet)
**Priority:** P1 - Blocked podcast integration (#338)
**Status:** ✅ Complete (2026-01-02) | **PRODUCTION READY**

### Deliverables Completed

**Phase 1: Extraction** ✅
- Script: `scripts/extract_external_resources.py` (276 lines)
- Parsed 313 markdown files across 6 levels
- Extracted resources from 210 modules with existing `[!resources]` sections
- Classified by type: YouTube, podcasts, articles, books, websites
- Output: `docs/resources/external_resources.yaml` (297KB)

**Phase 2: Merge ULP Mappings** ✅
- Script: `scripts/merge_podcast_mappings.py` (222 lines)
- Merged Gemini's 173 ULP podcast mappings
- Created 37 new module entries (modules without previous resources)
- Added 602 total podcast episodes with `match_reason` metadata
- Deduplication by episode_id and URL

**Phase 3: Validation** ✅
- Script: `scripts/validate_external_resources.py` (360 lines)
- Validates YAML structure and required fields
- Checks podcast episode_ids against `podcast_db.json`
- Detects duplicate URLs within modules
- Results: 3 errors (source markdown), 621 warnings (acceptable)

**Phase 4: Generation** ✅
- Script: `scripts/generate_resource_sections.py` (453 lines)
- Regenerated `[!resources]` sections for 247 modules
- Consistent formatting with emoji icons (🎧 📺 📖 📚 🌐)
- Sorted by type and relevance
- Preserved all original resources + added ULP podcasts

### Statistics

| Metric | Count |
|--------|-------|
| Modules with resources | 247 |
| Original extracted modules | 210 |
| New modules (podcast-only) | 37 |
| Total podcast episodes added | 602 |
| Markdown files updated | 247 |
| Validation errors | 3 (source markdown issues) |
| Validation warnings | 621 (missing descriptions) |

### Round-Trip Verification ✅

Tested on `a1-09-food-and-drinks`:
- **Before:** 1 YouTube + 1 podcast + 2 articles = 4 resources
- **After:** 1 YouTube + 5 podcasts + 2 articles = 8 resources
- **Result:** All original resources preserved + 4 new ULP podcast episodes added

### Known Issues (3 validation errors)

**Manual fixes needed:**
- `b1-25`: Incomplete/malformed URL in source markdown
- `b1-82`: Incomplete/malformed URL in source markdown
- `b1-84`: Incomplete/malformed URL in source markdown

**Warnings (621 - acceptable):**
- High-relevance resources lacking descriptions - can be enriched later

### Files Created

1. `scripts/extract_external_resources.py` - 276 lines
2. `scripts/merge_podcast_mappings.py` - 222 lines
3. `scripts/validate_external_resources.py` - 360 lines
4. `scripts/generate_resource_sections.py` - 453 lines
5. `docs/resources/external_resources.yaml` - 297KB (master resource database)

**Unblocks:** #338 (Phase 3b: ULP Podcast Integration - READY)

**Status:** PRODUCTION READY - All 247 modules updated with unified resources

---

## Issue #354: Refactor Resources from Markdown ✅ COMPLETE

**Agent:** C1-d (Claude Sonnet)
**Priority:** P1 - Cleanup after #353
**Status:** ✅ Complete (2026-01-02) | **PRODUCTION READY**

### Deliverables Completed

**All 6 Phases Complete:**

**Phase 1: Backup** ✅
- Created `curriculum/l2-uk-en/resources_backup/` (277 files)
- Preserved all original `[!resources]` sections
- Safety net before refactoring

**Phase 2: Injection in Generation** ✅
- Modified `scripts/generate_mdx.py` - Injects resources during MDX generation
- Modified `scripts/generate_json.py` - Injects resources during JSON generation
- Source: `docs/resources/external_resources.yaml`
- Template: `docusaurus/src/components/ResourcesSection.tsx` (React component)

**Phase 3: Remove from Source Markdown** ✅
- Script: `scripts/remove_resources_from_markdown.py` (213 lines)
- Cleaned 277 modules (A1-A2-B1-B2)
- Removed all `[!resources]` sections from curriculum markdown
- Single source of truth: `external_resources.yaml`

**Phase 4: Update Validation** ✅
- Modified `scripts/audit/core.py` - Removed resources section check
- Modified `scripts/validate_mdx.py` - Removed resources validation
- Resources no longer required in source markdown
- Validated during generation instead

**Phase 5: Deprecate Scripts** ✅
- Deprecated: `scripts/generate_resource_sections.py` (453 lines)
- Added deprecation notice to script header
- Removed from workflow documentation

**Phase 6: Documentation** ✅
- Updated `docs/ARCHITECTURE.md` - YAML injection architecture
- Updated `docs/SCRIPTS.md` - Removed resource generation references
- Updated `docs/MARKDOWN-FORMAT.md` - Resources no longer in source format
- Updated `CLAUDE.md` - Workflow changes
- Updated `claude_extensions/phases/stage-2-content.md` - No resources in markdown

### Statistics

| Metric | Count |
|--------|-------|
| Modules cleaned (initial) | 277 |
| Additional B2 modules cleaned | 8 |
| **Total files cleaned** | **285** |
| Backup files created | 277 |
| Scripts modified | 4 |
| Scripts deprecated | 1 |
| Documentation files updated | 5 |
| Lines of code added | 213 (cleanup script) |

### Testing Results ✅

**Validated full pipeline:**
- ✅ A1 M09: Resources injected correctly (1 YouTube + 5 podcasts + 2 articles)
- ✅ B1 M03: Resources injected correctly (sample test)
- ✅ B2 M01: Resources injected correctly (sample test)
- ✅ Audit passes without resources in markdown (A1 M09)
- ✅ MDX validation passes (resources injected during generation)
- ✅ JSON output includes resources from YAML

**Round-trip verification:**
```
Source markdown: NO [!resources] section (removed)
                     ↓
YAML database: external_resources.yaml (single source of truth)
                     ↓
Generation: Inject during MDX/JSON generation
                     ↓
Output: Resources appear in final HTML/JSON
```

### Architecture Achievement

**Before (Issue #353):**
- 304 `[!resources]` sections scattered across markdown
- No unified schema
- Manual maintenance nightmare
- Duplication risk

**After (Issue #354):**
- ✅ Single source of truth: `external_resources.yaml`
- ✅ Automated injection during generation (MDX + JSON)
- ✅ Clean markdown (content only, no resources)
- ✅ Matches activities pattern (activities also YAML-injected)
- ✅ 285 files cleaned, 277 backed up
- ✅ Full validation pipeline passes

**Status:** PRODUCTION READY - YAML architecture complete

---

## Issue #355: Activity Quality Validation Expansion 📋 OPEN

**Agent:** TBD (awaiting assignment)
**Priority:** HIGH - Quality validation critical for content excellence
**Status:** 📋 OPEN (2026-01-02)

### Problem Statement

Current validation (`/grammar-validate`, `/review-content`) focuses on **correctness** but lacks **quality dimensions**:

**7 Identified Gaps:**
1. No Naturalness Validation (robotic vs authentic Ukrainian)
2. No Difficulty Calibration (too easy/hard for CEFR level)
3. No Variety Detection (mechanical sentence patterns)
4. No Pedagogical Coherence (activities not testing module objectives)
5. No Engagement Validation (boring vs culturally relevant)
6. No Distractor Quality (nonsense vs plausible pedagogical errors)
7. Pipeline Integration Gaps (needs queue-based workflow)

### Proposed Solution

**Hybrid Validation Approach:**

1. **Deterministic Checks** (No API, Instant Feedback) - ✅ COMPLETE
   - Module: `scripts/audit/checks/activity_quality.py` (383 lines)
   - Functions: variety analysis, difficulty estimation, distractor quality, naturalness markers, cognitive load

2. **Manual Validation Rubrics** (Human Semantic Validation) - ⏳ PENDING
   - Expand `/review-content` Section 8 with detailed 5-dimension rubrics
   - CEFR-aware quality gates (B1: 3.5 naturalness, B2: 4.0, C1: 4.5, C2: 4.8)

3. **Queue-Based Workflow** - ⏳ PENDING
   - Generate quality queues with deterministic analysis pre-populated
   - Manual validation for semantic dimensions
   - Finalization script evaluates quality gates

### Architecture Decision

**DECISION:** ✅ **CONFIRMED - Merge into `/review-content`**
- User confirmed: "merge yes, this will have to be assigned to claude yes"
- Avoids duplication (Section 8 already covers Activity Quality)
- Single comprehensive review workflow

### Implementation Plan (6 Phases)

**Phase 1:** ✅ COMPLETE
- Analysis document created
- Deterministic checks module created

**Phase 2:** ⏳ PENDING (Command Integration) - **Assigned to Claude agent**
- ✅ Decision confirmed: Merge into `/review-content`
- Expand `/review-content` Section 8 with 5 quality dimension rubrics
- Delete `activity-validate.md` (functionality absorbed)
- Deploy: `npm run claude:deploy`

**Phase 3:** ⏳ PENDING (Queue Generation Script)
- Script: `scripts/audit/generate_activity_quality_queue.py`
- Pre-populate deterministic checks
- Leave semantic fields for manual validation

**Phase 4:** ⏳ PENDING (Finalization Script)
- Script: `scripts/audit/finalize_activity_quality.py`
- Evaluate CEFR-specific quality gates
- Generate audit reports

**Phase 5:** ⏳ PENDING (Audit Integration)
- Update `scripts/audit/gates.py` - Add quality gate
- Update `scripts/audit/core.py` - Integrate deterministic checks
- Update `scripts/audit/config.py` - Add quality thresholds

**Phase 6:** ⏳ PENDING (Testing & Documentation)
- Test on B2 sample module
- Update 3 documentation files
- Deploy commands

### Files Created (Phase 1)

- ✅ `docs/dev/issues/355-activity-quality-validation.md` (detailed issue)
- ✅ `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md` (600+ lines analysis)
- ✅ `scripts/audit/checks/activity_quality.py` (383 lines deterministic checks)
- ⚠️ `claude_extensions/commands/activity-validate.md` (may deprecate if merging)

### Next Steps

1. **Assign agent** for Phase 2-6 implementation
2. **Decision:** Merge into `/review-content` or keep separate
3. Implement queue generation + finalization scripts
4. Integrate into audit pipeline
5. Test and document

**Estimated Effort:** 6-8 hours (phases 2-6)

**Dependencies:** None (Phase 1 complete, ready for implementation)

---

## Issue #356: LIT Track YAML Conversion 📋 OPEN

**Agent:** TBD (awaiting assignment)
**Priority:** MEDIUM - Architecture consistency, pipeline integration
**Status:** 📋 OPEN (2026-01-02)

### Problem Statement

The LIT (Ukrainian Literature & Classics) track modules have not been converted to the YAML architecture used by A1, A2, B1, and B2 levels.

**Current LIT structure:**
- 14 LIT modules in `curriculum/l2-uk-en/lit/` (M01-M14)
- Activities embedded in markdown as "Завдання" sections (not extracted to YAML)
- Vocabulary uses 3-column specialized format (different from 6-column standard)
- Modules NOT validated by audit pipeline
- NO MDX/JSON generation for Docusaurus or Vibe app

**This blocks:**
- Unified pipeline processing across all levels
- Activity validation and quality checks
- Vocabulary enrichment workflows
- Consistent output generation

### LIT Modules Inventory (14 modules)

| Module | Title | Status |
|--------|-------|--------|
| 01 | Феномен Івана Котляревського | ❌ Not converted |
| 02 | Енеїда - Частина 1 | ❌ Not converted |
| 03 | Енеїда - Бенкет | ❌ Not converted |
| 04 | Енеїда - Війна | ❌ Not converted |
| 05 | Наталка Полтавка | ❌ Not converted |
| 06 | Квітка - Біографія | ❌ Not converted |
| 07 | Маруся | ❌ Not converted |
| 08 | Конотопська відьма | ❌ Not converted |
| 09 | Етнографія | ❌ Not converted |
| 10 | Квітка - Мова | ❌ Not converted |
| 11 | Молодий Шевченко | ❌ Not converted |
| 12 | Балади | ❌ Not converted |
| 13 | Гайдамаки | ❌ Not converted |
| 14 | Сон | ❌ Not converted (deleted from git) |

**Total:** 14 modules (13 active + 1 deleted)

### Recommended Approach: Option A (Full YAML Conversion)

**Implementation Plan (6 Phases):**

**Phase 1:** ⏳ Analysis & Inventory (2 hours)
- Audit all 14 LIT modules
- Catalog activity types (essays, debates, short responses)
- Identify vocabulary enrichment needs
- Create conversion strategy document

**Phase 2:** ⏳ YAML Schema Design (2 hours)
- Design activity YAML format for literary modules
- Types: `essay`, `debate`, `short-response`, `analysis`, `comparison`
- Handle long-form essay prompts (300-400 words)
- Define rubric structure for grading criteria

**Phase 3:** ⏳ Activity Extraction (12 hours)
- Extract activities from 14 modules to YAML
- Estimated: 14 modules × 3-5 activities × 15 min = 10-12 hours
- Validate YAML structure
- Test with sample module

**Phase 4:** ⏳ Vocabulary Decision (2 hours)
- Decision: Keep 3-column format or convert to 6-column?
- If keeping 3-column: Update audit to accept both formats
- If converting: Enrich with IPA, POS, Gender (like A1/A2/B1/B2)
- Recommendation: Keep 3-column (specialized literary terminology)

**Phase 5:** ⏳ Pipeline Integration (4 hours)
- Update `scripts/generate_mdx.py` to handle LIT modules
- Update `scripts/generate_json.py` for LIT output
- Update `scripts/audit_module.py` to validate LIT format
- Add LIT to `scripts/pipeline.py`
- Test full pipeline: `npm run pipeline l2-uk-en lit`

**Phase 6:** ⏳ Validation & Documentation (2 hours)
- Run audit on all 14 LIT modules
- Generate MDX for Docusaurus
- Generate JSON for Vibe app
- Update documentation:
  - `docs/ARCHITECTURE.md` - Add LIT track
  - `docs/MARKDOWN-FORMAT.md` - Document LIT activity types
  - `CLAUDE.md` - Add LIT workflow

**Total estimated effort:** 24 hours (3 full days)

### Activity Types for LIT Track

**Literary analysis activities (different from A1/A2/B1/B2):**

1. **essay** - Long-form critical writing (300-500 words)
   - Rubric: thesis, evidence, analysis, conclusion
   - Example: "Есе-Роздум" on Kotliarevsky's legacy

2. **debate** - Structured discussion prompt
   - Rubric: argument, counterargument, evidence
   - Example: "Історична Дискусія" on Masepa's choices

3. **short-response** - Brief analytical answer (100-200 words)
   - Rubric: clarity, evidence, interpretation
   - Example: "Аналіз Цитати" from Eneida

4. **analysis** - Close reading of text passage
   - Rubric: language analysis, context, interpretation
   - Example: Analyzing Shevchenko's poetic technique

5. **comparison** - Compare two works/authors/periods
   - Rubric: similarities, differences, synthesis
   - Example: Kotliarevsky vs. European mock-epic tradition

### Acceptance Criteria

- [ ] All 14 LIT modules converted to YAML activity format
- [ ] Vocabulary format decision made and implemented
- [ ] Audit pipeline validates LIT modules
- [ ] MDX generation works for LIT track
- [ ] JSON generation works for LIT track
- [ ] Full pipeline runs: `npm run pipeline l2-uk-en lit`
- [ ] Documentation updated (3 files)
- [ ] At least 1 sample module tested end-to-end

### Dependencies

- ✅ YAML architecture established (A1/A2/B1/B2 complete)
- ✅ Pipeline tools exist (`generate_mdx.py`, `generate_json.py`, `audit_module.py`)
- ⏳ Activity type definitions for literary modules (Phase 2)

### Files

**Issue document:** `docs/dev/issues/356-lit-track-yaml-conversion.md`

**LIT modules location:** `curriculum/l2-uk-en/lit/`

**Sample module:** `curriculum/l2-uk-en/lit/01-introduction-to-kotliarevsky.md`

### Notes

- **LIT track is post-C1** - Advanced literary analysis for proficient learners
- **Different pedagogy** - Essay-based, not quiz-based (requires new activity types)
- **3-column vocabulary** - Specialized format may be retained (literary terminology needs context)
- **User feedback:** "we forgot to convert LIT please create an issue about that"
- **Conversion can happen in parallel** with C1/C2 work (independent track)

---

## Issue #358: Epic: Complete External Content Coverage for All Modules 📋 OPEN

**Agent:** TBD (awaiting assignment)
**Priority:** HIGH - Organize all external content integration efforts
**Status:** 📋 OPEN (2026-01-03)

### Vision

Every curriculum module should have rich external content in `[!resources]` sections, prioritized by quality and pedagogical value.

### Prioritization Strategy

**Priority 1: ULP Podcasts 🎧 (HIGHEST)**
- **Source:** Ukrainian Lessons Podcast episodes
- **Status:** Issue #334 (Epic: Podcast Data Ingestion and Structuring)
- **Current:** 240 episodes cataloged, mapping in progress
- **Target:** Map all episodes to relevant modules (A1-B1 focus)

**Priority 2: ULP Blog Posts 📖 (HIGH)**
- **Source:** Ukrainian Lessons blog articles
- **Status:** ✅ COMPLETE (Issue #338)
- **Result:** 296 ULP resources integrated
- **Coverage:** A1 33.3%, A2 27.3%, B1 18.7%, B2 3.1%
- **Gap:** Need more B1-B2 content (ULP is beginner-focused)

**Priority 3: Verified Ukrainian Content 🇺🇦 (MEDIUM)**
- **Criteria:**
  - Created by Ukrainian speakers (native or heritage)
  - **B1+ ONLY:** 100% Ukrainian immersion (no English)
  - A1-A2: Bilingual content acceptable
  - Quality verified (accurate grammar, natural Ukrainian)
- **Sources to explore:**
  - YouTube creators (see issues #238, #239, #240, #304)
  - Ukrainian news outlets (Українська правда, Суспільне)
  - Educational platforms (Ukrainian Institute)
  - Cultural resources (museums, literature sites)

### Current Coverage Statistics

| Level | ULP Podcasts | ULP Blogs | YouTube | Other | Total Modules | Coverage |
|-------|--------------|-----------|---------|-------|---------------|----------|
| **A1** | TBD | 11/33 (33.3%) | 0 | 0 | 34 | **33.3%** |
| **A2** | TBD | 15/55 (27.3%) | 0 | 0 | 57 | **27.3%** |
| **B1** | TBD | 17/91 (18.7%) | TBD (#304) | 0 | 86 | **18.7%** |
| **B2** | TBD | 4/131 (3.1%) | TBD (#238) | 0 | 145 | **3.1%** |
| **C1** | N/A | 0 | TBD (#239) | 0 | 196 | **0%** |
| **C2** | N/A | 0 | TBD (#240) | 0 | 100 | **0%** |
| **LIT** | N/A | 0 | 0 | 0 | 14 | **0%** |

**Critical gaps:**
- **B2:** Only 3.1% coverage (4/145 modules) - ULP doesn't cover advanced topics
- **C1/C2:** 0% coverage - Need native Ukrainian educational content
- **LIT:** 0% coverage - Need literary analysis resources

### Implementation Phases

**Phase 1: ULP Podcast Integration ⏳ IN PROGRESS**
- **Owner:** Issue #334
- **Estimated:** 240 episodes × 1-2 modules each = 200-400 mappings
- **Tasks:**
  1. Complete podcast metadata ingestion (Issue #334)
  2. Map episodes to modules using same scoring algorithm as blog posts
  3. Add to `external_resources.yaml` with Priority 1
  4. Regenerate all modules with podcast links
- **Target coverage after Phase 1:**
  - A1: 60-70% (ULP's primary audience)
  - A2: 50-60%
  - B1: 30-40%
  - B2: 10-15% (ULP has limited advanced content)

**Phase 2: YouTube Content Curation ⏳ PENDING**
- **Owner:** Issues #238, #239, #240, #304
- **Estimated:** 50-100 videos per level
- **Tasks:**
  1. Research Ukrainian YouTube creators (educational, cultural, news)
  2. Verify quality (natural Ukrainian, accurate grammar)
  3. **B1+ constraint:** ONLY 100% Ukrainian content (no English)
  4. Map videos to modules by topic
  5. Add to `external_resources.yaml` with Priority 3
- **YouTube creator categories:**
  - Language learning: Easy Ukrainian, Ukrainian with Yana, Learn Ukrainian with Max
  - News/Current events: Українська правда, Суспільне, ICTV
  - Culture/History: Ukrainian Institute, Історична правда
  - Literature/Philosophy: Ukrainian book reviews, Shevchenko readings
  - Science/Tech: Ukrainian science communicators
- **Target coverage after Phase 2:**
  - B1: 60-70%
  - B2: 40-50%
  - C1: 30-40%
  - C2: 30-40%

**Phase 3: Other Verified Content 📋 PLANNED**
- **Owner:** TBD
- **Estimated:** 100-200 resources
- **Source types:**
  1. Podcasts (non-ULP): Fresh Mova Ukrainian, Ukrainian cultural podcasts
  2. Articles: Українська правда, BBC Україна, Ukrainian cultural sites
  3. Interactive resources: Ukrainian grammar drills (B1+), vocabulary games
  4. Literary resources (C1/C2/LIT): Project Gutenberg Ukrainian texts, Shevchenko digital archive, contemporary literature excerpts
- **Target coverage after Phase 3:**
  - All levels: 70-90%
  - C1/C2/LIT: 50-60% (specialized content harder to find)

### Quality Gates

**Content Verification Criteria (All levels):**
- ✅ Created by Ukrainian speakers (native or heritage)
- ✅ Accurate Ukrainian grammar (verified by native speaker or grammar checker)
- ✅ Natural phrasing (not translated from English)
- ✅ Relevant to module topic (grammar, vocabulary, culture)

**B1+ specific:**
- ✅ 100% Ukrainian immersion (no English explanations)
- ✅ CEFR-appropriate complexity
- ✅ Cultural authenticity (Ukrainian perspectives, not Western)

**Excluded content:**
- ❌ Machine-translated resources
- ❌ Content with Russianisms or Surzhyk (unless pedagogically intentional)
- ❌ Content created by non-Ukrainian speakers (B1+)
- ❌ English-language explanations (B1+, except for A1-A2)

### Priority Assignment Rules

**Priority 1 (Critical):**
- Exact topic match + exact level match
- ULP podcasts/blogs
- Example: "Dative case" episode → A2 dative module

**Priority 2 (High):**
- Strong topic match + adjacent level
- ULP content with partial relevance
- Example: "All cases" article → specific case module

**Priority 3 (Moderate):**
- Moderate topic match OR distant level
- YouTube videos, other verified content
- Example: Ukrainian culture video → cultural module

### Coverage Goals

**Short-term (Q1 2026):**
- ✅ ULP blog posts: COMPLETE (296 resources)
- 🔄 ULP podcasts: IN PROGRESS (Issue #334)
- **Target:** A1 70%, A2 60%, B1 40%

**Mid-term (Q2 2026):**
- 🎯 YouTube curation: B1-C2 (Issues #238-240, #304)
- **Target:** B1 60%, B2 40%, C1 30%

**Long-term (Q3-Q4 2026):**
- 🎯 Other verified content (all levels)
- **Target:** All levels 70%+, C1/C2/LIT 50%+

### Success Metrics

**When this epic is complete:**
- ✅ Every A1 module has 2-3 external resources (70%+ coverage)
- ✅ Every A2 module has 2-3 external resources (60%+ coverage)
- ✅ Every B1 module has 2-4 external resources (60%+ coverage)
- ✅ Every B2 module has 2-4 external resources (40%+ coverage)
- ✅ Every C1 module has 1-3 external resources (30%+ coverage)
- ✅ Every C2 module has 1-3 external resources (30%+ coverage)
- ✅ B1+ modules have ONLY 100% Ukrainian content
- ✅ All resources verified for quality (grammar, authenticity)

### Related Issues

**Completed:**
- ✅ Issue #338: Ukrainian Lessons Blog Integration - 296 resources added

**In Progress:**
- 🔄 Issue #334: Podcast Data Ingestion (ULP podcasts) - 240 episodes

**Pending:**
- ⏳ Issue #304: B1 Media (YouTube content)
- ⏳ Issue #238: B2 Media (YouTube content)
- ⏳ Issue #239: C1 Media (YouTube content)
- ⏳ Issue #240: C2 Media (YouTube content)

### Documentation

**Created:**
- `docs/resources/EXTERNAL_RESOURCES_SCHEMA.md` - YAML structure
- `docs/resources/external_resources.yaml` - Master database (production)
- `docs/resources/ukrainianlessons/` - ULP integration reports

**To create:**
- `docs/resources/CONTENT_VERIFICATION_GUIDE.md` - Quality criteria
- `docs/resources/YOUTUBE_CURATION_GUIDE.md` - YouTube vetting process
- `docs/resources/coverage_report.md` - Coverage tracking dashboard

### Dependencies

- ✅ Issue #338: ULP blog integration (COMPLETE)
- 🔄 Issue #334: ULP podcast ingestion (IN PROGRESS)
- ⏳ Issues #238-240, #304: YouTube content curation (PENDING)
- ✅ Generation scripts support priority-based sorting (COMPLETE)

### Notes

- **ULP bias toward beginners:** Ukrainian Lessons Podcast targets A1-B1, so B2/C1/C2 need other sources
- **B1+ immersion constraint:** Critical for pedagogical integrity - no English explanations allowed
- **Cultural authenticity:** Prefer Ukrainian creators over Western "Ukrainian language" content
- **Scalability:** Use automated scoring + manual verification workflow (proven effective with ULP blogs)

**Issue created:** 2026-01-03 by C1-a (Coordinator)
**Epic owner:** TBD (assign when ready to proceed with Phase 2)

---

## Issue #338: Ukrainian Lessons Integration ✅ COMPLETE

**Agent:** C1-c (Claude Sonnet, User's Claude Max)
**Priority:** P2 - Enhance content with additional external resources
**Status:** ✅ COMPLETE (2026-01-02) | **PRODUCTION READY**

### Phase 1: ✅ COMPLETE - Blog Discovery

**Completed by C1-c (2026-01-02):**

**Blog Discovery:**
- Discovered 402+ blog articles on Ukrainian Lessons
- Cataloged 28 high-value articles (grammar, vocab, culture, phrases)
- Created database: `docs/resources/ukrainianlessons/blog_db.json`
- Categorized by level: A1 (14), A2 (6), B1 (7), B2 (1)

**Content Breakdown:**
- 9 grammar guides (cases, tenses, aspect, prefixes)
- 5 vocabulary lists (family, food, clothes, animals)
- 4 phrasebooks (greetings, thank you, small talk)
- 4 cultural guides (Kyiv, customs, Shevchenko)
- 4 learning resources (dictionaries, study tips)
- 2 advanced guides (false friends, confusing words)

**Database created:** `docs/resources/ukrainianlessons/blog_db.json` (28 articles)

### Phase 2: ✅ COMPLETE - Automated Mapping & Scoring

**Completed by C1-c (2026-01-02):**

**Automated Mapping Results:**
- **301 high-quality mappings** created across 4 levels
- **76 Priority 1** (Critical/Essential matches)
- **205 Priority 2** (High relevance)
- **20 Priority 3** (Moderate relevance)

**Coverage by level:**
- A1: 19/33 modules (57.6%) - Excellent coverage ✅
- A2: 15/55 modules (27.3%) - Good coverage
- B1: 6/91 modules (6.6%) - Limited (ULP is beginner-focused)
- B2: 1/131 modules (0.8%) - Minimal (ULP doesn't cover advanced topics)

**Key Achievement:**
- ✅ **A1-01 Cyrillic Code I** now mapped to "Ukrainian Alphabet: Full Guide" (90 points, Priority 1)
- User's primary concern resolved

**Advanced Scoring Algorithm:**
- 4-dimension scoring (Topic Match, Level Match, Content Alignment, Source Priority)
- Weighted keyword matching (title words 3× vs topic words)
- Semantic keyword expansion (alphabet ↔ cyrillic, case ↔ accusative/genitive)
- Level inference for ULP episodes (ULP-001-050 = A1, 051-100 = A2, etc.)

**Files Created:**
- `docs/resources/ukrainianlessons/blog_db.json` - 29 blog articles catalog
- `docs/resources/ukrainianlessons/module_metadata.json` - 310 modules metadata
- `docs/resources/ukrainianlessons/resource_module_scores_final.json` - 301 scored mappings
- `docs/resources/ukrainianlessons/MAPPING_METHODOLOGY.md` - Algorithm methodology
- `docs/resources/ukrainianlessons/MAPPING_REPORT.md` - Initial analysis
- `docs/resources/ukrainianlessons/AUTOMATED_MAPPING_SUMMARY.md` - Final summary

**Sample Priority 1 Mappings:**
1. A1-01 Cyrillic Code I → Alphabet guide (90 points)
2. A1-09 Food & Drinks → "40+ Ukrainian Dishes" (85 points)
3. A1-11 Accusative I → Accusative Case guide (85 points)
4. A1-16 Genitive I → Genitive Case guide (85 points)
5. A1-21 Yesterday → Past Tense guide (85 points)
6. A1-22 Tomorrow → Future Tense guide (85 points)
7. A1-32 My Family → Family Vocabulary guide (85 points)

### Phase 3: ✅ COMPLETE - Manual Review & Verification

**Completed by C1-c (2026-01-02):**

**Manual Verification:**
- Reviewed all 76 Priority 1 (Critical/Essential) mappings → **100% approved**
- Spot-checked 19 Priority 2 samples → **100% approved**
- Zero false positives detected
- **Key achievement:** A1-01 alphabet guide verified (primary user concern resolved)

**Files Created:**
- `docs/resources/ukrainianlessons/PRIORITY1_REVIEW.md` - Full review of 76 critical mappings
- `docs/resources/ukrainianlessons/PRIORITY2_SPOT_CHECK.md` - Quality verification (19 samples)

### Phase 4: ✅ COMPLETE - Update external_resources.yaml

**Completed by C1-c (2026-01-02):**

**Integration:**
- Added 296 ULP resources to `docs/resources/external_resources.yaml`
- Added priority field (1-3) to all ULP resources
- Merged with existing 602 ULP podcast mappings
- YAML structure validated

The stray backup copy was removed in REMOVE-UNNEEDED-1107; see git history.

### Phase 5: ✅ COMPLETE - Update Generation Scripts

**Completed by C1-c (2026-01-02):**

**Script Modifications:**
- Modified `scripts/generate_mdx.py` - Implemented priority-based sorting
- Modified `scripts/generate_json.py` - Implemented priority-based sorting
- **Sorting order:** Priority 1 → Priority 2 → Priority 3, then relevance, then alphabetical

**Testing:**
- ✅ Priority 1 resources appear first in output
- ✅ Resource injection pipeline validated

### Phase 6: ✅ COMPLETE - Validation & Documentation

**Completed by C1-c (2026-01-02):**

**Validation:**
- ✅ A1-01 generation confirmed - alphabet guide appears FIRST in Articles section
- ✅ JSON output includes priority field and correct sorting
- ✅ 47 modules now have ULP content (A1: 11, A2: 15, B1: 17, B2: 4)

**Sample A1-01 Output Verified:**
```
📖 Articles:
- [Ukrainian Alphabet: Full Guide with Examples and Pronunciation]
  (https://www.ukrainianlessons.com/ukrainian-alphabet/) — Ukrainian Lessons
```

**Documentation Created:**
1. `docs/resources/ukrainianlessons/MAPPING_METHODOLOGY.md` - Scoring algorithm design
2. `docs/resources/ukrainianlessons/AUTOMATED_MAPPING_SUMMARY.md` - Comprehensive results (301 mappings)
3. `docs/resources/ukrainianlessons/PRIORITY1_REVIEW.md` - Manual review of 76 critical mappings
4. `docs/resources/ukrainianlessons/PRIORITY2_SPOT_CHECK.md` - Quality verification (19 samples)
5. `docs/resources/ukrainianlessons/IMPLEMENTATION_COMPLETE.md` - Full completion summary

### Completion Summary

**All 6 Phases Complete:**
- ✅ Phase 1: Blog Discovery (29 articles cataloged)
- ✅ Phase 2: Automated Mapping (301 high-quality mappings)
- ✅ Phase 3: Manual Review (76 Priority 1 + 19 Priority 2 verified, 100% approved)
- ✅ Phase 4: YAML Integration (296 ULP resources added)
- ✅ Phase 5: Generation Scripts (priority sorting implemented)
- ✅ Phase 6: Validation & Documentation (A1-01 verified, 5 docs created)

**Coverage Statistics:**

| Level | Modules with ULP | Coverage |
|-------|------------------|----------|
| A1    | 11/33            | 33.3%    |
| A2    | 15/55            | 27.3%    |
| B1    | 17/91            | 18.7%    |
| B2    | 4/131            | 3.1%     |

**Total:** 47 modules with ULP content across 4 levels

**Files Modified:**
- ✅ `docs/resources/external_resources.yaml` - Added 296 ULP resources with priority field
- ✅ `scripts/generate_mdx.py` - Priority-based sorting
- ✅ `scripts/generate_json.py` - Priority-based sorting

**Primary Goal Achieved:**
✅ **A1-01 "The Cyrillic Code I"** now has Ukrainian Alphabet guide as FIRST resource (Priority 1)

**Status:** PRODUCTION READY - All Ukrainian Lessons content integrated with priority sorting

### Previous Phases Complete

**Phase 3a (Issue #353):** ✅ Complete
- Extracted 247 modules with existing resources
- Merged 173 ULP podcast mappings
- Created unified YAML database (297KB)

**Refactor (Issue #354):** ✅ Complete
- YAML-based resource injection during generation
- Cleaned 285 markdown files
- Single source of truth architecture

---

## Issue #353: Extract External Resources ✅ ARCHIVED (Old)

**Priority:** P1 - Blocks podcast integration (#338)
**Status:** 🔄 NEW (2026-01-02)

### Problem

- 304 existing `[!resources]` sections in markdown (YouTube, articles, etc.)
- Need extraction before ULP podcast integration
- No unified schema for external resources

### Solution

1. **Extract** - Parse all 304 `[!resources]` sections → YAML
2. **Design schema** - Unified format for all resource types (podcasts, YouTube, articles, books)
3. **Merge ULP mappings** - Add Gemini's 173 podcast mappings to unified structure
4. **Generate** - Script to regenerate `[!resources]` sections from YAML

### Deliverables

- ✅ Schema designed: `docs/resources/EXTERNAL_RESOURCES_SCHEMA.md`
- ⏳ Extraction script: `scripts/extract_external_resources.py`
- ⏳ Merge script: `scripts/merge_podcast_mappings.py`
- ⏳ Validation script: `scripts/validate_external_resources.py`
- ⏳ Generation script: `scripts/generate_resource_sections.py`
- ⏳ Unified data: `docs/resources/external_resources.yaml`

### Dependencies

**Blocks:** #338 (Phase 3b: Podcast Integration)
**Uses:** Gemini's ULP mapping work (`ulp_mapping.yaml`)

### Next Steps

1. Implement extraction script
2. Run on all 304 modules
3. Merge ULP mappings
4. Validate and test round-trip generation
5. Unblock #338

## C1 Work In Progress 🔄

**Agent:** Gemini-Pro-C1 (Gemini Pro, User's subscription)
**Status:** 🔄 IN PROGRESS (2026-01-02)

### Current Tasks

**Metadata Generation:**
- Generating metadata for C1 modules (196 total planned)
- Preparing module structure and planning documents

**Biography Adjustments:**
- Refining C1 biographical content
- User feedback: "great changes, i love that" ✅
- Quality assessment: Excellent

**C1 Level Overview:**
- **Total modules planned:** 196 (per Ukrainian State Standard 2024)
- **Vocabulary target:** ~4,700 words (cumulative: ~9,780)
- **Focus:** Biographies, stylistics, folk culture, literature
- **Status:** Early planning/metadata phase

### Next Steps

- Complete C1 module metadata generation
- Finalize biography adjustments
- Begin C1 module content creation (TBD)

---

## Remaining B2 Work: M132-M145 (14 modules)

| Module | Title | Type | Status |
|--------|-------|------|--------|
| 132 | Медицина (поглиблено) | Domain | ❌ Not started |
| 133 | Технології та ШІ | Domain | ❌ Not started |
| 134 | Наука і дослідження | Domain | ❌ Not started |
| 135 | Мистецтво і література | Domain | ❌ Not started |
| 136 | Психологія та розум | Domain | ❌ Not started |
| 137 | Український менталітет | Culture | ❌ Not started |
| 138 | Сучасна діаспора | Culture | ❌ Not started |
| 139 | Релігія в Україні | Culture | ❌ Not started |
| 140 | Академічне письмо | Skills | ❌ Not started |
| 141 | Аналіз тексту | Skills | ❌ Not started |
| 142 | Capstone: Дослідження | Project | ❌ Not started |
| 143 | Capstone: Презентація | Project | ❌ Not started |
| 144 | B2 Підсумковий огляд | Review | ❌ Not started |
| 145 | B2 ФІНАЛЬНИЙ ІСПИТ | Exam | ❌ Not started |

## B1 Issues (15 modules need fixes)

### Issue #350: B1 Content Quality

**Word Count Issues (15 modules - need expansion):**
- M44: 1474/1500 (-26 words)
- M45: 1473/1500 (-27 words)
- M47: 1499/1500 (-1 word)
- M49: 1434/1500 (-66 words)
- M52: 1462/1500 (-38 words)
- M53: 1453/1500 (-47 words)
- M55: 1453/1500 (-47 words)
- M57: 1454/1500 (-46 words)
- M60: 1472/1500 (-28 words)
- M61: 1450/1500 (-50 words)
- M66: 1454/1500 (-46 words)
- M68: 1445/1500 (-55 words)
- M69: 1490/1500 (-10 words)
- M70: 1452/1500 (-48 words)
- M79: 1447/1500 (-53 words)

**All modules need minor content expansions (1-66 words each).**

### Issue #351: B1.7 Expansion ✅ COMPLETE

**Status:** ✅ Complete (2026-01-02)
- M81: Біг в Україні (1855 words, 97% immersion, 96% richness) ✅
- M82: Гори та трейлраннінг (1740 words, 97% immersion, 96% richness) ✅
- M83: Велосипед та водні види (1734 words, 97% immersion, 99% richness) ✅
- M84: Зимові види спорту (1651 words, 98% immersion, 96% richness) ✅
- Renumbering complete: M80-86 → M85-91 ✅
- Total B1 modules: 86 → 91 ✅

---

## Agent Assignments Available

**Priority 1 - B1 Word Count Fixes (15 modules) - ✅ COMPLETE**
- **Agent:** Gemini 3-flash (Google AI Pro #1)
- **Modules:** M44-45, M47, M49, M52-53, M55, M57, M60-61, M66, M68-70, M79
- **Task:** Add 1-66 words to each module (613 words minimum)
- **Delivered:** 2,984 words added (4.9× target)
- **Result:** All 15 modules pass audit + pipeline
- **Status:** ✅ Complete (2026-01-02)

**Priority 2 - B2 Word Count Fixes (8 modules) - ✅ COMPLETE**
- **Agent:** Gemini-Flash-B2 (gemini-3-flash, Google AI Pro #1)
- **Modules:** M116, M118-120, M123-124, M127-128
- **Task:** Add 8-97 words to each module (413 words minimum)
- **Context:** `docs/dev/B2_WORD_COUNT_FIXES.md`
- **Status:** ✅ Complete (2026-01-02)
- **Result:** All 8 modules now pass 1750-word B2 threshold

**Priority 3 - Extract External Resources (Issue #353) - ✅ COMPLETE**
- **Agent:** C1-d (Claude Sonnet, Claude Max)
- **Delivered:** 4 Python scripts + unified YAML database (1,311 lines code)
  - `scripts/extract_external_resources.py` - 276 lines
  - `scripts/merge_podcast_mappings.py` - 222 lines
  - `scripts/validate_external_resources.py` - 360 lines
  - `scripts/generate_resource_sections.py` - 453 lines
- **Output:** `docs/resources/external_resources.yaml` (297KB, 247 modules, 602 podcasts)
- **Status:** ✅ Complete (2026-01-02)
- **Result:** All 247 modules updated with unified resources, ULP podcasts integrated
- **Issues found:** 3 validation errors (B1-M25, M82, M84 - malformed URLs need manual fix)

**Priority 4 - Refactor Resources from Markdown (Issue #354) - ✅ COMPLETE**
- **Agent:** C1-d (Claude Sonnet, Claude Max)
- **Task:** Remove `[!resources]` from markdown, inject during generation (match activities pattern)
- **Deliverables:**
  - Modify `generate_mdx.py` and `generate_json.py` (inject resources from YAML)
  - Create `remove_resources_from_markdown.py` (cleanup 247 files)
  - Update validation scripts (audit, validate_mdx)
  - Deprecate `generate_resource_sections.py`
  - Update 4 documentation files
- **Context:** `docs/dev/CLAUDE_RESOURCE_REFACTOR_CONTEXT.md`
- **Status:** ✅ Complete (2026-01-02)
- **Result:** 285 files cleaned, YAML architecture complete

**Priority 5 - Activity Quality Validation (Issue #355) - 📋 AWAITING CLAUDE AGENT ASSIGNMENT**
- **Agent:** Claude Sonnet (TBD - specific agent to be assigned)
- **Task:** Expand activity quality validation system (6 phases)
- **Decision:** ✅ Confirmed - Merge into `/review-content` (not separate command)
- **Deliverables:**
  - **Phase 2:** Expand `/review-content` Section 8 with 5 quality dimension rubrics + delete `activity-validate.md`
  - **Phase 3:** Create `generate_activity_quality_queue.py` (queue generation script)
  - **Phase 4:** Create `finalize_activity_quality.py` (finalization script)
  - **Phase 5:** Integrate into audit pipeline (`gates.py`, `core.py`, `config.py`)
  - **Phase 6:** Testing & documentation (3 files)
- **Context:** `docs/dev/issues/355-activity-quality-validation.md`
- **Foundation Complete:** ✅ Phase 1 (analysis + deterministic checks module)
- **Estimated effort:** 6-8 hours (phases 2-6)

**Priority 6 - Build B2 remaining modules:**
- M132-M145 (14 modules: 5 domain, 3 culture, 2 skills, 4 capstone)

## Model Assignment Matrix

| Task Type | Model | Reasoning | Examples |
|-----------|-------|-----------|----------|
| **Vocabulary enrichment** | Claude Sonnet / Gemini 3-flash | Structured, repetitive data transformation | B2 M11-131 enrichment |
| **Word count fixes** | Claude Sonnet / Gemini 3-flash | Simple content expansion | B1 M44-70, B2 M116-128 |
| **Pedagogy fixes** | Claude Sonnet / Gemini 3-flash | H1/H2 changes, callout additions | B1 M81-84 (old) pedagogy |
| **Module content creation** | Claude Opus / Gemini 3-flash | Complex cultural narratives, domain expertise | B1 M81-84 (testing flash), B2 M132-145 |
| **Coordination/audits** | Claude Sonnet | File operations, batch processing | This session |

**Key Insight:**
- **Sonnet/Gemini 3-flash:** 95% quality at 20% cost for structured work
- **Opus/Gemini 3-flash:** Required for creative content creation
- Gemini 3-flash > Gemini 2.5-pro in capability

**Experiment Results (B1 M81-84):**
- ✅ gemini-3-flash validated for B1 cultural content creation
- 4/4 modules created with 96-99% richness, 97-98% immersion
- Quality equals gemini-3-pro at fraction of cost
- Recommendation: Use gemini-3-flash for B1 word count fixes

## Communication Protocol

1. Agents comment on their assigned issues with progress
2. Coordinator (this session) reviews and updates this file
3. Cross-agent dependencies flagged in issue comments
