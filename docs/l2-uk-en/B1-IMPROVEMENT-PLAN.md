# B1 Improvement Action Plan

**Created:** 2024-12-14
**Status:** Ready for implementation
**Scope:** B1 Curriculum Plan + Module Standards

This document consolidates improvement recommendations from pedagogical review before continuing B1 module development.

---

## Priority Matrix

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| P0 | State Standard 2024 gaps (participles, one-member sentences, synthetic future, passive -но/-то) | CEFR compliance | High |
| P0 | Fix vocabulary target discrepancy | Prevents confusion | Trivial |
| P0 | Add B1-skills module type | Correct audit targets | Low |
| P1 | Add assessment rubrics (M80) | CEFR alignment | Medium |
| P1 | Enhance checkpoint template | Better review | Medium |
| P1 | Add production activities to module template | Skill building | Low |
| P2 | Restructure M07-08 (aspect pairs) | Reduce fatigue | Medium |
| P2 | Add metacognition elements | Learner awareness | Low |
| P2 | Add spiral review pattern | Retention | Low |
| P3 | External resource integration | Authentic input | Medium |
| P3 | Add error anticipation boxes | L1 interference | Low |
| P3 | Add authentic task per module | Real-world skills | Medium |
| P3 | Audio placeholders | Future-proofing | Trivial |

---

## P0: Critical Fixes (Do First)

### 0. State Standard 2024 Compliance Gaps

**Priority:** P0 (Critical)
**Effort:** High
**Reference:** `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
**GitHub Issue:** [#113](https://github.com/krisztiankoos/curricula-opus/issues/113)

The Ukrainian State Standard 2024 (Каталог В) requires these grammar structures at B1 that need explicit coverage:

| Gap | Ukrainian Term | Action |
|-----|---------------|--------|
| Participle phrases | Дієприкметниковий зворот | Add dedicated module on adjectival participle phrases |
| Gerund phrases | Дієприслівниковий зворот | Add dedicated module on adverbial participle phrases |
| One-member sentences | Односкладні речення | Add coverage: означено-особові, неозначено-особові, безособові |
| Impersonal constructions | Безособові речення | Expand beyond basic "болить" pattern |
| Synthetic future | Майбутній синтетичний | Add explicit teaching of synthetic future (читатиму) |
| Passive -но/-то | Пасивні форми на -но/-то | Add coverage: Книгу написано. Двері зачинено. |

**Participle phrases implementation:**
```markdown
## Дієприкметниковий зворот — Participle Phrases

> [!observe] Pattern Discovery
>
> Ukrainian uses participle phrases where English often uses relative clauses:
>
> - Книга, **написана** автором → The book **written** by the author
> - Студент, **який читає** книгу → The student **reading** a book

| Type | Formation | Example |
|------|-----------|---------|
| Active present | -учий/-ячий | читаючий студент (reading student) |
| Active past | -вший/-лий | прочитавший студент (student who read) |
| Passive | -ний/-тий | написана книга (written book) |
```

**One-member sentences implementation:**
```markdown
## Односкладні речення — One-Member Sentences

| Type | Ukrainian | Example | Meaning |
|------|-----------|---------|---------|
| Означено-особові | definite-personal | Читаю книгу. | (I) am reading. |
| Неозначено-особові | indefinite-personal | Кажуть, що... | They say that... |
| Безособові | impersonal | Холодно. Можна. | It's cold. It's allowed. |
```

**Synthetic future implementation:**
```markdown
## Майбутній синтетичний — Synthetic Future

> [!observe] Two Ways to Say "I will read"
>
> - **Analytic:** буду читати (I will read - process)
> - **Synthetic:** читатиму (I will read - shorter form)

| Pronoun | Analytic | Synthetic |
|---------|----------|-----------|
| я | буду читати | читатиму |
| ти | будеш читати | читатимеш |
| він/вона | буде читати | читатиме |
| ми | будемо читати | читатимемо |
| ви | будете читати | читатимете |
| вони | будуть читати | читатимуть |
```

**Passive -но/-то implementation:**
```markdown
## Пасивні форми на -но/-то

> [!observe] Impersonal Passive
>
> Ukrainian has a special impersonal passive form:
> - Книгу написано. (The book has been written.)
> - Двері зачинено. (The door has been closed.)

