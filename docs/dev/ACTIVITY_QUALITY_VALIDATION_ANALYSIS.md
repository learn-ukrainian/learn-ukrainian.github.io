# Activity Quality Validation Analysis & Expansion Plan

**Date:** 2026-01-02
**Context:** User Request - Expand `/grammar-validate` to comprehensive activity quality validation
**Goal:** Ensure activities feel natural, have appropriate difficulty, and make sense for human learners

---

## Current State Analysis

### 1. Grammar Validation System (Existing)

**Components:**
- **Command:** `claude_extensions/commands/grammar-validate.md` (460 lines)
- **LLM Prompt:** `scripts/audit/ukrainian_grammar_validator_prompt.md` (304 lines)
- **Integration:** Gemini 2.0 Flash API with JSON-structured output

**What It Validates:**
```yaml
Grammar Correctness:
  - No Russianisms/Surzhyk (кушать → їсти)
  - No Calques ("робити сенс" → "мати сенс")
  - Case government errors
  - Aspect correctness
  - Motion verb prefixes (B1+)
  - Agreement (subject-verb, adjective-noun)

Pedagogical Awareness:
  - Level-appropriate expectations (A1-A2 vs B1-B2 vs C1-C2)
  - Intentional simplifications for teaching
  - Error vs pedagogical choice distinction

Output Format:
  - is_real_error: bool
  - error_type: russianism | calque | case_error | aspect_error | etc.
  - severity: critical | minor | pedagogical_ok | style_note
  - confidence: 0.7-1.0 (threshold: 0.7 for flagging)
```

**Activity Types Covered:**
- error-correction (validates error/answer pairs)
- fill-in (validates complete sentences)
- cloze (validates passages)
- unjumble (validates answer sentences)
- quiz (validates questions/options)
- translate (validates Ukrainian sentences)
- true-false (validates statements)

**Current Workflow:**
```bash
/module-create → /grammar-validate → /review-content → /module-stage-4
```

**Integration Points:**
- Queue files: `{level}/queue/{module}-grammar.yaml`
- Summary report: `{level}/audit/{module}-grammar.yaml`
- Used by: Module stage 4 (review & fix)

---

### 2. Audit Pipeline (Existing - scripts/audit/core.py)

**Gates System:**
```python
results = {
    'words': word_count_gate,          # Core content length
    'activities': activity_count_gate,  # Minimum activities
    'density': items_per_activity_gate, # Items per activity
    'unique_types': variety_gate,       # Activity type diversity
    'priority': priority_types_gate,    # Must-have activity types
    'engagement': engagement_boxes,     # Did You Know, etc.
    'audio': audio_links,              # Pronunciation audio
    'vocab': vocab_rows,               # Vocabulary count
    'structure': required_sections,    # Summary, Vocabulary
    'lint': markdown_format,           # Syntax errors
    'pedagogy': pedagogical_rules,     # Teaching quality
    'immersion': ukrainian_percentage, # Ukrainian vs English
    'richness': content_quality,       # B1+ richness scoring
    'grammar': grammar_validation      # Grammar queue status
}
```

**Pedagogical Checks (Existing):**
```python
check_markdown_format()          # Syntax issues
check_vocab_table_format()       # Vocabulary table structure
check_vocab_matches_plan()       # Curriculum plan compliance
check_metalanguage_scaffolding() # Grammar terms in vocab
check_activity_ukrainian_content() # Activities not all-English
check_resources_placement()      # Resources before activities
check_unjumble_word_match()     # Unjumble solvability
check_activity_header_format()  # Activity header syntax
check_content_quality()         # LLM-based content quality
```

**Richness Scoring (B1+ only):**
```python
calculate_richness_score() → {
    'score': 0-100,
    'threshold': 60-80 depending on type,
    'flags': ['repetitive_structure', 'sparse_examples', etc.]
}
```

---

### 3. Activity Schema (Existing - ACTIVITY-MARKDOWN-REFERENCE.md)

**Current Requirements:**

| Level | Activities | Items/Activity | Types | Complexity |
|-------|------------|----------------|-------|------------|
| A1 | 8+ | 5+ | 4+ | Basic (simple sentences) |
| A2 | 10+ | 6+ | 5+ | Elementary (compound sentences) |
| B1 | 12+ | 8-14+ | 5+ | Intermediate (natural phrasing) |
| B2 | 14+ | 10-16+ | 5+ | Advanced (nuanced options) |
| C1 | 16+ | 12-18+ | 5+ | Native-like (stylistic variation) |

