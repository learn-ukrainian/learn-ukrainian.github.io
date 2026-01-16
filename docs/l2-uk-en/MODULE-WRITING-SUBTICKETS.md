# Module Writing Subtickets

**Created:** 2026-01-15
**Source:** RFC #409 Plan Verification

This document contains subtickets for writing all missing modules. Each ticket can be assigned to an agent.

---

## Priority 0: Prerequisite — Rename Existing "Final" Modules

**⚠️ MUST BE DONE BEFORE WRITING NEW MODULES**

When we expand levels with new practical/skills modules, the existing "final" checkpoints become mid-level checkpoints. These need to be renamed to avoid confusion.

### Ticket RENAME-FINALS: Rename Existing Final Checkpoints

**Status:** Not started

| Level | Module | Current Name | New Name | Reason |
|-------|--------|--------------|----------|--------|
| A1 | M34 | `checkpoint-final-review` | `checkpoint-core-grammar` | Confirms grammar readiness before M35-44 practical |
| A2 | M56 | `checkpoint-vocabulary-expansion` | `checkpoint-full-grammar` | Confirms grammar readiness before M57-70 practical |
| B1 | M89 | `b1-grammar-integration` | `checkpoint-grammar-synthesis` | Confirms grammar readiness before M90-99 skills |
| B2 | M84 | `b2-finalnyy-ispyt` | `checkpoint-register-synthesis` | Confirms register readiness before M85-94 communication |

> **Note:** A2 M57-58 and B1 M90-91 were repurposed from review/integration modules to practical content.
> See A2-CURRICULUM-PLAN.md and B1-CURRICULUM-PLAN.md for the new module specifications.

**Files to update per module:**
1. `curriculum/l2-uk-en/{level}/meta/{num}-{old-slug}.yaml` → rename file + update `title`
2. `curriculum/l2-uk-en/{level}/{num}-{old-slug}.md` → rename file + update title
3. `curriculum/l2-uk-en/{level}/activities/{old-slug}.yaml` → rename file
4. `curriculum/l2-uk-en/{level}/vocabulary/{old-slug}.yaml` → rename file (if exists)
5. `docusaurus/docs/{level}/module-{num}.mdx` → regenerate after rename
6. Update any cross-references in curriculum plans

**Instructions:**
- Use `git mv` for file renames to preserve history
- Update internal `title:` and `slug:` fields in YAML/MD files
- Run `npm run pipeline` to regenerate MDX files
- The NEW final checkpoints (M44, M70, M99, M94) will be the true level assessments

---

## Priority 1: RFC #409 New Practical Modules (40 modules total)

These modules fill gaps identified in RFC #409 Curriculum Reorganization.

### Ticket A1-PRACTICAL: A1 Practical Scenarios (M35-44)

**Level:** A1
**Modules:** 10
**Status:** Not started
**Depends on:** RENAME-FINALS (M34 must be renamed first)

| Module | Slug | Title | Content |
|--------|------|-------|---------|
| M35 | at-the-cafe | At the Café | Ordering drinks, basic transactions |
| M36 | at-the-restaurant | At the Restaurant | Ordering food, understanding menus |
| M37 | at-the-market | At the Market | Buying produce, negotiating |
| M38 | at-the-store | At the Store | Shopping basics, asking for items |
| M39 | buying-tickets | Buying Tickets | Transport tickets, events |
| M40 | taking-transport | Taking Transport | Using buses, metro, taxis |
| M41 | phone-basics | Phone Basics | Simple calls, voicemail |
| M42 | introductions-extended | Introductions Extended | Meeting new people, small talk |
| M43 | emergency-basics | Emergency Basics | Help, police, medical |
| M44 | a1-final-exam | A1 Final Exam | CUMULATIVE: All A1 grammar + practical |

**Instructions:**
- Read `docs/l2-uk-en/A1-CURRICULUM-PLAN.md` for vocabulary/grammar constraints
- Read `docs/l2-uk-en/templates/` for module template
- Immersion: 25-50% Ukrainian
- Activity count: 8+ per module

---

### Ticket A2-PRACTICAL: A2 Practical Scenarios (M57-70)

**Level:** A2
**Modules:** 14 (M57-58 repurposed, M59-70 new)
**Status:** Not started

