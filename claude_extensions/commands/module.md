# /module

Unified entry point for building modules using the 7-phase workflow (content + skeleton deploy).

> **Vocabulary enrichment runs separately** after the entire track/course is content-complete.

## Usage

```
/module {level} {num}               # Build single module (phases 1-7)
/module {level} {start}-{end}       # Batch build
/module {level} {num} --from=PHASE  # Resume from specific phase
/module {level} {num} --refresh     # Refresh meta+activities (preserves .md content)
/module {level} {num} --check       # Check status only
```

## Examples

```bash
/module b2-hist 5               # Build module 5 (content + skeleton deploy)
/module b2-hist 1-5             # Build modules 1-5
/module b2-hist 5 --from=lesson # Resume from phase 3 (lesson)
/module c1-bio 12 --check       # Show which phases are complete
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────┐
│ CONTENT BUILD (Phases 1-6) - Can run in parallel        │
├─────────────────────────────────────────────────────────┤
│ Phase 1: /module-meta        → meta/{slug}.yaml         │
│ Phase 2: /module-meta-qa     → Validate meta            │
│          ↓ LOCKED                                       │
│ Phase 3: /module-lesson      → {slug}.md                │
│ Phase 4: /module-lesson-qa   → Validate content         │
│          ↓ LOCKED                                       │
│ Phase 5: /module-act         → activities/{slug}.yaml   │
│ Phase 6: /module-act-qa      → Validate activities      │
│          ↓ LOCKED                                       │
├─────────────────────────────────────────────────────────┤
│ SKELETON DEPLOY (Phase 7)                               │
├─────────────────────────────────────────────────────────┤
│ Phase 7: /module-integrate   → Create skeleton vocab    │
│                              → Generate MDX             │
│                              → Deploy module            │
└─────────────────────────────────────────────────────────┘

              Later, when track is complete:

┌─────────────────────────────────────────────────────────┐
│ VOCAB ENRICHMENT (Separate command)                     │
├─────────────────────────────────────────────────────────┤
│ /module-vocab-enrich {level}  → Extract vocab M1→MN     │
│                               → Update MDX with vocab   │
│                               → Update vocabulary.db    │
└─────────────────────────────────────────────────────────┘
```

---

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Parse Input

Extract:

- `level`: a1, a2, b1, b2, c1, c2, b2-hist, c1-bio, c1-hist, lit
- `num`: Module number or range (e.g., `5` or `1-5`)
- `flags`: --from=PHASE, --check, --refresh (optional)

**If range detected:** Jump to Batch Mode.

### Step 2: Resolve Module

**For tracks (b2-hist, c1-bio, c1-hist, lit):**

```bash
slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

**For core levels:**

```bash
slug=$(ls curriculum/l2-uk-en/${level}/${num:02d}-*.md | head -1 | xargs basename | sed 's/.md$//')
```

### Step 3: Detect Current State

Check which files exist:

```bash
has_meta=$(test -f curriculum/l2-uk-en/${level}/meta/${slug}.yaml && echo 1 || echo 0)
has_lesson=$(test -f curriculum/l2-uk-en/${level}/${slug}.md && echo 1 || echo 0)
has_activities=$(test -f curriculum/l2-uk-en/${level}/activities/${slug}.yaml && echo 1 || echo 0)
# Check for either module-N.mdx (core) or slug.mdx (tracks)
if [[ -f docusaurus/docs/${level}/module-${num}.mdx ]]; then
  has_mdx=1
elif [[ -f docusaurus/docs/${level}/${slug}.mdx ]]; then
  has_mdx=1
else
  has_mdx=0
