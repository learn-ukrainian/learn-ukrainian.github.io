# Core B Workflow: Full-Immersion Rebuild

> **Scope:** B1 M06-92 (87), B2 (94), C1 (106), C2 (100), B2-PRO (40), C1-PRO (50) = **477 modules**
> **Immersion:** 75-100% Ukrainian
> **Pedagogy:** TTT (B1-B2), CLIL (C1-C2), ESP (PRO tracks)
> **Key trait:** Fully immersed, Ukrainian throughout

---

## When to Use This Workflow

Use Core B for any module where the learner operates in Ukrainian:

| Level | Modules | Immersion | Pedagogy |
|-------|---------|-----------|----------|
| B1 M06-51 | Grammar (aspect, motion, complex sentences) | 85-100% | TTT |
| B1 M52-71 | Vocabulary (abstract, discourse, synonymy) | 100% | CBI |
| B1 M72-92 | Cultural + practical (regions, sports, news) | 100% | CBI/ESP |
| B2 M01-94 | Advanced grammar, register, idioms, domains | 100% | TTT/CBI |
| C1 M01-106 | Mastery grammar, stylistics, professional | 100% | CLIL |
| C2 M01-100 | Near-native, stylistic mastery, dialectal | 100% | CLIL |
| B2-PRO | Professional Ukrainian (40 modules) | 100% | ESP |
| C1-PRO | Expert professional Ukrainian (50 modules) | 100% | ESP |

> **For A1, A2, B1 M01-05:** Use [Core A Workflow](CORE-A-WORKFLOW.md).
> **For seminar tracks (B2-HIST, C1-BIO, LIT):** Use [Research-First Workflow](RESEARCH-FIRST-WORKFLOW.md).

---

## Phase 0: Research

> **More thorough than Core A, but not as deep as seminar tracks.** Core B research verifies grammar against the State Standard and ensures vocabulary is frequency-appropriate.

### What to Research

| Topic | Where to Look | Time |
|-------|---------------|------|
| **Grammar point** | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` — find exact §section | 10-15 min |
| **Vocabulary** | `lcorp.ulif.org.ua`, `sum.in.ua`, domain-specific lists for PRO | 5-10 min |
| **Cross-references** | Previous modules in sequence, builds-on/prepares-for chain | 5 min |
| **C2 stylistic features** | Academic linguistic sources (optional, C2 only) | 10-15 min |

**Total research: ~20-30 minutes per module** (vs. 60+ for seminar tracks).

### Research Note Template (Core B)

Save to: `curriculum/l2-uk-en/{level}/audit/{slug}-research.md`

```markdown
# Research: {Module Title}

**Level:** {level} | **Module:** {num}
**Researched:** {date}

## State Standard Reference
- Section: §X.X.X
- Grammar point: [description]
- Quote: "[exact wording from the standard]"
- Exceptions/nuances: [what the standard says]
- Level confirmation: [this grammar belongs at {level} per standard]

## Vocabulary Research
- Domain: [general / professional domain]
- Frequency verification: [source — lcorp.ulif.org.ua or domain list]
- Collocations: [natural pairings verified against corpus]

## Cross-References
- Builds on: [previous module(s) — grammar prerequisites]
- Prepares for: [future module(s) — where this grammar is used next]
- Recycled vocabulary: [words from prior modules reused here]
```

### PRO Track Research Additions

For B2-PRO and C1-PRO, add:

```markdown
## Domain-Specific Vocabulary
- Domain: [medicine / law / business / IT / etc.]
- Source: [domain vocabulary list, professional glossary]
- Register: [formal / technical / official]
- Verified collocations: [professional-context pairings]