**Activity Complexity Rules (from core.py):**
```python
ACTIVITY_COMPLEXITY = {
    'quiz': {
        'A1': {'min_items': 5},
        'A2': {'min_items': 6},
        'B1': {'min_items': 8},
        'B2': {'min_items': 10}
    },
    'fill-in': {
        'B1': {'min_items': 12, 'min_words': 8},
        'B2': {'min_items': 14, 'min_words': 10}
    },
    'error-correction': {
        'A2': {'min_items': 6},
        'B1': {'min_items': 8},
        'B2': {'min_items': 10}
    },
    # ... etc
}
```

---

## Gaps & Problems Identified

### 1. **No Naturalness Validation**
**Problem:** Activities can be grammatically correct but feel robotic or unnatural.

**Examples:**
```yaml
# ROBOTIC (grammatically correct but awkward):
quiz_question: "Яке слово є правильним для завершення речення?"
options: ["слово_а", "слово_б", "слово_в", "слово_г"]

# NATURAL:
quiz_question: "Як правильно сказати?"
options: ["Я їду до Львова", "Я їжджу до Львова", ...]
```

**Gap:** No check for:
- Conversational tone in quiz questions
- Real-world context in examples
- Natural Ukrainian phrasing vs calques from English pedagogy

---

### 2. **No Difficulty Calibration**
**Problem:** Activities marked as "B1" might be too easy (A2 level) or too hard (B2 level).

**Examples:**
```yaml
# TOO EASY for B1 (this is A2):
fill-in: "Я ___ студент."  # Obviously "є"
options: ["є", "був", "буду", "будеш"]

# TOO HARD for B1 (this is B2+):
fill-in: "Якби я ___ багатим, я б купив той будинок."
options: ["був", "буду", "є", "був би"]  # Requires subjunctive mood
```

**Gap:** No check for:
- Vocabulary difficulty vs level
- Grammar complexity vs level targets
- Cognitive load (too many new concepts at once)

---

### 3. **No Variety/Repetition Detection**
**Problem:** Activities can follow repetitive patterns that feel mechanical.

**Examples:**
```yaml
# REPETITIVE (all sentences start the same):
1. Я їду до Києва.
2. Я їду до Львова.
3. Я їду до Одеси.
4. Я їду до Харкова.

# VARIED (different subjects, verbs, contexts):
1. Я їду до Києва на потязі.
2. Вона летить до Львова завтра.
3. Ми приїхали до Одеси вчора.
4. Вони подорожують до Харкова щомісяця.
```

**Gap:** No check for:
- Sentence structure variety
- Vocabulary diversity
- Context diversity (not all about one topic)

---

### 4. **No Pedagogical Coherence Validation**
**Problem:** Activities might not align with module's learning objectives.

**Examples:**
```yaml
# INCOHERENT (module teaches dative, activity tests accusative):
module_focus: "Dative Case"
error-correction: "Я бачу студент." → "студента"  # This is accusative!

# COHERENT:
module_focus: "Dative Case"
error-correction: "Я даю книгу мій друг." → "моєму другу"
```

**Gap:** No check for:
- Activity grammar matches module grammar
- Activity vocabulary uses module vocabulary
- Progressive difficulty within activities section

---

### 5. **No Engagement/Interest Validation**
**Problem:** Activities can be boring or disconnected from learner interests.

**Examples:**
```yaml
# BORING (generic, no context):
translate: "The table is big."

# ENGAGING (cultural context, interesting):
translate: "Kyiv's metro is one of the deepest in the world."
```

**Gap:** No check for:
- Cultural relevance
- Interesting topics (not just "the book is on the table")
- Age-appropriate content (adult learners)

---

### 6. **No Distractor Quality Validation**
**Problem:** Quiz/fill-in options can have obvious wrong answers (bad distractors).

**Examples:**
```yaml
# POOR DISTRACTORS (too obvious):
question: "Як правильно: Я ___ до Києва."
options:
  - їду      # correct
  - стіл     # NONSENSE - not even a verb!
  - зелений  # NONSENSE - adjective
  - книга    # NONSENSE - noun

# GOOD DISTRACTORS (plausible wrong answers):
question: "Як правильно: Я ___ до Києва."
options:
  - їду      # correct (motion toward, unidirectional)
  - їжджу    # common mistake (habitual, not single trip)
  - йду      # common mistake (on foot, not by vehicle)
  - піду     # wrong tense (will go)
```