fi
```

**State detection:**

| has_meta | has_lesson | has_activities | has_mdx | State         |
| -------- | ---------- | -------------- | ------- | ------------- |
| 0        | 0          | 0              | 0       | `NEW`         |
| 1        | 0          | 0              | 0       | `META_DONE`   |
| 1        | 1          | 0              | 0       | `LESSON_DONE` |
| 1        | 1          | 1              | 0       | `ACT_DONE`    |
| 1        | 1          | 1              | 1       | `DEPLOYED`    |

### Step 4: Determine Start Phase

**If `--refresh` provided:**

Special flow (preserves `.md`, rebuilds everything else):
1. Phase 2 (Meta QA)
2. Phase 4 (Lesson QA) - *Skips Phase 3 generation*
3. Phase 5 (Activities Gen) - *Regenerates activities*
4. Phase 6 (Activities QA)
5. Phase 7 (Integrate)

**If `--from=PHASE` provided:**

| --from value | Start at Phase |
| ------------ | -------------- |
| meta         | 1              |
| lesson       | 3              |
| act          | 5              |
| integrate    | 7              |

**If `--check` provided:** Report state and exit.

**Otherwise auto-detect:**

| State         | Start Phase   |
| ------------- | ------------- |
| `NEW`         | 1 (meta)      |
| `META_DONE`   | 3 (lesson)    |
| `LESSON_DONE` | 5 (act)       |
| `ACT_DONE`    | 7 (integrate) |
| `DEPLOYED`    | Done          |

### Step 5: Execute Phases

**If `--refresh` mode:**
Execute specific sequence: 2 → 4 → 5 → 6 → 7.

**Otherwise (standard mode):**
Run phases sequentially from start phase:

**For each phase:**

1. Read phase instructions from `claude_extensions/phases/module-{phase}.md`
2. Execute phase
3. If QA phase FAILS → stop and report
4. If QA phase PASSES → continue to next phase

**Phase 7 (integrate) creates skeleton vocab automatically.**

### Step 6: Report

```
MODULE DEPLOYED: {level}/{slug}

Phases executed: {start_phase} → 7
Files generated:
  - meta/{slug}.yaml
  - {slug}.md
  - activities/{slug}.yaml
  - vocabulary/{slug}.yaml (skeleton)
  - docusaurus/docs/{level}/{mdx_filename}

Preview: http://localhost:3000/docs/{level}/{slug_or_module_num}

Note: Vocabulary table is empty. Run /module-vocab-enrich {level}
      after all modules are content-complete.
```

---

## Batch Mode

When input is a range (e.g., `/module b2-hist 1-5`):

```
For each module_num in range:
  1. Run /module {level} {module_num}
  2. If FAIL: Log and continue to next
  3. If PASS: Log and continue to next
```

**Batch summary:**

```
Batch: b2-hist 1-5
Results:
  - 1: DEPLOYED
  - 2: DEPLOYED
  - 3: FAIL at phase 4 (lesson-qa: word count)
  - 4: DEPLOYED
  - 5: DEPLOYED

Summary: 4/5 deployed
Failed: b2-hist-3 (needs manual fix)

Next: When all modules pass, run /module-vocab-enrich b2-hist
```

---

## Phase Reference

| Phase | Command           | Creates                                 | Validates            |
| ----- | ----------------- | --------------------------------------- | -------------------- |
| 1     | /module-meta      | meta/{slug}.yaml                        | -                    |
| 2     | /module-meta-qa   | -                                       | Meta validity        |
| 3     | /module-lesson    | {slug}.md                               | -                    |
| 4     | /module-lesson-qa | -                                       | Content quality      |
| 5     | /module-act       | activities/{slug}.yaml                  | -                    |
| 6     | /module-act-qa    | -                                       | Activity schema      |
| 7     | /module-integrate | vocabulary/{slug}.yaml (skeleton) + MDX | Cross-file alignment |

**Later:**

| Command                      | What it does                             |
| ---------------------------- | ---------------------------------------- |
| /module-vocab-enrich {level} | Extract vocab M1→MN in order, update MDX |

---

## Quick Examples

```bash
# Fresh build
/module b2-hist 5

# Resume after fixing lesson
/module b2-hist 5 --from=lesson

# Rebuild module artifacts (keeping lesson text)
/module b2-hist 5 --refresh

# Check what's done
/module b2-hist 5 --check

# Build batch
/module c1-bio 1-10

# After track complete: enrich vocabulary
/module-vocab-enrich b2-hist
```
