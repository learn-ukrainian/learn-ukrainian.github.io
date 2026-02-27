**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Factual Accuracy** | 8/10 | Russianism `надіятися` presented as standard; `піднімається` used for "getting up from bed" instead of `вставати`; claim about `сміятися над` being purely Russian influence is defensible but oversimplified |
| 2 | **Language Quality** | 7/10 | Two Russianisms in teaching content (`надіятися`, `піднімається`); colonial framing at line 401 defines Ukrainian pronunciation via contrast with Russian; minor euphony issue `у` after vowel on line 327 |
| 3 | **Immersion** | 9/10 | 22.6% is well within the 15-35% target band for modules 6-10; progressive bilingual scaffolding is well-executed with English explanations + Ukrainian examples throughout |
| 4 | **Activity Quality** | 8/10 | 10 activities with good variety (group-sort, match-up, quiz, fill-in, anagram); well-designed distractors; but `надіятися` propagated into 3 activities (lines 38, 318, 480); activity YAML is clean and schema-compliant |
| 5 | **Lesson Quality** | 8/10 | Engaging content with excellent analogies (mirror/laser beam). Section «Теорія: Відмінювання та групи» introduces 4 verb types + conjugation tables + preposition alert before any practice — significant cognitive load for A1. Maxim's Morning story is outstanding pedagogy. 4/5 on "Would I Continue?" (pacing concern in theory section) |
| 6 | **Richness** | 7/10 | 82% vs 95% threshold. Gaps: `cultural: 0/3` (only 1 `[!culture]` callout at line 418), `dialogues: 2/4` (Maxim story + gym dialogue, need 2 more). 6 callout boxes overall but cultural dimension specifically underserved |
| 7 | **LLM Fingerprint** | 8/10 | Section openings are reasonably varied. No structural monotony. Minor generic phrasing: "This distinction is vital for clarity" (line 222), "This is one of the most important pronunciation tips in the Ukrainian language" (line 388). Example formatting varies well across sections (bullet lists, tables, narrative story, dialogue). No detected `це не просто` / `це не лише` patterns |
| 8 | **Humanity & Warmth** | 9/10 | Warm tutor voice throughout. Good encouragement ("Knowing this history is your secret weapon" line 90). Friendly scenarios. Direct address used extensively. Minor miss: no explicit "You can now..." celebration at the very end — the summary (lines 422-435) lists rules but doesn't celebrate progress |

---

## Critical Issues Found

### Issue 1: Russianism `надіятися` taught as standard vocabulary [CRITICAL — Russicism]
- **Location:** Content line 208, vocabulary line 62, activities lines 38, 318, 480
- **Evidence:** Content line 208: «**Надіятися** (to hope) — to place hope.» and line 209: «*Ми надіємось на краще.*»
- **Problem:** `надіятися` is a Russianism (from Russian `надеяться`). Standard Ukrainian uses `сподіватися`. The module itself is INCONSISTENT — it uses `сподіватися` in the Maxim story at line 298 («Я **сподіваюсь** на гарний день!») and in the vocabulary glossary at line 308 («**сподіватися** — to hope»). Teaching A1 learners two words for "hope" — one standard, one a Russianism — without flagging the difference is confusing and pedagogically harmful. The vocabulary YAML also has BOTH `надіятися` (line 62) and `сподіватися` (line 88).
- **Confirmed by D.0 scanner:** YES — this was pre-flagged.
- **Fix:** Replace all instances of `надіятися` / `надіємось` / `надіюся` with `сподіватися` / `сподіваємось` / `сподіваюся` in content (lines 208-209), activities (lines 38, 318-325, 480), and vocabulary (line 62). Remove `надіятися` entry from vocabulary YAML entirely.

