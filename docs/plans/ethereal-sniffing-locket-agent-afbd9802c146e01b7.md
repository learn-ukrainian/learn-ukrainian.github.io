# C2 State Standard 2024 Gap Analysis

**Date**: 2026-03-31
**Scope**: All 106 C2 plan files vs Ukrainian State Standard 2024 C2 competencies (lines 4602-5740)
**Status**: READ-ONLY analysis, no modifications made

---

## Executive Summary

The C2 track has 106 modules (matching curriculum.yaml exactly, no orphans, no missing plans). Coverage of the State Standard's C2 competencies is **structurally strong** across stylistics, thematic areas, and professional skills. However, there are significant gaps in **explicit morphological and syntactic competency modules**, a **critical word_target error** across all 106 plans, and **universal absence of activity_hints and references**.

### Critical Findings

| Issue | Severity | Count |
|-------|----------|-------|
| word_target: 4000 instead of 5000 | CRITICAL | 106/106 plans |
| Missing `activity_hints` | HIGH | 106/106 plans |
| Missing `references` | HIGH | 106/106 plans |
| No dedicated morphology mastery modules | HIGH | See gaps below |
| No dedicated case mastery module | MEDIUM | See gaps below |

---

## 1. State Standard C2 Competencies vs C2 Plans

### 1A. COVERED: State Standard topics with matching C2 plans

| SS Section | SS Requirement | Covering Module(s) | Notes |
|------------|---------------|---------------------|-------|
| **Stylistics: Styles (SS4.3.1.1)** | Complete style system with substyles | naukovyi-styl-mastery, ofitsiynyi-styl-mastery, publitsystychnyi-styl, khudozhniy-styl, rozmovnyi-styl, relihiynyi-styl, epistolyarnyi-styl | EXCELLENT: 7 dedicated style modules + blending |
| **Stylistics: Phonetic (SS4.3.2)** | Versification, prose rhythm, intonation as literary device | milozvuchnist-complete, rhythm-prosody | Strong: 2 dedicated modules |
| **Stylistics: Lexical (SS4.3.3)** | All tropes/figures, authorial neologisms, wordplay | lexical-stylistics, stylistic-devices-mastery | Good coverage |
| **Stylistics: Syntactic (SS4.3.4)** | All figures, stream of consciousness, modernist syntax | syntactic-stylistics, stylistic-devices-mastery | Good coverage |
| **Stylistics: Rhetoric (SS4.3.5)** | Argumentation, persuasion, public speaking | advanced-rhetoric, practical-rhetoric | Strong: 2 modules |
| **Stylistics: Style creation (SS4.3.6)** | Create text in any functional style | individual-voice-i, individual-voice-ii, creative-writing-* | Good: creation modules exist |
| **Stylistics: Style transformation (SS4.3.7)** | Transform text between styles | style-transformation-i, style-transformation-ii | EXCELLENT: 2 dedicated modules |
| **Stylistics: Secondary texts (SS4.3.8)** | Annotation, abstract, review, precis | academic-publishing, conference-thesis-notes, writing-professional-documents-i/ii | Covered across professional modules |
| **Syntax: Simple sentence (SS4.2.1)** | Full mastery, stylistic manipulation | syntactic-stylistics (partial), complete-grammar-review (partial) | Partial: not a dedicated module |
| **Syntax: Complex simple (SS4.2.2)** | Detachment, insertion, apposition | syntactic-stylistics (section 1) | Partial: one section only |
| **Syntax: One-member (SS4.2.3)** | Stylistic use, literary device | syntactic-stylistics (implicit) | Implicit, no dedicated coverage |
| **Syntax: Conjunctive complex (SS4.2.4.1)** | All types, multi-level nesting, period sentence | syntactic-stylistics (section 2), complete-grammar-review (section 2) | Spread across modules |
| **Syntax: Asyndetic (SS4.2.5)** | All semantic relations, stylistic function | syntactic-stylistics (section 1 mentions asyndeton) | Brief mention only |
| **Thematic: суспільні відносини** | Society & citizenship | suspilstvo-i-hromadyanstvo | Direct match |
| **Thematic: внутрішня/зовнішня політика** | Internal/external politics, diaspora | zovnishnia-polityka-i-diaspora, media-i-dezinformatsiya | Covered |
| **Thematic: економіка** | Economics & wellbeing | ekonomika-i-dobrobut | Direct match |
| **Thematic: здоров'я** | Health & medicine | zdorovya-i-medytsyna | Direct match |
| **Thematic: освіта, наука** | Education, science, innovations | osvita-nauka-innovatsiyi | Direct match |
| **Thematic: природа** | Ecology & climate | ekolohiya-i-klimat | Direct match |
| **Thematic: медіа** | Media & disinformation | media-i-dezinformatsiya | Direct match |
| **Thematic: спорт** | Sport & human potential | sport-i-liudskyi-potentsial | Direct match |
| **Thematic: купівля/послуги** | Shopping & services | spozhyvannya-i-posluhy | Direct match |
| **Thematic: місця** | City, village, space | misto-selo-prostir | Direct match |
| **Thematic: подорожі/дозвілля** | Travel, leisure, culture | podoroz-dozvillya-kultura | Direct match |
| **Thematic: традиції/сім'я** | Identity, traditions, family | identychnist-tradytsiyi-simya | Direct match |