| Active | Passive -но/-то |
|--------|-----------------|
| Він написав книгу | Книгу написано |
| Вона зачинила двері | Двері зачинено |
| Ми виконали роботу | Роботу виконано |
```

**Action:**
- [ ] Add participle phrase module to B1.2 (Motion Verbs & Participles phase)
- [ ] Add gerund phrase module (дієприслівниковий зворот)
- [ ] Add one-member sentences coverage to Complex Sentences phase (B1.3)
- [ ] Expand impersonal constructions beyond "болить" pattern
- [ ] Add synthetic future explicit teaching to appropriate module
- [ ] Add passive -но/-то forms to Passive Voice section

---

### 1. Fix Vocabulary Target Discrepancy

**Priority:** P0 (Critical)
**GitHub Issue:** [#114](https://github.com/krisztiankoos/curricula-opus/issues/114)

**Problem:** Header claims ~2,400 words, actual plan delivers ~1,630 words.

**File:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`

**Action:** Update line 5 from:
```markdown
**Vocabulary Target:** ~2,400 words (level), ~4,550 cumulative
```
To:
```markdown
**Vocabulary Target:** ~1,630 words (level), ~3,430 cumulative
```

**Rationale:** The detailed vocabulary summary is accurate. 1,630 new words at B1 is appropriate for CEFR expectations.

---

### 2. Add B1-skills Module Type

**Problem:** M76-80 are skills modules but classified as vocabulary modules, causing incorrect audit targets.

**File:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

**Action:** Add new module type classification:

```markdown
### B1 Module Types

| Type | Modules | Min Words | Vocab | Immersion | Focus |
|------|---------|-----------|-------|-----------|-------|
| B1-grammar | 01-45 (excl. checkpoints) | 1250 | 20+ | 50-55% | Grammar acquisition |
| B1-vocab | 46-75 (excl. checkpoints) | 1250 | 25-30 | 60-65% | Thematic vocabulary |
| B1-skills | 76-79 | 1000 | 15-20 | 55-60% | Receptive skills, integration |
| B1-checkpoint | 10,20,35,45,55,65,75 | 800 | 10-15 | 60%+ | Review & assessment |
| B1-capstone | 80 | 1000 | 10 | 50%+ | Final assessment |
```

**Also update:** `scripts/audit/config.py` to recognize these module types.

---

## P1: High Priority (Do Before M06+)

### 3. Add Assessment Rubrics

**Problem:** M80 (Capstone) has no rubrics or CEFR alignment.

**File:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`

**Action:** Add new section after Vocabulary Summary:

```markdown
---

## B1 Exit Assessment Framework

### CEFR B1 Proficiency Descriptors

| Skill | B1 Descriptor | Assessment Evidence |
|-------|---------------|---------------------|
| Reading | Understands main points of clear standard texts on familiar matters | 70%+ on comprehension tasks |
| Writing | Can write simple connected text on familiar topics | 150+ words, logical structure, <5 major errors |
| Speaking | Can deal with most travel situations; can describe experiences | 2-min presentation, comprehensible delivery |
| Listening | Can understand main points of clear standard speech on familiar matters | 70%+ on listening comprehension |

### Ukrainian State Standard 2024 Exit Checklist

**Grammar (Каталог В) - Learner can:**
- [ ] Select correct aspect in all contexts (past, future, negation, imperative)
- [ ] Use motion verbs with appropriate prefixes
- [ ] Form and use adverbial participles (-ючи, -вши)
- [ ] Form and use passive constructions (-ний, -но)
- [ ] Construct all complex sentence types
- [ ] Use real (якщо) and unreal (якби) conditionals
- [ ] Use all three future forms appropriately

**Themes (Каталог Б) - Learner can discuss:**
- [ ] Society, politics, and institutions
- [ ] Media and communication
- [ ] Professional and work contexts
- [ ] Ukrainian regions and their characteristics
- [ ] Contemporary Ukrainian culture

### M80 Scoring Rubrics

#### Reading Comprehension (25 points)

