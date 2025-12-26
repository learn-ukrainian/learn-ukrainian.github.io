# Staged Generation Architecture

> **Problem:** LLM agents don't reliably follow complex constraints during module generation. They approximate, underdeliver, and rationalize failures.
>
> **Solution:** Remove agent discretion. Break generation into validated stages where scripts decide pass/fail.

> **Scope:** This architecture primarily targets **B1+ modules** where full Ukrainian immersion enables rich, engaging content. A1/A2 are scaffolding levels (learning Cyrillic, basic grammar) where mechanical accuracy matters more than richness. The staged workflow applies to all levels, but richness metrics are B1+ only.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INPUT DOCUMENTS                                  │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ Curriculum Plan  │  │ Module Template  │  │ Richness Guidelines  │  │
│  │ (vocab, grammar) │  │ (structure)      │  │ (activity specs)     │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                       │              │
│           └─────────────────────┴───────────────────────┘              │
│                                 │                                       │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: SKELETON                                                       │
│                                                                         │
│ Script: scripts/generate_skeleton.py                                    │
│                                                                         │
│ Input:  Curriculum plan + Template                                      │
│ Output: {module}-skeleton.md                                            │
│                                                                         │
│ Generates:                                                              │
│ - Frontmatter (from curriculum plan)                                    │
│ - All section headers (from template)                                   │
│ - Vocabulary table (from curriculum plan, pre-formatted)                │
│ - Word count targets per section                                        │
│ - Activity placeholders with specs                                      │
│                                                                         │
│ Gate: python3 scripts/check_gate.py skeleton {file}                     │
│       - Structure valid? (headers present)                              │
│       - Vocab table formatted?                                          │
│       - All placeholders have targets?                                  │
│       → PASS or FAIL (no agent interpretation)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ PASS ONLY
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: LESSON CONTENT                                                 │
│                                                                         │
│ Actor: LLM (fills prose sections)                                       │
│                                                                         │
│ Input:  {module}-skeleton.md                                            │
│ Output: {module}-content.md                                             │
│                                                                         │
│ LLM fills:                                                              │
│ - Presentation/Analysis prose (target from skeleton)                    │
│ - Practice prose (target from skeleton)                                 │
│ - Production prose (target from skeleton)                               │
│ - Engagement boxes (minimum from richness guide)                        │
│ - Example sentences and dialogues                                       │
│                                                                         │
│ Gate: python3 scripts/check_gate.py content {file}                      │
│       - Words >= target? (1500 for B1)                                  │
│       - Engagement boxes >= minimum? (5 for B1)                         │
│       - Example sentences >= minimum? (24 for B1)                       │
│       - Immersion >= target? (90% for B1)                               │
│       - Richness score >= threshold?                                    │
│       → PASS or FAIL (no agent interpretation)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ PASS ONLY
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: ACTIVITIES                                                     │
│                                                                         │
│ Actor: LLM (generates activities from lesson content)                   │
│                                                                         │
│ Input:  {module}-content.md + activity specs from richness guide        │
│ Output: {module}-complete.md                                            │
│                                                                         │
│ For each required activity type:                                        │
│ 1. Extract relevant content from lesson (vocab, sentences, examples)    │
│ 2. Show EXACT markdown format template                                  │
│ 3. Generate activity following format                                   │
│ 4. Validate format + item count immediately                             │
│ 5. If fail → regenerate that activity only                              │
│                                                                         │
│ Activities are DERIVED from content, not invented:                      │
│ - match-up: uses vocab table directly                                   │
│ - fill-in: extracts sentences, adds blanks                              │
│ - unjumble: takes sentences, scrambles words                            │
│ - cloze: takes paragraph, adds blanks                                   │
│ - quiz: questions about lesson content                                  │
│ - error-correction: modifies lesson sentences                           │
│                                                                         │
│ Gate: python3 scripts/check_gate.py activities {file}                   │
│       - All 12 activity types present? (B1)                             │
│       - Each activity >= minimum items?                                 │
│       - All formats valid? (callouts, structure)                        │
│       - Sentence complexity in range?                                   │
│       → PASS or FAIL (no agent interpretation)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ PASS ONLY
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: FINAL AUDIT                                                    │
│                                                                         │
│ Script: python3 scripts/audit_module.py {file}                          │
│                                                                         │
│ Full audit combining all checks:                                        │
│ - Structure, format, lint                                               │
│ - Word count, vocab count, engagement                                   │
│ - Activity validity, item counts, formats                               │
│ - Immersion percentage                                                  │
│ - Richness score                                                        │
│                                                                         │
│ Result: ✅ AUDIT PASSED or ❌ AUDIT FAILED                               │
│                                                                         │
│ Agent has NO discretion:                                                │
│ - ❌ = not done. Period.                                                │
│ - No "informational" exceptions                                         │
│ - No proceeding despite failures                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ PASS ONLY
┌─────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: OUTPUT GENERATION                                              │
│                                                                         │
│ Scripts:                                                                │
│ - npm run generate (MDX for Docusaurus)                                 │
│ - npm run generate:json (JSON for Vibe)                                 │
│ - npm run validate:mdx (content integrity)                              │
│ - npm run validate:html (browser rendering)                             │
│                                                                         │
│ Only runs after Stage 4 passes.                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Principles