### Issue 2: Russianism `піднімається` / `підніматися` in morning routine context [HIGH — Russicism]
- **Location:** Content line 258, vocabulary glossary line 305
- **Evidence:** Line 258: «Він повільно **піднімається** і йде у ванну.» and line 305: «**підніматися** — to get up / rise»
- **Problem:** For "getting up from bed in the morning," standard Ukrainian uses `вставати` (встає). The usage of `піднімається` in this context is a calque from Russian `поднимается`. `Піднімається` is correct for physical ascending/climbing, but for the morning routine meaning, `встає` is the natural Ukrainian choice.
- **Fix:** Line 258 → «Він повільно **встає** і йде у ванну.» Line 305 → «**вставати** — to get up (from bed)». Keep `підніматися` if used for physical rising elsewhere, but not for the "wake up → get out of bed" semantic slot.

### Issue 3: Colonial framing — Ukrainian pronunciation defined via Russian contrast [HIGH — Colonial]
- **Location:** Content line 401
- **Evidence:** Line 401: «This sound instantly distinguishes a native Ukrainian speaker. In Russian, the reflexive ending is hard and short. In Ukrainian, it is **soft** and **long**.»
- **Problem:** Defines Ukrainian phonetics by what Russian does first, treating Russian as the baseline. Ukrainian learners should learn the Ukrainian sound on its own terms. This is not a `[!myth-buster]` or `[!decolonization]` block — it's in the regular teaching prose.
- **Fix:** Rewrite to present the Ukrainian feature independently: "This sound instantly distinguishes a native Ukrainian speaker. The Ukrainian reflexive ending is **soft** and **long** — hold that gentle and smile." Remove the Russian comparison entirely.

### Issue 4: IPA stress errors in vocabulary YAML [HIGH — IPA]
- **Location:** Vocabulary lines 65, 77
- **Evidence (a):** Line 65: `прокидатися` IPA is `[prɔkɪdɑtɪsʲɑ]` — **missing stress marker** entirely. Correct: `` (stress on third syllable: проки**да**тися).
- **Evidence (b):** Line 77: `втомлюватися` IPA is `` — **wrong stress placement** on initial syllable. Correct: `` (stress on fourth syllable: втомлю**ва**тися). The symbol `ʍ` (voiceless labial-velar approximant) is also a non-standard IPA choice for Ukrainian `в` before voiceless consonants.
- **Fix:** (a) ``, (b) ``

### Issue 5: Richness below threshold — missing dialogues and cultural content [MEDIUM — Richness]
- **Location:** Entire module
- **Evidence:** Audit shows richness at 82% (threshold 95%). Gaps: `cultural: 0/3`, `dialogues: 2/4`. Module has only 2 dialogues (Maxim story lines 252-309, gym dialogue lines 339-374) and only 1 `[!culture]` callout (line 418).
- **Fix Plan:**
  - Add 1 short dialogue in section «Розминка: Що таке зворотні дієслова?» (e.g., parent asking child to wash hands — contrasting transitive/reflexive in natural speech).
  - Add 1 short dialogue in section «Культура: Секрети вимови» (e.g., someone apologizing on the street, demonstrating `Вибачте!` in context).
  - Add 2 `[!culture]` callouts: one in section «Теорія: Відмінювання та групи» about Ukrainian morning routine culture (cold water washing tradition), one in section «Практика: Дія на себе чи на іншого?» about greeting culture (cheek kissing, handshake norms for `вітатися`/`цілуватися`).

### Issue 6: Missing `вмиватися` conjugation table per meta specification [MEDIUM — Plan Compliance]
- **Location:** Section «Теорія: Відмінювання та групи»
- **Evidence:** Meta point 2 specifies "Full present tense paradigm for 'дивитися' **and 'вмиватися'**." Content provides tables for `сміятися` (lines 134-141) and `дивитися` (lines 153-160) but NOT `вмиватися`.
- **Fix:** Add a conjugation table for `вмиватися` (first conjugation verb) in the theory section to show contrast with second conjugation `дивитися`. This also addresses the richness `tables` dimension.

---

## Factual Verification

