Now I have all the data I need. Let me compile the full adversarial review.

---

## Linguistic Scan

**Russianisms:** None found. ✓
**Surzhyk:** None found. ✓
**Calques:** None found. ✓
**Paronyms:** None found. ✓
**Russian characters (ы, э, ё, ъ):** None found. ✓

**Factual error found:**

1. **"At the start of a sentence, always **і**"** — This is factually incorrect. Літвінова Grade 5 p.176 explicitly lists two rules for sentence-initial position: "**І** на початку речення або після розділового знака **перед приголосним**" AND "**Й** на початку речення або після розділового знака **перед голосним**: Й учимося грамотно писати." The module states an absolute ("always і") that contradicts the textbook it cites as a reference. While sentence-initial "Й" is rare in practice, teaching "always" is incorrect.

2. **Missing exception: і before я, ю, є, ї** — Avramenko Grade 5 p.117 explicitly states: "і перед й, я, ю, є, ї: її і його, Одеса і Ялта, лисиця і їжак." The module's simplified rule "after a vowel → й" would incorrectly predict *"Одеса й Ялта"* or *"її й його"*. These are common constructions learners will encounter. The module omits this without any caveat.

**VESUM notes:** All 12 "NOT IN VESUM" words are proper nouns (Дарина, Олексій, Олена, Тарас, Семен/Семеном, Львів/Львові/Львова, Одеси/Одесі) or the abbreviation "льв" used in a cluster list. No errors. "Есей" confirmed in VESUM ✓. "По-справжньому" confirmed ✓. "Солов'їна" confirmed ✓.

## Exercise Check

Four activity markers found:
1. `<!-- INJECT_ACTIVITY: quiz-u-or-v -->` — after "У чи В?" section ✓
2. `<!-- INJECT_ACTIVITY: quiz-i-or-y -->` — after "І чи Й?" section ✓
3. `<!-- INJECT_ACTIVITY: fill-in-z-iz-zi -->` — after з/із/зі content ✓
4. `<!-- INJECT_ACTIVITY: quiz-which-sounds-natural -->` — at end of Summary ✓

**Plan activity_hints mapping:**
- quiz: У or В? (10 items) → `quiz-u-or-v` ✓
- quiz: І or Й? (8 items) → `quiz-i-or-y` ✓
- fill-in: З, із, or зі? (6 items) → `fill-in-z-iz-zi` ✓
- quiz: Which sentence sounds more natural? (6 items) → `quiz-which-sounds-natural` ✓

All four markers present, properly placed after their respective teaching sections, evenly distributed. ✓

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four content_outline sections present with correct headings. Dialogue captures the plan's proofreading scenario (Студент writing, Друг correcting). However, the plan's dialogue_situations specifies "у городі/в городі, і яблука/й яблука, у школі/в школі" — none of these specific examples appear in the dialogue (module uses Львів, Київ, офіс instead). The город (garden) is mentioned in the intro but never features in the dialogue. All four activity markers match plan hints. Vocabulary coverage good (see dim 4). References to Авраменко and Літвінова textbooks integrated naturally into the prose. Section word balance is reasonable for a 1423-word module against 4×300 plan. |
| 2. Linguistic accuracy | 8/10 | All Ukrainian forms verified correct via VESUM. У/в rules match Правопис §23. З/із/зі rules match Літвінова p.177. However: (1) "At the start of a sentence, always **і**" is incorrect per Літвінова p.176 which shows "Й" before vowels at sentence start. (2) The і/й section omits the exception "і before я, ю, є, ї" from Avramenko p.117 — the simplified "after vowel → й" rule would produce wrong results for common words like "Ялта", "їжак". No Russianisms, surzhyk, or calques detected. |
| 3. Pedagogical quality | 8/10 | Good PPP flow: situation (proofreading essay) → pattern (rules with examples) → practice (activities). Each grammar point has 3+ Ukrainian examples ✓. The "listen-and-feel test" framing is excellent for A1 — matches how textbooks present this. However, the dialogue has a confusing moment: Дарина says "Так, правильно!" then immediately contradicts herself with "Ні, «в Києві!»" — a learner sees "Yes, correct!" followed by a correction, which muddles the teaching. The prose explanation after each dialogue effectively bridges to the rules section. |
| 4. Vocabulary coverage | 9/10 | Required vocab all present: у/в used extensively, і/й taught with examples, з/із/зі covered. Recommended vocab: Київ ✓ (multiple instances), Львів ✓ (multiple), офіс ✓ ("працює в офісі"), парк ✓ ("йдемо в парк"), театр ✓ ("йдуть у театр"). Words introduced naturally in dialogue context, not as lists. |
| 5. Exercise quality | 9/10 | All four markers placed correctly after relevant teaching. Types match plan exactly (2 quiz, 1 fill-in, 1 natural-sound quiz). Markers spread evenly: one per section. Cannot evaluate item-level logic (YAML generated separately), but placement and type mapping are correct. |
| 6. Engagement & tone | 9/10 | No motivational openers or meta-commentary. The proofreading scenario is genuinely engaging — two friends fixing an essay is natural and relatable. The "солов'їна мова" (nightingale language) cultural reference at the end is specific and earned. "Think of **зі** as a cushion" is a concrete metaphor. One minor deduction: the closing paragraph has a slightly promotional tone ("one of the features that give Ukrainian its reputation as the солов'їна мова") — showing rather than telling would be stronger. |
| 7. Structural integrity | 10/10 | All four H2 sections present and ordered per plan. Clean markdown. No duplicate summaries, no meta-commentary sections, no stray tags. Word count 1423 exceeds 1200 target ✓. Activity markers properly formatted as HTML comments. |
| 8. Cultural accuracy | 10/10 | Fully decolonized — Ukrainian euphony presented on its own terms, never compared to Russian. "Солов'їна мова" is an authentic Ukrainian cultural concept. City examples (Київ, Львів, Одеса) are all Ukrainian cities. No problematic framing. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers (Дарина, Олексій) with distinct roles ✓. Natural proofreading scenario ✓. Multi-turn with genuine interaction ✓. However: (1) Дарина's "Так, правильно!" → "Ні, «в Києві!»" is confusing (approves then contradicts). (2) The second dialogue block (і/й section) is really a continuation of the first — it works, but there's no separate dialogue for the з/із/зі pair, leaving that section as pure exposition. Plan specified one dialogue situation, so this isn't a structural violation, but the з/із/зі section feels lecture-heavy compared to the lively dialogue sections. |