## Authentic Scenarios
- Scenario 1: [real professional situation where this language is used]
- Scenario 2: [alternative context]
```

### C2 Research Additions

For C2 modules, add:

```markdown
## Stylistic Features
- Register awareness: [what stylistic distinctions this module teaches]
- Dialectal notes: [if relevant, regional variation from standard]
- Academic source: [linguistic reference for claims about style/register]
```

### When Research Is Required

| Scenario | Research? |
|----------|-----------|
| New module (no .md exists) | Yes |
| Rebuilding existing module | Yes — grammar must be verified against State Standard |
| Review only (content exists, passing audit) | No — review prompt handles verification |
| Expanding word count | Yes — new content needs verified grammar/vocab |

---

## Phase 1: Load Context

**Read ALL of these before writing:**

```
curriculum/l2-uk-en/plans/{level}/{slug}.yaml     # Source of truth
curriculum/l2-uk-en/{level}/meta/{slug}.yaml       # Pedagogy config
claude_extensions/quick-ref/{LEVEL}.md             # Level constraints
docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md    # Activity counts (ceiling!)
```

**Also read the appropriate tier guidance:**

| Level | Tier File |
|-------|-----------|
| B1, B2 Core, B2-PRO | `claude_extensions/commands/review-tiers/tier-2-core.md` |
| C1, C2, C1-PRO | `claude_extensions/commands/review-tiers/tier-4-advanced.md` |

### Key Constraints to Confirm

Before writing, confirm:

- [ ] **Word target** from meta (B1: 1500+, B2: 1750+, C1: 3000+, C2: 3000+)
- [ ] **Immersion** — 100% Ukrainian for all content (English only in vocab table)
- [ ] **Vocabulary** — ONLY what's in the plan
- [ ] **Grammar focus** — matches State Standard §reference from research
- [ ] **Activity types** — which are allowed/forbidden at this level
- [ ] **Template** — read the correct module-type template
- [ ] **Cross-references** — what prior modules this builds on

---

## Phase 2: Write Content

### Core B Writing Rules

**Everything in Ukrainian.** No English scaffolding.

- Grammar metalanguage in Ukrainian (відмінок, дієслово, доконаний вид)
- All examples, explanations, instructions in Ukrainian
- English appears ONLY in the vocabulary table (translation column)
- Natural, native-quality Ukrainian — no robotic constructions

### Level-Specific Requirements

**B1 M06-92:**
- TTT pedagogy for grammar modules (test before teaching)
- CBI for vocabulary/cultural modules
- 100% immersion (transitioned from B1.0 metalanguage bridge)
- FORBIDDEN: English annotations in explanations
- Reference existing B1 modules that passed review as templates

**B2:**
- Higher minimums: quiz 10 items, cloze 16 blanks
- Register awareness begins (formal/informal distinction)
- Culturally embedded examples mandatory
- `instruction` field (singular, not `instructions`)
- `essay-response` type (not `writing`)

**C1:**
- Content-heavy modules (Folk M56-85, Lit M86-105) have 10-12 activities, not 16+
- Golden Rule enforced: "Can learner answer without reading Ukrainian?" → rewrite
- FORBIDDEN: true-false, anagram, mark-the-words
- Semantic nuance required: modal hedging (можливо, ймовірно, водночас)
- Minimum 5 hedging markers per 1000 words

**C2:**
- Near-native complexity targets
- Latin/Greek scholarly terms acceptable
- Production-heavy activities
- Stylistic mastery (register switching, dialectal awareness)
- Highest minimums: cloze 20 blanks, fill-in 12 items

**PRO Tracks (B2-PRO, C1-PRO):**
- ESP (English for Specific Purposes) methodology adapted to Ukrainian
- Domain-specific scenarios (medicine, law, business, IT)
- Professional register throughout
- Authentic workplace dialogues and documents

### Outline Compliance

**Every subsection in the plan's `content_outline` must appear in the module.** This is the #1 failure mode across all levels.

### State Standard Compliance

When explaining grammar:
- Claims must match what the State Standard says in §reference
- If the standard has exceptions, include them
- If the standard contradicts common teaching shortcuts, follow the standard
- Cross-reference with research note before writing explanations

---

## Phase 3: Activities

### Philosophy

> **Minimal, correct, quality-focused.** A second app handles drill-heavy practice.

- Meet the **floor** from MODULE-RICHNESS-GUIDELINES-v2.md — don't exceed
- Activities test language skills using content as context, NOT content recall
- Golden Rule: "Can learner answer without reading Ukrainian?" → If YES, rewrite
- Focus on correctness over quantity

### Activity Counts (Ceiling, Not Target)

| Level | Activities | Items/Activity |
|-------|-----------|----------------|
| B1 | 8+ | 14+ |
| B2 | 10+ | 16+ |
| C1 | 12+ (10-12 for content-heavy) | 18+ |
| C2 | 16+ | 18+ |
| PRO | Domain-appropriate | Domain-appropriate |

### Activity Quality Checklist

- [ ] Every Ukrainian sentence is grammatically correct and natural
- [ ] Every quiz item has exactly one correct answer
- [ ] Distractors target real learner errors (not random wrong answers)
- [ ] No duplicate items
- [ ] YAML validates against `schemas/activities-{level}.schema.json`
- [ ] Activities test production, not just recognition (especially C1/C2)

---

## Phase 4: Audit & Review

### Run Audit

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{slug}.md
```