### Grammar Rules
| Claim | Location | Verdict |
|-------|----------|---------|
| -ся after consonants, -сь after vowels | Lines 125-130 | **Correct** — with accurate caveat that -ся is also allowed after vowels |
| -ся from Old Slavic `себе` | Lines 83-89 | **Correct** — well-established etymology |
| -ться pronounced as | Lines 393-398 | **Correct** — standard Ukrainian phonetics |
| `дивитися` is second conjugation | Line 149 | **Correct** |
| `сміятися з` is standard (not `над`) | Lines 212-216 | **Correct** — `з` is standard Ukrainian; `над` is a Russianism calque |
| `Вибачте` preferred over `Вибачаюсь` | Lines 407-416 | **Correct** — widely accepted prescriptive norm |
| `Я мию себе` sounds clinical/unusual | Line 98 | **Correct** — this form implies treating the body as an external object |

### Callout Box Verification
| Callout | Location | Verdict |
|---------|----------|---------|
| `[!warning]` "Don't Double Up!" | Line 101 | **Correct** — redundancy with `-ся` + `себе` is indeed an error |
| `[!tip]` Word Order Alert — "Я ся мию" as 300-year-old dialect | Line 162-166 | **Plausible** — reflexive particle placement was indeed different in older Ukrainian, though "300 years ago" is an approximation. Not strictly wrong but imprecise |
| `[!myth-buster]` Using both transitive and reflexive in one sentence | Line 246-250 | **Correct** — perfectly natural construction |
| `[!tip]` `Я займаюся українською мовою` as Russian influence | Lines 336-337 | **Correct** — `займатися` + instrumental for language study is indeed a Russianism; `вивчати` is standard |
| `[!culture]` "The Polite Choice" — `Вибачте` / `Пробачте` | Line 418-420 | **Correct** — accurate etiquette guidance |

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| **Russianisms** | 2 FOUND | `надіятися` (line 208, activities, vocab) and `піднімається` (line 258, vocab line 305). D.0 confirmed `надіятися`. |
| **Colonial framing** | 1 FOUND | Line 401: Ukrainian -ться pronunciation defined by Russian contrast. Not in a decolonization/myth-buster block. |
| **Grammar scope** | PASS | Content stays within present tense as scoped. Past/future tense correctly deferred to module a1-25. |
| **LLM filler** | PASS | No `це не просто` / `це не лише` patterns. No stacked abstract nouns. Minor generic phrasing (2 instances) but below threshold. |
| **Structural monotony** | PASS | Section openings are varied. Example formatting varies (tables, stories, dialogues, bullet lists). |
| **IPA accuracy** | 2 ERRORS | Missing stress in `прокидатися`, wrong stress in `втомлюватися`. |
| **Callout plausibility** | PASS | All callout claims verified as accurate or defensible. |
| **Word salad** | PASS | All paragraphs have clear logical threads. No random language alternation. |
| **Plan compliance** | 1 GAP | Missing `вмиватися` conjugation table specified in meta. |
| **Richness** | BELOW THRESHOLD | 82% vs 95%. Gaps: cultural (0/3), dialogues (2/4). |

---

## Verdict

**NEEDS REPAIR** — 3 critical/high issues require targeted fixes before pass:

1. **Replace `надіятися` → `сподіватися`** throughout content (line 208-209), activities (lines 38, 318-325, 480), and vocabulary (line 62). Remove duplicate vocab entry.
2. **Replace `піднімається` → `встає`** (line 258) and `підніматися` → `вставати` (line 305) in the morning routine context.
3. **Remove colonial framing** at line 401 — present Ukrainian -ться pronunciation without Russian baseline.
4. **Fix IPA stress** for `прокидатися` (vocab line 65) and `втомлюватися` (vocab line 77).
5. **Close richness gaps**: add 2 dialogues and 3 cultural callouts to bring richness above 95%.

The module's core pedagogy is strong — the mirror analogy, the Maxim story, the gym dialogue, and the transitive/reflexive contrast tables are all excellent A1 teaching. The issues are localized and repairable without structural changes. After the 5 fixes above, this module should pass all gates.