**Gap:** No check for:
- Distractors are plausible (same word class)
- Distractors target common errors
- Distractors are challenging but fair

---

### 7. **Pipeline Integration Gaps**
**Problem:** Grammar validation runs separately, not integrated with audit gates.

**Current state:**
```bash
# Manual workflow:
/module-create
/grammar-validate  # Runs separately, creates queue file
/review-content    # Manual review
/module-stage-4    # Fix issues

# Result: No automated quality gates
```

**Ideal state:**
```bash
npm run pipeline l2-uk-en b1 52  # Includes activity quality validation
  → audit_module.py
    → Grammar validation (existing)
    → Naturalness validation (NEW)
    → Difficulty validation (NEW)
    → Variety validation (NEW)
    → Coherence validation (NEW)
    → Engagement validation (NEW)
    → Distractor quality (NEW)
  → Generate if all gates pass
```

---

## Proposed Solution: Multi-Dimensional Activity Quality Validator

### Architecture

```
Activity Quality Validator (Expanded System)
├── Grammar Validator (existing - Gemini API)
│   ├── Russianisms/Surzhyk
│   ├── Calques
│   ├── Case/Aspect errors
│   └── Level-appropriate grammar
│
├── Naturalness Validator (NEW - Gemini API)
│   ├── Conversational tone
│   ├── Real-world context
│   ├── Natural phrasing
│   └── Authentic Ukrainian usage
│
├── Difficulty Calibrator (NEW - Gemini API + heuristics)
│   ├── Vocabulary difficulty
│   ├── Grammar complexity
│   ├── Cognitive load
│   └── CEFR alignment
│
├── Variety Detector (NEW - deterministic + Gemini)
│   ├── Sentence structure diversity
│   ├── Vocabulary reuse
│   ├── Context variety
│   └── Pattern repetition
│
├── Coherence Validator (NEW - Gemini API)
│   ├── Grammar alignment (activity ↔ module)
│   ├── Vocabulary alignment
│   ├── Learning objective fit
│   └── Progressive difficulty
│
├── Engagement Scorer (NEW - Gemini API)
│   ├── Cultural relevance
│   ├── Topic interest
│   ├── Age appropriateness
│   └── Real-world applicability
│
└── Distractor Analyzer (NEW - Gemini API)
    ├── Plausibility (same word class)
    ├── Target common errors
    ├── Appropriate difficulty
    └── No nonsense options
```

---

## Implementation Plan

### Phase 1: Expand Grammar Validator Prompt (1-2 hours)

**Current Gemini Prompt:** `scripts/audit/ukrainian_grammar_validator_prompt.md`

**Additions:**

```markdown
## NEW VALIDATION DIMENSIONS

### 1. Naturalness Assessment
Evaluate if the sentence/question sounds natural in Ukrainian:
- ✅ Natural: "Скільки коштує ця книга?" (conversational)
- ❌ Unnatural: "Яка є ціна цієї книги?" (overly formal/English-like)

Output:
- naturalness_score: 1-5 (5 = perfectly natural)
- unnaturalness_type: formal_register | calque_phrasing | robotic_structure
- natural_alternative: "suggested rewrite"

### 2. Difficulty Calibration
Assess if grammar/vocabulary matches CEFR level:
- A1-A2: Simple present/past, basic vocab
- B1: Aspect, cases, compound sentences
- B2: Passive, participles, advanced syntax
- C1-C2: Stylistic nuance, idioms, registers

Output:
- difficulty_level: A1 | A2 | B1 | B2 | C1 | C2
- difficulty_appropriateness: too_easy | appropriate | too_hard
- difficulty_reason: "uses subjunctive mood (B2+), module is B1"

### 3. Distractor Quality (for quiz/fill-in/error-correction)
Evaluate if wrong options are plausible:
- ✅ Good: Similar word class, targets common error
- ❌ Bad: Different word class, nonsense

Output:
- distractor_quality: 1-5 (5 = excellent distractors)
- distractor_issues: ["nonsense_option", "too_obvious"]
- distractor_suggestions: ["replace 'книга' with 'йду' (wrong motion verb)"]

### 4. Context Relevance
Evaluate if example is interesting/culturally relevant:
- ✅ Relevant: "Київський метрополітен – один з найглибших у світі."
- ❌ Generic: "Стіл є великий."

Output:
- context_score: 1-5 (5 = highly engaging)
- context_type: cultural | practical | generic | boring
- context_suggestion: "add cultural/historical context"
```

