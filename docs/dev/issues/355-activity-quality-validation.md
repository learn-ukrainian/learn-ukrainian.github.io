# Issue #355: Expand Activity Quality Validation - Naturalness, Difficulty, Engagement

**Status:** 📋 OPEN
**Priority:** HIGH
**Created:** 2025-01-02
**Assigned to:** TBD (awaiting agent assignment)

## Problem Statement

Current validation system (`/grammar-validate`, `/review-content`) focuses on **correctness** but lacks validation for **quality dimensions** that affect learner experience:

### 7 Identified Gaps:

1. **No Naturalness Validation** - Cannot detect robotic/translated phrasing vs authentic Ukrainian
2. **No Difficulty Calibration** - Activities may be too easy/hard for CEFR level
3. **No Variety Detection** - Mechanical sentence patterns not flagged
4. **No Pedagogical Coherence** - Activities may not test module objectives
5. **No Engagement Validation** - Boring vs culturally relevant content
6. **No Distractor Quality** - Nonsense options vs plausible pedagogical errors
7. **Pipeline Integration Gaps** - Manual workflow, needs queue-based system

### User Requirements (verbatim):

> "make sure we can properly use it to identify badly created activites, we have to make sure that the activites make sense for humans and dont have robotic feelings and they very, not too hard, not too easy"

## Proposed Solution

**Hybrid Validation Approach:**

### 1. Deterministic Checks (No API, Instant Feedback)
- ✅ **COMPLETE** - Module created: `scripts/audit/checks/activity_quality.py`
- Functions:
  - `analyze_sentence_variety()` - Detect mechanical repetition
  - `estimate_vocabulary_difficulty()` - Word length heuristics per CEFR level
  - `analyze_distractor_quality()` - Word class matching, plausibility
  - `check_natural_ukrainian_markers()` - Pronoun overuse, calques, discourse markers
  - `estimate_cognitive_load()` - Activity complexity + text complexity

### 2. Manual Validation Rubrics (Human Semantic Validation)
- Expand `/review-content` Section 8 with detailed quality rubrics
- 5 Quality Dimensions:
  1. **Grammar** - Linguistic correctness
  2. **Naturalness** - Authentic Ukrainian (1-5 scale)
  3. **Difficulty** - CEFR-appropriate challenge
  4. **Engagement** - Cultural relevance (1-5 scale)
  5. **Distractors** - Pedagogical soundness (1-5 scale)

### 3. CEFR-Aware Quality Gates
```yaml
B1:
  min_naturalness_avg: 3.5      # Acceptable+
  max_difficulty_inappropriate: 20%
  min_engagement_avg: 3.0       # Neutral+
  min_distractor_quality: 4.0   # Good

B2:
  min_naturalness_avg: 4.0      # Natural
  max_difficulty_inappropriate: 15%
  min_engagement_avg: 3.5
  min_distractor_quality: 4.2

C1:
  min_naturalness_avg: 4.5      # Highly natural
  max_difficulty_inappropriate: 10%
  min_engagement_avg: 4.0
  min_distractor_quality: 4.5

C2:
  min_naturalness_avg: 4.8      # Near-native
  max_difficulty_inappropriate: 5%
  min_engagement_avg: 4.5
  min_distractor_quality: 5.0
```

## Architecture Decision: Merge vs Separate Command

**DECISION:** ✅ **CONFIRMED - Merge into `/review-content`**

**Rationale:**
- Avoids duplication (Section 8 already covers "Activity Quality")
- Single comprehensive content review
- Consistent workflow
- User confirmed: "merge yes"

**Implementation:**
- Expand `/review-content` Section 8 with:
  - 8a. Grammar & Linguistic Accuracy → Add naturalness rubric (1-5 scale)
  - 8b. Answer Validity & Difficulty → Add difficulty calibration (CEFR-aware)
  - 8c. Distractor Quality → Add detailed analysis rubric (1-5 scale)
  - 8d. Engagement → NEW subsection (1-5 scale)
  - 8e. Variety → NEW subsection (mechanical repetition detection)
- Delete `claude_extensions/commands/activity-validate.md` (functionality absorbed)
- Keep `scripts/audit/checks/activity_quality.py` module for deterministic checks

