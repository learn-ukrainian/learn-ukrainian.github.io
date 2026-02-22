<!-- content-hash: 860a92cc11fc -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | Language Quality | 7 | IPA errors in vocabulary and content; incomplete sentence in pronunciation callout |
| 2 | Activity Quality | 7 | Untaught vocab in activities; reflexive past forms tested without grammar explanation |
| 3 | Richness | 8 | Good cultural hooks (Fedorov, ZUNR), varied dialogue contexts, museum persona |
| 4 | Lesson Quality | 7 | No warm greeting, massive motivational padding paragraph, good algorithm section |
| 5 | Immersion | 8 | 41.9% within 35-55% target for this grammar-focused module |
| 6 | LLM Fingerprint | 7 | ~150-word motivational filler paragraph at line 55; otherwise varied openings |
| 7 | Factual Accuracy | 7 | ZUNR language law date "15 лютого 1919" not in research notes, likely fabricated |
| 8 | Humanity & Warmth | 7 | No learner-facing greeting; encouragement mostly embedded in dialogues, not directed at learner |

---

## Critical Issues Found

### CRITICAL-1: Potentially Fabricated ZUNR Date (Factual Accuracy)

**Location:** Line 227, Section «Граматика: Минулий час дієслів», [!culture] callout

**Evidence:** The content states: «Саме 15 лютого 1919 року сталася ще одна подія. ЗУНР (Західноукраїнська Народна Республіка) **ухвали́ла** закон про українську мову.»

The research notes (research file line 19) mention ZUNR (1918-1919) and "закон про державну мову" but provide **no specific date**. The date "15 лютого 1919" appears nowhere in the research notes. This date appears to be fabricated to create a thematic parallel with the Fedorov date (February 15, 1574) used earlier in the lesson. Presenting an unverifiable historical date as fact in a [!culture] callout is a serious factual integrity issue.

**Fix:** Either verify the date with a reliable historical source and add it to the research notes, or remove the specific date and say something like «У 1919 році ЗУНР ухвалила закон про українську мову» — keeping it vague when the exact date isn't confirmed.

---

### CRITICAL-2: IPA Errors for "вчора" (Language Quality)

**Location:** Vocabulary file line 1; Content file line 49, Section «Розминка: Вчора і сьогодні»

**Evidence — Vocabulary file:** `ipa: '[ˈʍt͡ʃɔrɑ]'` — The symbol `ʍ` represents a voiceless labial-velar fricative (as in Scottish English "which"). This is not a Ukrainian phoneme. Ukrainian в before voiceless consonants is realized as [u̯] (non-syllabic close back rounded vowel). Furthermore, stress is marked on `ʍ` when it should be on `ɔ` (вчо́ра).

**Evidence — Content file line 49:** «Він звучить м'яко: [u̯t͡ʃɔrɑ].» — Uses the correct `u̯` symbol but is **missing the stress mark**. Should be `[u̯ˈt͡ʃɔrɑ]`.

The vocabulary file and content file are also **inconsistent with each other** — one uses `ʍ`, the other uses `u̯`.

**Fix:** Vocabulary: change to `[u̯ˈt͡ʃɔrɑ]`. Content line 49: change to `[u̯ˈt͡ʃɔrɑ]`. Both must match.

---

### CRITICAL-3: Incomplete Sentence in Pronunciation Callout (Language Quality)

**Location:** Line 49, Section «Розминка: Вчора і сьогодні», [!tip] callout

**Evidence:** «Слово **вчора** почина́ється зі зву́ка. Цей звук схожий на англійське "w" у слові "wow".» — The sentence «починається зі звука» ("starts with a sound") is semantically incomplete — it doesn't specify WHICH sound. Every word starts with a sound. The sentence should name the sound, e.g., «починається зі звука [u̯]» or «починається зі звука «в», який вимовляється як [u̯]».

**Fix:** Rewrite as: «Слово **вчора** почина́ється зі зву́ка [u̯]. Цей звук схожий на англійське "w"...»

---

### ISSUE-4: Motivational Padding Paragraph (LLM Fingerprint / Lesson Quality)

**Location:** Line 55, Section «Розминка: Вчора і сьогодні»

