# Session Summary: Activity Quality Validation Expansion
**Date:** 2026-01-02
**Coordinator:** Claude Sonnet (C1-a)
**Status:** ✅ COMPLETE - Issue #355 Created & Delegated

## Session Overview

User requested expansion of grammar validation system (`/grammar-validate`) to include **activity quality validation** beyond grammatical correctness. Focus on detecting:
- Robotic/unnatural phrasing
- Inappropriate difficulty for CEFR level
- Mechanical/repetitive patterns
- Low engagement content
- Poor distractor quality

## Primary Request (User's Words)

> "where they are working i need you to reivew the /grammar-validete prompt in claude_extentions, adjust it our pipline, indentify gaps an problems and make sure we can properly use it to identify badly created activites, we have to make sure that the activites make sense for humans and dont have robotic feelings and they very, not too hard, not too easy, amybe we need to adjust activity params as well."

## Key User Feedback During Implementation

1. **"we dont use api"** - System uses MANUAL validation, NOT automated API calls
2. **"we have review-content and grammar-validate we havve to be carefull not to duplicate features, maybe it would make sense to inspect if we should compbine them ?"** - Avoid creating duplicate functionality
3. **"no you should create an issue and implemenation plan and delegate it, our agents are waitijg for you and to assing tasks for them"** - Create issue and delegate, don't implement myself

## Work Completed

### Phase 1: Analysis & Foundation ✅ COMPLETE

**Analysis Document Created:**
- File: `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md` (600+ lines)
- Content: Comprehensive analysis with:
  - 7 identified gaps in current validation system
  - Multi-dimensional validator architecture proposal
  - 6-phase implementation plan
  - CEFR-aware quality thresholds
  - Migration strategy

**7 Identified Gaps:**
1. **No Naturalness Validation** - Cannot detect robotic/translated phrasing
2. **No Difficulty Calibration** - Activities may be too easy/hard for level
3. **No Variety Detection** - Mechanical sentence patterns not flagged
4. **No Pedagogical Coherence** - Activities may not test module objectives
5. **No Engagement Validation** - Boring vs culturally relevant content
6. **No Distractor Quality** - Nonsense options vs plausible errors
7. **Pipeline Integration Gaps** - Manual workflow needs queue-based system

**Deterministic Quality Checks Module:**
- File: `scripts/audit/checks/activity_quality.py` (383 lines)
- Functions implemented:
  ```python
  def analyze_sentence_variety(sentences: List[str]) -> Dict
      # Detect repetitive sentence patterns
      # Returns variety score (0-100%) and flags for mechanical repetition

  def estimate_vocabulary_difficulty(text: str, level_code: str) -> str
      # Estimate if vocabulary difficulty matches level
      # Returns: 'too_easy', 'appropriate', 'too_hard'
      # Uses word length heuristics + level-specific markers

  def analyze_distractor_quality(
      correct_answer: str,
      distractors: List[str],
      activity_type: str,
      level_code: str
  ) -> Dict
      # Analyze distractor quality for MC activities
      # Checks word class matching, plausibility, difficulty
      # Returns quality score (1-5) and specific issues

  def check_natural_ukrainian_markers(text: str) -> Dict
      # Check for natural Ukrainian vs robotic patterns
      # Detects pronoun overuse, calques, discourse markers
      # Returns naturalness issues and suggestions

  def estimate_cognitive_load(
      text: str,
      activity_type: str,
      level_code: str
  ) -> str
      # Estimate cognitive load: low, medium, high
      # Combines activity complexity + text complexity

  def validate_activity_quality_deterministic(
      text, activity_type, level_code, options, correct_answer
  ) -> Dict
      # Run all deterministic quality checks on an activity
      # Returns comprehensive quality assessment without API calls
  ```

**Validation Command Created (Draft):**
- File: `claude_extensions/commands/activity-validate.md`
- Features:
  - 5 quality dimensions (grammar, naturalness, difficulty, engagement, distractors)
  - CEFR-aware quality gates (B1: 3.5 naturalness, B2: 4.0, C1: 4.5, C2: 4.8)
  - Manual validation rubrics embedded
  - Queue-based workflow pattern
- **Status:** May be deprecated if merging into `/review-content`

### Phase 2: Issue Creation & Delegation ✅ COMPLETE

**Issue #355 Created:**
- File: `docs/dev/issues/355-activity-quality-validation.md`
- Content:
  - Problem statement (7 gaps identified)
  - Proposed solution (hybrid validation approach)
  - Architecture decision required (merge vs separate)
  - 6-phase implementation plan
  - Acceptance criteria
  - Deliverables per phase

**Agent Coordination Updated:**
- File: `docs/dev/AGENT_COORDINATION.md`
- Changes:
  - Added Issue #355 to tracking
  - Updated Analysis Documents section
  - Added Priority 5 agent assignment slot
  - Estimated effort: 6-8 hours (phases 2-6)

## Architecture Decision Required

**DECISION:** Merge into `/review-content` OR keep separate `/activity-validate`?

### Recommendation: Merge into `/review-content` ✓

