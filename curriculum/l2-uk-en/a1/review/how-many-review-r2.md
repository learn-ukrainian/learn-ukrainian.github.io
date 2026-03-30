All verifications complete. The "Голуб, Grade 6" reference is **confirmed real** (p. 161 of `6-klas-ukrmova-golub-2023`). Now let me compile the full review.

---

## Linguistic Scan

**Russianisms:** None found. сім is correctly taught as Ukrainian (with explicit warning against "сем"). ✓

**Surzhyk:** None found. ✓

**Calques:** None found. "Скільки коштує?" is standard Ukrainian. ✓

**Paronyms:** гривня/гривна distinction is correctly explained. VESUM confirms both as separate lemmas. СУМ-11 confirms: гривна = "Металева прикраса у вигляді обруча, яку носили на шиї" (neck ornament); гривня = monetary unit. ✓

**Russian characters (ы, э, ё, ъ):** None found. ✓

**Gender/case accuracy:**
- "одне тістечко" — тістечко is neuter, одне is correct neuter form ✓
- "три булочки" — plural after 3, correct ✓
- "Привіт, Тарасе!" — correct vocative of Тарас ✓
- "дев'яносто дві копійки" — копійка is feminine, дві correct ✓
- "Мені двадцять п'ять" / "Мені тридцять два" — два agrees with рік (masculine), correct even for female speaker Оленка ✓

**Phonetic/orthographic claims verified:**
- "шістнадцять is written without a soft sign before н — not 'шістьнадцять'" — VESUM confirms шістнадцять exists; шістьнадцять is NOT IN VESUM ✓
- "stress ALWAYS falls on the -на- syllable within -надцять" — Confirmed by Захарійчук Grade 4 (p. 111): "У числівниках від одинадцяти до дев'ятнадцяти наголошується склад -на-"; Литвинова Grade 6 (p. 223): "одинáдцять, дванáдцять, тринáдцять, чотирнáдцять"; Красоткіна poem in Краввцова Grade 3: "скрізь наголос над складом на́!" ✓

**Textbook references verified via RAG:**
- "Леся Вознюк (in Kravcova, Grade 2, p. 92)" — Confirmed: `2-klas-ukrmova-kravcova-2019-1_s0091` contains this exact rhyme by Леся Вознюк on p. 92 ✓
- "(Vashulenko, Grade 3)" for -надцять pattern — Confirmed: `3-klas-ukrainska-mova-vashulenko-2020-1_s0138` (p. 140) ✓
- "(Голуб, Grade 6)" for сорок etymology — Confirmed: `6-klas-ukrmova-golub-2023_s0164` (p. 161) contains exactly this etymology ✓

**One factual inaccuracy found:**
The module says the counting rhyme "puts numbers 1–7 into context." The full rhyme by Леся Вознюк (confirmed via RAG, p. 92) runs from 1 to 10: один, два, три, чотири, п'ять, шість, сім, вісім, дев'ять, десять. The module quotes only up to 7 with "..." and mischaracterizes the rhyme's scope. It should say "1–10."

## Exercise Check

**Marker inventory (4 markers):**
1. `<!-- INJECT_ACTIVITY: quiz-age -->` — after Dialogue 2 (age exchange) ✓ Matches plan hint 3 (quiz: Скільки років?)
2. `<!-- INJECT_ACTIVITY: fill-in-numbers -->` — after Numbers 1–20 section ✓ Matches plan hint 1 (fill-in: Write number in words)
3. `<!-- INJECT_ACTIVITY: quiz-prices -->` — after Tens/Hundreds section ✓ Matches plan hint 2 (quiz: Скільки коштує?)
4. `<!-- INJECT_ACTIVITY: fill-in-phone -->` — after phone number paragraph ✓ Matches plan hint 4 (fill-in: phone dictation)

