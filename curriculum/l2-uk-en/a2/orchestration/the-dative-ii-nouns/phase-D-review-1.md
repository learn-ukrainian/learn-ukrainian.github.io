**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Plan Compliance | 6/10 | 5 of 13 required vocabulary items (личити, заважати, вистачати, бракувати, підходити) are completely absent from the content. Quiz activity has 8 items, below plan's 12+ threshold. Plan-specific example «Дідусеві вісімдесят років» missing from age expressions. Collocation «давати відповідь» not practiced. |
| 2 | Lesson Quality | 8/10 | Warm, well-structured tutorial. "Would I Continue?" test: 4/5 pass (not overwhelmed ✅, instructions clear ✅, quick wins ✅, Ukrainian introduced gently ✅, would come back ✅ — but section «Вступ: Концепція адресата» uses «бенефіціаром» and section «Жіночий рід та чергування приголосних» uses «Палаталізацію задньоязикових», both intimidating for A2). Good closing with progress celebration at line 429. |
| 3 | Language Quality | 8/10 | Ukrainian grammar is consistently correct. No Russianisms detected. No colonial framing against Russian. Two terms too academic for A2: «бенефіціаром» (line 20) and «Палаталізацію задньоязикових» (line 206). Line 343 «Подарувати дві квіти живій людині» — «дві квітки» would be more standard with the numeral. |
| 4 | Immersion Balance | 9/10 | 56.9% Ukrainian hits the A2 Band 1 target (50-60%). English used for grammar explanations, Ukrainian for examples and dialogues. Scaffolding is well-graduated. The final sections (dialogues) are almost fully Ukrainian, appropriate for the end of the module. |
| 5 | Activity Quality | 7/10 | 12 activities with good variety (8 types). However: cloze blank 7 answer «людям» is contextually implausible at a family birthday party (should be «гостям»); cloze blank 10 answer «колегам» breaks narrative flow (showing birthday gifts to colleagues at a family event); fill-in sentence «Ми йдемо назустріч (муха)» (line 191) is absurd — no one walks towards a fly. Unjumble items require dative adjective forms (моїм, найкращим, шкільним) not taught in this noun-focused module. |
| 6 | Richness | 8/10 | Strong cultural hooks: flower etiquette (odd numbers), taboo gifts (knife/coin tradition), День Ангела. 8 callout boxes. 4 dialogue scenes. Clear grammar tables. Missing: «личити» clothing/style examples that plan required would add variety. |
| 7 | LLM Fingerprint | 8/10 | «не просто X, а Y» pattern appears twice (lines 336, 429). «luxurious choice of endings» (line 65) is purple prose for a textbook. Section openings are varied (no structural monotony). Metaphors: «поштова адреса» (line 33), «магніт» (line 267), «острів» (line 217), «стрілка» implied (line 35) — at 4, borderline. No cliched metaphors (діамант, двигун, etc.). |
| 8 | Factual Accuracy | 8/10 | Line 65: «This flexibility is a unique feature of Ukrainian, distinguishing it from neighboring Slavic languages» — this is factually incorrect. Polish uses -owi as a standard masculine dative ending with the same alternation system. Line 212 summary uses «Дочка → Дочці» when the lesson body teaches «Донька → Доньці» (line 179), creating learner confusion between two different words for "daughter". |

---

## Critical Issues Found

### Issue 1: PLAN_SCOPE_GAP — 5 Required Vocabulary Items Missing from Content

**Severity:** Critical
**Location:** Entire content; missing from sections «Ключові дієслова та керування» and «Практика: Етикет подарунків»

The plan's `vocabulary_hints.required` list includes 13 items. The following 5 are completely absent from the lesson prose:

1. **личити** (to suit) — Plan explicitly requires: "Practice the verb «личити» (Medium frequency) in descriptive contexts — use clothing and style examples: «ця сукня тобі личить»." The word appears in the vocabulary YAML but is never introduced or practiced in the content.
2. **заважати** (to bother) — In vocabulary YAML, absent from content.
3. **вистачати** (to be enough) — In vocabulary YAML, absent from content.
4. **бракувати** (to lack) — In vocabulary YAML, absent from content.
5. **підходити** (to suit) — Appears once in passing on line 398 «Книга завжди підходить **розумній людині**» inside a dialogue but is never explicitly taught.

Additionally, the plan-required collocation «давати відповідь» is absent.

**Fix:** Add a subsection to «Ключові дієслова та керування» covering these 5 verbs with examples. The «личити» verb specifically needs a clothing/style context per the plan. The impersonal verbs (вистачати, бракувати) form a natural group with Dative + Genitive constructions.

### Issue 2: FACTUAL_ERROR — False Uniqueness Claim for -ові Ending

**Severity:** Significant
**Location:** Section «Чоловічий та середній рід: -ові/-у», line 65

The text states: «This flexibility is a unique feature of Ukrainian, distinguishing it from neighboring Slavic languages.»