**Integration:**
- Expand JSON output schema to include new dimensions
- Keep confidence scoring (0.7 threshold)
- Add severity levels for each dimension

---

### Phase 2: Create Deterministic Variety Detector (2-3 hours)

**New Script:** `scripts/audit/checks/activity_variety.py`

```python
def check_activity_variety(activities: list[dict], level: str) -> list[dict]:
    """
    Detect repetitive patterns in activities.

    Returns violations list with:
    - type: VARIETY_REPETITION
    - severity: warning | error
    - issue: description
    - fix: suggestion
    """
    violations = []

    # 1. Sentence structure variety
    # Extract first 3 words of each sentence → detect repetition
    sentence_starts = defaultdict(int)
    for activity in activities:
        for item in activity.get('items', []):
            sentence = item.get('sentence', '') or item.get('statement', '')
            if sentence:
                start = ' '.join(sentence.split()[:3])
                sentence_starts[start] += 1

    # Flag if >40% start the same way
    total = sum(sentence_starts.values())
    for start, count in sentence_starts.items():
        if count / total > 0.4:
            violations.append({
                'type': 'VARIETY_REPETITION',
                'severity': 'warning',
                'issue': f'{count}/{total} sentences start with "{start}"',
                'fix': f'Vary sentence structure (different subjects/verbs)'
            })

    # 2. Vocabulary reuse
    # Extract all words → flag if <50% unique in activity
    all_words = []
    for activity in activities:
        # Extract words from sentences, questions, etc.
        text = extract_activity_text(activity)
        words = [w.lower() for w in re.findall(r'\b[\u0400-\u04ff]+\b', text)]
        all_words.extend(words)

    unique_ratio = len(set(all_words)) / len(all_words) if all_words else 1.0
    if unique_ratio < 0.5:
        violations.append({
            'type': 'VARIETY_VOCABULARY',
            'severity': 'warning',
            'issue': f'Only {unique_ratio:.0%} unique words across activities',
            'fix': 'Increase vocabulary diversity (use different nouns/verbs)'
        })

    # 3. Context diversity
    # Check if all activities use same topic
    topics = extract_topics(activities)  # Heuristic topic detection
    if len(topics) < 2:
        violations.append({
            'type': 'VARIETY_CONTEXT',
            'severity': 'warning',
            'issue': 'All activities focus on single topic/context',
            'fix': 'Add variety (different settings: home, work, city, etc.)'
        })

    return violations
```

**Integration:**
- Call from `scripts/audit/core.py` in pedagogical checks
- Add to audit report
- Warning-level (not blocking) for first iteration

---

### Phase 3: Create Coherence Validator (2-3 hours)

**New Script:** `scripts/audit/checks/activity_coherence.py`

```python
def check_activity_coherence(
    content: str,
    frontmatter: str,
    activities: list[dict],
    vocab_words: set[str],
    level: str
) -> list[dict]:
    """
    Validate activities align with module learning objectives.
    """
    violations = []

    # 1. Extract module grammar focus
    grammar_match = re.search(r'^grammar:\s*\n((?:\s+-\s+.*\n?)+)', frontmatter, re.MULTILINE)
    if grammar_match:
        grammar_items = re.findall(r'-\s+"?([^"\n]+)"?', grammar_match.group(1))
        module_grammar = set(g.lower() for g in grammar_items)

        # 2. Extract activity grammar (from error-correction, explanations)
        activity_grammar = set()
        for activity in activities:
            if activity.get('type') == 'error-correction':
                for item in activity.get('items', []):
                    explanation = item.get('explanation', '')
                    # Extract grammar terms: "dative case" → "dative"
                    terms = extract_grammar_terms(explanation)
                    activity_grammar.update(terms)

        # 3. Check overlap
        if activity_grammar and not activity_grammar & module_grammar:
            violations.append({
                'type': 'COHERENCE_GRAMMAR_MISMATCH',
                'severity': 'error',
                'issue': f'Activities teach {activity_grammar} but module focuses on {module_grammar}',
                'fix': 'Align activity grammar with module learning objectives'
            })

    # 4. Check vocabulary alignment
    # Activities should use module vocabulary
    activity_vocab = set()
    for activity in activities:
        text = extract_activity_text(activity)
        words = [w.lower() for w in re.findall(r'\b[\u0400-\u04ff]+\b', text)]
        activity_vocab.update(words)

    overlap = activity_vocab & vocab_words
    if overlap and len(overlap) / len(activity_vocab) < 0.3:
        violations.append({
            'type': 'COHERENCE_VOCAB_MISMATCH',
            'severity': 'warning',
            'issue': f'Only {len(overlap)}/{len(activity_vocab)} activity words from module vocabulary',
            'fix': 'Use more vocabulary from the Словник section in activities'
        })

    # 5. Progressive difficulty (first activities easier than last)
    # Use Gemini API to assess difficulty of each activity
    # Flag if difficulty curve is flat or descending

    return violations
```

