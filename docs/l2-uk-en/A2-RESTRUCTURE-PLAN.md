# A2 Restructure Plan - Compliance Updates

## Goal
Address specific A2 compliance gaps identified in `STATE-STANDARD-COMPLIANCE-ANALYSIS.md` and optimize module pacing.

Gaps to Address:
1.  **Explicit Aspect Pairs** (Drilling)
2.  **Verb Prefixes** (Morphology focus)
3.  **`свій` vs `його`** (Contrastive drill)
4.  **Numerals with Nouns** (Case agreement)

## Proposed Changes

### 1. Handling Existing Files (CRITICAL)
> [!IMPORTANT]
> A2 Modules 01-40 already exist on disk.
> **Strategy:** Use `mv` commands to rename existing files to their new numbers *before* creating new content to avoid overwriting.


### 2. Implementation Strategy: Assessment & Reasoning
**Status Assessment (2025-12-15):**
We sampled existing modules (M07, M12, M25) and found them to be **high quality**. The strategy prioritizes the **"Compliance Gap"** modules first.

**Decision Matrix & Thresholds:**
1.  **Compliance Modules (M08, M16, M17, M21, M36)**: **PRIORITY 1: CREATE**.
    *   These are missing entirely and are required for State Standard compliance.
2.  **Legacy/Thin Modules (M41, M43-M46)**: **PRIORITY 2: RECREATE**.
    *   *Assessment*: These files are significantly smaller (~6-8KB) than the enriched standard (~25KB).
    *   *Threshold*: Existing content < 600 words triggers **Recreation** (starting from scratch).
    *   *Target*: All final modules must exceed **800 words** (Instructional Core).
3.  **Split Modules (M07, M35)**: **PRIORITY 2: REFACTOR**.
    *   Remove content moved to new partners; expand remaining core.
4.  **Existing Robust Modules**: **PRIORITY 3: PATCH/ENRICH**.
    *   *Threshold*: Existing content 600-800 words triggers **Enrichment** (adding activities/narrative).

### 3. FAQ: Addressing Review Questions
*   **Q: Why 57 modules (was 50)?**
    *   A: A2 simulation revealed a significant vocabulary gap vs the ~2100 word target. The 5 new Grammar modules (Compliance) + 9 Vocab Expansion modules (M47-M55) are strictly necessary to hit C1 readiness without overwhelming density per module.
*   **Q: Is M47-M55 Essential?**
    *   A: **Yes.** Without them, A2 learners would exit with ~1200 words, far below the B1 entry requirement. These are "Service Modules" for vocabulary acquisition.

### 4. Vocabulary Strategy: Expansion & De-duplication
We will conduct a **Vocabulary Review** for every module during the patch/creation process:

1.  **Expansion**: Ensure each module introduces ~30 rich, relevant words (Instructional Core).
2.  **Drilling Focus**: Distinguish between "Active Vocabulary" (drilled in activities) and "Passive Vocabulary" (contextual in stories).
3.  **De-duplication Policy**:
    *   **Check**: Verify new words against the `vocab.db` (or accumulated project vocabulary) to prevent re-teaching known words.
    *   **polysemy**: Allow duplicates only if introducing a *distinctly different* meaning (e.g., *ручка* as 'pen' vs 'handle').
    *   **Form**: Ensure base forms (nominative/infinitive) are unique.

*   **[SPLIT] Module 07 ("Preposition Master Class")**:
    *   **M07: Spatial Prepositions** (в, на, під, над, за, перед, між). Focus on location/motion.
    *   **M08: Logical Prepositions** (для, без, через, про, з, до, від). Focus on relationships.
*   **[SPLIT] Module 31 ("Motion Verb Prefixes")**:
    *   **M35: Basic Motion Prefixes** (при-, ви-, у-, від-). Directional basics.
    *   **M36: Advanced Motion Prefixes** (пере-, за-, під-, об-, про-). Complex paths.

### 5. New Compliance Modules
*   **[NEW] Module 16:** Aspect Mastery: Common Pairs (Drilling).
*   **[NEW] Module 17:** Possessive: Свій vs Його.
*   **[NEW] Module 21:** Numerals & Nouns.