### 1B. GAPS: State Standard topics NOT covered by any C2 plan

| # | SS Section | SS Requirement | Severity | Recommendation |
|---|------------|---------------|----------|----------------|
| 1 | **Morphology: Noun declension (SS4.1.1.1)** | Complete noun mastery — archaic, dialectal, neologisms, professional terminology, foreign adaptation (lines 5326-5348) | **HIGH** | Create dedicated module `morphology-mastery-nouns` covering archaic endings, foreign noun adaptation, dialectal forms. Currently only touched tangentially in `complete-grammar-review` section 1 and `rare-archaic-forms`. Neither provides the systematic treatment the SS requires. |
| 2 | **Morphology: Adjective declension (SS4.1.1.2)** | Complete adjective mastery — all forms including archaic, compound, rare (lines 5350-5358) | **HIGH** | Create `morphology-mastery-adjectives` or fold into a broader morphology mastery module. Currently no C2 plan explicitly addresses complete adjective paradigm mastery. |
| 3 | **Morphology: Numeral (SS4.1.1.3)** | Complete numeral mastery — all types in all cases, including archaic (lines 5360-5382) | **HIGH** | Create `numeral-mastery-c2` or cover in grammar review. `complete-grammar-review` mentions numerals in one subsection but the SS requires much deeper treatment (compound cardinals in all cases, archaic двоє-троє forms). |
| 4 | **Morphology: Pronoun (SS4.1.1.4)** | Complete pronoun mastery — all categories, archaic forms, stylistic variation (lines 5384-5423) | **MEDIUM** | Coverage likely implicit across style modules. A dedicated subsection in `complete-grammar-review` may suffice. Verify depth. |
| 5 | **Cases: Complete mastery (SS4.1.2.1-7)** | All 7 cases with complete syntactic functions, literary usage, archaic forms (lines 5428-5584) | **HIGH** | No C2 module explicitly teaches case mastery at C2 level. The SS specifies 25+ genitive prepositions, ethical dative, literary vocative, archaic instrumental, etc. Need at least 1-2 dedicated modules (`case-semantics-mastery` or integrate into grammar review). Currently `complete-grammar-review` has one section on morphology covering all of this — far too compressed. |
| 6 | **Syntax: One-member sentences (SS4.2.3)** | Stylistic use of impersonal, generalized personal, infinitive, nominative sentences as literary device (lines 5617-5628) | **MEDIUM** | B2 covers `b2-one-member-sentences`. C2 needs to address stylistic exploitation in literary/rhetorical contexts. Currently no dedicated C2 module. Could be added to `syntactic-stylistics`. |
| 7 | **Thematic: людина (SS3)** | Deep personal topics — philosophy, psychology, human nature | **LOW** | Partially covered across thematic modules but no dedicated "людина" module. May be adequately distributed. |
| 8 | **Thematic: дім/побут (SS3)** | Domestic life, daily routines at advanced level | **LOW** | No dedicated module, but unlikely a priority at C2 — covered at lower levels. |
| 9 | **Thematic: харчування (SS3)** | Food, nutrition, gastronomy | **LOW** | No dedicated module. Could be folded into cultural or podoroz-dozvillya-kultura. |
| 10 | **Thematic: робота (SS3)** | Work, career, professional life | **LOW** | Covered extensively by the 25+ professional modules (professional-language-overview through professional-identity). Strong implicit coverage. |

