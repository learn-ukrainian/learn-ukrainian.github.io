<!-- content-hash: 9932f8d3846c -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | Plan Compliance | 7/10 | Adjective locative scope creep (4+ instances in lines 262, 340, 347, 357); missing required collocations «Де туалет?», «Де ви?», «Де це?»; missing Locative vs. Accusative discrimination exercise from plan |
| 2 | Lesson Quality | 9/10 | Excellent pacing, warm scenario-based opening, quick wins via basic locatives, progress celebration at end; no explicit "Today you'll learn..." objectives |
| 3 | Language Quality | 7/10 | Scope creep with adjective locative forms (a1-14 grammar); implausible examples «Музика у вусі» and «Кіт сидить на черепасі»; misleading "поверх = Floor" translation |
| 4 | Activity Quality | 8/10 | 10 activities with 6 types; solid grammar; good progression; missing Locative vs. Accusative discrimination; preposition fill-in only 8 items vs 20 in plan hints |
| 5 | Richness | 9/10 | Strong cultural hooks (shoes-off, housing types, post-horse etymology); 4 dialogues; named locations (Odesa, Deribasivska, Prague); 7 callout boxes; body-parts mnemonic |
| 6 | Humanity & Warmth | 9/10 | "Don't worry" ×2, "Good news" ×1, "Congratulations!" ×1, "your best friend" ×1; practice sections could use more in-line encouragement |
| 7 | LLM Fingerprint | 8/10 | No structural monotony; no AI clichés; no colonial framing; 2 implausible examples drag score |
| 8 | Factual Accuracy | 8/10 | Grammar rules correct; post-office etymology accurate; internal inconsistency: line 164 claims mutations "usually" happen in feminines, but practice drill at line 235 applies Х→С to masculine «поверх» |
| 9 | Immersion | 8/10 | 25.4% against 25-40% target — at bottom edge; grammar-heavy content justifies English but could include more Ukrainian phrases in practice sections |

---

## Critical Issues Found

### CRITICAL 1: Scope Creep — Adjective Locative Forms (Auto-Fail Category: Grammar Scope Violation)

The SCOPE comment (lines 1-7) explicitly states: "Adjective endings in Locative → a1-14". Yet the content introduces adjective/pronoun locative forms the learner cannot parse:

- **Line 262**: «Аптека **на цій вулиці**. Вона там, **у великому будинку**.» — demonstrative "цій" (loc. of "ця") and adjective "великому" (loc. of "великий")
- **Line 340**: «Я **у своїй кімнаті**.» — possessive pronoun "своїй" (loc. of "свій")
- **Line 347**: «Я живу **у спальному районі**» — adjective "спальному" (loc. of "спальний")
- **Line 357**: «Я живу **на Дерибасівській**» — substantivized adjective requiring locative agreement knowledge

**Fix**: Replace all adjective-locative forms with bare noun-only structures. For line 262: «Аптека на вулиці. Вона там, у будинку.» For line 340: «Де я? Я вдома. Я у кімнаті.» For line 347: rephrase without adjective or explicitly note it's aspirational. For line 357: «Я живу на вулиці Дерибасівська» or simply «Мій офіс у центрі.»

### CRITICAL 2: Implausible Ukrainian Examples

Two examples in section «Граматика: Місцевий відмінок» (subsection "Mutation Х → С") fail the plausibility test:

- **Line 195**: «Музика у **вусі**» — A native speaker would never say this. Music is heard in both ears, and "вусі" can be confused with "вуса" (mustache). Natural: «Навушник у вусі» or simply save the ear example for the mnemonic only.
- **Lines 196-197**: «Кіт сидить на **черепасі**» — Bizarre scenario. An A1 learner needs relatable, high-frequency examples, not cats sitting on turtles.

**Fix**: Replace line 195 with a plausible example, e.g., «Навушник у вусі» (earphone in the ear). Replace lines 196-197 with a simpler Х→С example or acknowledge this mutation is rare and skip the turtle example entirely.

### CRITICAL 3: Internal Grammar Inconsistency — Mutation Scope Claim vs. Practice

- **Line 164**: «This usually happens in **Feminine** nouns ending in **-ка**, **-га**, **-ха**.»
- **Line 235**: «**Пове́рх** (Floor) → Ends in -х. Change Х to С. Add -і. Результат: **На поверсі**» — "Поверх" is masculine, directly contradicting the "usually Feminine" claim.

Additionally, **"Floor" is a misleading translation** of "поверх". This word means "storey/level of a building" (e.g., "на третьому поверсі" = on the third floor), NOT the floor surface you walk on (which is "підлога", already taught earlier in the module at line 187).

**Fix**: Either (a) remove the поверх drill from section «Практика: Де це знаходиться?» since it contradicts the stated rule, or (b) amend line 164 to acknowledge that velar mutations also apply to some masculine nouns. Fix translation to "storey" or "building level."