### 6. Renumbering Map (Total 57 Modules)
| Old File | New File | Title | Action |
|---|---|---|---|
| `01-*.md` | `01-*.md` | Dative Pronouns | Keep |
| `02-*.md` | `02-*.md` | Dative Nouns | Keep |
| `03-*.md` | `03-*.md` | Dative Verbs | Keep |
| `04-*.md` | `04-*.md` | Instrumental I | Keep |
| `05-*.md` | `05-*.md` | Instrumental II | Keep |
| `06-*.md` | `06-*.md` | Being/Becoming | Keep |
| `07-preposition-master-class.md` | `07-spatial-prepositions.md` | Spatial Preps | **Split/Rewrite** |
| -- | `08-logical-prepositions.md` | Logical Preps | **New/Split** |
| `08-all-cases-practice.md` | `09-all-cases-practice.md` | Cases Practice | Rename (+1) |
| `09-at-the-post-office...md` | `10-at-the-post-office...md` | Post/Bank | Rename (+1) |
| `10-checkpoint-cases.md` | `11-checkpoint-cases.md` | Checkpoint A2.1 | Rename (+1) |
| `11-aspect-introduction.md` | `12-aspect-introduction.md` | Aspect Intro | Rename (+1) |
| `12-the-completed-past.md` | `13-the-completed-past.md` | Completed Past | Rename (+1) |
| `13-future-plans...md` | `14-future-plans...md` | Future Plans | Rename (+1) |
| `14-aspect-pairs...md` | `15-aspect-morphology.md` | Aspect Morphology | Rename (+1) |
| -- | `16-aspect-mastery-pairs.md` | Aspect Pairs Drill| **Create** |
| -- | `17-possessive-sviy.md` | Sviy vs Yoho | **Create** |
| `15-bigger-better...md` | `18-bigger-better...md` | Comparatives | Rename (+3) |
| `16-the-best-the-worst.md` | `19-the-best-the-worst.md` | Superlatives | Rename (+3) |
| `17-preferences...md` | `20-preferences...md` | Preferences | Rename (+3) |
| -- | `21-numerals-and-nouns.md` | Numerals | **Create** |
| `18-if-i-were.md` | `22-if-i-were.md` | Conditional | Rename (+4) |
| `19-smart-shopping.md` | `23-smart-shopping.md` | Shopping | Rename (+4) |
| `20-checkpoint...md` | `24-checkpoint...md` | Checkpoint A2.2 | Rename (+4) |
| `21-telling-stories.md` | `25-telling-stories.md` | Stories | Rename (+4) |
| `22-because-and-although.md` | `26-because-and-although.md` | Because/Although | Rename (+4) |
| `23-she-said-that.md` | `27-she-said-that.md` | Reported Speech | Rename (+4) |
| `24-i-think-that.md` | `28-i-think-that.md` | Opinions | Rename (+4) |
| `25-i-feel-like.md` | `29-i-feel-like.md` | Emotions | Rename (+4) |
| `26-in-order-to.md` | `30-in-order-to.md` | Purpose | Rename (+4) |
| `27-which-one.md` | `31-which-one.md` | Relative Clauses| Rename (+4) |
| `28-time-clauses.md` | `32-time-clauses.md` | Time Clauses | Rename (+4) |
| `29-at-the-doctor.md` | `33-at-the-doctor.md` | Doctor | Rename (+4) |
| `30-checkpoint.md` | `34-checkpoint.md` | Checkpoint A2.3 | Rename (+4) |
| `31-motion-verb-prefixes.md` | `35-basic-motion-prefixes.md` | Basic Motion | **Split/Rewrite** |
| -- | `36-advanced-motion-prefixes.md` | Adv Motion | **New/Split** |
| `32-action-verb-prefixes.md` | `37-action-verb-prefixes.md` | Action Prefixes | Rename (+5) |
| `33-noun-suffixes.md` | `38-noun-suffixes.md` | Noun Suffixes | Rename (+5) |
| `34-adj-suffixes.md` | `39-adj-suffixes.md` | Adj Suffixes | Rename (+5) |
| `35-root-families-i.md` | `40-root-families-i.md` | Roots I | Rename (+5) |
| `36-root-families-ii.md` | `41-root-families-ii.md` | Roots II | Rename (+5) |
| `36-wf-mastery.md` | `42-wf-mastery.md` | WF Mastery | Rename (+6 - was dup) |
| `37-checkpoint...md` | `43-checkpoint...md` | Checkpoint A2.4 | Rename (+6) |
| `38-food-and-cooking.md` | `44-food-and-cooking.md` | Food | Rename (+6) |
| `39-home-and-furniture.md` | `45-home-and-furniture.md` | Home | Rename (+6) |
| `40-nature-and-weather.md` | `46-nature-and-weather.md` | Nature | Rename (+6) |
| -- | `47-emotions-personality.md` | Emotions | **Create Plan** |
| -- | `48-work-professions.md` | Work | **Create Plan** |
| -- | `49-technology-media.md` | Tech | **Create Plan** |
| -- | `50-hobbies-leisure.md` | Hobbies | **Create Plan** |
| -- | `51-education-learning.md` | Education | **Create Plan** |
| -- | `52-shopping-services.md` | Shopping II | **Create Plan** |
| -- | `53-sports-fitness.md` | Sports | **Create Plan** |
| -- | `54-health-body.md` | Health | **Create Plan** |
| -- | `55-checkpoint-vocabulary.md` | Checkpoint A2.5 | **Create Plan** |
| -- | `56-a2-grammar-review.md` | Grammar Review | **Create Plan** |
| -- | `57-a2-capstone.md` | Capstone A2 | **Create Plan** |