| Score | Descriptor |
|-------|------------|
| 22-25 | Excellent: Understands main ideas and most supporting details accurately |
| 18-21 | Good: Understands main ideas, captures most details with minor gaps |
| 14-17 | Adequate: Understands main ideas, misses significant details |
| 10-13 | Developing: Partial understanding, frequent miscomprehension |
| 0-9 | Below B1: Does not demonstrate B1-level reading comprehension |

#### Writing Production (25 points)

| Criterion | 5 pts | 3 pts | 1 pt | 0 pts |
|-----------|-------|-------|------|-------|
| Task completion | Fully addresses all parts of prompt | Addresses most of prompt | Partially addresses prompt | Off-topic |
| Coherence | Clear logical flow with appropriate connectors | Generally organized with some gaps | Weak organization | No discernible structure |
| Grammar accuracy | 0-2 major errors | 3-5 major errors | 6-8 major errors | >8 major errors |
| Vocabulary range | Uses B1 vocabulary appropriately and varied | Adequate range with some repetition | Limited to high-frequency words | Basic A2 vocabulary only |
| Complexity | Regular use of complex sentences | Some complex sentences | Mostly simple sentences | Simple sentences only |

#### Grammar Test (25 points)

| Component | Points | Description |
|-----------|--------|-------------|
| Aspect selection | 8 | All contexts: past, future, negation, imperative |
| Motion verbs | 5 | Prefix meanings, uni/multi distinction |
| Participles | 4 | Adverbial and passive formation/usage |
| Complex sentences | 5 | Clause types, conjunctions, word order |
| Conditional | 3 | Real vs unreal, correct forms |

#### Vocabulary Test (25 points)

| Component | Points | Description |
|-----------|--------|-------------|
| Recognition | 10 | Match Ukrainian to English/definition |
| Production | 10 | Fill gaps with appropriate vocabulary |
| Collocation | 5 | Choose correct word combinations |

### Passing Threshold

**B1 Certificate:** 70+ points total (70%)
**B1 with Distinction:** 85+ points total (85%)

Learners scoring 60-69 receive "B1 Developing" designation with specific remediation recommendations.
```

---

### 4. Enhance Checkpoint Template

**Problem:** Checkpoint modules are sparse (10-15 vocab, basic activities, no self-assessment).

**File:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`

**Action:** Update all checkpoint module specifications to follow this template:

```markdown
#### Module XX: Checkpoint - [Phase Name]
**Review of:** Modules XX-XX
**Type:** B1-checkpoint

**CEFR Can-Do Targets (from this phase):**
- [ ] Can [specific descriptor 1]
- [ ] Can [specific descriptor 2]
- [ ] Can [specific descriptor 3]

**Assessment Areas:**
1. [Grammar point 1] - 5 items
2. [Grammar point 2] - 5 items
3. [Vocabulary domain] - 5 items
4. [Integrated skill] - 5 items

**Self-Assessment Rubric:**

| Skill | Not Yet (1) | Developing (2) | Achieved (3) |
|-------|-------------|----------------|--------------|
| [Skill 1] | Cannot do X without help | Can do X with support/time | Can do X independently |
| [Skill 2] | ... | ... | ... |
| [Skill 3] | ... | ... | ... |

**Vocabulary (15 words):** High-frequency items from M[XX-XX] requiring review

**Required Activities (minimum 10):**
1. **Diagnostic quiz** - 20 items covering all reviewed modules
2. **Authentic reading** - 250+ word text using target structures
3. **Error correction** - 10 items with common mistakes from phase
4. **Production task** - Write 100+ words using target structures
5. **Self-reflection** - What I can do / What I need to review
6. [Additional activities to reach 10 minimum]

**Remediation Guidance:**
- Score <60%: Review modules [specific list]
- Score 60-79%: Focus practice on [specific areas]
- Score 80%+: Ready to proceed
```

---

### 5. Add Production Activities to Module Template

**Problem:** Current modules are recognition-heavy (choose, identify, match). Limited production practice.

**File:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

**Action:** Add to Activity Requirements section:

```markdown
### Production Activity Requirements (B1+)

Each B1 grammar module MUST include at least 2 production activities:

#### Required Production Types (choose 2+):

**1. Guided Translation (translate)**
```markdown
## translate: Переклад з підказками
> Translate to Ukrainian using the target grammar.

