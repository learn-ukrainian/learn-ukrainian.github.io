# Test Scenario: B2-HIST M41 Full Pipeline

**Test ID:** b2-hist-m41-full-pipeline
**Track:** B2-HIST (Ukrainian History)
**Module:** 41 - Козацтво: Витоки (Cossack Origins)
**Issue:** #461

---

## Objective

Run module 41 through the complete 9-phase workflow to validate:
1. AI-optimized template compliance
2. Phase locking mechanism
3. Output quality (audit pass rate)
4. Cross-LLM consistency (Claude vs Gemini)

---

## Pre-Test Setup

Before running, ensure:
- [ ] Clean working directory (no uncommitted changes to test module)
- [ ] Backup existing files if rebuilding: `meta/kozatstvo-vytoky.yaml`, `kozatstvo-vytoky.md`, etc.
- [ ] Note the LLM being used (Claude/Gemini) and version

---

## Test Execution

### Phase 1: Meta Generation

**Command:**
```
/module-meta b2-hist 41
```

**Expected output:** `curriculum/l2-uk-en/b2-hist/meta/kozatstvo-vytoky.yaml`

**Check:**
- [ ] word_target is ~4000
- [ ] content_outline has 4-6 sections with word targets
- [ ] activity_hints includes `reading` and `essay-response`
- [ ] vocabulary_hints has 15-25 terms

---

### Phase 2: Meta QA

**Command:**
```
/module-meta-qa b2-hist 41
```

**Expected:** PASS or list of violations

**Check:**
- [ ] All required fields present
- [ ] Word targets within range
- [ ] Objectives use measurable verbs

---

### Phase 3: Lesson Generation

**Command:**
```
/module-lesson b2-hist 41
```

**Expected output:** `curriculum/l2-uk-en/b2-hist/kozatstvo-vytoky.md`

**Check:**
- [ ] Sections match content_outline from meta
- [ ] Word count within 10% of target
- [ ] 100% Ukrainian (no English except technical terms)
- [ ] No activities in markdown file

---

### Phase 4: Lesson QA

**Command:**
```
/module-lesson-qa b2-hist 41
```

**Expected:** PASS or list of violations

**Check:**
- [ ] Word count gate passed
- [ ] Sections match outline
- [ ] No AI contamination detected
- [ ] Naturalness score >= 8

---

### Phase 5: Activity Generation

**Command:**
```
/module-act b2-hist 41
```

**Expected output:** `curriculum/l2-uk-en/b2-hist/activities/kozatstvo-vytoky.yaml`

**Check:**
- [ ] 3-10 activities
- [ ] Includes `reading` type
- [ ] Includes `essay-response` type (150-250 words)
- [ ] YAML is bare list (not wrapped in `activities:`)

---

### Phase 6: Activity QA

**Command:**
```
/module-act-qa b2-hist 41
```

**Expected:** PASS or list of violations

**Check:**
- [ ] Schema valid
- [ ] Required types present
- [ ] No forbidden activity types (match-up, fill-in, etc. if seminar-style)

---

### Phase 7: Integration

**Command:**
```
/module-integrate b2-hist 41
```

**Expected output:** `docusaurus/docs/b2-hist/kozatstvo-vytoky.mdx`

**Check:**
- [ ] MDX generated successfully
- [ ] Cross-file alignment (meta ↔ content ↔ activities)
- [ ] `npm run pipeline` passes

---

### Phase 8: Vocabulary Extraction

**Command:**
```
/module-vocab b2-hist 41
```

**Expected output:** `curriculum/l2-uk-en/b2-hist/vocabulary/kozatstvo-vytoky.yaml`

**Check:**
- [ ] 20-25 vocabulary items
- [ ] All words appear in content or activities
- [ ] Schema valid (lemma, ipa, translation, pos)

---

### Phase 9: Vocabulary QA

**Command:**
```
/module-vocab-qa b2-hist 41
```

**Expected:** PASS or list of violations

**Check:**
- [ ] Schema valid
- [ ] No duplicates with previous modules
- [ ] IPA format correct

---

## Post-Test Analysis

### Results Summary

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Meta | | |
| 2. Meta-QA | | |
| 3. Lesson | | |
| 4. Lesson-QA | | |
| 5. Act | | |
| 6. Act-QA | | |
| 7. Integrate | | |
| 8. Vocab | | |
| 9. Vocab-QA | | |

### Quality Metrics

| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Word count | | 4000 ±10% | |
| Activity count | | 3-10 | |
| Vocabulary count | | 20-25 | |
| Naturalness score | | ≥8 | |
| Audit pass rate | | 100% | |

### Observations

**Template Compliance:**
-

**Phase Locking:**
-

**Issues Found:**
-

**Comparison Notes (if both LLMs tested):**
-

---

## Files to Save

After test completion, copy results to:
```
tests/workflow/results/{claude|gemini}/b2-hist-m41/
├── meta.yaml
├── lesson.md
├── activities.yaml
├── vocabulary.yaml
├── integrate.mdx
└── test-report.md
```