> **Note:** M57-58 are repurposed from review modules. Update their content to practical scenarios.
> See A2-CURRICULUM-PLAN.md Phase A2.6 for specifications.

| Module | Slug | Title | Content |
|--------|------|-------|---------|
| M57 | practical-intro | Practical Introduction | Overview of real-world scenarios |
| M58 | practical-warm-up | Practical Warm-up | Transition exercises |
| M59 | at-the-doctor | At the Doctor | Medical appointments, symptoms |
| M60 | at-the-pharmacy | At the Pharmacy | Buying medicine, prescriptions |
| M61 | hotel-accommodation | Hotel Accommodation | Booking, check-in, complaints |
| M62 | rental-accommodation | Rental Accommodation | Renting apartments, contracts |
| M63 | scheduling-appointments | Scheduling Appointments | Making appointments |
| M64 | scheduling-interviews | Scheduling Interviews | Job interviews, preparation |
| M65 | social-situations-formal | Social Situations: Formal | Formal events, etiquette |
| M66 | social-situations-informal | Social Situations: Informal | Casual gatherings, friends |
| M67 | modern-communication-email | Modern Communication: Email | Basic emails, messaging |
| M68 | modern-communication-social | Modern Communication: Social | Social media, chat |
| M69 | combined-practice | Combined Practice | Integration of M57-68 |
| M70 | a2-final-exam | A2 Final Exam | CUMULATIVE: All A2 grammar + practical |

**Instructions:**
- Read `docs/l2-uk-en/A2-CURRICULUM-PLAN.md` for vocabulary/grammar constraints
- Immersion: 65-80% Ukrainian
- Activity count: 8+ per module

---

### Ticket B1-SKILLS: B1 Communication Skills (M90-99)

**Level:** B1
**Modules:** 10 (M90-91 repurposed, M92-99 new)
**Status:** Not started

> **Note:** M90-91 are repurposed from integration review modules. Update their content to communication skills.
> See B1-CURRICULUM-PLAN.md Phase B1.9 for specifications.

| Module | Slug | Title | Content |
|--------|------|-------|---------|
| M90 | grammar-in-context | Grammar in Context | Applying grammar to practical communication |
| M91 | vocabulary-in-context | Vocabulary in Context | Applying vocabulary to practical communication |
| M92 | email-writing-basics | Email Writing Basics | Structure, tone, common phrases |
| M93 | formal-letters | Formal Letters | Official correspondence |
| M94 | informal-writing | Informal Writing | Personal messages, blogs |
| M95 | podcast-listening | Podcast Listening | Comprehension strategies |
| M96 | note-taking-skills | Note-taking Skills | Lectures, meetings |
| M97 | discussion-skills | Discussion Skills | Expressing opinions, agreeing/disagreeing |
| M98 | debate-basics | Debate Basics | Argumentation, counterarguments |
| M99 | b1-final-exam | B1 Final Exam | CUMULATIVE: All B1 grammar + skills |

**Instructions:**
- Read `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`
- Immersion: 75-90% Ukrainian
- Activity count: 12+ per module

---

### Ticket B2-COMM: B2 Communication Skills (M85-94)

**Level:** B2
**Modules:** 10
**Status:** Not started

| Module | Slug | Title | Content |
|--------|------|-------|---------|
| M85 | professional-email-basics | Professional Email: Basics | Business email structure |
| M86 | professional-email-advanced | Professional Email: Advanced | Complex correspondence |
| M87 | professional-reports-basics | Professional Reports: Basics | Report structure |
| M88 | professional-reports-advanced | Professional Reports: Advanced | Data presentation |
| M89 | news-analysis-basics | News Analysis: Basics | Reading news critically |
| M90 | news-analysis-advanced | News Analysis: Advanced | Media bias, rhetoric |
| M91 | presentation-skills-basics | Presentation Skills: Basics | Structure, delivery |
| M92 | presentation-skills-advanced | Presentation Skills: Advanced | Q&A, persuasion |
| M93 | discussion-debate | Discussion & Debate | Professional discussions |
| M94 | b2-final-exam | B2 Final Exam | CUMULATIVE: All B2 grammar + skills |