1. I was reading all evening. (use: весь вечір)
   > [!answer] Я читав книгу весь вечір.
   > [!hint] Process = imperfective
```

**2. Sentence Transformation (transform)**
```markdown
## transform: Зміна виду
> Change the aspect and observe the meaning change.

1. Я читав книгу. (make result-focused)
   > [!answer] Я прочитав книгу.
   > [!explanation] Adding result focus requires perfective.
```

**3. Micro-Writing (micro-write)**
```markdown
## micro-write: Короткий текст
> Write 4-6 sentences about [topic] using both aspects.

**Prompt:** Describe your yesterday morning. Use at least 2 imperfective verbs (process) and 2 perfective verbs (completed actions).

**Model answer:**
Вчора вранці я прокинувся о сьомій (pf). Я снідав і дивився новини (impf, impf). Потім я поїхав на роботу (pf). Дорогою я слухав музику (impf).
```

**4. Dialogue Completion (dialogue-complete)**
```markdown
## dialogue-complete: Завершіть діалог
> Complete the dialogue using appropriate forms.

А: Що ти ___ (робити) вчора ввечері?
Б: Я ___ (читати) книгу. А потім ___ (подивитися) фільм.
А: І як, ___ (сподобатися)?
```

### Activity Balance Check

For B1-grammar modules, verify:
- Recognition activities: 8-10 (quiz, match-up, fill-in, true-false, etc.)
- Production activities: 2-4 (translate, transform, micro-write, dialogue-complete)
- Integrated activities: 2-3 (cloze, error-correction with explanation)
```

---

## P2: Medium Priority (Before M10 Checkpoint)

### 6. Restructure M07-08 (Aspect Pairs)

**Problem:** 10 consecutive aspect modules risks learner fatigue. M07-08 are pure vocabulary drilling.

**Current:**
```
M01-06: Aspect core
M07: Aspect Pairs Expansion I (30 pairs)
M08: Aspect Pairs Expansion II (30 pairs)
M09: Integration Practice
M10: Checkpoint
```

**Proposed:**
```
M01-06: Aspect core (unchanged)
M07: Aspect Pairs Combined (40 pairs - merge best from both)
M08: "Робочий тиждень" - Thematic Application Module (NEW)
M09: Integration Practice (unchanged)
M10: Checkpoint (unchanged)
```

**File:** `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`

**Action:**

1. Merge M07-08 vocabulary into single M07 (select 40 most useful pairs)
2. Create new M08 thematic module:

```markdown
#### Module 08: Робочий тиждень — Aspect in Action
**Type:** B1-grammar (thematic application)
**Grammar:** All aspect contexts applied to work/daily routine

**Scenario:** Follow a Ukrainian professional through their work week, using all aspect patterns naturally.

**Key Applications:**
- Describing daily routine (imperfective)
- Reporting completed tasks (perfective)
- Making plans (future aspect)
- Giving instructions to colleagues (imperative aspect)
- Explaining what you haven't done yet (negation)

**Vocabulary (20 words):**
робочий день, завдання, зустріч, дедлайн, проєкт, команда, колега, начальник, звіт, презентація, перерва, обід, нарада, домовленість, відрядження, відпустка, понеділок, п'ятниця, вихідні, тиждень

**Narrative Structure:**
- Понеділок: Planning the week (future aspect)
- Вівторок-четвер: Doing and completing tasks (past aspect, result/process)
- П'ятниця: Reporting what's done/not done (negation, "ще не")
- Weekend: Reflecting on habits (repeated actions)

**Signature Activity Concepts:**
1. Reading: "Тиждень Олени" - extended narrative
2. Role-play: Report to boss (что зробив/що ще не зробив)
3. Writing: Describe your typical work week
4. Dialogue: Planning meeting with colleague
```

---

### 7. Add Metacognition Elements

**Problem:** Learners don't know why they're learning aspect or how to self-assess.

**Action:** Add two standard elements to every B1 module template:

**A. "Why This Matters" box (after title, before Diagnostic):**

```markdown
> 🎯 **Чому це важливо**
>
> [2-3 sentences explaining real-world impact of this grammar point]
>
> Native speakers instantly notice wrong aspect choices. Mastering this distinction
> is what separates "textbook Ukrainian" from natural speech.
```

