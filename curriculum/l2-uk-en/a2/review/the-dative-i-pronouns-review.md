<!-- content-hash: 43b39dfd27d0 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | Language Quality | 8/10 | Mostly solid Ukrainian; two grammatical inconsistencies (case after "треба" at L324 vs L224; Cyrillic inside IPA at L112); "Чому?" ambiguity unaddressed at L22 |
| 2 | Lesson Quality | 8/10 | 4/5 on "Would I Continue?" — good pacing and encouragement at end, but cold opening (no warm greeting); excellent cultural hooks; clear progression WELCOME→PRESENT→PRACTICE→CELEBRATE |
| 3 | Activity Quality | 9/10 | 12 activities, 7 distinct types, strong distractor design; good recognition→production progression; unjumble items (activity 4) have 7-8 word chains which may overwhelm A2 |
| 4 | Richness | 8/10 | 8 engagement boxes across 5 callout types; strong cultural content (threshold taboo, flower norms, bread and salt); missing explicit teaching of дякувати despite plan requirement |
| 5 | LLM Fingerprint | 7/10 | "ключ до" metaphor repeated 3× (L14, L18, L89); "це не просто" rhetoric used 2× (L59, L87); 3/5 H2 sections open with English-first pattern |
| 6 | Immersion Balance | 9/10 | 51.2% — right in target range (50-60%); English explanations for grammar, Ukrainian for examples and dialogues; well-scaffolded |
| 7 | Factual Accuracy | 8/10 | Grammar rules are accurate; cultural claims verifiable; case governance after "треба" inconsistently presented; "Чому?" dative question pedagogically misleading without disambiguation |

**Overall: 57/70**

---

## Critical Issues Found

### Issue 1 (Grammar — CRITICAL): Contradictory case after "треба"

**Location**: Section «Практика» L324 vs Section «Презентація» L224

The module teaches two contradictory constructions for "I need coffee":

- L224 (in `[!context]` box): «Мені треба каву» — explicitly labeled "Using Accusative case, common in speech"
- L324 (in practice drill): «Мені треба кава» — uses Nominative without explanation

A2 learners seeing both forms in the same module will be confused. The module must pick one approach and be consistent. Standard grammar would favor either «Мені потрібна кава» (Nominative with agreeing потрібна) or «Мені треба кави» (Genitive). The Accusative form «Мені треба каву» is colloquial. Using bare Nominative «Мені треба кава» after invariable "треба" is non-standard.

**Fix**: Align L324 to match L224, or better yet, use the standard construction «Мені потрібна кава» in the practice drill (which is already taught at L218-220) and reserve the «треба» + noun discussion for the [!context] callout.

### Issue 2 (Plan Compliance — MODERATE): дякувати not explicitly taught

**Location**: Missing from sections «Презентація» and «Стани і дієслова»

The plan (meta content_outline, section 3, point 4) specifically requires: *"explaining why «допомагати» (to help) and «дякувати» (to thank) require Dative (кому?)"*. The content covers допомагати in a dedicated subsection (L272-279) but never explicitly teaches дякувати as a dative-governing verb. It appears only as "Дякую" in dialogues (L78, L382, L385, L390, L403, L427) without explicit grammar instruction. Vocabulary YAML includes it (L156-159: `governs Dative case (дякую тобі)`), but the lesson prose never makes this explicit.

**Fix**: Add a brief subsection under «Дієслова з Давальним відмінком» (after L292) teaching дякувати with examples: «Дякую **тобі** за подарунок», «Дякую **вам** за допомогу». Show that it takes Dative, not Accusative.

### Issue 3 (LLM Fingerprint — MODERATE): "ключ до" metaphor repetition

**Locations**: L14, L18, L89

The "key to" metaphor is used three times in close proximity:

- L14: «це ключ до вираження ваших почуттів, потреб та бажань»
- L18: «Це ключ до вираження ваших почуттів та потреб»
- L89: «Це ключ до справжнього розуміння українського менталітету»

Lines 14 and 18 are nearly identical (same sentence structure within 4 lines). This is a clear LLM generation artifact — the model repeated its own framing across the epigraph and the section opening.

**Fix**: Keep "ключ до" in one location only (suggest L14 in the epigraph). Replace L18 with a different framing (e.g., «Він відкриває двері до вашого внутрішнього світу»). Replace L89 with a direct statement (e.g., «Ви почнете думати українською, а не перекладати з англійської»).

### Issue 4 (Notation — MINOR): Cyrillic in IPA context

**Location**: Section «Презентація» L112

The text reads: «Зверніть увагу на м'якість у вимові — [нʲ]». The symbol inside brackets is Cyrillic "н" rather than Latin IPA "n". Correct IPA should be [nʲ]. Additionally, the comparison to English "nice" is misleading — English /n/ before /aɪ/ is not palatalized the way Ukrainian /nʲ/ is.

**Fix**: Change `[нʲ]` to `[nʲ]`. Replace the "nice" comparison with a more accurate description (e.g., "The tip of your tongue touches your palate softly, producing a [nʲ] sound — softer than English 'n'").

### Issue 5 (Pedagogy — MODERATE): "Чому?" ambiguity

**Location**: Section «Вступ» L22

The lesson states the Dative answers «Кому?» — To whom? and «Чому?» — To what? without noting that «Чому?» overwhelmingly means "Why?" in everyday Ukrainian. For an A2 learner who has already encountered «Чому?» = "Why?" in A1, this creates real confusion. The dual meaning needs acknowledgment.

