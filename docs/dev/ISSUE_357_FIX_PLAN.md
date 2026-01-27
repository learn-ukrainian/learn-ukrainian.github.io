# Issue #357 Clarification Plan

**Date:** 2026-01-03
**Problem:** Confusion between LIT track and C1/C2 literature modules
**Assigned to:** C1-c (coordination), Gemini (execution)

---

## The Problem

**Issue #357 and LIT_MIGRATION_STRATEGY.md incorrectly conflate two independent curricula:**

### 1. LIT Track (Standalone Specialization)

- **Modules:** LIT-001 to LIT-030
- **Location:** `curriculum/l2-uk-en/lit/`
- **Prerequisite:** C1 Core completion (strict)
- **Focus:** Golden Age Ukrainian Literature (19th century)
- **Authors:** Котляревський, Квітка-Основ'яненко, Шевченко, Куліш, Нечуй-Левицький
- **Pedagogy:** Graduate-level literary seminar (essay-based, external reading)
- **Template:** `docs/l2-uk-en/templates/lit-module-template.md`
- **Skill:** `claude_extensions/skills/literature-module-architect/`

### 2. C1 Literature Modules (Part of C1 Core)

- **Modules:** C1.6 Phase (M146-160)
- **Location:** `curriculum/l2-uk-en/c1/`
- **Prerequisite:** C1.1-C1.5 phases
- **Focus:** Full Ukrainian Literary Canon (Classics to Contemporary)
- **Authors:** Shevchenko, Франко, Леся Українка, Розстріляне відродження, Шістдесятники, Contemporary
- **Pedagogy:** C1-level language mastery through literature
- **Template:** `docs/l2-uk-en/templates/c1-literature-module-template.md`
- **Skill:** None (uses generic C1 skills)

**These are INDEPENDENT tracks. LIT is NOT "future C1/C2 modules."**

---

## What Gemini Thinks (Incorrectly)

Based on Issue #357 and LIT_MIGRATION_STRATEGY.md, Gemini believes:
- LIT migration strategy applies to both LIT track (LIT-001-014) AND C1/C2 literature modules
- The "Reading Hall" pattern should extend to C1/C2
- This is ONE migration covering two curricula

**This is wrong.** Issue #357 is ONLY about LIT track (14-30 modules in `curriculum/l2-uk-en/lit/`).

---

## Required Changes

### 1. Update Issue #357 on GitHub

**Current body (line 4-5):**
```markdown
## Scope
- **Location:** `curriculum/l2-uk-en/lit/`
- **Modules:** LIT-001 to LIT-014 (and future C1/C2).
```

**Change to:**
```markdown
## Scope
- **Location:** `curriculum/l2-uk-en/lit/`
- **Modules:** LIT-001 to LIT-030 (Ukrainian Literature & Classics specialization track)
- **Note:** This is a standalone post-C1 track, NOT part of C1/C2 core curriculum
```

### 2. Update LIT_MIGRATION_STRATEGY.md

**Current (line 4):**
```markdown
**Scope:** LIT-001 to LIT-014 (and future C1/C2 Literature modules)
```

**Change to:**
```markdown
**Scope:** LIT-001 to LIT-030 (Ukrainian Literature & Classics specialization track)
```

**Add new section after line 5:**
```markdown
## Important Distinction: LIT vs C1 Literature

**This strategy applies ONLY to the LIT track** (`curriculum/l2-uk-en/lit/`).

| Aspect | LIT Track | C1 Literature (M146-160) |
|--------|-----------|--------------------------|
| **Location** | `curriculum/l2-uk-en/lit/` | `curriculum/l2-uk-en/c1/` |
| **Prerequisite** | C1 Core complete | C1.1-C1.5 phases |
| **Focus** | Golden Age (19th century) | Full Canon (Classics to Contemporary) |
| **Pedagogy** | Graduate seminar (essay-based) | C1 language mastery through literature |
| **Template** | `lit-module-template.md` | `c1-literature-module-template.md` |

**C1/C2 literature modules use standard C1/C2 YAML architecture** (not this LIT-specific strategy).
```

### 3. Update My Review Comment on Issue #357