**B. "Self-Check" box (after Summary, before Словник):**

```markdown
> ✅ **Перевірте себе**
>
> Before moving on, can you:
> - [ ] [Key skill 1 from this module]?
> - [ ] [Key skill 2 from this module]?
> - [ ] [Key skill 3 from this module]?
>
> If you checked all boxes, proceed to the next module.
> If not, review the Analysis section and try the Practice activities again.
```

**File:** Add to module template in `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

---

### 8. Add Spiral Review Pattern

**Problem:** Linear progression with no systematic revisiting of previous material.

**Action:** Add 2-3 review items from previous module(s) to each module's Activities section.

**Template:**

```markdown
## quiz: Повторення (М[XX-1])
> Quick review from the previous module.

1. [Question testing M[XX-1] content]
   - [x] correct
   - [ ] distractor
   - [ ] distractor
   > [Explanation referencing previous module]

2. [Question testing M[XX-2] content if applicable]
   ...

3. [Question testing M[XX-1] content]
   ...
```

**Rule:**
- M02+: Include 3 review items from M(n-1)
- M05+: Include 2 items from M(n-1), 1 item from M(n-3)
- Checkpoints: Include items from entire phase

**File:** Add to activity requirements in `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

---

## P3: Lower Priority (Ongoing Improvement)

### 9. External Resource Integration

**Problem:** Modules lack authentic audio/video input. Placeholder "audio coming soon" isn't actionable.

**Solution:** Curate links to high-quality external resources:
- Ukrainian Lessons Podcast (Anna Ohoiko)
- ukrainianlessons.com grammar/vocab pages
- YouTube channels (TBD - user curating list)

**Integration Options (decide after resource gathering):**

| Option | Description | Use Case |
|--------|-------------|----------|
| Per-module links | Specific episode/video for each topic | Grammar modules with matching external content |
| Resource boxes | `> 📺 **Dive Deeper**` callout with 2-3 links | General enrichment |
| Dedicated section | "External Resources" after Activities | Comprehensive reference |
| Integrated tasks | "Watch this clip, then answer..." | Active listening practice |

**Template (draft):**

```markdown
> 📺 **Зовнішні ресурси**
>
> **Podcast:** [Ukrainian Lessons Ep. XX - Topic Name](url)
> *10 min listen - covers [specific point from this module]*
>
> **Video:** [Channel Name - Video Title](url)
> *5 min watch - native speaker examples of [grammar point]*
>
> **Reading:** [ukrainianlessons.com - Article](url)
> *Alternative explanation with additional examples*
```

**Status:** ⏳ Awaiting resource list from user

**Action items:**
- [ ] User gathers YouTube channels, podcast episodes, website links
- [ ] Map resources to modules (which content fits which topic)
- [ ] Decide integration format
- [ ] Add to module template
- [ ] Retrofit to existing modules

---

### 10. Add Error Anticipation Boxes

**Problem:** No explicit guidance on L1 interference patterns.

**Action:** Add 1-2 error anticipation boxes per grammar module:

```markdown
> ⚠️ **Типова помилка**
>
> English speakers often say: *"Я ніколи не прочитав цю книгу"*
>
> **Why:** English uses "have read" (perfective-like) with "never."
>
> **Ukrainian rule:** ніколи + недоконаний
>
> **Correct:** "Я ніколи не **читав** цю книгу."
```

**Common L1 interference points for B1:**
- Aspect: Using perfective with frequency markers
- Aspect: Using imperfective with "ще не"
- Motion: Confusing unidirectional/multidirectional
- Participles: Word order (English places participle phrases differently)
- Conditionals: Using future in "if" clause (якщо буду → якщо матиму)

---

### 11. Add Authentic Task per Module

**Problem:** Activities are drill-focused; limited real-world application.

**Action:** Add one authentic task to each module:

| Module | Authentic Task |
|--------|---------------|
| M01 | Read short Ukrainian news paragraph, identify all verb aspects |
| M02 | Listen to audio clip (future), mark single vs repeated events |
| M03 | Watch 30-sec video clip, describe using process + result |
| M04 | Write 5-sentence plan for tomorrow |
| M05 | "Proofread" a foreigner's text, correct aspect errors |
| M06 | Write 3 polite requests and 3 direct commands for workplace |
| M07 | Read job posting, identify aspect pairs in requirements |
| M08 | Role-play: phone call reporting on weekly tasks |
| M09 | Extended writing: "My last vacation" mixing all aspects |
| M10 | Full practice test simulating B1 assessment format |