---

### MAJOR 1: Missing Required Plan Collocations

The plan's `vocabulary_hints.required` lists these as essential:
- «Де ти?» — present (line 249, 296) ✓
- «Де ви?» — absent ✗
- «Де це?» — absent ✗ (only used as section title «Де це знаходиться?», not as a taught collocation)
- «Де туалет?» — absent ✗ (this is arguably the #1 survival phrase for a beginner)

**Fix**: Add these three collocations to section «Вступ: Питання «Де?»», ideally near lines 37-49 where other "learn as vocabulary items" phrases are presented. «Де туалет?» especially should be presented as a survival phrase.

### MAJOR 2: Missing Locative vs. Accusative Discrimination Exercise

The plan calls for: "Discrimination exercise: Static Location (Locative) vs. Directional Motion (Accusative). Contrast «Я у парку» with the common error «*Я в парк»." Line 25 of the content mentions the Де/Куди distinction briefly, but no activity tests this. The research notes (line 25) also flag this as a common learner error.

**Fix**: Add a true-false or multiple-choice activity contrasting static locative with directional accusative: «Я у парку» (correct for "I am in the park") vs. «*Я в парк» (incorrect).

---

### MINOR 1: Missing Euphony Example «У Львові»

The plan specifically calls for «У Львові (avoid clusters)» as a euphony teaching example. The content uses other cities (Odesa, London) but omits this canonical example of consonant cluster avoidance.

**Fix**: Add «У Львові» to the euphony section (near lines 117-119) as it's the textbook example of why «*В Львові» violates euphony.

### MINOR 2: Fleeting Vowel Tangent

Lines 285-290 introduce "fleeting vowels" (стілець → стільці) which is not in the plan or meta outline. While the tone is casual ("Don't stress about it yet"), it adds cognitive load at a point where learners are already processing consonant mutations.

**Fix**: Either remove the tangent or reduce it to a single line noting "some words change slightly" without naming the pattern.

---

## Factual Verification

| Claim | Source Line | Verdict |
|-------|------------|---------|
| Locative ending is -і for most nouns | 132 | **Correct** — per State Standard §4.2.3.3 |
| К→Ц, Г→З, Х→С mutations | 167-169 | **Correct** — standard velar mutation rule |
| Post office etymology (post-horse stations) | 105 | **Correct** — "пошта" derives from postal relay system |
| Events take "на" (на концерті, на роботі) | 98-100 | **Correct** |
| Cities and countries use "в/у" | 80-83 | **Correct** |
| Euphony: avoid consonant clusters with у/в | 111-128 | **Correct** (simplified but appropriate for A1) |
| "Поверх" = "Floor" | 235 | **Misleading** — means "storey/building level", not floor surface (підлога) |
| Mutations "usually" happen in feminine nouns | 164 | **Overgeneralized** — also applies to some masculine and neuter nouns, contradicted by own practice drill |

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from meta present | ✅ All 4: «Вступ: Питання «Де?»», «Граматика: Місцевий відмінок», «Практика: Де це знаходиться?», «Застосування: Моя кімната і місто» |
| Learning objectives covered | ✅ All 4 objectives addressed |
| Russianisms | ✅ None found |
| Colonial framing | ✅ None found |
| LLM clichés | ✅ None found |
| Scope violations | ❌ Adjective locative forms (4 instances) — a1-14 grammar used |
| Implausible examples | ❌ 2 found (lines 195, 196-197) |
| Factual errors | ⚠️ 1 misleading translation, 1 internal inconsistency |
| Required collocations present | ❌ Missing «Де туалет?», «Де ви?», «Де це?» |
| Activity coverage | ⚠️ Missing Locative vs Accusative discrimination exercise |
| Word count | ✅ 2752/2000 (137.6%) — above target |
| Immersion | ✅ 25.4% (within 25-40% target, but at bottom edge) |
| Engagement boxes | ✅ 7 callout boxes (observe, tip×3, myth-buster, context, model-answer) |

---

## Verdict

**CONDITIONAL PASS** — The module is fundamentally well-constructed with strong pacing, warm tone, good cultural hooks, and accurate grammar teaching. The PPP arc works well for A1 learners. However, three categories of issues require targeted fixes before approval:

1. **Scope creep** (Critical): Remove or replace all adjective/pronoun locative forms (4 instances) that belong to a1-14
2. **Implausible examples** (Critical): Replace «Музика у вусі» and «Кіт сидить на черепасі» with natural sentences
3. **Internal inconsistency** (Critical): Fix the feminine-only mutation claim vs. masculine "поверх" contradiction, and correct the misleading translation
4. **Missing collocations** (Major): Add «Де туалет?», «Де ви?», «Де це?» to the intro

Estimated repair: targeted fixes in ~8 specific locations. No section rewrites needed. The module's core structure, dialogues, and activity set are strong.