---

### Phase 4: Update Grammar Validation Command (1 hour)

**File:** `claude_extensions/commands/grammar-validate.md`

**Changes:**

```markdown
## UPDATED WORKFLOW

1. **Extract Activities** (unchanged)
   Parse markdown/YAML → activity items → queue file

2. **Validate Grammar** (unchanged)
   Gemini API → grammar correctness → confidence scoring

3. **NEW: Validate Quality Dimensions**
   Gemini API → naturalness, difficulty, engagement, distractors

4. **NEW: Detect Variety Issues**
   Deterministic analysis → repetition, vocabulary diversity

5. **NEW: Check Coherence**
   Module grammar ↔ activity grammar alignment
   Module vocabulary ↔ activity vocabulary alignment

6. **Generate Summary Report**
   Combined report with all dimensions:
   - grammar_validation: {...}
   - naturalness_validation: {...}
   - difficulty_validation: {...}
   - variety_validation: {...}
   - coherence_validation: {...}
   - engagement_validation: {...}
   - distractor_validation: {...}

## UPDATED OUTPUT FORMAT

```yaml
# {module}-grammar.yaml (expanded to include all dimensions)
module_id: b1-52-abstract-concepts-ideas
level: B1
total_items: 67
validation_timestamp: 2026-01-02T15:30:00Z

summary:
  grammar_passed: 62
  grammar_failed: 5

  naturalness_high: 45      # NEW
  naturalness_medium: 18    # NEW
  naturalness_low: 4        # NEW

  difficulty_appropriate: 58  # NEW
  difficulty_too_easy: 3      # NEW
  difficulty_too_hard: 6      # NEW

  variety_score: 72%          # NEW
  variety_flags: 2            # NEW

  coherence_score: 85%        # NEW
  coherence_violations: 1     # NEW

  engagement_score: 68%       # NEW

  distractor_quality: 4.2/5   # NEW

items:
  - activity: error-correction
    sentence_with_error: "Це важлива концепцію."
    error: "концепцію"
    answer: "концепція"

    # EXISTING
    validate:
      error_is_real_mistake: true
      corrected_sentence_valid: true
      explanation: "Називний після 'це'"
      confidence: 0.95
      error_type: "case_error"
      severity: "minor"

    # NEW DIMENSIONS
    naturalness:
      score: 4
      issues: []
      suggestion: null

    difficulty:
      level: B1
      appropriateness: "appropriate"
      reason: "teaches dative case (B1 curriculum)"

    distractors:
      quality: 5
      issues: []
      suggestions: []

    engagement:
      score: 3
      type: "practical"
      suggestion: "add cultural context (Ukrainian naming conventions)"
```

---

### Phase 5: Update Audit Pipeline Integration (2-3 hours)

**File:** `scripts/audit/core.py`

**Changes:**

```python
# Add new imports
from .checks.activity_variety import check_activity_variety
from .checks.activity_coherence import check_activity_coherence

# In audit_module():

# ... existing code ...