## Findings

**[LINGUISTIC ACCURACY] [MAJOR]**
Location: "І чи Й?" section, tip box area — `"At the start of a sentence, always **і**: **«І він прийшов»** ("And he came")."`
Issue: Літвінова Grade 5 p.176 explicitly teaches "Й на початку речення або після розділового знака перед голосним: Й учимося грамотно писати." The claim "always і" is factually incorrect. While sentence-initial "Й" is uncommon, teaching an absolute rule that contradicts the cited textbook is wrong.
Fix: Soften "always" to reflect the primary rule without overclaiming. Change to "usually **і**" with the example preserved — this is truthful and doesn't overload A1 with the exception.

**[PEDAGOGICAL QUALITY / DIALOGUE QUALITY] [MAJOR]**
Location: First dialogue block — `"Так, правильно! «Живе» — голосний Е. «У Києві»... Ні, «в Києві!»" *(Yes, correct! "Zhyve" — vowel E. "U Kyievi"... No, "v Kyievi!")*`
Issue: Дарина says "Так, правильно!" (Yes, correct!) and then immediately corrects "у Києві" to "в Києві." An A1 learner reads "Yes, correct!" and accepts the form — then gets confused when it's immediately contradicted. The self-correction process may be realistic, but at A1, clarity beats authenticity.
Fix: Replace "Так, правильно!" with "Зачекай..." (Wait...) so Дарина signals she's analyzing, not approving.

**[LINGUISTIC ACCURACY] [MINOR]**
Location: "І чи Й?" section — the complete set of rules presented.
Issue: Avramenko Grade 5 p.117 teaches "і перед й, я, ю, є, ї: її і його, Одеса і Ялта, лисиця і їжак." The module's simplified rule "after a vowel → й" does not cover this exception. A learner applying the module's rule would produce *"Одеса й Ялта"* (wrong). For A1, a brief mention is sufficient.
Fix: Add a one-sentence note after the tip box acknowledging this exception with one example.

**[PLAN ADHERENCE] [MINOR]**
Location: Dialogue section — entire dialogue block.
Issue: Plan's `dialogue_situations` specifies examples "у городі/в городі, і яблука/й яблука, у школі/в школі" with город(m), школа(f), яблуко(n) demonstrating gender variety. The actual dialogue uses Львів, Київ, офіс (all masculine) — missing the feminine and neuter examples from the plan.
Fix: Not fixing — the current dialogue works well and the gender point is minor for a phonetics-focused module. Informational only.

## Verdict: REVISE

Two MAJOR findings (incorrect absolute rule about sentence-initial і/й; confusing dialogue approval-then-contradiction) and one MINOR linguistic gap (missing і before я/ю/є/ї). The module is strong overall — good structure, natural engagement, correct core rules — but the factual error in the і/й section and the pedagogically confusing dialogue moment must be fixed before shipping. Both fixes are surgical.

<fixes>
- find: "Так, правильно! «Живе» — голосний Е. «У Києві»... Ні, «в Києві!» *(Yes, correct! \"Zhyve\" — vowel E. \"U Kyievi\"... No, \"v Kyievi!\")*"
  replace: "Зачекай... «Живе» — голосний Е. «У Києві»... Ні, «в Києві!» *(Wait... \"Zhyve\" — vowel E. \"U Kyievi\"... No, \"v Kyievi!\")*"
- find: "At the start of a sentence, always **і**: **«І він прийшов»** (\"And he came\")."
  replace: "At the start of a sentence, **і** is standard: **«І він прийшов»** (\"And he came\")."
- find: "Quick test: does the word before end in a vowel? → **й**. Does it end in a consonant? → **і**."
  replace: "Quick test: does the word before end in a vowel? → **й**. Does it end in a consonant? → **і**. Exception: before words starting with **я, ю, є, ї** (which begin with a [й] sound), use **і** even after a vowel: **Одеса і Ялта**, **її і його**."
</fixes>
