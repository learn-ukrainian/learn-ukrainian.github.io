# Core A Workflow: Mixed-Language Rebuild

> **Scope:** A1 (44), A2 (70), B1 M01-05 (5) = **119 modules**
> **Immersion:** 10-75% Ukrainian (graduated by level/phase)
> **Pedagogy:** PPP (A1/A2), Metalanguage Bridge (B1 M01-05)
> **Key trait:** English explanations + Ukrainian content

---

## When to Use This Workflow

Use Core A for any module where the learner still needs English scaffolding:

| Level | Modules | Immersion Target |
|-------|---------|------------------|
| A1 M01-05 | The Cyrillic Code, Gender, This is/I am | 10-15% |
| A1 M06-10 | Objects, Verbs, Questions, Reflexives | 15-25% |
| A1 M11-20 | Accusative, Locative, Possessives, City | 25-35% |
| A1 M21-34 | Tenses, Modals, Routine, Family | 35-40% |
| A1 M35-44 | Practical scenarios (Café, Market) | 35-40% |
| A2 M01-25 | Cases, Aspect, Comparison | 40-60% |
| A2 M26-55 | Complex sentences, Word formation | 50-70% |
| A2 M56-70 | Practical, Exam | 60-75% |
| B1 M01-05 | Metalanguage bridge (grammar terms in Ukrainian) | ~50% |

> **B1 M01-05 note:** These modules teach Ukrainian grammatical metalanguage (відмінок, дієслово, etc.). They use a **bridge pedagogy** — not PPP, not TTT — introducing terms in Ukrainian with English support. See `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`.

> **For B1 M06+ and all higher levels:** Use [Core B Workflow](CORE-B-WORKFLOW.md).

---

## Phase 0: Lightweight Research

> **This is NOT seminar-track deep research.** Core A research is short, focused lookups — not multi-source academic investigation.

### What to Research

| Topic | Where to Look | Time |
|-------|---------------|------|
| **Grammar point** | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` | 5-10 min |
| **Vocabulary frequency** | `lcorp.ulif.org.ua`, `sum.in.ua` | 5 min |
| **Cultural hook** | `uk.wikipedia.org`, quick web search | 5 min |

**Total research: ~15-20 minutes per module** (vs. 60+ for seminar tracks).

### Research Note Template (Core A — Lightweight)

Save to: `curriculum/l2-uk-en/{level}/research/{slug}-research.md`

```markdown
# Research: {Module Title}

**Level:** {level} | **Module:** {num}
**Researched:** {date}

## State Standard Reference
- Section: §X.X.X
- Required grammar: [what the standard says about this grammar point]
- Level placement: [confirms this belongs at A1/A2/B1.0]

## Vocabulary Check
- Core words: [list, confirmed high-frequency]
- Frequency source: [lcorp.ulif.org.ua / sum.in.ua]
- Any surprises: [words that seem too rare or too advanced]