# After pedagogical checks, add quality checks
if yaml_activities or found_activity_types:
    # 1. Variety check (deterministic)
    variety_violations = check_activity_variety(
        yaml_activities or extract_embedded_activities(content),
        level_code
    )
    pedagogical_violations.extend(variety_violations)

    # 2. Coherence check
    coherence_violations = check_activity_coherence(
        content,
        frontmatter_str,
        yaml_activities or extract_embedded_activities(content),
        vocab_words,
        level_code
    )
    pedagogical_violations.extend(coherence_violations)

    # 3. Grammar validation check (existing, but expand report)
    if grammar_summary:
        # NEW: Extract additional quality metrics
        naturalness_avg = grammar_summary.get('naturalness_avg', 0)
        difficulty_issues = grammar_summary.get('difficulty_inappropriate', 0)

        if naturalness_avg < 3.0:  # Average naturalness below 3/5
            pedagogical_violations.append({
                'type': 'ACTIVITY_NATURALNESS_LOW',
                'severity': 'warning',
                'issue': f'Average naturalness score {naturalness_avg:.1f}/5 (target: 3.5+)',
                'fix': 'Rewrite activities with more natural, conversational Ukrainian'
            })

        if difficulty_issues > len(yaml_activities) * 0.2:  # >20% difficulty issues
            pedagogical_violations.append({
                'type': 'ACTIVITY_DIFFICULTY_MISMATCH',
                'severity': 'warning',
                'issue': f'{difficulty_issues} activities at wrong difficulty level',
                'fix': 'Adjust vocabulary/grammar complexity to match module level'
            })
```

**New Gate (optional):**
```python
# Add activity_quality gate
results['activity_quality'] = evaluate_activity_quality(
    grammar_summary,
    variety_violations,
    coherence_violations
)
```

---

### Phase 6: Update Activity Parameters/Schema (1-2 hours)

**Consider adding to activity YAML schema:**

```yaml
# NEW OPTIONAL FIELDS for explicit quality targets

- type: error-correction
  title: Виправте помилки
  difficulty_target: B1          # NEW: Explicit difficulty level
  naturalness_target: high       # NEW: high | medium | low
  engagement_hint: "cultural"    # NEW: cultural | practical | conversational

  items:
    - sentence: "Це важлива концепцію."
      error: "концепцію"
      answer: "концепція"
      options: [....]
      explanation: "..."

      # NEW: Optional quality metadata (for validation tracking)
      _quality:
        naturalness_score: 4
        difficulty_level: B1
        distractor_quality: 5
        validated_at: 2026-01-02
```

**Benefits:**
- Explicit quality expectations per activity
- Can track validation history
- Can regenerate only low-quality activities

---

## Updated Workflow

### Before (Current):
```bash
1. Create module → manually write activities
2. Run audit → check structure, counts
3. /grammar-validate → queue file, manual review
4. Fix issues manually
5. /module-stage-4 → finalize
```

### After (Proposed):
```bash
1. Create module → manually write activities
2. Run audit → structure + counts + variety + coherence
   ├─ Variety violations flagged
   └─ Coherence violations flagged
3. /grammar-validate → comprehensive quality validation
   ├─ Grammar correctness (existing)
   ├─ Naturalness scoring (NEW)
   ├─ Difficulty calibration (NEW)
   ├─ Engagement scoring (NEW)
   └─ Distractor quality (NEW)
4. Review multi-dimensional report
5. Fix issues (clear actionable suggestions)
6. /module-stage-4 → finalize

# OR: Fully automated pipeline
npm run pipeline l2-uk-en b1 52
  → audit (includes all quality checks)
  → PASS/FAIL based on quality gates
  → generate only if quality threshold met
```

---

## Configuration Thresholds

**Add to** `scripts/audit/config.py`:

```python
# Activity Quality Thresholds
ACTIVITY_QUALITY_CONFIG = {
    'A1': {
        'min_naturalness_avg': 2.5,      # Lower bar for beginner activities
        'max_difficulty_inappropriate': 0.30,  # 30% can be slightly off
        'min_variety_score': 40,         # 40% vocabulary diversity
        'min_coherence_score': 60,       # 60% grammar/vocab alignment
        'min_engagement_avg': 2.0,       # Basic engagement
        'min_distractor_quality': 3.0,   # Decent distractors
    },
    'A2': {
        'min_naturalness_avg': 3.0,
        'max_difficulty_inappropriate': 0.25,
        'min_variety_score': 50,
        'min_coherence_score': 70,
        'min_engagement_avg': 2.5,
        'min_distractor_quality': 3.5,
    },
    'B1': {
        'min_naturalness_avg': 3.5,      # Higher bar for intermediate
        'max_difficulty_inappropriate': 0.20,
        'min_variety_score': 60,
        'min_coherence_score': 75,
        'min_engagement_avg': 3.0,
        'min_distractor_quality': 4.0,
    },
    'B2': {
        'min_naturalness_avg': 4.0,      # Near-native naturalness
        'max_difficulty_inappropriate': 0.15,
        'min_variety_score': 65,
        'min_coherence_score': 80,
        'min_engagement_avg': 3.5,
        'min_distractor_quality': 4.2,
    },
    'C1': {
        'min_naturalness_avg': 4.5,      # Native-like naturalness
        'max_difficulty_inappropriate': 0.10,
        'min_variety_score': 70,
        'min_coherence_score': 85,
        'min_engagement_avg': 4.0,
        'min_distractor_quality': 4.5,
    },
}
```

---

## Example Report Output

**Terminal Output:**
```
Auditing curriculum/l2-uk-en/b1/52-abstract-concepts-ideas.md...