**Template:**

```markdown
## authentic: [Task Name]
> [Real-world task description]

**Source:** [Authentic text/audio/video - can be placeholder for now]

**Task:** [What learner must do]

**Success criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

---

### 12. Audio Placeholders

**Problem:** All modules show "ℹ️ No audio" - no indication audio is planned.

**Action:** Add placeholder audio sections to module template:

```markdown
> 🔊 **Послухайте** *(Audio coming in future update)*
>
> - "Я читав книгу весь вечір" — hear imperfective rhythm
> - "Я прочитав книгу" — hear perfective finality
>
> *[Placeholder: Native speaker recordings will demonstrate aspect distinction]*
```

This signals to learners (and future content creators) that audio is part of the vision.

---

## Implementation Checklist

### Phase 1: Before M06 (Critical)

**GitHub Issue:** [#115](https://github.com/krisztiankoos/curricula-opus/issues/115) (Build modules 01-80)

- [ ] Fix vocabulary target in B1-CURRICULUM-PLAN.md header
- [ ] Add B1-skills module type to MODULE-RICHNESS-GUIDELINES-v2.md
- [ ] Update audit config to recognize new module types

### Phase 2: Before M10 (High Priority)
- [ ] Add assessment rubrics section to B1-CURRICULUM-PLAN.md
- [ ] Update checkpoint template (apply to M10 first)
- [ ] Add production activity requirements to guidelines
- [ ] Add production activities to M01-05 (retrofit)

### Phase 3: Before M20 (Medium Priority)
- [ ] Restructure M07-08 (merge + add thematic module)
- [ ] Add metacognition boxes to module template
- [ ] Add spiral review pattern to activity requirements
- [ ] Retrofit metacognition to M01-10

### Phase 4: Ongoing
- [ ] Gather external resources (YouTube, podcast, ukrainianlessons.com)
- [ ] Map resources to modules
- [ ] Add external resource integration to template
- [ ] Add error anticipation boxes as modules are written
- [ ] Add authentic tasks as modules are written
- [ ] Add audio placeholders to template

---

## Estimated Effort

| Task | Time Estimate |
|------|---------------|
| P0 fixes (vocab, module types) | 30 min |
| Assessment rubrics | 1-2 hours |
| Checkpoint template + apply to M10 | 1 hour |
| Production activity requirements | 30 min |
| Retrofit production to M01-05 | 2-3 hours |
| M07-08 restructure | 2-3 hours |
| Metacognition template | 30 min |
| Spiral review pattern | 30 min |
| **Total before continuing** | ~8-10 hours |

---

## Success Criteria

After implementing this plan:

1. **Vocabulary targets** are internally consistent
2. **Module types** correctly categorize all 80 modules
3. **M80** has complete CEFR-aligned rubrics
4. **Checkpoints** include self-assessment and remediation guidance
5. **Every grammar module** has 2+ production activities
6. **M07-08** restructured to reduce grammar fatigue
7. **Every module** has "why this matters" and "self-check" elements
8. **Every module** includes spiral review from previous modules

**Result:** B1 curriculum upgraded from B+/A- to A grade.

---

## Implementation Strategy

### Component Chain

When adding a curriculum improvement, keep these components in sync:

| Component | Purpose | Location |
|-----------|---------|----------|
| **Curriculum Plan** | WHAT to teach | `docs/l2-uk-en/B1-CURRICULUM-PLAN.md` |
| **Module Creation Prompts** | HOW to write modules | `claude_extensions/commands/module-create.md`, `docs/l2-uk-en/module-prompt.md` |
| **Richness Guidelines** | QUALITY standards | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` |
| **Audit Config** | THRESHOLDS (min vocab, immersion %) | `scripts/audit/config.py` |
| **Audit Checks** | VERIFY compliance | `scripts/audit/checks/*.py` |
| **Existing Modules** | FIX based on audit | `curriculum/l2-uk-en/b1/` |
| **Vocabulary DB** | REBUILD after changes | `npm run vocab:rebuild` |
| **Generators** | If format changes | `scripts/generate-mdx.ts`, `scripts/generate-json.ts` |