## Cultural Hook (1-2 facts)
- Fact: [verified, specific detail — not from memory]
- Source: [URL]
- How to use: [where in the module this fits naturally]
```

### When Research Is Required

| Scenario | Research? |
|----------|-----------|
| New module (no .md exists) | Yes |
| Rebuilding existing module | Yes — grammar claims must be verified |
| Review only (content exists, passing audit) | No — review prompt handles verification |
| Expanding word count | Yes — new content needs sourced facts |

---

## Phase 1: Load Context

**Read ALL of these before writing a single word:**

```
curriculum/l2-uk-en/plans/{level}/{slug}.yaml     # Source of truth
curriculum/l2-uk-en/{level}/meta/{slug}.yaml       # Pedagogy config
claude_extensions/quick-ref/{LEVEL}.md             # Level constraints
docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md    # Activity counts (ceiling!)
claude_extensions/commands/review-tiers/tier-1-beginner.md  # A1/A2 quality bar
```

### Key Constraints to Confirm

Before writing, confirm:

- [ ] **Word target** from meta (A1 graduated: 300→750, A2: 1000+, B1.0: 1500+)
- [ ] **Immersion %** from quick-ref (graduated per phase)
- [ ] **Vocabulary** — ONLY what's in the plan
- [ ] **Grammar focus** — matches State Standard §reference from research
- [ ] **Activity types** — which are allowed/forbidden at this level
- [ ] **Template** — read the correct module-type template

---

## Phase 2: Write Content

### Core A Writing Rules

**English portions (explanations, instructions):**
- B1-readable English (accessible to non-native English speakers)
- Contractions OK ("you'll", "don't", "it's")
- Warm, tutoring tone — not academic
- Simple sentences, clear structure

**Ukrainian portions (examples, practice, dialogues):**
- Natural, native-quality Ukrainian
- No Russianisms, no calques
- Case agreement, verb aspects, gender — all correct
- Appropriate vocabulary for level

**L1/L2 Balance:**
- Follow graduated immersion targets from quick-ref
- English for explanations, Ukrainian for content/practice
- As level progresses, English decreases
- B1 M01-05 bridge: ~50% (English metalanguage, Ukrainian examples)

### A1-Specific Requirements

- **IPA pronunciation** for all new vocabulary
- **Transliteration**: M01-10 full, M11-20 vocab only, M21-34 first occurrence, M35+ none
- **Emotional safety**: Welcome → Curious → Quick win → Encouraged → Progress visible
- **"Would I Continue?" test**: Read as a nervous beginner — would they come back?
- **Cognitive load**: ≤5-7 new words per section, ≤2 concepts before practice

### A2-Specific Requirements

- **No transliteration** anywhere
- **Max 15 words per sentence** in Ukrainian
- Grammar terms must be added to vocabulary if explained
- Error-correction activities introduced (new at A2)

### B1 M01-05 Specific Requirements

- **Metalanguage bridge** — NOT PPP, NOT TTT
- Unique pedagogy: introducing Ukrainian grammar terminology (відмінок, дієслово, etc.)
- ~50% immersion (English for explaining metalanguage, Ukrainian for examples/practice)
- Prepares learner for 100% immersion from M06 onwards
- Template: `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`

### Outline Compliance

**Every subsection in the plan's `content_outline` must appear in the module.** This is the #1 failure mode — don't skip subsections.

---

## Phase 3: Activities

### Philosophy

> **Minimal, correct, quality-focused.** A second app handles drill-heavy practice.

- Meet the **floor** from MODULE-RICHNESS-GUIDELINES-v2.md — don't exceed
- Every activity item must be verified for grammar accuracy
- Focus on correctness over quantity
- If in doubt, fewer items done well > more items with errors

### Activity Counts (Ceiling, Not Target)

| Level | Activities | Items/Activity |
|-------|-----------|----------------|
| A1 | 8+ (ceiling from guidelines) | 12+ |
| A2 | 10+ (ceiling from guidelines) | 12+ |
| B1 M01-05 | 8+ (ceiling from guidelines) | 14+ |

### Activity Quality Checklist

- [ ] Every quiz item has exactly one correct answer
- [ ] Every fill-in sentence is grammatically correct with answer inserted
- [ ] Every cloze target word is appropriate for level
- [ ] Every unjumble answer forms a natural sentence
- [ ] No duplicate items
- [ ] YAML validates against `schemas/activities-{level}.schema.json`

---

## Phase 4: Audit & Review

### Run Audit

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{slug}.md
```

### Review with Core A Prompt

```
/review-content-core-a {LEVEL} {NUM}
```

Uses the [Core A review prompt](../claude_extensions/commands/review-content-core-a.md) — adapted for mixed-language modules with L1/L2 balance checks, beginner safety audit, IPA verification, and State Standard compliance.

### Quality Bar

| Metric | Target |
|--------|--------|
| Audit | All gates pass |
| Word count | ≥95% of target |
| Review overall | ≥8.5/10 |
| No dimension below auto-fail threshold | Required |
| IPA transcriptions | All verified |
| State Standard compliance | Grammar matches §reference |

---

## Differences from Seminar Workflow

| Aspect | Core A | Seminar (RESEARCH-FIRST-WORKFLOW.md) |
|--------|--------|--------------------------------------|
| Research depth | 15-20 min (focused lookups) | 60+ min (deep academic research) |
| Research sources | State Standard, frequency lists, 1-2 cultural facts | Ukrainian academic sources, archives, primary sources |
| Research note | ~15 lines | 50+ lines with callout planning |
| Callout planning | Not required | 12-15 callouts planned upfront |
| Word targets | 300-1500 (graduated) | 4000+ |
| Activities | Meet floor, don't exceed | 4-9 seminar-style |
| Language mix | English + Ukrainian | 100% Ukrainian |
| Propaganda filter | Not applicable | Required |
| Semantic nuance | Not applicable | Required at C1+ |

---

## Quick Reference

| Metric | Core A Requirement |
|--------|--------------------|
| Levels | A1, A2, B1 M01-05 |
| Total modules | 119 |
| Research | Lightweight (State Standard + frequency + 1-2 cultural facts) |
| Immersion | 10-75% (graduated) |
| Pedagogy | PPP (A1/A2), Metalanguage Bridge (B1 M01-05) |
| Activities | Meet floor, quality over quantity |
| IPA | Required for all new vocabulary |
| State Standard | Grammar must reference §section |
| Review prompt | `/review-content-core-a` |
| Batch size | 3-5 modules (simpler than seminar) |