### Review with Standard v4 Prompt

```
/review-content-v4 {LEVEL} {NUM}
```

Core B uses the standard [review-content-v4](../claude_extensions/commands/review-content-v4.md) prompt, which already handles:
- Full Ukrainian verification (Russianisms, calques)
- Propaganda filter (relevant for B2+ cultural content)
- Semantic nuance gate (C1+)
- 14-dimension scoring
- State Standard compliance check (added for grammar modules)

### Quality Bar

| Metric | Target |
|--------|--------|
| Audit | All gates pass |
| Word count | ≥95% of target |
| Review overall | ≥8.5/10 |
| No dimension below auto-fail threshold | Required |
| State Standard compliance | Grammar matches §reference |
| Naturalness | ≥8/10 (native-level) |

---

## Differences from Other Workflows

| Aspect | Core B | Core A | Seminar |
|--------|--------|--------|---------|
| Research depth | 20-30 min | 15-20 min | 60+ min |
| Grammar verification | State Standard §ref | State Standard §ref | Primary sources + Standard |
| Callout planning | Not required | Not required | 12-15 callouts upfront |
| Word targets | 1500-3000+ | 300-1500 | 4000+ |
| Activities | Meet floor, quality focus | Meet floor, quality focus | 4-9 seminar-style |
| Language | 100% Ukrainian | English + Ukrainian | 100% Ukrainian |
| Propaganda filter | Yes (B2+ cultural) | No | Yes (all content) |
| Semantic nuance | Yes (C1+) | No | Yes (C1+) |
| Review prompt | `/review-content-v4` | `/review-content-core-a` | `/review-content-v4` |

---

## Batch Processing

### Recommended Batch Size

| Level | Batch Size | Rationale |
|-------|------------|-----------|
| B1 | 3-5 modules | Shorter modules, similar patterns |
| B2 | 2-4 modules | Medium complexity |
| C1 | 2-3 modules | Higher complexity, more content |
| C2 | 2 modules | Highest complexity |
| PRO | 2-3 modules | Domain research adds overhead |

### Sequential Batching

For large lists (6+ modules):
1. Process first batch (2-4 modules)
2. Audit all in batch
3. Report and checkpoint
4. Continue after confirmation

---

## Quick Reference

| Metric | Core B Requirement |
|--------|--------------------|
| Levels | B1 M06+, B2, C1, C2, B2-PRO, C1-PRO |
| Total modules | 477 |
| Research | Moderate (State Standard + frequency + cross-refs) |
| Immersion | 75-100% (100% from B1.2 onwards) |
| Pedagogy | TTT (B1-B2), CLIL (C1-C2), ESP (PRO) |
| Activities | Meet floor, quality over quantity |
| State Standard | Grammar must reference §section |
| Review prompt | `/review-content-v4` |
| Batch size | 2-5 modules (depends on level) |