**Evidence:** A single ~150-word English paragraph beginning "Talking about the past is essential for building relationships" that repeats the same motivational point multiple times — "your world is very small", "you open a door to your entire life", "share your memories, your experiences, and your culture", "moves you from being an observer to being a storyteller". This is classic LLM filler: abstract motivation saying the same thing 4 different ways without any concrete pedagogical content or Ukrainian language.

For an A1 learner, this wall of English text after the time expressions section and before the next subsection disrupts pacing and provides no new vocabulary or grammar. It violates the "small chunks, frequent practice" principle.

**Fix:** Cut to 2-3 sentences max, or replace with a quick micro-exercise that lets the learner practice the time expressions just introduced.

---

### ISSUE-5: Activity Tests Vocabulary Not Taught in Content (Activity Quality)

**Location:** Activities file lines 28-29 (match-up), lines 308-311 (fill-in)

**Evidence (match-up):** The "Час (Time Expressions)" match-up includes «сьогодні вранці» → "this morning" and «сьогодні ввечері» → "this evening". The content teaches «вчора зранку», «вчора вдень», «вчора ввечері» — but never teaches the «сьогодні + time of day» constructions. Additionally, the content consistently uses «зранку» while the activity uses «вранці» — a different (though valid) form that could confuse A1 learners.

**Evidence (fill-in):** The "Моє вчора" activity tests «прокидалася» (answer at line 309), but the content at line 241 teaches «вставати» (to get up), not «прокидатися» (to wake up). These are distinct verbs. While «прокидатися» is in the vocabulary list, it never appears in the lesson narrative.

**Fix:** In the match-up, replace «сьогодні вранці» with «вчора зранку» to align with taught content, or add these expressions to the lesson. In the "Моє вчора" fill-in, replace «прокидалася» with a form of «вставати» (e.g., «вставала»), or add «прокидатися» to the lesson narrative.

---

### ISSUE-6: Reflexive Past Tense Forms Tested Without Explanation (Activity Quality)

**Location:** Activities file lines 91-93 (fill-in for дивитися)

**Evidence:** The fill-in item "Ми __________ новий фільм" with answer «дивилися» and options `["дивився", "дивилася", "дивилося", "дивилися"]` tests reflexive past tense forms. The grammar section in «Граматика: Минулий час дієслів» teaches only the non-reflexive pattern (-в/-ла/-ло/-ли). The reflexive -ся extension is never explained. The practice section at line 244 introduces «дивився / дивилася» as vocabulary but without grammatical explanation of how -ся attaches to past forms.

**Fix:** Either add a brief note in the grammar section (e.g., "For reflexive verbs like дивитися, add -ся after the past tense ending: дивився, дивилася, дивилося, дивилися") or replace this activity item with a non-reflexive verb.

---

### ISSUE-7: Missing Warm Opening / Learner Greeting (Humanity & Warmth)

**Location:** Lines 9-13, Section «Розминка: Вчора і сьогодні»

**Evidence:** The module opens directly with an abstract motivational question «Чому це важливо?» followed by philosophical prose ("life is made of memories and stories"). There is no "Привіт!" or learner-facing greeting. The first use of "Привіт" appears only at line 277, inside a dialogue (character speech, not tutor addressing learner). For A1.3 learners, the opening should feel like walking into a comfortable tutoring session, not a philosophy lecture.

The "Would I Continue?" test WELCOME criterion expects a warm greeting and context setting. The current opening misses the greeting element.

**Fix:** Add a direct greeting before the quote block: "Привіт! Welcome back. Today's lesson is going to change everything — we're finally stepping into the past."

---

## Factual Verification

| Claim | Source | Status |
|-------|--------|--------|
| Ivan Fedorov printed the "Apostol" on February 15, 1574 in Lviv | Research notes line 18: confirmed "15 лютого 1574 року Іван Федоров у Львові видав 'Апостол'" | **PASS** |
| ZUNR passed a language law on February 15, 1919 | Research notes line 19: mentions ZUNR and language law but **no date given** | **FAIL — unverifiable** |
| Past tense formation: stem + -в/-ла/-ло/-ли | Research notes line 4: confirmed per State Standard §4.2.4.1 | **PASS** |
| "Йти" → ішов/ішла in past tense (suppletive stem) | Research notes line 24: confirmed "йти (ішов/ішла/ішли)" | **PASS** |
| "Їсти" → їв/їла in past tense | Research notes line 23: confirmed "їсти (їв/їла)" | **PASS** |
| "В минулому році" is incorrect; use "минулого року" | Research notes line 11: confirmed "минулого року" without preposition | **PASS** |