### 1. Script Decides, Agent Obeys

```python
# Agent runs:
result = subprocess.run(['python3', 'scripts/check_gate.py', 'content', file])

# Script returns:
if result.returncode == 0:
    print("PASS")  # Agent may proceed
else:
    print("FAIL: Words 943/1500")  # Agent must fix before proceeding
```

The agent cannot interpret, rationalize, or override. `FAIL` means stop.

### 2. Stages Are Separate Conversations

Each stage is a discrete task:
- Stage 1 completes → file saved
- New conversation for Stage 2
- Agent cannot "push through" failures across stages

This prevents context pollution and scope creep.

### 3. Activities Derive From Content

| Activity | Source from Validated Lesson |
|----------|------------------------------|
| match-up | Vocabulary table → word/translation pairs |
| fill-in | Extract sentences → add blanks |
| unjumble | Take sentences → scramble words |
| cloze | Take paragraph → add blanks |
| quiz | Generate questions about lesson content |
| mark-the-words | Text passage from lesson |
| error-correction | Modify lesson sentences |
| translate | Sentence pairs from lesson |
| dialogue-reorder | Dialogue from lesson |

The LLM transforms validated content into activity format. No invention.

### 4. Hard Gates With Absolute Thresholds

| Gate | Metric | B1 Threshold | Pass Condition |
|------|--------|--------------|----------------|
| content | Word count | 1500 | `words >= 1500` |
| content | Engagement | 5 | `boxes >= 5` |
| content | Examples | 24 | `examples >= 24` |
| content | Immersion | 90% | `ukr_ratio >= 0.90` |
| content | Richness | 70 | `richness_score >= 70` |
| activities | Types | 12 | `activity_types >= 12` |
| activities | Items/type | 14 | `min(items_per_activity) >= 14` |
| activities | Format | 100% | `all_formats_valid` |

---

## Richness & Dryness Metrics

### Measuring Dryness (Inverse of Richness)

Content is "dry" when it lacks engagement, variety, and authentic feel. We measure richness; low richness = dry.

### Richness Score Components

| Component | Weight | Measurement | Target (B1) |
|-----------|--------|-------------|-------------|
| **Engagement boxes** | 15% | Count of 💡🎬🌍🎭🎯 callouts | 5+ |
| **Example sentences** | 20% | Sentences with Ukrainian examples | 24+ |
| **Mini-dialogues** | 15% | Dialogue exchanges (А:/Б: patterns) | 4+ |
| **Variety score** | 10% | Unique sentence starters / total sentences | > 0.6 |
| **Cultural references** | 10% | Named people, places, traditions | 3+ |
| **Real-world contexts** | 10% | Practical scenarios mentioned | 3+ |
| **Question density** | 5% | Interactive questions in prose | 5+ |
| **Proverbs/idioms** | 5% | Phraseological units introduced | 1+ |
| **Visual elements** | 5% | Tables, comparison boxes, tip callouts | 3+ |
| **Paragraph variety** | 5% | Std dev of paragraph lengths | > 20 words |