✅ GATE: Word Count (1847/1500)
✅ GATE: Activities (12/12)
✅ GATE: Density (67 items across 12 activities)
✅ GATE: Unique Types (6/5)
✅ GATE: Priority Types (all present)
⚠️  GATE: Engagement (4/5 boxes - add 1 more)
✅ GATE: Vocabulary (32/25)
✅ GATE: Structure (summary + vocab present)
✅ GATE: Lint (0 errors)
⚠️  GATE: Pedagogy (3 warnings)
✅ GATE: Immersion (95% Ukrainian)
✅ GATE: Richness (74% > 65% threshold)

🆕 GATE: Activity Quality
  ✅ Grammar: 62/67 passed (5 flagged for review)
  ⚠️  Naturalness: 3.4/5 avg (target: 3.5+)
     → 4 activities below 3.0 (marked in report)
  ✅ Difficulty: 58/67 appropriate (3 too easy, 6 too hard)
  ⚠️  Variety: 58% vocab diversity (target: 60%+)
     → Sentence starts repetitive: "Це важлива..." (12 times)
  ✅ Coherence: 85% grammar alignment
  ⚠️  Engagement: 2.8/5 avg (target: 3.0+)
     → Add cultural/practical context to 8 activities
  ✅ Distractors: 4.1/5 quality

⚠️  PEDAGOGICAL WARNINGS:
  [VARIETY_REPETITION] 12/67 sentences start with "Це важлива..."
     → FIX: Vary sentence structure (different subjects/verbs)

  [ACTIVITY_NATURALNESS_LOW] 4 activities scored <3.0 naturalness
     → Activities: error-correction #3, fill-in #7, quiz #2, translate #5
     → FIX: Rewrite with more conversational Ukrainian

  [ACTIVITY_ENGAGEMENT_LOW] 8 activities lack cultural context
     → FIX: Add Ukrainian cultural examples (philosophy, literature, etc.)

📊 RECOMMENDATION: PROCEED WITH FIXES (Moderate)
  - Fix 3 pedagogical warnings
  - Improve naturalness in 4 activities
  - Add variety to sentence structures
  - Enhance engagement with cultural context

Report: curriculum/l2-uk-en/b1/audit/52-abstract-concepts-ideas-review.md
Grammar Report: curriculum/l2-uk-en/b1/audit/52-abstract-concepts-ideas-grammar.yaml

✅ AUDIT PASSED (with warnings - recommended fixes before publishing)
```

---

## Cost & Performance Estimates

### API Costs (Gemini 2.0 Flash):
```
Current (grammar only):
  ~50-70 items per module → ~$0.02-0.03 per module

Expanded (all dimensions):
  ~50-70 items × 6 validations → ~$0.10-0.15 per module

Full B1 (86 modules):
  86 × $0.12 avg = ~$10.32 total

Full B2 (145 modules):
  145 × $0.12 avg = ~$17.40 total
```

### Runtime:
```
Current:
  ~30-60 seconds per module (Gemini API latency)

Expanded (parallel requests):
  ~45-90 seconds per module (6 dimensions batched)

