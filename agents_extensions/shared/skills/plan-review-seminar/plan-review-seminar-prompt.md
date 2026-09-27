# Plan Review Prompt — Seminar Tracks

You are reviewing a Ukrainian language course plan YAML file for seminar tracks (FOLK, HIST, BIO, ISTORIO, LIT and subtracks, OES, RUTH). Your job is to find errors, weaknesses, and gaps BEFORE content is built from this plan.

**Key difference from core reviews:** Seminar tracks have NO State Standard mapping. Authority comes from external knowledge sources (Wikipedia, Literary RAG) and domain expertise, not government curriculum documents.

## Authority Sources

You have THREE authority sources. Use ALL of them:

1. **Wikipedia (Ukrainian)** — Use `mcp__sources__query_wikipedia` to verify people, events, dates, places. Wikipedia is the primary factual authority for Ukrainian history, biography, and culture. Search in Ukrainian. Available modes:
   - `mode='summary'` — quick intro paragraph (default)
   - `mode='extract'` — full article text (up to 50K chars) for deep verification
   - `mode='sections'` — list section headings with indices
   - `mode='section'` + `section=N` — read a specific section (get indices from mode='sections')
   - `mode='search'` — keyword search when you don't know the exact title

   Results are cached locally (30-day TTL). Use `force_refresh=true` for fresh data.

2. **Literary RAG** — Use `mcp__sources__search_literary` to verify primary source references. The RAG contains chronicles, poetry, legal texts, and other primary Ukrainian literary sources. For plans that cite specific works (Povist mynulykh lit, Kobzar, Ruska Pravda, etc.), verify the citations exist in the corpus.

3. **VESUM + GRAC** — Use `mcp__sources__verify_word` for vocabulary existence, `mcp__sources__query_grac` for frequency, `mcp__sources__query_r2u` for Russicism checks. Same as core reviews.

**Textbook RAG** (`mcp__sources__search_text`) is also available for grammar concepts if the plan includes grammar teaching. Search in Ukrainian.

## Input

Read the plan YAML file, then systematically check every item below.

## Size Policy (#4801)

Do not review seminar plans with a single fixed target table. The plan
`word_target` is the current floor until an explicit plan/policy revision
changes it, and dossier/source density controls justified expansion above that
floor.

Review size in three parts:

1. `word_target` must be numeric and must not be silently lowered from the
   existing locked plan.
2. Section budgets must align with the plan floor unless the plan carries an
   explicit size-policy rationale.
3. Expansion above coverage must be source-backed and pedagogically useful; if
   the dossier is thin, flag research incompleteness or plan/policy mismatch
   instead of demanding filler.

Typical advisory ranges:

| Band | Advisory range |
|------|----------------|
| Sparse dossier | 3800-5000 |
| Normal dossier | 5000-6500 |
| Dense dossier | 6500-8000 |
| Exceptional dossier | 8000+ only with explicit justification |

---

## Checks

### 1. RULE COMPLIANCE (blockers — any failure = plan REJECTED)

Flag as **CRITICAL**.

- [ ] **word_target has policy authority** — Numeric floor is present and either matches the locked plan/default or carries an explicit size-policy rationale. Do not auto-fail FOLK solely for being 4000 or 5000; flag unresolved plan/policy mismatch instead.
- [ ] **Section budgets sum correctly** — Sum all section `words:` values. Must be within +/-10% of `word_target`.
- [ ] **No section >10% under its budget** — Each section's word count should not be more than 10% below its stated target.
- [ ] **Required fields present** — module, level, sequence, slug, version, title, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona.
- [ ] **Version is a string** — `version: '2.0'` not `version: 2.0`.

### 2. FACTUAL ACCURACY (MANDATORY — replaces State Standard check)

**This is the most important check for seminar plans.** Historical/biographical/literary claims must be verifiable.

For each factual claim in `content_outline`, `objectives`, and `vocabulary_hints`:

