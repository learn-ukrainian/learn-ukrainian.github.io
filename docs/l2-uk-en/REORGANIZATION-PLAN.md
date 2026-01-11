# Curriculum Reorganization Plan

**Status:** 📋 PLANNING
**Target:** After A1-C1 production ready
**Created:** 2026-01-11

---

## Executive Summary

This plan reorganizes the Ukrainian curriculum to:
1. Add missing practical communication modules to A1-B2
2. Move specialized history/biography content to optional tracks
3. Create a professional Ukrainian track
4. Maintain all existing content (no deletions)

**Guiding Principle:** Grammar alone is useless. Vocabulary needs context. Cultural content (folk arts, music, regions) provides that context and stays in core. Deep dives (96 biographies, 61 history modules) become optional tracks.

---

## Part 1: Current State Analysis

### Module Counts by Level

| Level | Current | Core Content | Specialized Content |
|-------|---------|--------------|---------------------|
| A1 | 34 | 34 (all) | - |
| A2 | 58 | 58 (all) | - |
| B1 | 91 | 91 (all) | - |
| B2 | 145 | 84 (M01-70, M132-145) | 61 (M71-131 History) |
| C1 | 202 | 106 (M01-35, M132-202) | 96 (M36-131 Biographies) |
| C2 | 100 | 100 (all) | - |

### Specialized Tracks (Existing)

| Track | Modules | Status | Purpose |
|-------|---------|--------|---------|
| LIT | 30 | 14 written | Classical Ukrainian Literature |
| OES | 30 | Planned | Old East Slavic linguistics (decolonization) |
| RUTH | 30 | Planned | Ruthenian linguistics (continuity proof) |

### Identified Gaps

#### A1 Gaps (Survival Ukrainian)
| Gap | Description | Priority |
|-----|-------------|----------|
| Restaurant ordering | No functional cafe/restaurant scenarios | HIGH |
| Shopping/market | Numbers exist but no checkout scenarios | HIGH |
| Transportation | No ticket buying, transit scenarios | HIGH |
| Phone calls | Completely missing | HIGH |
| Self-introduction | Exists but thin, needs expansion | MEDIUM |
| Numbers in context | Money, prices, quantities in real scenarios | HIGH |
| Emergencies | Basic emergency phrases missing | HIGH |

#### A2 Gaps (Real-world Independence)
| Gap | Description | Priority |
|-----|-------------|----------|
| Doctor/pharmacy | Health vocab exists, no roleplay scenarios | HIGH |
| Hotel/apartment | Completely missing | HIGH |
| Job interview | Completely missing | HIGH |
| Making appointments | Completely missing | HIGH |
| Directions | Exists but thin | MEDIUM |
| Social media/texting | Modern register missing | MEDIUM |

#### B1 Gaps (Functional Communication)
| Gap | Description | Priority |
|-----|-------------|----------|
| Podcast listening | No explicit listening skills training | MEDIUM |
| Written correspondence | Completely missing | HIGH |
| Debate/discussion | Discourse markers exist, no debate training | MEDIUM |
| News comprehension | M82-86 exist but thin | LOW |

#### B2 Gaps (Professional Basics)
| Gap | Description | Priority |
|-----|-------------|----------|
| Professional email | Registers covered, no email-specific | HIGH |
| Meeting participation | Completely missing | HIGH |
| Presentation skills | Completely missing | HIGH |
| Technical documentation | Completely missing | MEDIUM |

#### C1 Gaps
- No content gaps identified
- Structure issue: 96 biographies should be optional track

#### C2 Gaps
- No gaps identified
- Well-structured for mastery level

---

## Part 2: Target State

### New Track Structure