Remove this section from my comment (posted 2026-01-03):
```markdown
### Vocabulary Format Decision

**Question:** LIT modules use 3-column specialized format. Should they:
- (A) Keep 3-column (LIT-specific exception)
- (B) Convert to 6-column standard (consistency with A1-C2)

**Recommendation:** Keep 3-column for now. LIT track is post-C1 specialization with different pedagogical goals. Revisit during C1/C2 literature module design.
```

**Replace with:**
```markdown
### Vocabulary Format Decision

**Decision:** Keep 3-column format for LIT track.

**Rationale:**
- LIT is a standalone post-C1 specialization with distinct pedagogy (graduate seminar style)
- 3-column format (Термін/Слово | Визначення | Контекст/Коментар) suits literary/historical focus
- C1/C2 literature modules (separate curriculum) use standard 6-column format
- No conflict - these are independent tracks
```

And remove this line:
```markdown
**Coordination:** Notify C1-a if pattern should extend to C1/C2 literature modules
```

Replace with:
```markdown
**Scope:** LIT track only (LIT-001 to LIT-030). C1/C2 literature modules use standard C1/C2 architecture.
```

### 4. Update literature-module-architect Skill

**File:** `claude_extensions/skills/literature-module-architect/SKILL.md`

**Add after line 47 (after "Atomic Architecture" section):**

```markdown
## CRITICAL: LIT Track vs C1 Literature

**This skill is ONLY for LIT track modules** (`curriculum/l2-uk-en/lit/`).

| What | LIT Track | C1 Literature |
|------|-----------|---------------|
| **Location** | `curriculum/l2-uk-en/lit/` | `curriculum/l2-uk-en/c1/` |
| **Modules** | LIT-001 to LIT-030 | C1.6 Phase (M146-160) |
| **Pedagogy** | Graduate seminar (essay-based) | C1 language mastery |
| **Use this skill?** | ✅ YES | ❌ NO (use C1 skills) |

**DO NOT confuse these tracks.** If working on C1 modules (M146-160), use C1 templates and skills.
```

### 5. Update lit-module-template.md

**File:** `docs/l2-uk-en/templates/lit-module-template.md`

**Add after line 7 (after "Prerequisite:"):**

```markdown
## ⚠️ CRITICAL: LIT Track vs C1 Literature

**This template is ONLY for LIT track modules (LIT-001 to LIT-030).**

C1 core curriculum has its own literature modules (C1.6 Phase: M146-160) which use:
- Template: `c1-literature-module-template.md`
- Location: `curriculum/l2-uk-en/c1/`
- Different pedagogy (C1 language mastery, not graduate seminar)

**If you're creating C1 literature modules, STOP. Use the C1 template instead.**
```

---

## Execution Plan

### Phase 1: Clarify Issue #357 (Gemini)

1. Update Issue #357 body on GitHub (scope clarification)
2. Update LIT_MIGRATION_STRATEGY.md (add distinction section)
3. Post clarification comment on Issue #357 explaining the fix

### Phase 2: Update Skills & Templates (C1-c)

1. Update `literature-module-architect/SKILL.md` (add LIT vs C1 distinction)
2. Update `lit-module-template.md` (add warning section)
3. Update my review comment on Issue #357 (remove C1/C2 coordination note)

### Phase 3: Deploy (User)

1. Run `npm run claude:deploy` to deploy skill changes
2. Verify Gemini understands the corrected scope

---

## Success Criteria

After these changes:
- ✅ Issue #357 clearly states scope is LIT-001 to LIT-030 only
- ✅ LIT_MIGRATION_STRATEGY.md distinguishes LIT from C1 literature
- ✅ literature-module-architect skill warns against C1 confusion
- ✅ lit-module-template.md warns users about the distinction
- ✅ Gemini understands LIT migration applies ONLY to LIT track
- ✅ No more "future C1/C2" references causing confusion

---

## Timeline

**Immediate:** Update Issue #357 and LIT_MIGRATION_STRATEGY.md (Gemini)
**Next:** Update skills and templates (C1-c)
**Final:** Deploy and verify understanding

**Assignees:**
- **Gemini (G1):** Phase 1 (GitHub updates)
- **Claude (C1-c):** Phase 2 (Skills/templates)
- **User:** Phase 3 (Deploy)