- [ ] **Verify people** — Use `mcp__sources__query_wikipedia` for every named person. Verify: correct name spelling, correct dates, correct role/title. Ghost people (invented or confused identities) are **CRITICAL**.
- [ ] **Verify events** — Use `mcp__sources__query_wikipedia` for every named event. Verify: correct date, correct location, correct participants. Wrong dates are **HIGH**.
- [ ] **Verify places** — Named locations should be historically accurate for the period discussed. Anachronistic place names are **MEDIUM** (e.g., using modern city names for medieval locations without noting the historical name).
- [ ] **Verify primary sources** — If the plan references specific documents (chronicles, letters, legal codes), use `mcp__sources__search_literary` to check they exist. Ghost sources (invented documents) are **CRITICAL**.

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

- [ ] **VESUM check** — Use `mcp__sources__verify_word` for each Ukrainian word. Empty result = ghost word. Flag as **CRITICAL**.
- [ ] **Russicism check** — For words that might be shared with Russian, use `mcp__sources__query_r2u` to check. Flag as **HIGH**. Skip for clearly Ukrainian words.
- [ ] **Domain vocabulary appropriate** — Vocabulary should match the track domain (historical terms for HIST, literary terms for LIT, Old East Slavic terms for OES/RUTH). Flag as **LOW** if vocabulary is too generic.
- [ ] **Frequency check** — Use `mcp__sources__query_grac` (mode: frequency) on required vocabulary. For seminar tracks, low-frequency domain-specific words are expected and acceptable (unlike core levels where rare words are flagged).

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
- [ ] Person's dates verifiable via Wikipedia
- [ ] Connection to broader Ukrainian history/culture shown

#### ISTORIO (Historiography)
- [ ] Historiographical method discussed (not just history retold)
- [ ] Multiple perspectives on events/sources
- [ ] Source criticism component present

#### LIT and subtracks (lit-drama, lit-essay, lit-doc, lit-crimea, lit-fantastika, lit-hist-fic, lit-humor, lit-war, lit-youth)
- [ ] Literary analysis, not plot summary
- [ ] Author/work verifiable via Wikipedia or Literary RAG
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

#### FOLK (Folklore / Folk Culture)

- [ ] Apply `docs/folk-epic/FOLK-FRAMING-STANDARD.md` as a hard gate.
- [ ] No pagan-core / Christian-shell framing. Christian heritage is not a veneer over a hidden pagan essence.
- [ ] No occult, demonology-as-belief, or magic-as-core explanatory frame in teacher prose.
- [ ] Cosmogonic, demonological, or magic vocabulary appears only with source discipline and framing caveats, never as the module thesis.
- [ ] No Soviet/Russian demonizing lens: Ukrainian folk culture is not primitive, backward, superstition, banditry, or "Little Russian" material.
- [ ] Public learner sources use public URLs; internal corpus chunk IDs must not appear in public-facing or plan-facing learner surfaces.
- [ ] Primary readings are school-canonical/public-source grounded where applicable, and hosted texts use the full public text rather than snippets.

## Output Format

```markdown
# Plan Review (Seminar): {slug}

**Track:** {track} | **Sequence:** {sequence} | **Version:** {version}
**Verdict:** PASS / FAIL / NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS/FAIL | Plan floor: X; size-policy status/rationale |
| section_budgets | PASS/FAIL | Sum = X vs track target (+/-Z%) |
| required_fields | PASS/FAIL | Missing: ... |
| version_string | PASS/FAIL | ... |

## Factual Accuracy
| Claim | Source Used | Verified? | Notes |
|-------|------------|-----------|-------|
| Person: X (dates) | Wikipedia | YES/NO | ... |
| Event: Y (date) | Wikipedia | YES/NO | ... |
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

- **Batch Wikipedia lookups**: Wikipedia results are cached locally (30 days). Repeated queries for the same person/event are instant. Use `mode='extract'` for deep verification, `mode='summary'` for quick checks.
- **Prioritize CRITICAL**: If a CRITICAL issue is found, still complete the review but mark verdict as FAIL immediately
- **Search in Ukrainian**: "Тарас Шевченко" not "Taras Shevchenko", "Голодомор" not "Holodomor"
- **Track context matters**: A plan about Holodomor in HIST needs different checks than the same topic in ISTORIO (which focuses on historiographical method)
