VESUM confirms: **вивчати** = вивч-**ати** (suffix -ати), **малювати** = малю-**вати** (suffix -увати/-ювати). Neither is -яти. This is a confirmed factual error. Let me now compile the full review.

---

## Linguistic Scan

**Four separate checks:**

1. **Russianisms:** None found. All vocabulary is standard Ukrainian (VESUM-verified: 20/20 core words confirmed). No Russian ghost words.

2. **Surzhyk:** None found. No mixed forms detected.

3. **Calques:** No calques detected. `search_style_guide` returned no matches for "працювати в офісі" or "готувати вечерю" as calque patterns. Both are natural Ukrainian collocations.

4. **Paronyms:** None found.

**Morphological error found:**

> "Group I infinitives end in **-ати** (**читати**, **слухати**, **гуляти**, **знати**), **-увати** (**готувати**, **працювати**), or **-яти** (**вивчати**, **малювати** — to draw)."

This is **factually wrong**. VESUM `verify_lemma` confirms:
- **вивчати** = stem `вивч-` + suffix `-ати` → belongs to the **-ати** group, NOT -яти
- **малювати** = stem `маль-` + suffix `-ювати` → belongs to the **-увати/-ювати** group, NOT -яти

Both verbs are miscategorized. A learner who memorizes this will parse Ukrainian infinitives incorrectly.

**No Russian characters (ы, э, ё, ъ) found.** All case endings and gender assignments verified correct.

## Exercise Check

**Activity markers found (4 total):**

| # | Marker ID | Location | Plan match |
|---|-----------|----------|------------|
| 1 | `fill-in-conjugation` | After conjugation table (Section 2) | ✓ Plan hint 1: fill-in conjugation (10 items) |
| 2 | `quiz-verb-forms` | After person examples (Section 3) | ✓ Plan hint 2: quiz correct form (8 items) |
| 3 | `match-person-to-form` | After more examples (Section 3) | ✓ Plan hint 3: match person↔form (6 items) |
| 4 | `fill-in-context` | End of Section 3 | ✓ Plan hint 4: complete sentence (6 items) |

**Assessment:** All 4 plan `activity_hints` have corresponding markers. Markers placed AFTER relevant teaching content — correct sequencing. Markers 2–4 cluster in Section 3, but this matches the plan's focus (person forms are drilled there). Marker 1 stands alone in Section 2 after the conjugation table. Acceptable distribution.