## detailed content for New Modules

### Module 08: Logical Prepositions
*   **Focus:** Abstract relationships.
*   **Content:** для (benefit), без (absence), через (cause/path), про (topic).

### Module 16: Aspect Mastery - Common Pairs
*   **Focus:** Pure drilling.
*   **Content:** pair drills.

### Module 17: Possessive: Свій vs Його
*   **Focus:** Contrastive.

### Module 21: Numerals & Nouns
*   **Focus:** 1, 2-4, 5+ patterns.

### Module 35/36: Motion Prefixes Split
*   **M35:** при-, ви-, в-, від- (Basic entry/exit).

## Acceptance Criteria for A2 Compliance

All modules (new and updated) must meet the following criteria to be considered "State Standard Compliant":

### 1. Pedagogical Compliance
- [ ] **Drilling**: M16 must contain at least 4 "Transform" or "Rapid Fire" activities for aspect pairs.
- [ ] **Contrast**: M17 must explicitly contrast `свій` vs `його` in at least 3 scenarios.
- [ ] **Logic**: M08 must differentiate `для` vs `на` and `через` vs `тому що`.
- [ ] **Agreement**: M21 must cover 1, 2-4, and 5+ case agreement patterns with <10% error rate in generated examples.
- [ ] **Vocabulary**: No exact duplicates of words taught in A1 or previous A2 modules (unless distinct polysemy).

### 2. Module Richness (Audit Pass)
- [ ] **Word Count**: > 800 words (Instructional Core).
- [ ] **Activity Density**: > 8 activities per module, > 12 items per activity.
- [ ] **Immersion**: A2 Target is 35-45% Ukrainian. Narratives should be 100% UT (Ukrainian Text) where possible.
- [ ] **Vocab Count**: ~30 active words per module.

### 3. Verification
- [ ] **Automated**: `audit_module.py` passes with zero failures.
- [ ] **Manual**: Human review confirms "Patch vs Recreate" decision was correctly applied.




## GitHub Tracking

We are tracking the creation of these new modules via the following GitHub issues:

| Module | Issue ID |
|---|---|
| **M08: Logical Prepositions** | #143 |
| **M16: Aspect Mastery** | #144 |
| **M17: Possessive: Свій vs Його** | #145 |
| **M21: Numerals & Nouns** | #146 |
| **M36: Advanced Motion Prefixes** | #148 |
| **M47-M55: Vocab Expansion** | #147 |