## Implementation Plan

### Phase 1: ✅ COMPLETE (Analysis & Initial Implementation)
- ✅ Created analysis document: `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md`
- ✅ Created deterministic checks: `scripts/audit/checks/activity_quality.py`
- ✅ Created command draft: `claude_extensions/commands/activity-validate.md` (may deprecate)

### Phase 2: Command Integration (ASSIGN TO CLAUDE AGENT)
**Decision:** ✅ Confirmed - Merge into `/review-content`

**Tasks:**
1. Expand `/review-content` Section 8 with detailed rubrics:
   - **8a. Grammar & Linguistic Accuracy** - Add naturalness rubric (1-5 scale)
     - 1 = Robotic/translated, 2 = Unnatural, 3 = Acceptable, 4 = Natural, 5 = Highly natural
     - Include deterministic checks: pronoun overuse, calques, discourse markers
   - **8b. Answer Validity & Difficulty** - Add CEFR calibration
     - too_easy | appropriate | too_hard per CEFR level
     - Include deterministic checks: word length heuristics, advanced vocabulary markers
   - **8c. Distractor Quality** - Add detailed analysis rubric (1-5 scale)
     - 1 = Nonsense, 2 = Weak, 3 = Acceptable, 4 = Good, 5 = Excellent
     - Include deterministic checks: word class matching, length plausibility, root relation
   - **8d. Engagement** - NEW subsection (1-5 scale)
     - 1 = Boring/generic, 2 = Low, 3 = Neutral, 4 = Engaging, 5 = Highly engaging
     - Focus: cultural relevance, contemporary topics
   - **8e. Variety** - NEW subsection
     - Mechanical repetition detection, sentence structure diversity
     - Include deterministic checks: variety score (0-100%)
2. Add CEFR-specific quality gates to command:
   - B1: 3.5 naturalness, 20% difficulty tolerance, 3.0 engagement, 4.0 distractors
   - B2: 4.0 naturalness, 15% difficulty tolerance, 3.5 engagement, 4.2 distractors
   - C1: 4.5 naturalness, 10% difficulty tolerance, 4.0 engagement, 4.5 distractors
   - C2: 4.8 naturalness, 5% difficulty tolerance, 4.5 engagement, 5.0 distractors
3. Delete `claude_extensions/commands/activity-validate.md` (functionality absorbed)
4. Deploy: `npm run claude:deploy`

**Deliverables:**
- Updated `claude_extensions/commands/review-content.md` (expanded Section 8)
- Deleted `claude_extensions/commands/activity-validate.md`
- Deployment complete

### Phase 3: Queue Generation Script (ASSIGN TO AGENT)
**Tasks:**
1. Create `scripts/audit/generate_activity_quality_queue.py`
2. Features:
   - Extract activities from module markdown
   - Run deterministic checks (`activity_quality.py`)
   - Generate queue file: `curriculum/l2-uk-en/{level}/queue/{module}-quality.yaml`
   - Pre-populate with automatic analysis (variety, difficulty, distractors)
   - Leave semantic fields (naturalness, engagement) for manual validation

**Input:** Module markdown file
**Output:** Queue YAML with structure:
```yaml
module: "01-passive-voice-system"
level: "B2"
activities:
  - id: "quiz-passive-forms"
    type: "quiz"
    text: "Який варіант правильний?"

    # Deterministic checks (auto-populated)
    deterministic_checks:
      variety_score: 85
      vocabulary_difficulty: "appropriate"
      cognitive_load: "medium"
      naturalness_issues:
        - "Overuse of pronouns: 12 in 6 sentences (2.0 per sentence)"
      distractor_quality: 4

    # Manual validation (human fills this)
    naturalness: null        # 1-5 scale
    difficulty: null         # too_easy | appropriate | too_hard
    engagement: null         # 1-5 scale
    distractor_score: null   # 1-5 scale
    issues: []
    suggestions: []
```

**Deliverables:**
- `scripts/audit/generate_activity_quality_queue.py`
- Add npm script: `"activity:queue": "python scripts/audit/generate_activity_quality_queue.py"`