```
CORE PATH (Required - everyone does this):
┌─────────────────────────────────────────────────────────────────────┐
│ A1 Core (34) + A1 Practical Scenarios (NEW ~10)     = ~44 modules  │
│ A2 Core (58) + A2 Practical Scenarios (NEW ~12)     = ~70 modules  │
│ B1 Core (91) + B1 Skills Enhancement (NEW ~8)       = ~99 modules  │
│ B2 Core (84) + B2 Professional Basics (NEW ~10)     = ~94 modules  │
│ C1 Core (106)                                        = 106 modules  │
│ C2 Core (100)                                        = 100 modules  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              SPECIALIZED TRACKS (Choose based on interest):
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  📜 HISTORY & BIOGRAPHY TRACK (EXISTING - relocated)                │
│  ├── B2-HIST: Ukrainian History (61 modules) [from B2 M71-131]     │
│  └── C1-BIO: Famous Ukrainians (96 modules) [from C1 M36-131]      │
│                                                                     │
│  💼 PROFESSIONAL TRACK (NEW)                                        │
│  ├── B2-PRO: Business Ukrainian (40 modules)                       │
│  └── C1-PRO: Professional Mastery (50 modules)                     │
│                                                                     │
│  📚 LITERATURE TRACK (EXISTING)                                     │
│  └── LIT: Classical Literature (30 modules) [14 written]           │
│                                                                     │
│  🔤 LINGUISTICS TRACK (EXISTING - planned)                          │
│  ├── OES: Old East Slavic (30 modules)                             │
│  └── RUTH: Ruthenian (30 modules)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Folder Structure After Reorganization

```
curriculum/l2-uk-en/
├── a1/                    # A1 Core + Practical (renumbered)
├── a2/                    # A2 Core + Practical (renumbered)
├── b1/                    # B1 Core + Skills (renumbered)
├── b2/                    # B2 Core only (M01-70 grammar/phraseology + M71-84 skills)
├── c1/                    # C1 Core only (M01-35 academic + M36-141 stylistics/arts/lit)
├── c2/                    # C2 Core (unchanged)
│
├── b2-hist/               # NEW: B2 History Track (relocated from b2/M71-131)
├── c1-bio/                # NEW: C1 Biography Track (relocated from c1/M36-131)
│
├── b2-pro/                # NEW: B2 Professional Track
├── c1-pro/                # NEW: C1 Professional Track
│
├── lit/                   # LIT Track (existing)
├── oes/                   # OES Track (planned)
└── ruth/                  # RUTH Track (planned)
```

---

## Part 3: Detailed Reorganization Steps

### Phase 1: Add New Practical Modules

#### A1 New Modules (~10 modules)

| New # | Title | Content | Placement |
|-------|-------|---------|-----------|
| A1-35 | At the Café | Ordering drinks, snacks, asking for bill | After M34 |
| A1-36 | At the Restaurant | Full meal ordering, dietary needs, complaints | After A1-35 |
| A1-37 | At the Market | Quantities, prices, bargaining basics | After A1-36 |
| A1-38 | At the Store | Checkout, payment methods, bags | After A1-37 |
| A1-39 | Buying Tickets | Metro, bus, train tickets | After A1-38 |
| A1-40 | Taking Transport | On the bus/metro, stops, transfers | After A1-39 |
| A1-41 | Phone Basics | Answering, "wrong number", simple messages | After A1-40 |
| A1-42 | Introductions Extended | Detailed self-intro, meeting people | After A1-41 |
| A1-43 | Emergency Basics | Help, police, hospital, lost | After A1-42 |
| A1-44 | A1 Practical Checkpoint | Assessment of practical scenarios | After A1-43 |

**Note:** These may require renumbering existing M34 checkpoint or inserting after it.

#### A2 New Modules (~12 modules)

| New # | Title | Content | Placement |
|-------|-------|---------|-----------|
| A2-59 | At the Doctor | Symptoms, body parts review, prescriptions | After M58 |
| A2-60 | At the Pharmacy | Medications, dosages, side effects | After A2-59 |
| A2-61 | Hotel Check-in | Reservations, room types, amenities | After A2-60 |
| A2-62 | Apartment Rental | Viewing, lease terms, utilities | After A2-61 |
| A2-63 | Making Appointments | Scheduling, confirming, cancelling | After A2-62 |
| A2-64 | Job Interview Basics | Introduction, experience, questions | After A2-63 |
| A2-65 | Giving Directions | Landmarks, distance, navigation | After A2-64 |
| A2-66 | Asking for Directions | When lost, using maps, public transit | After A2-65 |
| A2-67 | Social Media Ukrainian | Posts, comments, messaging style | After A2-66 |
| A2-68 | Texting & Messaging | Abbreviations, emoji, informal register | After A2-67 |
| A2-69 | Online Services | Banking app, delivery, booking | After A2-68 |
| A2-70 | A2 Practical Checkpoint | Assessment of practical scenarios | After A2-69 |

#### B1 New Modules (~8 modules)

| New # | Title | Content | Placement |
|-------|-------|---------|-----------|
| B1-92 | Email Writing Basics | Structure, greetings, closings | After M91 |
| B1-93 | Formal Letters | Official requests, complaints | After B1-92 |
| B1-94 | Informal Correspondence | Friends, family, casual tone | After B1-93 |
| B1-95 | Podcast Listening I | News podcasts, note-taking | After B1-94 |
| B1-96 | Podcast Listening II | Interview podcasts, following argument | After B1-95 |
| B1-97 | Expressing Opinions | Agreement, disagreement, hedging | After B1-96 |
| B1-98 | Debate Skills | Argumentation, counterpoints | After B1-97 |
| B1-99 | B1 Skills Checkpoint | Assessment of communication skills | After B1-98 |

#### B2 New Modules (~10 modules)

These become the CORE B2 skills modules (part of core, not B2-PRO track):

| New # | Title | Content | Placement |
|-------|-------|---------|-----------|
| B2-85 | Professional Email I | Formal structure, requests | After current skills |
| B2-86 | Professional Email II | Follow-ups, attachments, threads | After B2-85 |
| B2-87 | Meeting Participation | Vocabulary, phrases, protocols | After B2-86 |
| B2-88 | Meeting Facilitation | Leading discussions, summarizing | After B2-87 |
| B2-89 | Presentation Structure | Openings, transitions, conclusions | After B2-88 |
| B2-90 | Presentation Delivery | Visual aids, Q&A handling | After B2-89 |
| B2-91 | Reading Technical Docs | Manuals, specifications | After B2-90 |
| B2-92 | Summarizing Information | Reports, briefs, abstracts | After B2-91 |
| B2-93 | B2 Core Integration | Combining all B2 skills | After B2-92 |
| B2-94 | B2 Core Capstone | Final B2 core assessment | After B2-93 |

---

### Phase 2: Relocate History & Biography to Tracks

#### B2-HIST Track (from B2 M71-131)

**Source:** `curriculum/l2-uk-en/b2/71-*.md` through `curriculum/l2-uk-en/b2/131-*.md`
**Destination:** `curriculum/l2-uk-en/b2-hist/01-*.md` through `curriculum/l2-uk-en/b2-hist/61-*.md`

| Old Path | New Path | New Module # |
|----------|----------|--------------|
| b2/71-kyivan-rus-origins.md | b2-hist/01-kyivan-rus-origins.md | B2-HIST-01 |
| b2/72-*.md | b2-hist/02-*.md | B2-HIST-02 |
| ... | ... | ... |
| b2/131-*.md | b2-hist/61-*.md | B2-HIST-61 |

**Curriculum Plan:** Create `B2-HIST-CURRICULUM-PLAN.md`

#### C1-BIO Track (from C1 M36-131)

**Source:** `curriculum/l2-uk-en/c1/36-*.md` through `curriculum/l2-uk-en/c1/131-*.md`
**Destination:** `curriculum/l2-uk-en/c1-bio/01-*.md` through `curriculum/l2-uk-en/c1-bio/96-*.md`

| Old Path | New Path | New Module # |
|----------|----------|--------------|
| c1/36-*.md | c1-bio/01-*.md | C1-BIO-01 |
| c1/37-*.md | c1-bio/02-*.md | C1-BIO-02 |
| ... | ... | ... |
| c1/131-*.md | c1-bio/96-*.md | C1-BIO-96 |

**Curriculum Plan:** Create `C1-BIO-CURRICULUM-PLAN.md`

---

### Phase 3: Renumber Core Modules After Relocation

#### B2 Core Renumbering

After moving M71-131 to b2-hist:

| Old # | New # | Content |
|-------|-------|---------|
| M01-40 | M01-40 | Grammar (unchanged) |
| M41-70 | M41-70 | Phraseology (unchanged) |
| M132-145 | M71-84 | Skills & Capstone (renumbered) |
| NEW | M85-94 | New professional basics modules |

**New B2 Core total:** 94 modules

#### C1 Core Renumbering

After moving M36-131 to c1-bio:

| Old # | New # | Content |
|-------|-------|---------|
| M01-20 | M01-20 | Academic Foundation (unchanged) |
| M21-35 | M21-35 | Professional & Social (unchanged) |
| M132-151 | M36-55 | Advanced Stylistics (renumbered) |
| M152-187 | M56-91 | Folk Culture & Arts (renumbered) |
| M188-202 | M92-106 | Literature Complete (renumbered) |

**New C1 Core total:** 106 modules

---

### Phase 4: Create New Tracks

#### B2-PRO Track (40 modules)

**Purpose:** Business and professional Ukrainian for career-focused learners
**Prerequisite:** B2 Core (M01-70)
**Folder:** `curriculum/l2-uk-en/b2-pro/`

| Phase | Modules | Content |
|-------|---------|---------|
| B2-PRO.1 | M01-15 | Business Communication |
| B2-PRO.2 | M16-30 | Technical & Domain-Specific |
| B2-PRO.3 | M31-40 | Media & Public Discourse |

**Detailed Module Plan:**

**Phase B2-PRO.1: Business Communication (M01-15)**
| # | Title | Content |
|---|-------|---------|
| 01 | Business Email Foundations | Tone, structure, etiquette |
| 02 | Email: Requests & Proposals | Asking, offering, negotiating |
| 03 | Email: Follow-ups & Threads | Continuing conversations |
| 04 | Business Letters | Formal correspondence |
| 05 | Proposals & Bids | Writing competitive proposals |
| 06 | Meeting Vocabulary | Terms, roles, procedures |
| 07 | Meeting Participation | Contributing, questioning |
| 08 | Meeting Facilitation | Leading, summarizing, action items |
| 09 | Negotiation Language | Persuasion, compromise |
| 10 | Negotiation Scenarios | Salary, contracts, partnerships |
| 11 | Phone & Video Calls | Professional etiquette |
| 12 | Small Talk & Networking | Building relationships |
| 13 | Business Checkpoint | Assessment M01-12 |
| 14 | Business Writing Integration | Combined practice |
| 15 | Business Communication Capstone | Final business assessment |

**Phase B2-PRO.2: Technical & Domain-Specific (M16-30)**
| # | Title | Content |
|---|-------|---------|
| 16 | IT Vocabulary I | Hardware, software, systems |
| 17 | IT Vocabulary II | Development, cloud, security |
| 18 | Technical Documentation | Reading specs, manuals |
| 19 | Legal Basics | Contracts, terms, clauses |
| 20 | Legal Documents | Reading and summarizing |
| 21 | Legal Correspondence | Formal legal writing |
| 22 | Finance Vocabulary | Banking, investment, accounting |
| 23 | Financial Reports | Reading balance sheets |
| 24 | Finance Communication | Client communication |
| 25 | Medical Ukrainian | Healthcare terminology |
| 26 | Medical Scenarios | Patient, provider communication |
| 27 | Scientific Writing Basics | Research vocabulary |
| 28 | Technical Checkpoint | Assessment M16-27 |
| 29 | Cross-Domain Practice | Combined technical scenarios |
| 30 | Technical Integration | Final technical assessment |

**Phase B2-PRO.3: Media & Public Discourse (M31-40)**
| # | Title | Content |
|---|-------|---------|
| 31 | News Analysis I | Reading Ukrainian news critically |
| 32 | News Analysis II | Bias detection, source evaluation |
| 33 | Journalism Writing | Article structure, headlines |
| 34 | Public Speaking I | Speech structure, delivery |
| 35 | Public Speaking II | Persuasion, audience awareness |
| 36 | Debate Skills Advanced | Formal debate structure |
| 37 | Interview Skills | Being interviewed, interviewing |
| 38 | Media Checkpoint | Assessment M31-37 |
| 39 | B2-PRO Integration | Combined professional practice |
| 40 | B2-PRO Capstone | Final track assessment |

**Curriculum Plan:** Create `B2-PRO-CURRICULUM-PLAN.md`

#### C1-PRO Track (50 modules)

**Purpose:** Advanced professional and academic Ukrainian
**Prerequisite:** B2-PRO or B2 Core + demonstrated need
**Folder:** `curriculum/l2-uk-en/c1-pro/`

| Phase | Modules | Content |
|-------|---------|---------|
| C1-PRO.1 | M01-15 | Executive Communication |
| C1-PRO.2 | M16-30 | Academic Publishing |
| C1-PRO.3 | M31-45 | Industry Specialization |
| C1-PRO.4 | M46-50 | Mastery & Capstone |

**High-level Content:**
- Executive communication (board meetings, stakeholder management)
- Academic publishing (journal articles, peer review, conferences)
- Industry deep dives (choose 2-3 domains)
- Translation and interpretation basics
- Cross-cultural business communication
- Leadership and management language

**Curriculum Plan:** Create `C1-PRO-CURRICULUM-PLAN.md` (detailed module specs TBD)

---

## Part 4: New Curriculum Plan Documents

### Documents to Create

| Document | Purpose |
|----------|---------|
| `B2-HIST-CURRICULUM-PLAN.md` | Plan for relocated B2 History track |
| `C1-BIO-CURRICULUM-PLAN.md` | Plan for relocated C1 Biography track |
| `B2-PRO-CURRICULUM-PLAN.md` | Plan for new B2 Professional track |
| `C1-PRO-CURRICULUM-PLAN.md` | Plan for new C1 Professional track |

### Documents to Update

| Document | Changes |
|----------|---------|
| `A1-CURRICULUM-PLAN.md` | Add practical scenario modules (A1-35 to A1-44) |
| `A2-CURRICULUM-PLAN.md` | Add practical scenario modules (A2-59 to A2-70) |
| `B1-CURRICULUM-PLAN.md` | Add skills modules (B1-92 to B1-99) |
| `B2-CURRICULUM-PLAN.md` | Remove history section, add core skills, update phase structure |
| `C1-CURRICULUM-PLAN.md` | Remove biography section, renumber, update phase structure |
| `template_mappings.yaml` | Add mappings for b2-hist, c1-bio, b2-pro, c1-pro |

---

## Part 5: Template Requirements

### New Templates to Create

| Template | For |
|----------|-----|
| `a1-practical-module-template.md` | A1 scenario modules |
| `a2-practical-module-template.md` | A2 scenario modules |
| `b1-skills-module-template.md` | B1 correspondence/listening |
| `b2-pro-module-template.md` | B2 Professional track |
| `c1-pro-module-template.md` | C1 Professional track |
| `b2-hist-module-template.md` | B2 History track (adapt from existing) |
| `c1-bio-module-template.md` | C1 Biography track (adapt from existing) |

---

## Part 6: Module Count Summary

### Before Reorganization

| Level/Track | Modules |
|-------------|---------|
| A1 | 34 |
| A2 | 58 |
| B1 | 91 |
| B2 | 145 |
| C1 | 202 |
| C2 | 100 |
| LIT | 30 |
| OES | 30 |
| RUTH | 30 |
| **TOTAL** | **720** |

### After Reorganization

| Level/Track | Modules | Status |
|-------------|---------|--------|
| **CORE PATH** | | |
| A1 Core | 44 | 34 existing + 10 new |
| A2 Core | 70 | 58 existing + 12 new |
| B1 Core | 99 | 91 existing + 8 new |
| B2 Core | 94 | 70 existing + 14 existing + 10 new |
| C1 Core | 106 | 35 + 20 + 36 + 15 (renumbered) |
| C2 Core | 100 | unchanged |
| **Core Total** | **513** | |
| | | |
| **SPECIALIZED TRACKS** | | |
| B2-HIST | 61 | relocated from B2 |
| C1-BIO | 96 | relocated from C1 |
| B2-PRO | 40 | new |
| C1-PRO | 50 | new |
| LIT | 30 | existing |
| OES | 30 | planned |
| RUTH | 30 | planned |
| **Tracks Total** | **337** | |
| | | |
| **GRAND TOTAL** | **850** | +130 from current |

---

## Part 7: Implementation Phases

### Prerequisites (Do First)
- [ ] Complete A1-C1 to production ready status
- [ ] All existing modules pass audit and pipeline
- [ ] Document current state in version control

### Phase A: Planning Complete
- [ ] This document finalized
- [ ] GitHub issue created for tracking
- [ ] Team review and approval

### Phase B: Infrastructure Updates
- [ ] Update `template_mappings.yaml` for new tracks
- [ ] Create new folder structure
- [ ] Update pipeline scripts to handle new paths
- [ ] Update audit scripts for new tracks
- [ ] Update MDX generator for new track routing

### Phase C: Content Relocation
- [ ] Move B2 M71-131 to b2-hist (with renumbering script)
- [ ] Move C1 M36-131 to c1-bio (with renumbering script)
- [ ] Renumber B2 core (M132-145 → M71-84)
- [ ] Renumber C1 core (M132-202 → M36-106)
- [ ] Update all internal references and links

### Phase D: Create New Curriculum Plans
- [ ] Create B2-HIST-CURRICULUM-PLAN.md
- [ ] Create C1-BIO-CURRICULUM-PLAN.md
- [ ] Create B2-PRO-CURRICULUM-PLAN.md
- [ ] Create C1-PRO-CURRICULUM-PLAN.md
- [ ] Update existing curriculum plans (A1, A2, B1, B2, C1)

### Phase E: Create New Modules
- [ ] A1 practical scenarios (10 modules)
- [ ] A2 practical scenarios (12 modules)
- [ ] B1 skills modules (8 modules)
- [ ] B2 core skills (10 modules)

### Phase F: Create New Tracks
- [ ] B2-PRO modules (40 modules)
- [ ] C1-PRO modules (50 modules)

### Phase G: Validation
- [ ] All modules pass audit
- [ ] All modules pass pipeline
- [ ] Landing pages updated
- [ ] Documentation updated

---

## Part 8: Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing links | HIGH | Use redirect mapping, update all refs |
| Module renumbering errors | HIGH | Automated scripts with verification |
| Template mismatches | MEDIUM | Validate templates before creation |
| Pipeline failures | MEDIUM | Test on single module first |
| Scope creep | MEDIUM | Strict phase gating |

---

## Part 9: Open Questions

1. **A1 Checkpoint:** Should A1-34 checkpoint remain as M34, or move to after new practical modules?
2. **B2 Prerequisites:** Should B2-PRO require B2-HIST or just B2 Core?
3. **Track Sequencing:** Can tracks be done in parallel or must follow sequence?
4. **LIT Expansion:** When/how to expand LIT to include modern literature?
5. **Localization:** Should track names be in Ukrainian for immersed learners?

---

## Appendix A: Track Prerequisite Map

```
A1 Core (44)
    │
    ▼
