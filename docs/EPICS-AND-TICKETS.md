# Epics & Tickets - Learn Ukrainian Project

## Overview

**Primary Goal:** Complete high-quality Ukrainian curriculum (A1→C2)
**Secondary Goal:** Contribute datasets to Ukrainian NLP community

---

## Epic Structure

```
Epic 1: B1 Curriculum Completion (PRIMARY - Q1 2025)
Epic 2: Grammar Validation Workflow (SUPPORTING - Q1 2025) ✅
Epic 3: NLP Dataset Extraction (SECONDARY - Q2 2025)
Epic 4: NLP Community Contribution (SECONDARY - Q2-Q3 2025)
```

**Note:** A1 (34 modules) and A2 (57 modules) are COMPLETE. Focus is on B1.

---

# EPIC 1: B1 Curriculum Completion

**Status:** In Progress (52/85 modules exist, 18/85 converted to new MD+YAML format)
**Priority:** P0 (Critical)
**Timeline:** Q1 2025 (3 months)
**Success Criteria:**
- [ ] All 85 B1 modules created
- [ ] All modules converted to MD+YAML format
- [ ] All modules validated for grammar quality (Ukrainian Grammar Validator)
- [ ] Pipeline generates valid MDX + JSON
- [ ] Ready for learner testing

**Content Quality:** ✅ Validated 3 template types (Dec 27) - HIGH QUALITY

---

## Tickets - Epic 1

### E1-T1: Test md_to_yaml Migration (Phase 1 - Single Module)

**Status:** ✅ Done
**Priority:** P0
**Estimated Effort:** 2 hours → Actual: 2 hours
**Assignee:** Krisztián
**Completed:** 2025-12-27

**Description:**
Test md_to_yaml.py conversion on single module (M17) to validate migration approach.

See: `docs/B1-MIGRATION-TEST-PLAN.md` for detailed plan.

**Acceptance Criteria:**
- [x] M17 converts to YAML successfully
- [x] All 12 activities extracted correctly
- [x] Module passes audit
- [x] Pipeline generates valid MDX + JSON
- [x] No content loss detected

**Issues Found:**
- M17 used non-standard cloze format (named blanks vs numbered) - FIXED
- Cloze parser only supports numbered blank format as documented

**Blockers:** None (resolved)

---

### E1-T2: Batch Migration Test (Phase 2 - M17-M21)

**Status:** Todo
**Priority:** P0
**Estimated Effort:** 4 hours
**Assignee:** Krisztián

**Description:**
Batch convert M17-M21 (motion verbs phase) to validate migration works at scale.

**Acceptance Criteria:**
- [ ] All 5 modules convert successfully
- [ ] All pass audit
- [ ] All generate valid MDX/JSON
- [ ] Activity counts match expectations

**Blockers:** E1-T1 (must pass single module test first)

---

### E1-T3: Full Migration (Phase 3 - M17-M51)

**Status:** Todo
**Priority:** P0
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Convert all remaining B1 modules (M17-M51) to MD+YAML format in batches.

**Batches:**
- M17-M25: Motion verbs (9 modules)
- M26-M34: Complex sentences I (9 modules)
- M35-M41: Complex sentences II (7 modules)
- M42-M51: Advanced grammar (10 modules)

**Acceptance Criteria:**
- [ ] All 34 modules converted
- [ ] All pass audit
- [ ] All generate valid MDX/JSON
- [ ] No content loss detected

**Blockers:** E1-T2 (must pass batch test first)

---

### E1-T4: Create Missing B1 Modules (M54-M85)

**Status:** Todo
**Priority:** P0
**Estimated Effort:** 4 weeks
**Assignee:** Krisztián

**Description:**
Create 33 missing B1 modules following curriculum plan:
- M54-M71: Vocabulary expansion (18 modules)
- M72-M81: Cultural modules (10 modules)
- M82-M86: Integration modules (5 modules)

**Acceptance Criteria:**
- [ ] All 33 modules created in MD+YAML format
- [ ] All pass audit
- [ ] All validated with Ukrainian Grammar Validator
- [ ] All generate valid MDX/JSON

**Blockers:** E1-T3 (migration complete first ensures consistent format)

---

### E1-T5: B1 Vocabulary Database Rebuild

**Status:** Todo
**Priority:** P1
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
After all B1 modules complete, rebuild vocabulary database to validate:
- No duplicate entries
- All vocabulary used in activities is defined
- Cumulative vocabulary count accurate