Can optimize with batch API calls (single request, multiple validations)
```

---

## Migration Strategy

### Phase 1: Non-Breaking Addition (Week 1)
- Expand Gemini prompt to include new dimensions
- Update grammar validation command
- Add variety/coherence checks to audit
- **No breaking changes** - new validations are warnings only

### Phase 2: B1 Testing (Week 2)
- Run expanded validation on all B1 modules (86)
- Collect quality metrics
- Refine thresholds based on real data
- Fix outliers manually

### Phase 3: Gate Integration (Week 3)
- Add activity_quality gate to audit
- Make quality thresholds blocking (fail audit if below)
- Update documentation
- Train on how to fix common issues

### Phase 4: Full Rollout (Week 4)
- Apply to B2, C1, C2
- Backfill A1-A2 with quality validation
- Create quality dashboard (track metrics over time)

---

## Success Metrics

**Before:**
- Grammar validation only
- 247 modules pass audit structurally
- Unknown activity quality (no metrics)

**After:**
- Multi-dimensional quality validation
- 247 modules pass audit + quality gates
- Measurable activity quality:
  - Naturalness: 3.5+ avg
  - Difficulty: 80%+ appropriate
  - Variety: 60%+ diversity
  - Coherence: 75%+ alignment
  - Engagement: 3.0+ avg
  - Distractors: 4.0+ quality

**Learner Impact:**
- Activities feel natural (not robotic)
- Appropriate challenge (not too easy/hard)
- Engaging content (not boring)
- Clear learning progression

---

## Implementation Status (Updated: 2026-01-02)

**Phase 1: Expanded Validation Command** ✅ COMPLETE
- ✅ Created `/activity-validate` command (`claude_extensions/commands/activity-validate.md`)
- ✅ Expanded 5 quality dimensions (grammar, naturalness, difficulty, engagement, distractors)
- ✅ Added CEFR-aware quality gates per level (B1: 3.5 naturalness, B2: 4.0, C1: 4.5, C2: 4.8)
- ✅ Integrated validation workflow and detailed reporting requirements
- ✅ Manual validation guidance with rubrics embedded in command

**Phase 2: Deterministic Quality Checks** ✅ COMPLETE
- ✅ Created `scripts/audit/checks/activity_quality.py` module (code-based, no API)
- ✅ Implemented `analyze_sentence_variety()` - detects repetitive patterns
- ✅ Implemented `estimate_vocabulary_difficulty()` - word length heuristics + level markers
- ✅ Implemented `analyze_distractor_quality()` - word class matching, plausibility checks
- ✅ Implemented `check_natural_ukrainian_markers()` - pronoun overuse, calques, discourse markers
- ✅ Implemented `estimate_cognitive_load()` - activity + text complexity
- ✅ Composite function `validate_activity_quality_deterministic()` runs all checks

**Phase 3: Queue Generation** ⏳ PENDING
- ⏸️ Create `scripts/generate_activity_quality_queue.py`
- ⏸️ Parse activities from markdown/YAML
- ⏸️ Extract sentences, options, metadata
- ⏸️ Output to `queue/{module}-quality.yaml`

**Phase 4: Finalization Script** ⏳ PENDING
- ⏸️ Create `scripts/finalize_activity_quality.py`
- ⏸️ Calculate quality gate scores
- ⏸️ Generate audit file (`audit/{module}-quality.yaml`)
- ⏸️ Update review reports
- ⏸️ Clean up queue files

**Phase 5: Audit Integration** ⏳ PENDING
- ⏸️ Update `scripts/audit/gates.py` - add `evaluate_activity_quality()` gate
- ⏸️ Update `scripts/audit/core.py` - integrate quality checks
- ⏸️ Add quality thresholds to `scripts/audit/config.py`

**Phase 6: Deployment & Testing** ⏳ PENDING
- ⏸️ Deploy to `.claude/` directory: `npm run claude:deploy`
- ⏸️ Test on sample B1 module (M52 recommended)
- ⏸️ Document in `docs/ARCHITECTURE.md`
- ⏸️ Update `CLAUDE.md` with quality validation workflow

---

## Next Steps

1. ✅ **Review analysis** - User confirmed approach (no API, manual + deterministic)
2. ⏳ **Complete Phase 3-6** - Queue generation, finalization, audit integration, deployment
3. ⏳ **Test on B1 M52** - Full validation on one complete module
4. ⏳ **Iterate based on results** - Refine thresholds and deterministic heuristics
5. ⏳ **Roll out to B1** - Validate all 86 B1 modules for quality
6. ⏳ **Create Issue #355** (optional) - Track implementation of activity quality validation

---

**Status:** Implementation in progress. Phases 1-2 complete (command + deterministic checks). Awaiting completion of phases 3-6.