All 4 plan `activity_hints` have corresponding markers. Markers placed after relevant teaching content. Spread across 3 of 4 sections (Dialogues, Numbers, Tens+Hundreds). No issues.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections covered with correct pacing. All 4 objectives met: counting 1–100 (§2–§3), prices with гривня (§3 + Dialogue 1), age formula as chunk (Dialogue 2 + §4), phone numbers (§3 + §4). Plan references cited: ULP Ep9 mentioned ("ULP Ep9: Anna teaches numbers through real prices" per plan — module aligns). Авраменко Grade 6 classification referenced in plan, not explicitly cited in prose, but Голуб Grade 6, Вашуленко Grade 3, and Краввцова Grade 2 cited instead — all verified real. Dialogue 1 uses bakery setting from `dialogue_situations` rather than market stall from `content_outline` — plan self-contradicts; module chose the more detailed specification. Minor deduction for not citing ULP explicitly in prose. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian forms VESUM-verified (29/29 batch check). гривня/гривна distinction verified via СУМ-11 and VESUM lemma lookup. Stress claim on -надцять confirmed by three independent textbook sources (Захарійчук, Литвинова, Красоткіна). шістнадцять spelling correct (шістьнадцять NOT IN VESUM). Gender agreement correct throughout (одне тістечко, дві копійки, два роки). No Russianisms, no surzhyk, no calques. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: dialogues present numbers in context (bakery prices, age exchange) → explicit pattern teaching (chunks, not grammar analysis) → practice integration (self-check questions). Numbers taught through concrete objects: "один стіл, два стільці, три книги, чотири ручки, п'ять зошитів." Age formula taught as memorized chunk ("feel it through repetition, do not analyze it") — matches plan's "NO case grammar." Counting rhyme from textbook is excellent pedagogy. Irregulars (сорок, дев'яносто) highlighted with real etymology from Голуб Grade 6. One missed opportunity: the rhyme is truncated at 7 when the full 1–10 version would reinforce more numbers. |
| 4. Vocabulary coverage | 10/10 | All required vocab used naturally in prose: один–десять (§2), двадцять/тридцять/сорок (§3), сто/тисяча (§3), скільки (Dialogues + §4), коштує (Dialogue 1 + §4), гривня/гривні/гривень (§3 + §4), рік/роки/років (Dialogue 2 + §4). All recommended vocab present: п'ятдесят–дев'яносто (§3), двісті/триста/п'ятсот (§3), копійка (§3: "дев'яносто дві копійки"), номер (§3 + §4), нуль (§3 phone section). No vocabulary introduced as bare lists — all in context. |
| 5. Exercise quality | 9/10 | 4 markers matching 4 plan hints exactly. Each placed after its teaching section. Types match plan: 2× fill-in (numbers, phone) + 2× quiz (ages, prices). Markers cannot be evaluated for answer logic (generated by separate tool), but placement and type alignment are correct. |
| 6. Engagement & tone | 9/10 | No motivational openers, no "Let us explore...", no "You have unlocked..." Zero LLM filler detected. Tone is direct and instructional: "Three of these need extra attention when you say them aloud" (concrete), "Try counting objects from earlier modules" (actionable). Cultural details: Ukrainian phone format 0XX-XXX-XX-XX, real operator codes (097, 050, 073), гривня currency, bakery setting with real Ukrainian foods (торт, булочка, тістечко, хліб). Counting rhyme adds authentic literary flavor. Self-check in §4 is engaging ("Продиктуйте свій номер телефону по-українськи"). One borderline sentence: "Reading this aloud is excellent pronunciation practice" — slightly tells rather than shows, but provides a concrete action. |
| 7. Structural integrity | 10/10 | All 4 H2 sections from plan present and correctly ordered: Діалоги → Числа 1-20 → Десятки і сотні → Підсумок. No duplicate summaries, no meta-commentary sections, no stray tags. Clean markdown. Word count 1,379 vs 1,200 target — 15% above minimum ✓. |
| 8. Cultural accuracy | 10/10 | Decolonized: Ukrainian presented entirely on its own terms. сорок etymology grounded in Ukrainian/East Slavic trade history, not compared to Russian. сім explicitly distinguished from Russian "сем." гривня as Ukrainian currency vs гривна as historical ornament — correct and culture-affirming. Phone format is authentically Ukrainian. No "like Russian but..." framing anywhere. |
| 9. Dialogue quality | 9/10 | Named speakers throughout: Покупець/Пекар (Dialogue 1), Оленка/Тарас (Dialogue 2). Dialogue 1 is a natural multi-turn bakery exchange with realistic price progression (200₴ cake, 15₴ bread, 45₴ buns, 20₴ pastry). Dialogue 2 is a natural age conversation with family members mentioned (сестра, брат). Both dialogues serve clear pedagogical goals. Тарас's family ages create a believable context (he's 25, sister 18, brother 11). One minor note: Dialogue 1 is purely transactional (asking prices), but this is inherent to the topic and the exchange feels natural with varied items and a polite close ("Добре. Дякую, до побачення!"). |

## Findings

```
[3. Pedagogical quality] [SEVERITY: minor]
Location: §2 "Numbers 1-20", paragraph 2: "A counting rhyme by Леся Вознюк (in Kravcova, Grade 2, p. 92) puts numbers 1–7 into context"
Issue: The full rhyme covers numbers 1–10 (continuing through вісім, дев'ять, десять/телятко), not just 1–7. The module truncates the quote at "сім" with "..." and incorrectly describes the rhyme as covering only 1–7. This undersells the rhyme's pedagogical value and is factually inaccurate about the source material.
Fix: Change "1–7" to "1–10" and extend the quote to include the full rhyme (вісім through десять), which is a valuable teaching resource for all ten numbers.
```

## Verdict: REVISE

One minor factual inaccuracy about the counting rhyme's scope. All dimensions score ≥9, but the review protocol requires zero findings mentioning inaccuracies for PASS. The fix is minimal and improves the module's pedagogical value by including the complete rhyme.

<fixes>
- find: "A counting rhyme by Леся Вознюк (in Kravcova, Grade 2, p. 92) puts numbers 1–7 into context: «Один і два — росла трава, три, чотири — покосили, п'ять — на сонечку сушили, шість — в копичку поскладали, сім — корівку годували...» Reading this aloud is excellent pronunciation practice."
  replace: "A counting rhyme by Леся Вознюк (in Kravcova, Grade 2, p. 92) puts numbers 1–10 into context: «Один і два — росла трава, три, чотири — покосили, п'ять — на сонечку сушили, шість — в копичку поскладали, сім — корівку годували, вісім — молочко давала, дев'ять — діток напувала, десять — привела телятко. Починаймо все спочатку!» Reading this aloud is excellent pronunciation practice for all ten base numbers."
</fixes>