**Acceptance Criteria:**
- [ ] `npm run vocab:rebuild` runs successfully
- [ ] No vocabulary violations flagged
- [ ] Cumulative A1+A2+B1 vocabulary ~3,300 words

**Blockers:** E1-T4 (must complete all modules first)

---

### E1-T6: B1 Full Pipeline Validation

**Status:** Todo
**Priority:** P0
**Estimated Effort:** 2 days
**Assignee:** Krisztián

**Description:**
Run full pipeline on all 85 B1 modules:
- Generate MDX for Docusaurus
- Generate JSON for Vibe app
- Validate MDX integrity
- Validate HTML rendering

**Acceptance Criteria:**
- [ ] All 85 modules generate valid MDX
- [ ] All 85 modules generate valid JSON
- [ ] MDX validation passes (no content loss)
- [ ] HTML validation passes (rendering works)
- [ ] No broken activities in browser

**Blockers:** E1-T4, E1-T5

---

# EPIC 2: Grammar Validation Workflow

**Status:** In Progress
**Priority:** P1 (High - supports Epic 1)
**Timeline:** Q1 2025
**Success Criteria:**
- [ ] Ukrainian Grammar Validator prompt documented
- [ ] Manual validation workflow established
- [ ] Pattern log tracking interesting findings
- [ ] Zero Russianisms/calques in final content

---

## Tickets - Epic 2

### E2-T1: Finalize Ukrainian Grammar Validator Prompt

**Status:** Done ✅
**Priority:** P1
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Create and document Ukrainian Grammar Validator prompt adapted from Ukrainian Tutor Gem.

**Acceptance Criteria:**
- [x] Prompt file created: `scripts/audit/ukrainian_grammar_validator_prompt.md`
- [x] Usage documented in CLAUDE.md
- [x] Examples provided

**Blockers:** None

---

### E2-T2: Create NLP Pattern Log Template

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 1 hour
**Assignee:** Krisztián

**Description:**
Create a simple log file to track interesting linguistic patterns found during validation.

**Template:**
```markdown
# NLP Patterns Log - A2

## Calques Found
- Module X: [calque] → [natural Ukrainian]

## Russianisms Fixed
- Module Y: [russianism] → [Ukrainian]

## Pedagogical Simplifications
- Module Z: [teaching form] (natural: [native form])
```

**Acceptance Criteria:**
- [ ] Template file created: `curriculum/l2-uk-en/nlp-patterns-log.md`
- [ ] Instructions added to CLAUDE.md
- [ ] Easy to update during module review

**Blockers:** None

---

### E2-T3: Validate A2 M01-M05 with Gemini

**Status:** Todo
**Priority:** P1
**Estimated Effort:** 2 hours
**Assignee:** Krisztián

**Description:**
Use Gemini Grammar Validator to review first 5 A2 modules for:
- Grammar accuracy
- Calques
- Russianisms
- Natural Ukrainian expressions

**Acceptance Criteria:**
- [ ] All 5 modules reviewed with Gemini
- [ ] Any issues found and fixed
- [ ] Patterns logged in nlp-patterns-log.md
- [ ] Validation workflow tested and working

**Blockers:** E2-T2

---

### E2-T4: Add Audit Script Enhancement (Optional)

**Status:** Todo
**Priority:** P3 (Nice to have)
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Add simple vocabulary coverage check to audit:
- Check if Ukrainian words in activities are in module vocabulary
- Flag undefined words
- Non-blocking warning

