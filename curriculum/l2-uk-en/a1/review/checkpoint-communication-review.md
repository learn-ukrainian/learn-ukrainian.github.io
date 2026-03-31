Good, all imperative forms are confirmed. Now I have enough data for the full review.

---

## Linguistic Scan

**Russianisms:** None found.
**Surzhyk:** None found.
**Calques:** None found.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.
**Gender/case errors:** None found. All verified forms are correct per VESUM.

**Issue found:**

1. **"З ярмарком!"** — The greeting formula `З + instrumental` is taught for **holidays** (З Різдвом!, З Великоднем!). "З ярмарком!" is not an established Ukrainian greeting. It mechanically applies the formula to a non-holiday event, which is pedagogically misleading — learners may think this pattern works for any event. No native speaker would say "З ярмарком!" This teaches the formula incorrectly.

2. **Forward reference in section 1:** "In the reading text above, Olena used all of them in one short phone call" — but the reading text appears in the *next* section (Читання), not above. The word "above" is factually wrong at this point in the module.

## Exercise Check

- **activity-1**: placed after Читання section → tests reading comprehension. ✓
- **activity-2**: placed after conjunctions in Граматика → tests conjunction knowledge. ✓ Matches plan hint #2 (quiz, conjunctions).
- **activity-3**: placed after holiday greetings in Граматика → tests holiday formula. ✓ Matches plan hint #4 (quiz, holiday match).
- **activity-4**: placed after Діалог → tests integrated skills. ✓

**4 markers total, matching 4 plan activity_hints.** Placement is logical — each follows the relevant teaching content. However, activity-1 and activity-3 seem to map to plan hints #1 and #4 respectively, while plan hints #1 (fill-in vocative+imperative) and #3 (fill-in complex sentences) don't have clearly corresponding markers. The markers are generic IDs, so the actual YAML exercises will determine correctness. Marker placement is sound.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 content_outline sections present with correct headings. Dialogue uses the school fair scenario from `dialogue_situations` with плакати, квитки, напої, стільці. All 5 objectives covered (vocative, imperative, conjunctions, що/де/коли, holidays). Summary lists all 5 skills. Minor deduction: the forward reference ("reading text above") breaks the planned section ordering logic. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian forms verified against VESUM. Vocative forms correct (Олено, Тарасе, Андрію, друже, мамо). Imperative forms correct (читай/читайте, пиши/пишіть, дай/дайте, принеси/принесіть). Conjunction explanations accurate. No Russianisms, surzhyk, calques, or paronyms found. Style guide check clean. |
| 3. Pedagogical quality | 9/10 | Good PPP flow: self-check → reading → grammar summary → connected dialogue → summary. Grammar tables with 6 vocative examples and 4 imperative verb pairs. Each conjunction has an example sentence. Subordinating conjunctions each demonstrated with a full sentence. Reading comprehension questions follow the text. Minor deduction: the forward reference undermines the intended flow. |
| 4. Vocabulary coverage | 10/10 | Plan has no required/recommended vocabulary. All plan-mentioned words appear naturally in prose: кутя, колядки, свічки, плакати, квитки, напої, стільці. Holiday vocabulary integrated (Різдво, Великдень, Новий рік, день народження). Vocative examples from plan all present (Олено, Тарасе, Андрію). |
| 5. Exercise quality | 9/10 | 4 markers correctly placed after teaching sections. Each tests language skills, not content recall. Reading comprehension questions ("Що просить Олена?", "Що має Тарас?") require understanding Ukrainian text. Dialogue analysis task ("circle every vocative, imperative, conjunction") is a solid integrative exercise. |
| 6. Engagement & tone | 8/10 | No motivational openers or "magic of" language. Dialogue scenario is concrete and realistic (school fair). Reading practice is a natural phone call scenario. However: "З ярмарком!" at the end of the dialogue is forced/unnatural — no Ukrainian would say this. The forward reference ("In the reading text above") is confusing. Summary uses checklist format which is clear but slightly mechanical ("✅ Ти можеш..."). |
| 7. Structural integrity | 9/10 | All H2 headings present and correctly ordered. Word count 1190 vs. 1000 target — well within range. Clean markdown. Minor: the forward reference is a structural error (section 1 references section 2 as "above"). |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. Holiday traditions (кутя, колядки for Різдво) are authentic. No "like Russian but..." comparisons. Decolonized throughout. |
| 9. Dialogue & conversation quality | 8/10 | School fair dialogue has named speakers (Організатор, Олена, Тарас, Волонтери) with distinct voices. Natural task distribution scenario. However, "З ярмарком!" is an invented, unnatural greeting that undermines the dialogue's realism. The reading practice dialogue (Olena/Taras phone call) is more natural and better executed. |

## Findings

```
[ENGAGEMENT & TONE / DIALOGUE QUALITY] [MAJOR]
Location: Діалог section, final line: "Волонтери: З ярмарком! *(Happy fair!)*"
Issue: "З ярмарком!" is not a real Ukrainian greeting. The formula З + instrumental is for holidays/celebrations (З Різдвом!, З Великоднем!), not arbitrary events. No native speaker would say this. It teaches learners that the formula is universally applicable, which is incorrect. At A1, learners internalize examples as rules — this sets a bad pattern.
Fix: Replace with a natural celebratory line that doesn't misuse the greeting formula.
```

```
[PLAN ADHERENCE / STRUCTURAL INTEGRITY] [MAJOR]
Location: Що ми знаємо? section, final paragraph: "In the reading text above, Olena used all of them in one short phone call"
Issue: The reading text appears in the NEXT section (Читання), not above. "Above" is factually wrong at this position. The learner hasn't read the text yet, so this paragraph makes no sense.
Fix: Move this paragraph to after the reading section, or change "above" to "below" and reframe as a preview.
```

## Verdict: REVISE

Two major findings: one pedagogical error (invented greeting "З ярмарком!" that misapplies the З + instrumental formula) and one structural error (forward reference to content that appears later). Both require fixes before the module can ship.

<fixes>
- find: "З ярмарком! *(Happy fair!)*"
  replace: "Чудово, починаємо! *(Wonderful, let's begin!)*"
- find: "These five skills work together. In the reading text above, Olena used all of them in one short phone call — she addressed Taras by name, asked him to bring something, explained why, linked her thoughts into longer sentences, and wished him a happy holiday. That is what A1.7 communication looks like."
  replace: "These five skills work together. In the reading passage below, you will see Olena use all of them in one short phone call — she addresses Taras by name, asks him to bring something, explains why, links her thoughts into longer sentences, and wishes him a happy holiday. That is what A1.7 communication looks like."
</fixes>