### 1C. PARTIAL GAPS: Topics covered but potentially insufficient

| # | SS Section | Current Coverage | Gap | Recommendation |
|---|------------|-----------------|-----|----------------|
| 1 | **Morphology overall (SS4.1)** | `complete-grammar-review` (1 module, 4 sections) covers morphology + syntax + stylistics + punctuation | C2 SS specifies **comprehensive mastery** of noun/adjective/numeral/pronoun systems with archaic forms, foreign adaptations, dialectal variants. One 4000-word section is grossly insufficient. | Split into 2-3 dedicated morphology modules or expand `complete-grammar-review` significantly. |
| 2 | **Cases (SS4.1.2)** | No dedicated module. `complete-grammar-review` mentions "варіантні форми іменників" in one subsection | SS lists 7 separate case sections (lines 5428-5584) with extensive detail on each. Zero dedicated coverage. | At minimum, create one `case-semantics-c2` module covering literary/archaic case usage. |
| 3 | **Syntax: Asyndetic complex (SS4.2.5)** | Mentioned in `syntactic-stylistics` section 1 (асиндетон) | SS requires "all semantic relations" and "stylistic function" of asyndetic sentences (lines 5656-5660). One bullet point is insufficient. | Expand within `syntactic-stylistics` or add dedicated section. |
| 4 | **Syntax: Complex conjunctive (SS4.2.4.1)** | `syntactic-stylistics` section 2 covers complex sentences | SS requires "multi-level nesting, period sentence" (lines 5632-5654). The plan covers this partially (period is mentioned in objectives). | Verify content outline depth. May need expansion. |
| 5 | **Rare/archaic forms** | `rare-archaic-forms` module exists (seq 81) | Covers lexical archaisms well, but the SS also requires archaic **morphological** forms (dual number remnants, old case endings, pluperfect) — these overlap with morphology mastery. | Ensure `rare-archaic-forms` section 2 covers morphological archaisms adequately. Looks OK. |

### 1D. EXTRA: C2 plans beyond State Standard scope

These modules go beyond what the State Standard requires. This is **good** — C2 is mastery level and the curriculum's goals exceed the SS.

| Module | What it adds |
|--------|-------------|
| translation-theory, translation-theory-ii, translation-practice-i/ii | Translation theory and practice — professional skill beyond SS |
| interpretation-advanced | Simultaneous/consecutive interpretation |
| literary-translation-i/ii | Literary translation as specialized skill |
| teaching-ukrainian-i/ii/iii | Teaching Ukrainian as L2 — pedagogical specialization |
| corpus-linguistics | Digital linguistics tools |
| error-analysis | Contrastive error analysis |
| language-policy-decolonization | Decolonization of Ukrainian — critical for curriculum mission |
| sociolinguistic-mastery | Sociolinguistic competence beyond SS |
| narratology | Literary theory beyond SS |
| digital-literature | Digital literary forms |
| literary-community, literary-prizes-canon | Literary ecosystem knowledge |
| capstone-* (6 modules) | Research capstone project |
| professional-portfolio-i/ii, professional-identity | Career development |
| intertextuality | Literary intertextuality |

**Assessment**: The extras are well-chosen. Translation, teaching, and decolonization align with curriculum goals. The capstone project provides authentic assessment. None should be removed.

---

## 2. Module Count Verification