**Update flow:**
```
Curriculum Plan updated
    ↓
Module Creation Prompts updated
    ↓
Richness Guidelines updated (if quality standards change)
    ↓
Audit Script updated (to detect compliance)
    ↓
Run audit → Fix existing modules
    ↓
Rebuild vocabulary DB → Regenerate output
```

### Two Types of Improvements

| Type | Approach | Examples |
|------|----------|----------|
| **Curriculum/Plan** | Manual/Strategic | Vocabulary targets, module specs, phase structure |
| **Module Fixes** | Audit-Driven | Activity counts, IPA, metalanguage, immersion % |

**For curriculum changes:** Review → Update plan → Update prompts → Apply to new modules

**For module fixes:** Add audit check → Run audit → Fix flagged modules → Re-run to verify

### GitHub Issue Sync

**When module structure changes (add/shift/reorder), update related GitHub issues:**

| Change | Action |
|--------|--------|
| Add modules | Update "Build modules XX-XX" issue title and description |
| Remove modules | Update issue title and description |
| Reorder phases | Update issue descriptions to reflect new module ranges |
| Split/merge modules | Update issue scope accordingly |

**Issues for this level:** #113-#116

### Vocabulary Workflow (Phased)

**GitHub Issue:** [#116](https://github.com/krisztiankoos/curricula-opus/issues/116) (Finalize vocabulary)

**Problem:** Expanding vocabulary at module level during creation leads to endless recursion.

**Solution:** Phased approach:

| Phase | Action | Vocabulary Handling |
|-------|--------|---------------------|
| **Planning** | Set targets in curriculum plan | Define minimum words per module carefully |
| **Creation** | Write modules following plan | Use EXACTLY the vocabulary from plan - NO improvisation |
| **Level Complete** | All modules exist | Run audit, finalize vocabulary in MD + DB |

```
Curriculum Plan (vocabulary targets set)
    ↓
Module Creation (use plan vocabulary EXACTLY)
    ↓
Level fully built (all modules exist)
    ↓
Vocabulary Audit (verify counts, find gaps)
    ↓
Finalize vocabulary (MD files + rebuild DB)
    ↓
Verify totals match plan
```

**Key rules:**
- During creation: NO vocabulary improvisation, follow plan exactly
- Vocabulary finalization happens ONCE per level, at the end
- Audit script drives the finalization, not manual review

---

## Technical Reminders

### Vocabulary Commands

```bash
npm run vocab:rebuild    # Rebuild master vocabulary database
python3 scripts/audit_module.py [path]  # Validate module vocabulary
```

### Immersion & Metalanguage Scaffolding

**Critical:** Linguistic/grammatical terminology must be explicitly taught BEFORE using it in Ukrainian explanations.

**Problem:** At B1's 50-70% immersion, learners encounter advanced Ukrainian metalanguage without explanation:
- "Утворіть дієприкметник" — but what is "дієприкметник"?
- "Визначте вид дієслова" — but what is "визначте" or "вид"?
- "Односкладне речення" — but what does this mean?

**Solution:** B1 must explicitly teach these grammatical terms as vocabulary:

| Term | Ukrainian | When to Introduce |
|------|-----------|-------------------|
| participle | дієприкметник | Before participle module |
| gerund | дієприслівник | Before gerund module |
| passive voice | пасивний стан | Before passive module |
| active voice | активний стан | Before passive module |
| conditional | умовний спосіб | Before conditional module |
| one-member sentence | односкладне речення | Before syntax module |
| impersonal | безособовий | Before impersonal constructions |
| motion verbs | дієслова руху | Before motion verb module |

**Implementation:**
- Add grammatical terms to vocabulary sections BEFORE they appear in Ukrainian instructions
- Include instruction verbs: визначте (identify), утворіть (form), змініть (change), поставте (put)
- First occurrence: provide English equivalent in parentheses
- Subsequent occurrences: Ukrainian only (true immersion)

Without this scaffolding, high immersion becomes confusion rather than natural learning.