### Phase 4: Finalization Script (ASSIGN TO AGENT)
**Tasks:**
1. Create `scripts/audit/finalize_activity_quality.py`
2. Features:
   - Read completed queue file (manual validation done)
   - Calculate quality scores per dimension
   - Evaluate CEFR-specific quality gates
   - Generate audit report: `curriculum/l2-uk-en/{level}/audit/{module}-quality.md`
   - Report format:
     - Quality scores (naturalness avg, engagement avg, etc.)
     - Gate evaluation (PASS/FAIL per dimension)
     - Issues summary (grouped by severity)
     - Recommendations

**Deliverables:**
- `scripts/audit/finalize_activity_quality.py`
- Add npm script: `"activity:finalize": "python scripts/audit/finalize_activity_quality.py"`

### Phase 5: Audit Pipeline Integration (ASSIGN TO AGENT)
**Tasks:**
1. Update `scripts/audit/gates.py`:
   - Add `activity_quality_gate()` function
   - Evaluate quality thresholds per CEFR level
2. Update `scripts/audit/core.py`:
   - Integrate `activity_quality.py` deterministic checks
   - Add quality gate to main audit flow
   - Update gate results dict
3. Update `scripts/audit/config.py`:
   - Add quality thresholds per level (B1/B2/C1/C2)

**Deliverables:**
- Modified `scripts/audit/gates.py`
- Modified `scripts/audit/core.py`
- Modified `scripts/audit/config.py`
- Test: Run audit on B2 sample module, verify quality checks appear

### Phase 6: Testing & Documentation (ASSIGN TO AGENT)
**Tasks:**
1. **Test workflow:**
   - Generate quality queue for B2 M01
   - Manually validate 2-3 activities
   - Run finalization script
   - Verify audit report generated correctly
2. **Update documentation:**
   - `docs/SCRIPTS.md` - Add quality validation workflow
   - `docs/ARCHITECTURE.md` - Document quality validation architecture
   - `CLAUDE.md` - Add quality validation to workflow
3. **Deploy:**
   - `npm run claude:deploy`

**Deliverables:**
- Test results (sample queue + audit report)
- Updated documentation (3 files)
- Deployed commands

## Acceptance Criteria

- [ ] **Phase 2:** `/review-content` Section 8 expanded with 5 quality dimensions OR `/activity-validate` finalized (decision made)
- [ ] **Phase 3:** Queue generation script creates valid YAML with deterministic checks pre-populated
- [ ] **Phase 4:** Finalization script evaluates quality gates and generates audit reports
- [ ] **Phase 5:** Audit pipeline runs deterministic quality checks automatically
- [ ] **Phase 6:** Full workflow tested on B2 module, documentation updated

**Quality Gates Must Evaluate:**
- Naturalness avg (1-5 scale)
- Difficulty appropriateness (% too_easy/too_hard)
- Engagement avg (1-5 scale)
- Distractor quality avg (1-5 scale)
- Variety score (0-100%)

**Manual Validation Rubrics Must Include:**
- Naturalness scoring guide (1=robotic, 5=highly natural)
- Difficulty calibration guide (per CEFR level)
- Engagement scoring guide (1=boring, 5=highly engaging)
- Distractor quality guide (1=nonsense, 5=pedagogically sound)

## Dependencies

- ✅ `scripts/audit/checks/activity_quality.py` (Phase 1 complete)
- ✅ `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md` (Phase 1 complete)
- Requires decision: Merge vs separate command (Phase 2)

## References

- **Analysis document:** `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md`
- **Deterministic checks:** `scripts/audit/checks/activity_quality.py`
- **Existing commands:**
  - `claude_extensions/commands/review-content.md` (Section 8: Activity Quality)
  - `claude_extensions/commands/grammar-validate.md` (workflow pattern)
- **User requirements:** See conversation summary

## Notes

- System uses **manual validation workflow**, NOT automated API calls
- Deterministic checks provide instant feedback, manual validation handles semantic quality
- CEFR-aware thresholds ensure level-appropriate quality expectations
- Queue-based workflow matches existing `/grammar-validate` pattern
- **User explicitly warned against duplication** - prefer merging into `/review-content`