**Instructions:**
- Read `docs/l2-uk-en/B2-CURRICULUM-PLAN.md`
- Immersion: 100% Ukrainian
- Activity count: 12+ per module

---

## Priority 2: C2 Core Curriculum (100 modules)

### Ticket C2-CORE: C2 Full Curriculum (M01-100)

**Level:** C2
**Modules:** 100
**Status:** Not started (0/100 written)

This is a large ticket that should be broken into sub-tickets:

- **C2-P1:** Morphological Mastery (M01-30) — 30 modules
- **C2-P2:** Literary Writing (M31-50) — 20 modules
- **C2-P3:** Academic/Professional Writing (M51-70) — 20 modules
- **C2-P4:** Rhetoric & Public Speaking (M71-90) — 20 modules
- **C2-P5:** Specialization & Capstone (M91-100) — 10 modules

**Instructions:**
- Read `docs/l2-uk-en/C2-CURRICULUM-PLAN.md` for full specifications
- Immersion: 100% Ukrainian
- Activity count: 16+ per module
- Model answers required for all creative tasks

---

## Priority 3: Professional Tracks (90 modules)

### Ticket B2-PRO-FULL: B2 Professional Track (M01-40)

**Level:** B2-PRO
**Modules:** 40
**Status:** Not started (0/40 written)

**Phases:**
- **B2-PRO.1:** Business Communication (M01-15) — 15 modules
- **B2-PRO.2:** Technical & Domain-Specific (M16-30) — 15 modules
- **B2-PRO.3:** Media & Public Discourse (M31-40) — 10 modules

**Instructions:**
- Read `docs/l2-uk-en/B2-PRO-CURRICULUM-PLAN.md`
- Immersion: 100% Ukrainian
- Activity count: 12+ per module

---

### Ticket C1-PRO-FULL: C1 Professional Mastery Track (M01-50)

**Level:** C1-PRO
**Modules:** 50
**Status:** Not started (0/50 written)

**Phases:**
- **C1-PRO.1:** Executive Communication (M01-15) — 15 modules
- **C1-PRO.2:** Academic Publishing (M16-30) — 15 modules
- **C1-PRO.3:** Industry Specialization (M31-40) — 10 modules
- **C1-PRO.4:** Translation & Cross-Cultural (M41-50) — 10 modules

**Instructions:**
- Read `docs/l2-uk-en/C1-PRO-CURRICULUM-PLAN.md`
- Immersion: 100% Ukrainian
- Activity count: 16+ per module

---

## Priority 4: Literature Track (16 remaining modules)

### Ticket LIT-REMAINING: Literature Track Completion

**Level:** LIT
**Modules:** 16 remaining (14 written, 16 to write)
**Status:** In progress

**Remaining modules per LIT-CURRICULUM-PLAN.md:**
- Check which modules LIT-015 through LIT-030 need writing
- Each module focuses on one author or work
- 100% Ukrainian, no English

**Instructions:**
- Read `docs/l2-uk-en/LIT-CURRICULUM-PLAN.md`
- Read `docs/l2-uk-en/templates/lit-module-template.md`
- Activity count: 16+ per module

---

## Summary Table

| Ticket | Level | Modules | Priority | Effort |
|--------|-------|---------|----------|--------|
| A1-PRACTICAL | A1 | 10 | 1 | Medium |
| A2-PRACTICAL | A2 | 12 | 1 | Medium |
| B1-SKILLS | B1 | 8 | 1 | Medium |
| B2-COMM | B2 | 10 | 1 | Medium |
| C2-CORE | C2 | 100 | 2 | Very High |
| B2-PRO-FULL | B2-PRO | 40 | 3 | High |
| C1-PRO-FULL | C1-PRO | 50 | 3 | High |
| LIT-REMAINING | LIT | 16 | 4 | Medium |
| **TOTAL** | — | **246** | — | — |

---

## Assignment Guidelines

When assigning these tickets to agents:

1. **Use the appropriate skill:** `/module-create` for full module creation
2. **Provide context:** Point agent to the curriculum plan and template
3. **Set expectations:** Specify activity count and immersion level
4. **Review output:** Run `/module-stage-4` for quality check

---

*Last updated: 2026-01-15*