### Richness Score Calculation

```python
def calculate_richness_score(content: str, level: str) -> int:
    """Returns richness score 0-100."""

    targets = RICHNESS_TARGETS[level]
    scores = {}

    # Count components
    scores['engagement'] = min(count_engagement_boxes(content) / targets['engagement'], 1.0)
    scores['examples'] = min(count_examples(content) / targets['examples'], 1.0)
    scores['dialogues'] = min(count_dialogues(content) / targets['dialogues'], 1.0)
    scores['variety'] = calculate_variety_score(content)
    scores['cultural'] = min(count_cultural_refs(content) / targets['cultural'], 1.0)
    scores['realworld'] = min(count_realworld(content) / targets['realworld'], 1.0)
    scores['questions'] = min(count_questions(content) / targets['questions'], 1.0)
    scores['proverbs'] = min(count_proverbs(content) / targets['proverbs'], 1.0)
    scores['visual'] = min(count_visual_elements(content) / targets['visual'], 1.0)
    scores['paragraph_var'] = calculate_paragraph_variety(content)

    # Weighted sum
    weights = {
        'engagement': 0.15, 'examples': 0.20, 'dialogues': 0.15,
        'variety': 0.10, 'cultural': 0.10, 'realworld': 0.10,
        'questions': 0.05, 'proverbs': 0.05, 'visual': 0.05,
        'paragraph_var': 0.05
    }

    total = sum(scores[k] * weights[k] for k in scores)
    return int(total * 100)
```

### Dryness Indicators (Automatic Flags)

| Indicator | Condition | Severity | Excluded Module Types |
|-----------|-----------|----------|----------------------|
| NO_ENGAGEMENT | engagement_boxes < 2 | Critical | — |
| WALL_OF_TEXT | max_paragraph > 200 words | Warning | history, biography, literature, folk-culture |
| REPETITIVE_STARTERS | variety_score < 0.4 | Warning | — |
| NO_DIALOGUE | dialogues == 0 | Critical | history, biography, literature |
| NO_EXAMPLES | examples < 10 | Critical | — |
| ABSTRACT_ONLY | realworld_refs == 0 | Warning | — |
| GRAMMAR_DUMP | explanation_ratio > 0.7 | Warning | — |

**Context-aware flags:** Some module types (history, biography, literature, folk-culture) are narrative-heavy by design. Extended prose is expected content, not a flaw. The flags above exclude these types where appropriate.

---

## Integration With Existing Documents

### Document Hierarchy

```
docs/l2-uk-en/
├── {LEVEL}-CURRICULUM-PLAN.md      # Source of truth for module content
│   ├── Module number, title, phase
│   ├── Grammar scope (exact points to cover)
│   ├── Vocabulary list (exact words)
│   └── Cultural/thematic focus
│
├── templates/
│   ├── b1-grammar-module-template.md    # Structure template
│   ├── b1-vocab-module-template.md
│   ├── b1-checkpoint-module-template.md
│   └── ...
│
├── MODULE-RICHNESS-GUIDELINES-v2.md     # Activity specs, counts, density
│   ├── Activity types per level
│   ├── Items per activity
│   ├── Sentence complexity
│   └── Engagement requirements
│
└── STAGED-GENERATION-ARCHITECTURE.md   # This document - workflow
```

### Stage 1 (Skeleton) Inputs

| Input | Source |
|-------|--------|
| Frontmatter | Curriculum plan (module, title, level, phase, objectives) |
| Section headers | Template (Presentation, Practice, Production, etc.) |
| Vocabulary table | Curriculum plan (exact words, formatted as table) |
| Activity list | Richness guide (12 types for B1) |
| Word targets | Richness guide (1500 for B1) |

### Stage 2 (Content) Inputs

| Input | Source |
|-------|--------|
| Skeleton | Stage 1 output |
| Grammar scope | Curriculum plan |
| Example patterns | Template |
| Engagement types | Richness guide |
| Immersion target | Richness guide |