---

## Section-Level Assessment

### Section «Розминка: Вчора і сьогодні» (Lines 15-71)
**Strengths:** Museum curator persona established early (line 31). Cultural hook with Fedorov is well-integrated — past tense examples emerge naturally from the historical narrative. Time expressions (вчора зранку/вдень/ввечері) are clearly presented with translations. The [!warning] box about «Жодних прийменників!» at line 67-68 is excellent — anticipates a real learner error.

**Weaknesses:** Incomplete sentence at line 49 in the pronunciation tip. Motivational padding at line 55 (~150 words of abstract English). No warm greeting at the opening. The genitive case is mentioned at line 60 which is technically scope-adjacent but handled well as "memorize these phrases."

### Section «Граматика: Минулий час дієслів» (Lines 73-321)
**Strengths:** Excellent step-by-step "algorithm" (lines 78-87) — clear, visual, and beginner-friendly. Summary table at lines 122-128 is clean. [!observe] box about gender agreement (lines 133-139) addresses a real common error. The "Was Working" trap at lines 174-182 is well-explained. Irregular verbs (їсти, йти) are presented with clear examples. The Curator's Yesterday narrative at lines 211-223 provides immersive contextualized practice. Negation section (lines 141-157) is a valuable addition even though not in the outline.

**Weaknesses:** This section is very long (covering lines 73-321, roughly 60% of the module). The ZUNR date at line 227 is unverifiable. The [!note] about ішов/йшов alternation (lines 203-208) may be cognitively heavy for A1 — the euphonic alternation is a nice-to-know, not a must-know.

### Section «Практика: Спогади про вчора» (Lines 231-321)
**Strengths:** Excellent variety — building blocks (line 240-244), male/female narrative models (lines 246-250), collocations table (lines 255-263), four natural dialogues with different registers (casual, specific time, family, work). The office story (lines 311-313) adds professional context. The [!myth-buster] on ходити vs йти (lines 317-321) addresses a real confusion point. The dialogues feel natural — «Молодці» at line 297 is a realistic parent response.

**Weaknesses:** The male narrative (line 247) and female narrative (line 250) are quite long for A1 — each is a solid paragraph of unbroken Ukrainian with no English glosses. The office narrative (line 312) is even longer. Some learners at A1.3 may feel overwhelmed by these extended blocks.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from outline present? | **PASS** — 3/3 content_outline sections present as H2 |
| Vocabulary scope matches plan? | **PARTIAL** — All required vocab present; «прокидатися» in vocab but not in content narrative |
| Grammar scope respected? | **PASS** — Past tense formation, gender agreement, time expressions all within scope |
| All learning objectives addressed? | **PASS** — Form past tense ✓, gender endings ✓, time expressions ✓, describe past events ✓ |
| Russianisms? | **PASS** — No Russianisms detected |
| Colonial framing? | **PASS** — No Ukrainian-vs-Russian comparisons; English used as comparison point (appropriate) |
| Calque errors? | **PASS** — "Was working" calque explicitly addressed as an error to avoid |
| Activity errors? | **FAIL** — Untaught vocab in activities (сьогодні вранці, прокидалася); reflexive forms untaught |
| IPA accuracy? | **FAIL** — ʍ in vocabulary file is wrong phoneme; stress missing in content IPA |
| Factual accuracy? | **FAIL** — ZUNR date unverifiable |

---

## Verdict

**NEEDS REVISION** — The module has strong pedagogical bones: the grammar algorithm is clear, the museum curator persona works, and the dialogues feel natural. However, three issues require fixes before approval:

1. **Factual integrity** — The ZUNR date must be verified or generalized (Critical-1)
2. **IPA correctness** — Both the vocabulary file and content pronunciation box need fixing (Critical-2, Critical-3)
3. **Activity-content alignment** — Activities test forms and vocabulary not taught in the lesson (Issues 5-6)

Secondary fixes (motivational padding, warm opening, section pacing) would elevate the module from adequate to good but are not blockers.

**Priority fix order:** Critical-1 → Critical-2 → Critical-3 → Issue-5 → Issue-6 → Issue-4 → Issue-7