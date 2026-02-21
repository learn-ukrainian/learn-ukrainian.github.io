# Track & Level Architecture

> **Scope:** How tracks and levels are structured, what makes seminar tracks different from core, and pedagogy per level.

---

## Track Overview

| Track | Level | Type | Modules | Word Target | Pedagogy |
|-------|-------|------|---------|-------------|---------|
| `a1` | A1 | Core | 44 | 750w | PPP |
| `a2` | A2 | Core | 71 | 1000w | PPP |
| `b1` | B1 | Core | 94 | 1500w | TTT |
| `b2` | B2 | Core | 95 | 1750w | TTT |
| `c1` | C1 | Core | 109 | 3000w | CLIL |
| `c2` | C2 | Core | 101 | 3000w | CLIL |
| `b2-pro` | B2 | Core (professional) | 40 | 1750w | CLIL |
| `c1-pro` | C1 | Core (professional) | 50 | 3000w | CLIL |
| `b2-hist` | B2 | Seminar | 140 | 5000w | CBI |
| `c1-bio` | C1 | Seminar | 172 | 5000w | CBI |
| `c1-hist` | C1 | Seminar | 136 | 5000w | CBI |
| `lit` | C1+ | Seminar | 218 | 2500w | CBI |
| `oes` | C2 | Seminar | 100 | 3000w | CBI |
| `ruth` | C2 | Seminar | 100 | 3000w | CBI |

---

## Core vs Seminar: Key Differences

| Dimension | Core tracks | Seminar tracks |
|-----------|-------------|----------------|
| **Purpose** | Grammar/vocabulary acquisition | Content-based deep learning |
| **Pedagogy** | PPP / TTT / CLIL | CBI (Content-Based Instruction) |
| **Module topics** | Sequential grammar/vocab progression | Independent topics (history, biography) |
| **Consistency need** | High — vocabulary must build | Low — each module is standalone |
| **Track context** | Inject last 5 modules | **Empty — omit entirely** |
| **Research phase** | Lightweight | Deep (3+ academic sources) |
| **Activities** | Drills, grammar, matching | Reading, essays, critical analysis |
| **Immersion** | Graduated (A1: 10-40%, B2: 100%) | 98-100% always |
| **Primary sources** | Optional | Required (2+) |

---

## Pedagogy Models

### PPP (Presentation–Practice–Production)
Used for: A1, A2

Structure:
1. **Presentation** — introduce grammar/vocab in context
2. **Practice** — controlled exercises
3. **Production** — free use in context

Immersion: graduated from English-heavy (A1) to mostly Ukrainian (A2).

### TTT (Test–Teach–Test)
Used for: B1, B2

Structure:
1. **Diagnostic** — test what students already know
2. **Teaching** — fill the gaps
3. **Verification** — test again with harder items

Immersion: 90-100% Ukrainian.

### CLIL (Content and Language Integrated Learning)
Used for: C1, C2, B2-PRO, C1-PRO

Structure:
- Language learned through authentic content
- Grammar points emerge from real text
- No artificial drills — language in context only

Immersion: 100% Ukrainian.

### CBI (Content-Based Instruction)
Used for: All seminar tracks

Structure:
- Content drives everything
- Language is the medium, not the subject
- University seminar style — reading, analysis, discussion

Immersion: 98-100%. No grammar scaffolding. Full literary Ukrainian.

---

## Plan → Meta → Content → Activities: The Build Chain

```
plans/{track}/{slug}.yaml          ← SOURCE OF TRUTH
    ↓ Phase A reads
{track}/meta/{slug}.yaml           ← STRUCTURAL BLUEPRINT
    ↓ Phase B reads
{track}/{slug}.md                  ← CONTENT (lesson prose)
    ↓ Phase C reads
{track}/activities/{slug}.yaml     ← ACTIVITIES
{track}/vocabulary/{slug}.yaml     ← VOCABULARY
    ↓ Phase D reads
{track}/review/{slug}-review.md    ← ADVERSARIAL REVIEW
    ↓ Phase E reads
docusaurus/docs/{track}/{slug}.mdx ← PUBLISHED OUTPUT
```

**Never write content without first reading the plan.** The plan defines vocabulary scope, section names, objectives — everything Phase B must respect.

---

## Module Numbering

Modules are numbered within their track. Numbers are stable references (do not change when modules are added/reordered at the end).

```bash
# Get slug for a number
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from batch_gemini_config import slug_for_num
print(slug_for_num('c1-bio', 28))  # → 'danylo-apostol'
"
```

---

## Directory Structure

```
curriculum/l2-uk-en/
├── plans/{track}/{slug}.yaml         # Plan (source of truth)
├── {track}/
│   ├── meta/{slug}.yaml              # Build config
│   ├── {slug}.md                     # Content prose
│   ├── activities/{slug}.yaml        # Activities
│   ├── vocabulary/{slug}.yaml        # Vocabulary
│   ├── research/{slug}-research.md   # Research notes (seminar only)
│   ├── review/{slug}-review.md       # Adversarial review
│   ├── audit/{slug}-audit.md         # Audit report
│   ├── status/{slug}.json            # Cached audit result
│   └── orchestration/{slug}/         # Build state
│       ├── state-v3.json             # v3 pipeline state
│       ├── state.json                # v2 pipeline state
│       └── placeholders.yaml         # Template variables
```

---

## CEFR Level Mapping

| Level | Description | Ukrainian learner profile |
|-------|-------------|--------------------------|
| A1 | Beginner | First exposure to Ukrainian, Cyrillic alphabet |
| A2 | Elementary | Basic communication, simple sentences |
| B1 | Intermediate | Can navigate everyday situations in Ukrainian |
| B2 | Upper-intermediate | Can discuss abstract topics, read news |
| C1 | Advanced | Near-native fluency, complex academic discourse |
| C2 | Mastery | Full professional and academic proficiency |

---

## Seminar Track Specifics

### b2-hist (B2 History)
- Ukrainian history from proto-Slavic period to modern day
- Decolonization perspective mandatory
- 140 modules, ~700,000 words total when complete

### c1-bio (C1 Biography)
- 172 Ukrainian historical and cultural figures
- Biographical narrative arc required (birth → impact → legacy)
- Living people: "Значення" / "Вплив" sections; deceased: "Спадщина" / "Наслідки"

### c1-hist (C1 History)
- Advanced historiographical analysis
- Multiple perspectives, contested narratives
- Higher linguistic sophistication than b2-hist

### lit (Literature)
- Ukrainian literary works, essays, criticism
- 100% Ukrainian, no grammar scaffolding
- Essay and reflection format, not drills

### oes (Old East Slavic)
- Primary source literacy (Kyivan Rus texts)
- Grammar reconstruction and paleography
- University-level philological approach

### ruth (Ruthenian / Middle Ukrainian)
- XIV-XVIII century documents
- Legal, administrative, religious texts
- Cossack-era language forms