### Stage 3 (Activities) Inputs

| Input | Source |
|-------|--------|
| Lesson content | Stage 2 output |
| Activity specs | Richness guide (types, counts, density) |
| Format templates | ACTIVITY-MARKDOWN-REFERENCE.md |
| Sentence complexity | Richness guide (10-14 words for B1 fill-in) |

---

## Scripts To Build

### 1. `scripts/generate_skeleton.py`

```bash
python3 scripts/generate_skeleton.py l2-uk-en b1 43

# Reads: B1-CURRICULUM-PLAN.md, b1-grammar-module-template.md
# Outputs: curriculum/l2-uk-en/b1/43-{slug}-skeleton.md
```

### 2. `scripts/check_gate.py`

```bash
python3 scripts/check_gate.py skeleton curriculum/l2-uk-en/b1/43-*-skeleton.md
python3 scripts/check_gate.py content curriculum/l2-uk-en/b1/43-*-content.md
python3 scripts/check_gate.py activities curriculum/l2-uk-en/b1/43-*-complete.md

# Returns: exit code 0 (PASS) or 1 (FAIL with message)
```

### 3. `scripts/extract_for_activities.py`

```bash
python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-*-content.md

# Outputs JSON:
# {
#   "vocabulary": [{"uk": "слово", "en": "word"}, ...],
#   "sentences": ["Це речення.", "Інше речення.", ...],
#   "dialogues": [{"a": "Привіт!", "b": "Привіт!"}, ...],
#   "paragraphs": ["Paragraph text...", ...]
# }
```

### 4. `scripts/calculate_richness.py`

```bash
python3 scripts/calculate_richness.py curriculum/l2-uk-en/b1/43-*.md

# Outputs:
# Richness Score: 78/100
# Components:
#   Engagement: 5/5 (100%)
#   Examples: 22/24 (92%)
#   Dialogues: 4/4 (100%)
#   Variety: 0.65 (65%)
#   ...
# Flags:
#   ⚠️ EXAMPLES below target (22/24)
```

---

## Migration Path

### Existing Passing Modules
- Keep as-is
- No rebuild needed

### Existing Failing Modules (M43, M46-49)
1. Extract lesson content (prose sections)
2. If content is dry (< 1500 words): rebuild from skeleton
3. If content is okay: regenerate activities using new Stage 3

### New Modules (M44-45, M50+)
- Use full staged workflow from start

---

## Appendix: Level-Specific Thresholds

### B1 Thresholds

| Gate | Metric | Threshold |
|------|--------|-----------|
| content | Words | 1500 |
| content | Engagement boxes | 5 |
| content | Examples | 24 |
| content | Dialogues | 4 |
| content | Immersion | 90% |
| content | Richness score | 70 |
| activities | Types | 12 |
| activities | Items/activity | 14 |
| activities | Fill-in words | 10-14 |
| activities | Unjumble words | 12-16 |
| vocab | Count | 25+ (grammar) / 35+ (vocab) |

### B2 Thresholds

| Gate | Metric | Threshold |
|------|--------|-----------|
| content | Words | 1750 |
| content | Engagement boxes | 6 |
| content | Examples | 24 |
| content | Dialogues | 4 |
| content | Immersion | 100% |
| content | Richness score | 75 |
| activities | Types | 14 |
| activities | Items/activity | 16 |
| activities | Fill-in words | 12-16 |
| activities | Unjumble words | 14-18 |
| vocab | Count | 20+ (grammar) / 25+ (phrase) |

### C1 Thresholds

| Gate | Metric | Threshold |
|------|--------|-----------|
| content | Words | 2000 |
| content | Engagement boxes | 7 |
| content | Examples | 30 |
| content | Dialogues | 5 |
| content | Immersion | 100% |
| content | Richness score | 80 |
| activities | Types | 16 |
| activities | Items/activity | 18 |
| activities | Fill-in words | 14-18 |
| activities | Unjumble words | 16-20 |
| vocab | Count | 25+ |