**Fix**: Add a brief note at L22: "Be careful: «Чому?» in everyday speech most often means 'Why?'. As a Dative question ('To what?'), it is used primarily in grammar contexts and formal Ukrainian. In daily conversation, you will mostly use «Кому?» (To whom?)."

### Issue 6 (Structure — MINOR): H1 `# Підсумок` should be H2

**Location**: L447

All content sections use `##` (H2) for major divisions, but the summary uses `#` (H1). This breaks the heading hierarchy.

**Fix**: Change `# Підсумок` to `## Підсумок`.

---

## Factual Verification

### Callout Box Audit

| Callout | Location | Type | Claim | Verdict |
|---------|----------|------|-------|---------|
| Українська гостинність | L42-44 | [!culture] | Hosts ask «Вам зручно?» / «Що вам дати?» | **PASS** — Standard Ukrainian hospitality behavior |
| Ритм мови | L125-127 | [!tip] | Мені/Тобі rhyme | **PASS** — Both end in -і with penultimate stress |
| Типова помилка | L171-173 | [!warning] | «Я подобаю музику» is incorrect | **PASS** — Correct; подобатися requires dative subject |
| Як сказати "I need a coffee" | L222-224 | [!context] | «Мені треба каву» uses Accusative, common in speech | **PASS** — Colloquial Accusative after "треба" is attested |
| "Мені приємно" | L264-266 | [!culture] | Standard polite response when meeting someone | **PASS** — Standard Ukrainian etiquette |
| Подарунки через поріг | L300-302 | [!myth-buster] | Never pass items across the threshold | **PASS** — Well-documented Ukrainian superstition |
| Квіти для живих | L352-354 | [!culture] | Odd number of flowers for living, even for funerals | **PASS** — Well-known cultural rule across Eastern Europe |
| Хліб і сіль | L412-414 | [!history-bite] | Bread and salt as ancient hospitality symbol | **PASS** — Documented Slavic tradition; claims are reasonable |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Dative pronoun paradigm (мені, тобі, йому, їй, нам, вам, їм) | L99-108 | **PASS** — All forms correct |
| подобатися governs Dative + Nominative subject | L147-189 | **PASS** — Correctly explained with singular/plural agreement |
| Verb agreement with подобається/подобаються | L177-184 | **PASS** — Singular/plural distinction correct |
| потрібен/потрібна/потрібне gender agreement | L216-220 | **PASS** — Masculine/feminine/neuter correctly demonstrated |
| Impersonal state constructions (Dative + adverb) | L234-257 | **PASS** — Standard Ukrainian impersonal pattern |
| допомагати governs Dative | L272-279 | **PASS** — Correct; standard dative verb |
| дзвонити governs Dative | L282-285 | **PASS** — Correct |
| "Мені треба кава" (Nominative after треба) | L324 | **FLAG** — Non-standard; contradicts L224 |

---

## Verification Summary

| Check | Result | Notes |
|-------|--------|-------|
| Colonial framing | **CLEAR** | No Russian comparisons found |
| Russianisms | **CLEAR** | No кушать, приймати участь, etc. |
| LLM fingerprint patterns | **FLAGGED** | "ключ до" 3×; "це не просто" 2×; English-first section openings 3/5 |
| Factual accuracy (callouts) | **CLEAR** | All 8 callout boxes verified |
| Grammar accuracy | **FLAGGED** | Case inconsistency after "треба" (L224 vs L324) |
| Plan compliance | **FLAGGED** | дякувати not explicitly taught; "Культурний код та етикет" section from meta not standalone H2 (content distributed via callouts) |
| Activity errors | **CLEAR** | All 12 activities verified, items are correct |
| Beginner safety | **PASS** | 4/5 on "Would I Continue?" test — warm closing, cold opening |
| Section coverage | All 5 H2 sections referenced: «Вступ», «Презентація», «Стани і дієслова», «Практика», «Діалоги» |

### Sections Referenced

- Section «Introduction / Вступ»: "ключ до" repetition (L14, L18), Чому? ambiguity (L22)
- Section «Presentation / Презентація»: Cyrillic IPA (L112), "ключ до" (L89), подобатися/потрібно coverage strong
- Section «States and Verbs / Стани і дієслова»: Well-structured physical→emotional states, missing дякувати
- Section «Practice / Практика»: Case inconsistency (L324), good error correction drill (L356-371)
- Section «Dialogues / Діалоги»: Strong real-world scenarios, implicit дякувати usage

---

## Verdict

**PASS WITH FIXES**

The module is a solid A2 grammar lesson with strong pedagogy — the подобатися inversion explanation is particularly well-executed, the dialogues are natural and culturally rich, and the 12 activities provide excellent variety. The 51.2% immersion ratio is right on target.

However, three issues require repair before the module is fully sound:

1. **The "треба" + noun case inconsistency** (L224 vs L324) is the most urgent — an A2 learner will be confused seeing both "каву" and "кава" in the same module without explanation.
2. **дякувати needs explicit teaching** per the plan's own requirements — a 3-sentence subsection would suffice.
3. **The "ключ до" triple repetition** is a visible LLM artifact that should be deduplicated.

The remaining issues (Cyrillic IPA, "Чому?" ambiguity, H1 heading, missing warm greeting) are minor polish items that don't block content quality but should be addressed.