**Rationale:**
- User feedback: "we havve to be carefull not to duplicate features"
- `/review-content` Section 8 already covers "Activity Quality":
  - Structural integrity
  - Answer validity ("only ONE correct answer exists linguistically")
  - Linguistic accuracy
  - Pedagogical alignment
  - Distractor plausibility
- Single comprehensive review workflow
- Consistent with existing patterns

**Implementation if merged:**
- Expand `/review-content` Section 8 with detailed rubrics:
  - 8a. Grammar & Linguistic Accuracy → Add naturalness rubric (1-5 scale)
  - 8b. Answer Validity & Difficulty → Add CEFR calibration
  - 8c. Distractor Quality → Add detailed analysis rubric (1-5 scale)
  - 8d. Engagement → NEW subsection (1-5 scale)
  - 8e. Variety → NEW subsection (mechanical repetition detection)
- Delete `/activity-validate` command
- Keep `activity_quality.py` module for deterministic checks

## Implementation Plan (6 Phases)

### Phase 1: ✅ COMPLETE (This Session)
- Analysis document created
- Deterministic checks module created
- Command draft created

### Phase 2: ⏳ PENDING (Command Integration)
**Assigned to:** TBD (awaiting agent assignment)
**Tasks:**
1. Decide: merge into `/review-content` or keep separate?
2. If merge (recommended):
   - Expand `/review-content` Section 8 with detailed rubrics
   - Delete `claude_extensions/commands/activity-validate.md`
3. If separate:
   - Finalize `/activity-validate` command
   - Clearly differentiate from `/review-content`
4. Deploy: `npm run claude:deploy`

**Deliverables:**
- Updated `claude_extensions/commands/review-content.md` OR finalized `activity-validate.md`

### Phase 3: ⏳ PENDING (Queue Generation Script)
**Assigned to:** TBD
**Tasks:**
1. Create `scripts/audit/generate_activity_quality_queue.py`
2. Features:
   - Extract activities from module markdown
   - Run deterministic checks (`activity_quality.py`)
   - Generate queue file: `curriculum/l2-uk-en/{level}/queue/{module}-quality.yaml`
   - Pre-populate with automatic analysis (variety, difficulty, distractors)
   - Leave semantic fields (naturalness, engagement) for manual validation

**Output format:**
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

### Phase 4: ⏳ PENDING (Finalization Script)
**Assigned to:** TBD
**Tasks:**
1. Create `scripts/audit/finalize_activity_quality.py`
2. Features:
   - Read completed queue file (manual validation done)
   - Calculate quality scores per dimension
   - Evaluate CEFR-specific quality gates
   - Generate audit report: `curriculum/l2-uk-en/{level}/audit/{module}-quality.md`

**Quality Gates (CEFR-aware):**
```python
B1: {
    'min_naturalness_avg': 3.5,      # Acceptable+
    'max_difficulty_inappropriate': 0.20,  # 20%
    'min_engagement_avg': 3.0,       # Neutral+
    'min_distractor_quality': 4.0    # Good
}
B2: {
    'min_naturalness_avg': 4.0,      # Natural
    'max_difficulty_inappropriate': 0.15,
    'min_engagement_avg': 3.5,
    'min_distractor_quality': 4.2
}
C1: {
    'min_naturalness_avg': 4.5,      # Highly natural
    'max_difficulty_inappropriate': 0.10,
    'min_engagement_avg': 4.0,
    'min_distractor_quality': 4.5
}
C2: {
    'min_naturalness_avg': 4.8,      # Near-native
    'max_difficulty_inappropriate': 0.05,
    'min_engagement_avg': 4.5,
    'min_distractor_quality': 5.0
}
```

**Deliverables:**
- `scripts/audit/finalize_activity_quality.py`
- Add npm script: `"activity:finalize": "python scripts/audit/finalize_activity_quality.py"`

### Phase 5: ⏳ PENDING (Audit Integration)
**Assigned to:** TBD
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

### Phase 6: ⏳ PENDING (Testing & Documentation)
**Assigned to:** TBD
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

## Files Created This Session

1. ✅ `docs/dev/issues/355-activity-quality-validation.md` (detailed issue)
2. ✅ `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md` (600+ lines analysis)
3. ✅ `scripts/audit/checks/activity_quality.py` (383 lines deterministic checks)
4. ✅ `claude_extensions/commands/activity-validate.md` (command draft - may deprecate)
5. ✅ `docs/dev/SESSION_2026-01-02_ACTIVITY_QUALITY.md` (this summary)

## Files Modified This Session