This is factually incorrect. Polish has the masculine dative ending -owi (e.g., bratu → bratowi) with the same alternation pattern between short and long forms. The -ові/-owi ending is a shared feature across multiple Slavic languages, not unique to Ukrainian. Presenting false claims about Ukrainian linguistic uniqueness is pedagogically harmful — it undermines trust when learners discover the claim is wrong.

**Fix:** Replace with accurate framing: "The ending -ові is very characteristic of Ukrainian and gives your speech a natural, melodic quality." Remove the comparative claim entirely.

### Issue 3: ACTIVITY_PLAUSIBILITY — Cloze Narrative Breaks and Absurd Fill-In

**Severity:** Significant
**Location:** Activities file, cloze (lines 393-404), fill-in (line 191)

Three plausibility failures:

1. **Cloze blank 7** (line 393-395): In a family birthday narrative, «Ми пропонуємо {{7}} чай і торт» has answer «людям» (to people). At a birthday party, you offer tea to «гостям» (guests), not generically to «people». Blank 6 already uses «гостям», so this forces an unnatural synonym.

2. **Cloze blank 10** (line 402-404): «Брат показує свої подарунки {{10}}» has answer «колегам» (to colleagues). The entire narrative is a family birthday with guests and friends. Colleagues appearing to view birthday gifts breaks the scene logic.

3. **Fill-in** (line 191): «Ми йдемо назустріч (муха)» — "We go to meet a fly" is absurd. No natural speaker would produce this sentence. It exists solely to practice the х→с shift but sacrifices plausibility entirely.

**Fix:** Cloze blank 7 → change answer to «дітям» or «всім» with appropriate options. Cloze blank 10 → change to «друзям» or «гостям». Fill-in муха → replace with a natural dative context like «Я дав їжу (муха)» or «Не заважай (муха)» — though even these are marginal; consider replacing with a more common х-stem word or removing.

### Issue 4: TERMINOLOGY_MISMATCH — Summary Uses Different Word Than Body

**Severity:** Moderate
**Location:** Section «Жіночий рід та чергування приголосних», line 212 (summary box)

The lesson body on line 179 teaches: «Донь**к**а — Донь**ц**і»

But the summary box on line 212 presents: «Дочка → Дочці»

While both «донька» and «дочка» are valid Ukrainian words for "daughter" (and both undergo к→ц), switching terminology between the body and the summary creates confusion for an A2 learner who just spent the lesson learning «донька». The summary should reinforce what was taught, not introduce a synonym.

**Fix:** Change line 212 from «Дочка → Дочці» to «Донька → Доньці» to match the body.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| -ові ending is "unique" to Ukrainian vs. neighboring Slavic languages | Line 65, Section «Чоловічий та середній рід: -ові/-у» | **FALSE** — Polish has -owi as standard |
| Age expressed with Dative subject + years | Lines 48-60, Section «Вступ: Концепція адресата» | **CORRECT** — Standard §4.2.2.3 confirms |
| Consonant shifts Г→З, К→Ц, Х→С before -і | Lines 155-206, Section «Жіночий рід та чергування приголосних» | **CORRECT** — standard palatalization |
| Odd flowers for living, even for funerals | Lines 336-343, Section «Практика: Етикет подарунків» | **CORRECT** — well-documented cultural practice |
| Knife/watch taboo with coin buyback | Lines 354-360, Section «Практика: Етикет подарунків» | **CORRECT** — established superstition |
| Yellow flowers symbolize separation in romantic context | Lines 346-352, Section «Практика: Етикет подарунків» | **CORRECT** — common cultural belief |
| День Ангела (Name Day) is a major celebration | Lines 372-376, Section «Діалоги: День Ангела» | **CORRECT** |
| «Допомагати» requires Dative, not Accusative | Lines 279-287, Section «Ключові дієслова та керування» | **CORRECT** |
| Dative plural always -ам/-ям | Lines 216-263, Section «Plural: Даруємо всім!» | **CORRECT** |

---

## Section-by-Section Analysis

### Section «Вступ: Концепція адресата» (lines 15-61)
Good conceptual introduction with the "postal address" metaphor. The English-to-Ukrainian mapping (adding "to"/"for") is pedagogically sound. Age expressions are covered. However, «бенефіціаром» on line 20 is an overly academic term for A2 — a learner at this level would struggle with this word even in their L1. Replace with «отримувач» which is already used elsewhere in the section. The plan-specific example «Дідусеві вісімдесят років» is absent — replaced with «Студентові двадцять років» and «Батькові п'ятдесят років», which serve the same function but don't match the plan.

### Section «Чоловічий та середній рід: -ові/-у» (lines 62-136)
Well-organized with clear paradigm tables. The euphony (милозвучність) subsection on line 104 is excellent — the alternation rule «панові директору» vs. «пану директору» is clearly demonstrated. However, the false uniqueness claim on line 65 must be corrected. The warning box on line 97-102 correctly contrasts Dative and Accusative, though the parenthetical "(Accusative/Genitive)" on line 100 is confusing — «бачу брата» is Accusative (animate masculine), not Genitive. This needs clarification.