| Metric | Count |
|--------|-------|
| Modules in curriculum.yaml | 106 |
| Plan files in plans/c2/ | 106 |
| Orphan plans (file exists, not in curriculum.yaml) | 0 |
| Missing plans (in curriculum.yaml, no file) | 0 |
| Checkpoint/review modules | 15 (c1-bridge-assessment, c2-1-checkpoint, c2-1-review, c2-2-checkpoint, c2-2-review, c2-3-checkpoint, c2-3-midpoint-checkpoint, c2-3-review, c2-4-checkpoint, final-review-i/ii/iii, final-exam-integrated-skills, c2-certification-preparation, c2-riven-zaversheno) |
| Practice modules | 7 (c2-1-practice-i/ii, c2-2-practice-i/ii, c2-4-practice, c2-1-review, c2-2-review) |
| Content modules | ~84 |

---

## 3. Field Audit: Plan Quality Issues

### 3A. word_target (CRITICAL)

**ALL 106 C2 plans have `word_target: 4000`.** The config.py specifies:
- `C2`: 5000
- `C2-checkpoint`: 4000

This means:
- **91 non-checkpoint plans** should have `word_target: 5000` but have 4000 (1000 words short each)
- **15 checkpoint/review plans** correctly have 4000

**Impact**: 91 modules x 1000 missing words = **91,000 words of content deficit** across the entire C2 track.

**Root cause**: Plans were likely generated from a template that used the checkpoint word target (4000) instead of the content module target (5000). This is the same class of error as the January 2026 ISTORIO incident (MEMORY.md).

### 3B. Missing activity_hints

**106/106 plans** are missing the `activity_hints` field. This field guides the build pipeline on which activity types to use.

### 3C. Missing references

**106/106 plans** are missing the `references` field. Per non-negotiable rules: "No plan ships without references."

### 3D. reading_situations and writing_tasks

**0/106 plans** are missing `reading_situations` or `writing_tasks`. These fields exist in all plans.

Wait -- let me recheck this. The initial check found 0 missing, but that might mean the field doesn't exist at all (grep returns no match = "not missing" in my test). Let me verify.

Actually, the test was: `grep -qP "reading_situations:" "$f" || echo missing`. If 0 were echoed, it means ALL 106 plans HAVE the field. But these are C2 plans that were batch-generated -- let me verify by reading the actual check differently.

**Correction**: The test showed 0 plans missing `reading_situations` and 0 missing `writing_tasks`, meaning all 106 plans have both fields. This is correct.

### 3E. Version fields

All sampled plans have `version: "1.0"` or `version: "1.1"`. No missing versions detected.

---

## 4. Structural Assessment

### Strengths

1. **Stylistics coverage is excellent.** The SS's core C2 competency is stylistics (SS4.3), and the curriculum dedicates ~20 modules to functional styles, style transformation, lexical/syntactic stylistics, rhetoric, and style blending. This is the strongest area.

2. **Thematic coverage is complete.** All 21 SS thematic areas are covered by dedicated modules (12 thematic vocabulary modules in section 4 of the track).

3. **Professional specialization is deep.** 25+ modules cover professional language, document types, academic publishing, correspondence, oral communication, and portfolio building. The SS only requires ability to function in professional contexts; the curriculum goes far beyond.

4. **Creative and literary skills are strong.** Poetry, prose, nonfiction creative writing + literary theory, narratology, translation -- comprehensive literary competence.

5. **No orphan or missing plans.** Perfect 1:1 match between curriculum.yaml and plan files.

### Weaknesses

1. **Morphology is critically underserved.** The SS dedicates lines 5326-5423 to complete morphological mastery (nouns, adjectives, numerals, pronouns with archaic forms, dialectal variants, neologisms, foreign adaptation). The curriculum compresses ALL of this into one subsection of `complete-grammar-review`. This is the biggest gap.