1. ✅ `docs/dev/AGENT_COORDINATION.md` (added Issue #355 tracking)

## Errors and Course Corrections

### Error 1: Assumed API-based validation
**User feedback:** "we dont use api"
**Fix:** Pivoted to manual validation workflow + deterministic code checks

### Error 2: Created duplicate functionality
**User feedback:** "we have review-content and grammar-validate we havve to be carefull not to duplicate features"
**Fix:** Recommended merging into `/review-content` Section 8

### Error 3: Started implementing instead of delegating
**User feedback:** "no you should create an issue and implemenation plan and delegate it"
**Fix:** Created Issue #355 and delegated to agents (this session)

## Quality Dimensions Defined

### 1. Grammar (Linguistic Correctness)
- Russianisms, Surzhyk, calques
- Case agreement, aspect usage
- **Source:** Existing `/grammar-validate` + Ukrainian grammar validator prompt

### 2. Naturalness (1-5 scale)
**Rubric:**
- 1 = Robotic/translated (sounds like English)
- 2 = Unnatural (grammatically correct but awkward)
- 3 = Acceptable (functional but not native-like)
- 4 = Natural (authentic Ukrainian phrasing)
- 5 = Highly natural (idiomatic, native-like)

**Deterministic checks:**
- Pronoun overuse detection
- Calque identification ("я маю" → "у мене є")
- Discourse marker presence (ну, от, взагалі)

### 3. Difficulty (CEFR-appropriate)
**Categories:**
- `too_easy` - Below level expectations
- `appropriate` - Matches level
- `too_hard` - Above level expectations

**Deterministic checks:**
- Word length heuristics (A1: 4-8 letters, B2: 7-13, C2: 9-16)
- Advanced vocabulary markers (C1/C2 words in lower levels)
- Cognitive load estimation

### 4. Engagement (1-5 scale)
**Rubric:**
- 1 = Boring/generic (could be any language textbook)
- 2 = Low engagement (functional but dull)
- 3 = Neutral (acceptable but unremarkable)
- 4 = Engaging (culturally relevant, interesting)
- 5 = Highly engaging (memorable, motivating)

**Focus:** Cultural relevance, contemporary topics, real-world context

### 5. Distractors (1-5 scale for MC activities)
**Rubric:**
- 1 = Nonsense (random unrelated words)
- 2 = Weak (obviously wrong, different word class)
- 3 = Acceptable (plausible but not pedagogically targeted)
- 4 = Good (same word class, plausible errors)
- 5 = Excellent (pedagogically sound, common learner errors)

**Deterministic checks:**
- Word class matching (verb endings, noun endings, adjective endings)
- Length plausibility (similar character counts)
- Root relation (related forms vs random words)

## CEFR-Aware Quality Thresholds

| Level | Min Naturalness Avg | Max Difficulty Inappropriate | Min Engagement Avg | Min Distractor Quality |
|-------|---------------------|------------------------------|--------------------|-----------------------|
| **B1** | 3.5 (acceptable+) | 20% | 3.0 (neutral+) | 4.0 (good) |
| **B2** | 4.0 (natural) | 15% | 3.5 | 4.2 |
| **C1** | 4.5 (highly natural) | 10% | 4.0 | 4.5 |
| **C2** | 4.8 (near-native) | 5% | 4.5 | 5.0 (excellent) |

**Rationale:**
- Lower levels (B1) = More tolerance for acceptable/functional quality
- Higher levels (C2) = Near-native naturalness expected
- Difficulty tolerance decreases with level (C2 must be precisely calibrated)

## Next Steps for Agents

1. **Review Issue #355** - `docs/dev/issues/355-activity-quality-validation.md`
2. **Decide architecture** - Merge into `/review-content` or keep separate?
3. **Implement Phase 2** - Command integration (expand Section 8 or finalize new command)
4. **Implement Phase 3** - Queue generation script
5. **Implement Phase 4** - Finalization script
6. **Implement Phase 5** - Audit pipeline integration
7. **Implement Phase 6** - Testing & documentation

## Success Metrics

**When Issue #355 is complete:**
- ✅ Manual validation rubrics embedded in command (5 dimensions)
- ✅ Queue generation script pre-populates deterministic checks
- ✅ Finalization script evaluates CEFR-specific quality gates
- ✅ Audit pipeline runs deterministic checks automatically
- ✅ Full workflow tested on B2 sample module
- ✅ Documentation updated (3 files)
- ✅ No duplication between `/grammar-validate` and `/review-content`

**Quality validation coverage:**
- Grammar correctness → `/grammar-validate` (existing)
- Activity quality (5 dimensions) → `/review-content` Section 8 (expanded)
- Deterministic checks → `activity_quality.py` (automatic)
- Semantic validation → Manual queue-based workflow

## Context for Agents

**Full context available in:**
- `docs/dev/issues/355-activity-quality-validation.md` (issue document)
- `docs/dev/ACTIVITY_QUALITY_VALIDATION_ANALYSIS.md` (analysis)
- `scripts/audit/checks/activity_quality.py` (deterministic checks code)
- `claude_extensions/commands/review-content.md` (existing command to expand)
- `claude_extensions/commands/grammar-validate.md` (workflow pattern reference)

**Key principles:**
- **Manual validation** - NOT automated API calls
- **CEFR-aware** - Different thresholds per level
- **Avoid duplication** - Merge with existing commands where possible
- **Queue-based workflow** - Matches `/grammar-validate` pattern
- **Hybrid approach** - Deterministic checks (free) + manual validation (detailed rubrics)

---

**Session Status:** ✅ COMPLETE - Ready for agent assignment
