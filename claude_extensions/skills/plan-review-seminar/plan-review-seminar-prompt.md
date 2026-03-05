# Plan Review Prompt — Seminar Tracks

You are reviewing a Ukrainian language course plan YAML file for seminar tracks (HIST, BIO, ISTORIO, LIT and subtracks, OES, RUTH). Your job is to find errors, weaknesses, and gaps BEFORE content is built from this plan.

**Key difference from core reviews:** Seminar tracks have NO State Standard mapping. Authority comes from external knowledge sources (ESU, Wikipedia, Literary RAG) and domain expertise, not government curriculum documents.

## Authority Sources

You have FOUR authority sources. Use ALL of them:

1. **ESU (Encyclopedia of Modern Ukraine)** — Use `mcp__rag__search_esu` to verify people, events, dates, places. ESU is the primary factual authority for Ukrainian history, biography, and culture. Search in Ukrainian.

2. **Wikipedia (Ukrainian)** — Use `mcp__rag__query_wikipedia` to cross-reference dates, events, biographical facts. Use as a secondary check when ESU doesn't cover a topic or for broader context.

3. **Literary RAG** — Use `mcp__rag__search_literary` to verify primary source references. The RAG contains chronicles, poetry, legal texts, and other primary Ukrainian literary sources. For plans that cite specific works (Povist mynulykh lit, Kobzar, Ruska Pravda, etc.), verify the citations exist in the corpus.

4. **VESUM + GRAC** — Use `mcp__rag__verify_word` for vocabulary existence, `mcp__rag__query_grac` for frequency, `mcp__rag__query_r2u` for Russicism checks. Same as core reviews.

**Textbook RAG** (`mcp__rag__search_text`) is also available for grammar concepts if the plan includes grammar teaching. Search in Ukrainian.

## Input

Read the plan YAML file, then systematically check every item below.

## Word Targets (from config.py)

**NEVER lower these. If the plan has a different value, flag as CRITICAL.**

| Track | target_words |
|-------|-------------|
| HIST | 5000 |
| ISTORIO | 5000 |
| BIO | 5000 |
| LIT (all subtracks) | 5000 |
| OES | 5000 |
| RUTH | 5000 |

---

## Checks

### 1. RULE COMPLIANCE (blockers — any failure = plan REJECTED)

Flag as **CRITICAL**.

- [ ] **word_target matches config** — Must be 5000 for all seminar tracks.
- [ ] **Section budgets sum correctly** — Sum all section `words:` values. Must be within +/-10% of `word_target`.
- [ ] **No section >10% under its budget** — Each section's word count should not be more than 10% below its stated target.
- [ ] **Required fields present** — module, level, sequence, slug, version, title, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona.
- [ ] **Version is a string** — `version: '2.0'` not `version: 2.0`.

### 2. FACTUAL ACCURACY (MANDATORY — replaces State Standard check)

**This is the most important check for seminar plans.** Historical/biographical/literary claims must be verifiable.

For each factual claim in `content_outline`, `objectives`, and `vocabulary_hints`:

- [ ] **Verify people** — Use `mcp__rag__search_esu` for every named person. Verify: correct name spelling, correct dates, correct role/title. Ghost people (invented or confused identities) are **CRITICAL**.
- [ ] **Verify events** — Use `mcp__rag__search_esu` and `mcp__rag__query_wikipedia` for every named event. Verify: correct date, correct location, correct participants. Wrong dates are **HIGH**.
- [ ] **Verify places** — Named locations should be historically accurate for the period discussed. Anachronistic place names are **MEDIUM** (e.g., using modern city names for medieval locations without noting the historical name).
- [ ] **Verify primary sources** — If the plan references specific documents (chronicles, letters, legal codes), use `mcp__rag__search_literary` to check they exist. Ghost sources (invented documents) are **CRITICAL**.

### 3. SOURCE QUALITY

- [ ] **Sources listed** — Plan should have a `sources:` field with at least 2-3 references.
- [ ] **Source types appropriate** — Should include at least one `primary` or `reference` type source.
- [ ] **No ghost URLs** — Do not verify URLs (they may be valid but inaccessible), but check that source names correspond to real works/articles.
- [ ] **Primary sources match content** — If `content_outline` discusses a specific document, it should appear in `sources:` or `vocabulary_hints`.

### 4. DECOLONIZATION STANCE (MANDATORY)

**Every seminar plan must be checked for imperial framing. This is non-negotiable.**

- [ ] **No Russian-centric framing** — History told from Ukrainian perspective. Events are not presented as appendices to Russian history. Flag as **HIGH** if the plan frames Ukrainian events primarily through Russian lens.
- [ ] **No "common heritage" myths** — Claims like "shared cradle of three brotherly nations" or "common Kyivan Rus heritage" for Russia/Ukraine/Belarus are imperial propaganda. Flag as **CRITICAL**.
- [ ] **Correct terminology** — "Kyivan Rus" not "Kievan Russia". "Ukrainian lands" not "Little Russia". Proper Ukrainian transliteration of names. Flag as **HIGH**.
- [ ] **Agency preserved** — Ukrainians are subjects of their own history, not objects of others' actions. Plans should not reduce Ukrainians to passive recipients of external influence. Flag as **MEDIUM**.
- [ ] **Decolonization section present** — For HIST and ISTORIO plans, check if `content_outline` includes explicit decolonization perspective (myth-busting, counter-narrative). Not required for every plan, but should be present in most. Flag as **LOW** if missing.

### 5. VOCABULARY VERIFICATION (use VESUM + GRAC)

For every word in `vocabulary_hints.required` and `vocabulary_hints.recommended`, and in the `vocabulary:` list if present:

- [ ] **VESUM check** — Use `mcp__rag__verify_word` for each Ukrainian word. Empty result = ghost word. Flag as **CRITICAL**.
- [ ] **Russicism check** — For words that might be shared with Russian, use `mcp__rag__query_r2u` to check. Flag as **HIGH**. Skip for clearly Ukrainian words.
- [ ] **Domain vocabulary appropriate** — Vocabulary should match the track domain (historical terms for HIST, literary terms for LIT, Old East Slavic terms for OES/RUTH). Flag as **LOW** if vocabulary is too generic.
- [ ] **Frequency check** — Use `mcp__rag__query_grac` (mode: frequency) on required vocabulary. For seminar tracks, low-frequency domain-specific words are expected and acceptable (unlike core levels where rare words are flagged).

### 6. YAML QUALITY

- [ ] **No YAML syntax issues** — Strings with colons, quotes, or special characters must be properly quoted.
- [ ] **No Latin characters in Ukrainian text** — Check for Latin lookalikes (a/a, o/o, c/c, i/i, e/e).
- [ ] **Prerequisites are valid** — Listed prerequisites should reference existing plans or reasonable external dependencies.
- [ ] **Connects_to references valid** — Cross-references to other modules should use real slugs or module IDs.

### 7. PEDAGOGICAL QUALITY (Seminar-Specific)

- [ ] **Objectives are analytical, not encyclopedic** — Objectives should require analysis, evaluation, or synthesis — not just recall. "Analyze the political reasons for X" not "List the facts about X". Flag as **HIGH** if objectives are pure recall.
- [ ] **Content outline has narrative arc** — Sections should build toward insight, not just dump facts. Look for: hook, development, climax/insight, resolution. Flag as **MEDIUM** if flat structure.
- [ ] **Activity hints match seminar level** — Types should include: reading, critical-analysis, essay-response, comparative-study. Simple quiz/fill-blank types are inappropriate for seminars. Flag as **MEDIUM**.
- [ ] **Persona appropriate** — Voice should be scholarly but engaging (not textbook-dry). Role should connect to the topic.

### 8. TRACK-SPECIFIC CHECKS

#### HIST (History)
- [ ] Content outline mentions primary sources (at least referenced)
- [ ] Chronological accuracy (events in correct order)
- [ ] Decolonization perspective present

#### BIO (Biography)
- [ ] Life arc present (birth → development → achievement → legacy)
- [ ] Person's dates verifiable via ESU
- [ ] Connection to broader Ukrainian history/culture shown

#### ISTORIO (Historiography)
- [ ] Historiographical method discussed (not just history retold)
- [ ] Multiple perspectives on events/sources
- [ ] Source criticism component present

#### LIT and subtracks (lit-drama, lit-essay, lit-doc, lit-crimea, lit-fantastika, lit-hist-fic, lit-humor, lit-war, lit-youth)
- [ ] Literary analysis, not plot summary
- [ ] Author/work verifiable via ESU or Literary RAG
- [ ] Intertextual connections mentioned

#### OES (Old East Slavic)
- [ ] Old East Slavic linguistic concepts accurate
- [ ] Primary texts referenced are real (use Literary RAG to verify)
- [ ] Grammar/vocabulary appropriate for historical period

#### RUTH (Ruthenian/Early Ukrainian)
- [ ] Historical language period accurate (14th-18th century)
- [ ] Primary texts referenced are real
- [ ] Language evolution from OES shown where relevant

---

## Output Format

```markdown
# Plan Review (Seminar): {slug}

**Track:** {track} | **Sequence:** {sequence} | **Version:** {version}
**Verdict:** PASS / FAIL / NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS/FAIL | Plan: X, Config: 5000 |
| section_budgets | PASS/FAIL | Sum = X vs target 5000 (+/-Z%) |
| required_fields | PASS/FAIL | Missing: ... |
| version_string | PASS/FAIL | ... |

## Factual Accuracy
| Claim | Source Used | Verified? | Notes |
|-------|------------|-----------|-------|
| Person: X (dates) | ESU / Wikipedia | YES/NO | ... |
| Event: Y (date) | ESU / Wikipedia | YES/NO | ... |
| Source: Z | Literary RAG | YES/NO | ... |

## Decolonization Check
| Item | Status | Details |
|------|--------|---------|
| No Russian-centric framing | PASS/FAIL | ... |
| No imperial myths | PASS/FAIL | ... |
| Correct terminology | PASS/FAIL | ... |
| Ukrainian agency | PASS/FAIL | ... |

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| ... | OK/FAIL | ... |

## Issues Found

### CRITICAL (must fix before build)
1. ...

### HIGH (should fix before build)
1. ...

### MEDIUM (fix if possible)
1. ...

### LOW (informational)
1. ...

## Suggested Fixes
[Concrete YAML edits with old/new]
```

---

## Batch Execution

Iterate over plan files:

```
for each plan in plans/{track}/*.yaml:
    run plan-review-seminar with plan_path and track
    save output to {track}/audit/{slug}-plan-review.md
```

### Efficiency Notes

- **Batch ESU lookups**: For plans about the same person/event across tracks (e.g., Shevchenko in BIO and LIT), cache the ESU result mentally
- **Prioritize CRITICAL**: If a CRITICAL issue is found, still complete the review but mark verdict as FAIL immediately
- **Search in Ukrainian**: "Тарас Шевченко" not "Taras Shevchenko", "Голодомор" not "Holodomor"
- **Track context matters**: A plan about Holodomor in HIST needs different checks than the same topic in ISTORIO (which focuses on historiographical method)