No inline DSL exercises to check logic on — all exercises are injected via markers.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct topics. Both dialogues match plan specs (Dialogue 1: kitchen/what do you do with я/ти/він,вона; Dialogue 2: work/school context). Варзацька Grade 4 p.129 cited correctly (RAG confirmed the table exists at that page). Six essential verbs all present in conjugation table. Self-check in Підсумок matches plan exactly. Minor gap: recommended vocab **грати** (to play) absent from prose entirely. |
| 2. Linguistic accuracy | 8/10 | **Critical error:** вивчати and малювати wrongly classified as -яти infinitives (see Linguistic Scan). All conjugated forms verified correct against VESUM (читаю/читаєш/читає ✓, готую/готуєш/готує ✓, працюю/працюєш/працює ✓). No Russianisms, no surzhyk, no calques. Case forms in examples correct (книгу = acc.sg of книга ✓, пісню = acc.sg of пісня ✓). |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow: dialogues present verbs in situation → conjugation table extracts pattern → person-focused practice drills. RAG-confirmed textbook approach (Варзацька p.129, Захарійчук p.110 paradigm tables). Smart choice to focus on 3 singular persons first ("cover 90% of A1 conversations"), then plural for recognition only. Accusative case acknowledged but deferred ("learn as chunks for now") — good scope management. робити flagged as Group II preview — prevents future confusion. |
| 4. Vocabulary coverage | 9/10 | All 6 required verbs (читати, знати, працювати, слухати, гуляти, готувати) used naturally in dialogues and examples — not as bare lists. Recommended: робити ✓ (as chunk), вивчати ✓ (Dialogue 2), малювати ✓ (mentioned in Section 2), вечеря ✓, музика ✓. Missing: **грати** (to play) — recommended but absent. CEFR check: all verbs A1-appropriate (PULS confirms готувати=A1, працювати=A1, гуляти=A1). |
| 5. Exercise quality | 9/10 | 4 markers matching all 4 plan hints in type and focus. Markers placed after relevant teaching sections. Fill-in-conjugation after table ✓, quiz after person examples ✓, match-up after drilling persons ✓, contextual fill-in as capstone ✓. Cannot verify distractor quality (YAML generated separately), but placement logic is sound. |
| 6. Engagement & tone | 10/10 | No motivational openers, no "Let us explore," no gamified language. Opens with a concrete scene: "Юля is in the kitchen. Something smells amazing." Dialogue tip uses genuine pattern observation ("Помітив/-ла?"). Humor in "Вона завжди слухає музику!" Natural teacher voice: "Drill those three verb forms first." Mnemonic: "ти завжди -єш" — catchy and accurate. |
| 7. Structural integrity | 10/10 | All 4 H2 sections present in plan order. Word count 1308/1200 (109% — within range). No duplicate summaries. No meta-commentary. Clean markdown. Conjugation tables render correctly. No stray tags or formatting artifacts. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No "like Russian but..." comparisons. Textbook source (Варзацька) properly cited. Names are Ukrainian (Юля, Сашко, Олена, Андрій, Марина). Setting is natural (shared kitchen, after-work meeting). |
| 9. Dialogue & conversation quality | 10/10 | Dialogue 1: kitchen scene with named speakers (Юля cooking, Сашко curious), natural flow, three persons emerge organically, ends with personality detail ("Вона завжди слухає музику!"). Dialogue 2: post-work meeting (Андрій student, Марина office worker), natural progression from work → study → evening plans. Neither dialogue is interrogative. Both match plan's `dialogue_situations` spec. |

## Findings

**[LINGUISTIC ACCURACY] [SEVERITY: critical]**
Location: Section 2 "Перша дієвідміна", paragraph 1: `"or **-яти** (**вивчати**, **малювати** — to draw)"`
Issue: вивчати is вивч+**ати** (confirmed by VESUM: infinitive stem `вивч-`), NOT -яти. малювати is маль+**ювати** (VESUM: infinitive `малювати`, conjugation `малюю/малюєш` shows stem `малю-` from `-ювати`), NOT -яти. Both verbs are assigned to the wrong infinitive suffix category. A learner who memorizes this will mis-analyze Ukrainian verb morphology.
Fix: Reclassify вивчати under -ати and малювати under -увати/-ювати. Drop -яти (no A1-appropriate examples available; it can be introduced when relevant verbs appear in later modules).

**[VOCABULARY COVERAGE] [SEVERITY: minor]**
Location: Entire module
Issue: Recommended vocabulary item **грати** (to play) from plan's `vocabulary_hints.recommended` does not appear anywhere in the prose.
Fix: Could be woven into an example sentence or mentioned in passing, but this is recommended (not required) vocabulary. No content fix needed — noting for completeness.

## Verdict: REVISE

One critical linguistic error (wrong morphological classification of вивчати and малювати as -яти verbs) must be fixed before shipping. This is a factual error about Ukrainian grammar that learners would memorize incorrectly. All other dimensions are strong (9-10). Once the fix below is applied, module should pass.

<fixes>
- find: "Group I infinitives end in **-ати** (**читати**, **слухати**, **гуляти**, **знати**), **-увати** (**готувати**, **працювати**), or **-яти** (**вивчати**, **малювати** — to draw)."
  replace: "Group I infinitives end in **-ати** (**читати**, **слухати**, **гуляти**, **знати**, **вивчати**) or **-увати/-ювати** (**готувати**, **працювати**, **малювати** — to draw)."
</fixes>