A2 Core (70)
    │
    ▼
B1 Core (99)
    │
    ▼
B2 Core (94) ──────────────────────────────┐
    │                                       │
    ├───► B2-HIST (61) ───► C1-BIO (96)    │
    │                                       │
    └───► B2-PRO (40) ───► C1-PRO (50)     │
                                            │
    ┌───────────────────────────────────────┘
    ▼
C1 Core (106)
    │
    ├───► LIT (30) ───► [expand later]
    │
    ├───► OES (30)
    │
    └───► RUTH (30)
    │
    ▼
C2 Core (100)
```

---

## Appendix B: File Naming Conventions

### Core Levels
- `a1/01-module-slug.md` through `a1/44-module-slug.md`
- `a2/01-module-slug.md` through `a2/70-module-slug.md`
- etc.

### Specialized Tracks
- `b2-hist/01-module-slug.md` through `b2-hist/61-module-slug.md`
- `c1-bio/01-module-slug.md` through `c1-bio/96-module-slug.md`
- `b2-pro/01-module-slug.md` through `b2-pro/40-module-slug.md`
- `c1-pro/01-module-slug.md` through `c1-pro/50-module-slug.md`

### Curriculum Plans
- `B2-HIST-CURRICULUM-PLAN.md`
- `C1-BIO-CURRICULUM-PLAN.md`
- `B2-PRO-CURRICULUM-PLAN.md`
- `C1-PRO-CURRICULUM-PLAN.md`

---

*Last updated: 2026-01-11*