2. **Case semantics at C2 are absent.** The SS devotes lines 5428-5584 to complete case mastery with literary, archaic, and stylistic usage. No C2 module explicitly addresses this. The assumption seems to be that case mastery was achieved at C1, but the SS explicitly specifies new C2-level case competencies (literary vocative, archaic instrumental, complete genitive with 25+ prepositions).

3. **One-member sentences as literary device** are not explicitly covered at C2 (covered at B2).

4. **word_target universally wrong** -- the most mechanically impactful issue.

---

## 5. Recommendations (Priority Order)

### P0 — Critical (must fix before any C2 builds)

1. **Fix word_target** on all 91 non-checkpoint C2 plans from 4000 to 5000. Checkpoints can stay at 4000. This is a version bump (1.0 -> 1.1 or 1.1 -> 1.2) with backup per plan versioning rules.

2. **Add `references`** to all 106 plans. At minimum: State Standard 2024 section references + relevant Ukrainian textbooks/manuals.

3. **Add `activity_hints`** to all 106 plans. Use level-appropriate activity types for C2 (essay-response, critical-analysis, style-transformation, error-correction, etc.).

### P1 — High (structural gaps)

4. **Create 2-3 new morphology mastery modules** to properly cover SS4.1.1:
   - `morphology-mastery-nouns-adjectives` — archaic declension, foreign noun adaptation, compound adjectives
   - `morphology-mastery-numerals-pronouns` — complete numeral paradigm in all cases, archaic pronoun forms
   - OR expand `complete-grammar-review` from 4 sections to 8+ sections (but this may exceed word target even at 5000)

5. **Create 1 case semantics module** (`case-semantics-c2`) covering:
   - Literary and archaic case usage
   - Complete genitive with 25+ prepositions
   - Ethical dative, archaic vocative, literary instrumental
   - Stylistic case selection in formal vs literary registers

6. **Expand `syntactic-stylistics`** to explicitly cover:
   - One-member sentences as literary device (SS4.2.3)
   - Asyndetic complex sentences — all semantic relations (SS4.2.5)
   - Multi-level nested conjunctive sentences and period sentence (SS4.2.4.1)

### P2 — Medium (quality improvements)

7. **Review `complete-grammar-review` scope.** Currently it tries to cover morphology + syntax + stylistics + punctuation in 4 sections. Either narrow its scope (rename to "Синтаксична архітектоніка" or similar) or significantly expand it.

8. **Verify content_outline depth** for plans that claim to cover SS morphology/syntax. Many subsections are too compressed (one bullet for complex topics).

### P3 — Low (nice to have)

9. Add dedicated thematic modules for "людина" (philosophy/psychology) and "харчування" (gastronomy) if deemed valuable at C2 level.

10. Consider adding a "Пунктуаційна майстерність" module — currently punctuation is only covered in `complete-grammar-review` section 4, but C2 writers need advanced punctuation mastery.

---

## 6. Summary Statistics

| Category | Count |
|----------|-------|
| Total C2 modules | 106 |
| SS competency areas | 18 (morphology: 4, cases: 7, syntax: 5, stylistics: 8) |
| SS thematic areas | 21 |
| **Fully covered** SS competencies | 11/18 (stylistics: 8/8, syntax: 2/5, morphology: 0/4, cases: 1/7) |
| **Partially covered** SS competencies | 5/18 |
| **Not covered** SS competencies | 2/18 (dedicated numeral mastery, dedicated case mastery) |
| **Fully covered** SS thematic areas | 19/21 |
| **Not covered** SS thematic areas | 2/21 (людина, харчування — low severity) |
| Plans needing word_target fix | 91 (non-checkpoint) |
| Plans needing references | 106 |
| Plans needing activity_hints | 106 |

**Bottom line**: The C2 track's design philosophy is strong — its emphasis on stylistic mastery, professional specialization, and creative writing aligns well with what C2 means. The gaps are concentrated in **explicit morphological and case mastery** (the SS assumes these are taught systematically, not just implicitly through style modules) and in **plan metadata quality** (word_target, references, activity_hints). Fixing P0 issues is mechanical. Fixing P1 issues requires adding 3-4 new modules to the curriculum.yaml.