### Section «Жіночий рід та чергування приголосних» (lines 137-213)
The consonant shift presentation (Г→З, К→Ц, Х→С) is the strongest section in the module. The observe box on line 169-171 encouraging oral practice is excellent pedagogy. The summary table on lines 200-204 is clean. However, line 206 uses «Палаталізацію задньоязикових» — this is B2-level linguistic terminology that will intimidate an A2 learner. The explanation that follows is actually quite clear in plain language; the technical label is unnecessary.

### Section «Plural: Даруємо всім!» (lines 214-263)
Clear and well-scaffolded. The "safe island" framing on line 217 is encouraging. The fact box on lines 257-262 connecting Dative -ам with Instrumental -ами is a genuinely useful memory aid. However, line 234 «Хлопці — **Хлопцям** (Wait, this is soft! See below.)» — the parenthetical English interjection breaks the flow of a Ukrainian example list. It should be moved to a separate note.

### Section «Ключові дієслова та керування» (lines 264-332)
Covers давати, дарувати, допомагати, телефонувати, пояснювати, розповідати, надсилати, відповідати, писати — 9 verbs. The decolonization box on lines 281-287 appropriately addresses the «допомагати» + Dative rule without colonial framing. The verb table on lines 326-331 is a useful reference. **Major gap**: личити, заважати, вистачати, бракувати, підходити are all absent despite being plan-required.

### Section «Практика: Етикет подарунків» (lines 333-368)
Culturally rich and engaging. The flower etiquette, color symbolism, and taboo gifts with the coin workaround are well-presented and memorable. The hospitality subsection (lines 362-368) naturally demonstrates multiple dative uses. Line 343: «Подарувати дві квіти живій людині» — standard form would be «дві квітки» (numeral + nominative plural of «квітка»). «Квіти» is the general-use plural, not the numeral-accompanied form.

### Section «Діалоги: День Ангела» (lines 370-417)
Four scenes covering greeting, gift selection, gift-giving, and hospitality. Dialogues are natural and culturally authentic. The culture box on lines 385-389 nicely cross-references Genitive case (for wished things) with Dative (for the recipient). However, the dialogues never use «личити» in the gift-selection scene (Scene 2, line 392), where the plan specifically called for discussing what "suits" the recipient.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing (Ukrainian defined via Russian) | **PASS** — no Russian comparisons found |
| Russianisms | **PASS** — no Russianisms detected |
| Structural monotony (3+ sections start same way) | **PASS** — all section openings are varied |
| "не просто X, а Y" rhetoric (threshold: 2+) | **FLAG** — found 2 instances (lines 336, 429), exactly at threshold |
| Purple prose | **MINOR** — «luxurious choice» (line 65), borderline |
| Metaphor density (threshold: >4) | **PASS** — 4 metaphors, at limit |
| Callout monotony | **PASS** — 8 callouts with 7 different types |
| Example plausibility | **FAIL** — «Ми йдемо назустріч (муха)» in activities |
| Plan vocabulary coverage | **FAIL** — 5/13 required items absent |
| Activity item counts vs plan | **PARTIAL** — quiz 8/12+, fill-in 24/15+, match-up 10/10+ |
| "Would I Continue?" test | **4/5 PASS** — comfortable pacing, clear instructions, quick wins, gentle introduction; minor overwhelm risk from academic terminology |
| Humanity markers (direct address ≥15) | **PASS** — abundant "ви" throughout |
| Encouragement phrases (≥3) | **PASS** — line 429 celebration, multiple encouraging interjections |
| Progress celebration at end | **PASS** — line 429: «Тепер ви можете не просто говорити українською, а й робити приємне іншим людям» |

---

## Verdict

**NEEDS REPAIR**

The module's lesson prose is warm, well-structured, and culturally engaging — the consonant shift sections and gift etiquette content are especially strong. However, it has a critical plan compliance gap: 5 of 13 required vocabulary items are entirely absent from the content, including «личити» which had specific practice requirements in the plan. The factual error about the -ові ending being "unique to Ukrainian" must be corrected. Three activity items have plausibility failures that would confuse A2 learners (walking towards a fly, offering tea to "people" at a birthday party, showing birthday gifts to colleagues).

**Required repairs before pass:**
1. Add the 5 missing required verbs (личити, заважати, вистачати, бракувати, підходити) to the content with examples
2. Correct the false uniqueness claim on line 65
3. Fix the 3 implausible activity items (cloze blanks 7, 10; fill-in муха sentence)
4. Align summary terminology (line 212: Дочка → Донька)
5. Replace «бенефіціаром» (line 20) and optionally remove «Палаталізацію задньоязикових» (line 206)