**Acceptance Criteria:**
- [ ] New check in `scripts/audit/checks/vocabulary.py`
- [ ] Warns about undefined vocabulary
- [ ] Non-blocking (doesn't fail audit)
- [ ] Tested on A1/A2 modules

**Blockers:** None (optional enhancement)

---

# EPIC 3: NLP Dataset Extraction (Phase 1)

**Status:** Not Started
**Priority:** P2 (Medium - secondary goal)
**Timeline:** Q2 2025 (after A2 complete)
**Success Criteria:**
- [ ] 3 datasets extracted and validated
- [ ] Documentation written
- [ ] Released on GitHub with CC-BY-4.0 license

---

## Tickets - Epic 3

### E3-T1: Create Graded Corpus Extraction Script

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 2 days
**Assignee:** Krisztián

**Description:**
Extract all Ukrainian sentences from A1+A2 modules, tag with CEFR level.

**Output Format:**
```json
{
  "level": "A2",
  "module": 5,
  "sentence": "Я дав книгу моєму другу.",
  "grammar_focus": ["dative_case"],
  "word_count": 5
}
```

**Acceptance Criteria:**
- [ ] Script: `scripts/extract_corpus.py`
- [ ] Extracts from all A1 (34) + A2 (50) modules
- [ ] Outputs valid JSON
- [ ] README with dataset description
- [ ] ~5,000-10,000 sentences extracted

**Blockers:** E1-T6 (A2 must be complete)

---

### E3-T2: Create Error Correction Dataset Extraction Script

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 3 days
**Assignee:** Krisztián

**Description:**
Extract error→correct pairs from all error-correction activities.

**Output Format:**
```json
{
  "level": "A2",
  "module": 5,
  "error_sentence": "Я дав книгу мій друг",
  "correct_sentence": "Я дав книгу моєму другу",
  "error_type": "case_agreement",
  "error_span": {"start": 17, "end": 25, "text": "мій друг"},
  "correction_span": {"start": 17, "end": 29, "text": "моєму другу"}
}
```

**Acceptance Criteria:**
- [ ] Script: `scripts/extract_errors.py`
- [ ] Parses error-correction activity format
- [ ] Extracts error spans accurately
- [ ] Outputs valid JSON
- [ ] README with dataset description
- [ ] ~500-1000 error pairs extracted

**Blockers:** E1-T6

---

### E3-T3: Export Vocabulary Database to JSON

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Export `curriculum/l2-uk-en/vocabulary.db` to JSON with CEFR levels.

**Output Format:**
```json
{
  "word": "книга",
  "ipa": "/ˈkn̪ɪɦɑ/",
  "pos": "noun",
  "gender": "feminine",
  "english": "book",
  "level": "A1",
  "first_module": 3
}
```

**Acceptance Criteria:**
- [ ] Script: `scripts/export_vocabulary.py`
- [ ] Exports all A1+A2 vocabulary (~1,800 words)
- [ ] Outputs valid JSON
- [ ] README with dataset description

**Blockers:** E1-T5 (vocabulary rebuild)

---

### E3-T4: Dataset Documentation & README

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Write comprehensive documentation for all 3 datasets.

**Include:**
- Dataset description
- Format specification
- Example entries
- Statistics (size, coverage)
- License (CC-BY-4.0)
- Citation format
- How to use

**Acceptance Criteria:**
- [ ] README.md for each dataset
- [ ] LICENSE file (CC-BY-4.0)
- [ ] CITATION.cff for academic citation
- [ ] Examples in documentation

**Blockers:** E3-T1, E3-T2, E3-T3

---

### E3-T5: GitHub Release - Phase 1 Datasets

**Status:** Todo
**Priority:** P2
**Estimated Effort:** 1 day
**Assignee:** Krisztián

**Description:**
Release Phase 1 datasets on GitHub.

**Include:**
- Corpus dataset (JSON)
- Error correction dataset (JSON)
- Vocabulary dataset (JSON)
- Documentation
- License

**Acceptance Criteria:**
- [ ] GitHub release created
- [ ] All files uploaded
- [ ] Release notes written
- [ ] Announcement post drafted (optional)

**Blockers:** E3-T4

---

# EPIC 4: NLP Community Contribution (Phase 2)

**Status:** Not Started
**Priority:** P3 (Low - long-term goal)
**Timeline:** Q2-Q3 2025
**Success Criteria:**
- [ ] Engaged with Ukrainian NLP community
- [ ] Shared findings publicly
- [ ] Optional: Paper submitted to UNLP 2026

---

## Tickets - Epic 4

### E4-T1: Calque Detection Dataset Creation

**Status:** Todo
**Priority:** P3
**Estimated Effort:** 1 week
**Assignee:** Krisztián

**Description:**
Run Gemini validation on all A1+A2 modules specifically to detect calques.

**Output Format:**
```json
{
  "calque": "робити сенс",
  "source_language": "English",
  "source_phrase": "make sense",
  "natural_ukrainian": "мати сенс",
  "level": "B1",
  "module": 15
}
```

**Acceptance Criteria:**
- [ ] Script to batch-validate modules with Gemini
- [ ] Calques extracted and validated
- [ ] Dataset JSON created
- [ ] README documentation

**Blockers:** E1-T6, Gemini API access (or manual validation)

---

### E4-T2: Test Curriculum Against nlp_uk

**Status:** Todo
**Priority:** P3
**Estimated Effort:** 3 days
**Assignee:** Krisztián

**Description:**
Run nlp_uk on A1+A2 modules to find false positives (pedagogical simplifications flagged as errors).

**Deliverables:**
- Report of false positives
- Exception list for educational content
- GitHub issue on brown-uk/nlp_uk with findings

**Acceptance Criteria:**
- [ ] nlp_uk installed and tested
- [ ] False positive report created
- [ ] Issue submitted to nlp_uk repo (if valuable feedback)

**Blockers:** E1-T6

---

### E4-T3: Write Blog Post - "Building a Ukrainian Curriculum"

**Status:** Todo
**Priority:** P3
**Estimated Effort:** 2 days
**Assignee:** Krisztián

**Description:**
Write blog post about:
- Building Ukrainian curriculum as a Hungarian
- Challenges (calques, Russianisms, pedagogical decisions)
- Tools used (Gemini, nlp_uk, Stanza)
- Datasets released
- Contribution to Ukrainian NLP

**Acceptance Criteria:**
- [ ] Blog post written (~2000 words)
- [ ] Published on personal blog or Medium
- [ ] Shared in Ukrainian NLP communities

**Blockers:** E3-T5 (need datasets released first)

---

### E4-T4: UNLP 2026 Paper Submission (Optional)

**Status:** Todo
**Priority:** P4 (Optional - if ambitious)
**Estimated Effort:** 3-4 weeks
**Assignee:** Krisztián

**Description:**
Submit research paper to UNLP 2026 workshop (May 29-30, 2026).

**Possible Topics:**
- "A Large-Scale CEFR-Graded Ukrainian Corpus"
- "Error Correction Dataset for Ukrainian Learners"
- "Pedagogical Simplifications in Ukrainian Education"

**Acceptance Criteria:**
- [ ] Paper written (~8 pages)
- [ ] Datasets released publicly
- [ ] Submitted before deadline (~March 2026)

**Blockers:** E3-T5, significant time commitment

---

# Roadmap Timeline

```
Q1 2025 (Jan-Mar)
├─ Epic 1: A2 Curriculum Completion [P0]
│  ├─ E1-T1: Modules 06-15 (Week 1-2)
│  ├─ E1-T2: Modules 16-25 (Week 3-4)
│  ├─ E1-T3: Modules 26-35 (Week 5-6)
│  ├─ E1-T4: Modules 36-50 (Week 7-9)
│  ├─ E1-T5: Vocabulary Rebuild (Week 10)
│  └─ E1-T6: Pipeline Validation (Week 10-11)
│
└─ Epic 2: Grammar Validation [P1]
   ├─ E2-T1: Finalize prompt ✅
   ├─ E2-T2: Create pattern log (Week 1)
   ├─ E2-T3: Validate M01-M05 (Week 1)
   └─ E2-T4: Audit enhancement (Optional - Week 5)

Q2 2025 (Apr-Jun)
├─ Epic 3: Dataset Extraction [P2]
│  ├─ E3-T1: Corpus extraction (Week 1-2)
│  ├─ E3-T2: Error extraction (Week 2-3)
│  ├─ E3-T3: Vocabulary export (Week 3)
│  ├─ E3-T4: Documentation (Week 4)
│  └─ E3-T5: GitHub release (Week 4)
│
└─ Epic 4: Community Contribution [P3]
   ├─ E4-T1: Calque dataset (Week 5-6)
   └─ E4-T2: Test with nlp_uk (Week 7)

Q3 2025 (Jul-Sep)
└─ Epic 4 (continued)
   ├─ E4-T3: Blog post (Week 1-2)
   └─ E4-T4: UNLP paper (Optional - Q3-Q4)
```

---

# Priority Legend

- **P0 (Critical):** Blocking curriculum completion
- **P1 (High):** Directly supports P0 work
- **P2 (Medium):** Secondary goals, scheduled after P0 complete
- **P3 (Low):** Nice-to-have, community contribution
- **P4 (Optional):** Aspirational, time permitting

---

# Labels for GitHub Issues

If importing to GitHub, use these labels:

```
epic
epic:curriculum
epic:validation
epic:datasets
epic:community

priority:p0
priority:p1
priority:p2
priority:p3

status:todo
status:in-progress
status:blocked
status:done

effort:1-day
effort:1-week
effort:2-weeks
effort:1-month
```

---

**Next Step:** Import these to your project tracker (GitHub Issues / Projects)?
