## Linguistic Scan
- Factually wrong classification in `У чи В?`: `This rule applies not only to prepositions but also to some word prefixes, such as the alternating forms **вже** (already) and **уже** (already).` VESUM verification returns both `вже` and `уже` as `adv`, so they are standalone adverbs, not prefixes.
- Factually wrong absolute rule in `І чи Й?`: `Just like the preposition **у**, the conjunction **і** is always used at the very beginning of a sentence, no matter what word follows it.` Textbook search returns Grade 5 p.176 with sentence-initial `Й` before a vowel: `Й учимося грамотно писати.`

## Exercise Check
- Found 4 markers: `quiz-u-or-v`, `quiz-i-or-y`, `fill-in-z-iz-zi`, `quiz-euphony-comparison`.
- Marker IDs match all 4 `activity_hints`.
- Each marker comes after the relevant teaching block, and the markers are spread sensibly through the module.
- No inline DSL exercise blocks are present here, so only marker placement/id logic could be reviewed. No marker-placement issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All four planned H2 sections are present and in order; the prose cites Avramenko and Litvinova directly; required/recommended vocabulary appears naturally in context: `в Києві`, `у Львові`, `в офісі`, `в парк`, `у театр`. |
| 2. Linguistic accuracy | 6/10 | Two factual grammar claims are wrong: `вже/уже` are called “word prefixes,” and `і` is called “always” sentence-initial, but school-textbook evidence allows sentence-initial `й` before vowels. |
| 3. Pedagogical quality | 7/10 | The module has strong example density, but it teaches one key `і/й` rule incorrectly as an absolute: `the conjunction **і** is always used at the very beginning of a sentence`. That is harmful in a rule-teaching module. |
| 4. Vocabulary coverage | 10/10 | All required forms are taught in prose (`у/в`, `і/й`, `з/із/зі`), and all recommended words are used naturally (`Київ`, `Львів`, `офіс`, `парк`, `театр`). |
| 5. Exercise quality | 9/10 | The four markers match the planned quiz/fill-in progression and appear after the relevant explanations. The only reason this is not a 10 is that the actual injected item logic is not visible in this draft. |
| 6. Engagement & tone | 9/10 | The tone is mostly teacherly and practical rather than gamified; lines like `Read your sentences aloud and trust your ears` support the lesson well. |
| 7. Structural integrity | 10/10 | Clean markdown, all expected H2 headings present, no dangling sections, and pipeline word count is `1565`, which is above the `1200` target. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian on its own terms and makes no Russian-comparison claims or cultural misstatements. |
| 9. Dialogue & conversation quality | 7/10 | Dialogue 1 is usable, but Dialogue 2 contains a self-reference error: `> **Максим:** Ні, я і Максим йдемо в парк.` That makes the exchange sound artificial and confusing. |

## Findings
1. `[Linguistic accuracy] [SEVERITY: critical]`  
Location: `This rule applies not only to prepositions but also to some word prefixes, such as the alternating forms **вже** (already) and **уже** (already).`  
Issue: `вже/уже` are not prefixes; VESUM identifies both as adverbs. This teaches the wrong grammatical category.  
Fix: Change `word prefixes` to `standalone words` and identify `вже/уже` as adverbs.

2. `[Linguistic accuracy] [SEVERITY: critical]`  
Location: `Just like the preposition **у**, the conjunction **і** is always used at the very beginning of a sentence, no matter what word follows it.`  
Issue: This is false as stated. Textbook evidence for milozvuchnist allows sentence-initial `й` before vowels.  
Fix: Rewrite the sentence to say that sentence-initial `і` is standard before consonants, while `й` can appear before vowels.

3. `[Dialogue & conversation quality] [SEVERITY: major]`  
Location: `> **Максим:** Ні, я і Максим йдемо в парк. *(No, Maksym and I are going to the park.)*`  
Issue: The speaker refers to himself by name inside his own answer, which makes the dialogue unnatural and confusing.  
Fix: Replace the second `Максим` with a different noun phrase, such as `мій брат`.

## Verdict: REVISE
Critical factual grammar errors are present, and both `Linguistic accuracy` and `Pedagogical quality` fall below 9. The module is structurally solid, but it should not ship until those claims are corrected.

<fixes>
- find: "This rule applies not only to prepositions but also to some word prefixes, such as the alternating forms **вже** (already) and **уже** (already)."
  replace: "This rule applies not only to prepositions but also to some standalone words, such as the alternating adverbs **вже** (already) and **уже** (already)."
- find: "Just like the preposition **у**, the conjunction **і** is always used at the very beginning of a sentence, no matter what word follows it."
  replace: "At the beginning of a sentence, **і** is standard before a consonant, while **й** can appear before a vowel."
- find: "> **Максим:** Ні, я і Максим йдемо в парк. *(No, Maksym and I are going to the park.)*"
  replace: "> **Максим:** Ні, я і мій брат йдемо в парк. *(No, my brother and I are going to the park.)*"
</fixes>