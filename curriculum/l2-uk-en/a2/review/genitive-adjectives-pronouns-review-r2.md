## Linguistic Scan
- **Critical teaching error:** `Feminine possessive pronouns in the Genitive case take endings that sound like \`-еї\` or \`-ої\`.` The taught forms in the same paragraph are `моєї`, `твоєї`, so the feminine Genitive ending here is `-єї`, not `-еї`.

## Exercise Check
- 5/5 plan markers are present exactly once: `fill-in-genitive-adjectives`, `quiz-possessive-pronouns`, `match-up-nom-to-gen`, `fill-in-demonstratives-full-phrases`, `error-correction-genitive-agreement`.
- Marker placement is correct: each appears after the relevant teaching section.
- Marker IDs match the plan’s `activity_hints`.
- No inline DSL exercise blocks are present, so exercise logic beyond marker placement is not inspectable here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three H2 sections match the plan and required/recommended vocabulary is present, but the plan references are not integrated at all: `Заболот`, `ULP`, and `Ukrainian Lessons` occur 0 times in the module text. The final full-phrase modeling also stays mostly with masculine/feminine examples: `для моєї старшої сестри`, `без того важливого документа`, `для цього нового друга`, while neuter is only isolated earlier in `нового міста`, `доброго слова`. |
| 2. Linguistic accuracy | 8/10 | One factual teaching bug: `Feminine possessive pronouns in the Genitive case take endings that sound like \`-еї\` or \`-ої\`.` That contradicts the actual forms immediately given: `моєї`, `твоєї`. |
| 3. Pedagogical quality | 7/10 | The module has a PPP skeleton, but it wastes space on abstraction instead of procedure: `This agreement is the core rhythm of the Ukrainian language. It might take some time...` gives motivation, not a usable rule. The climax section also under-models neuter full phrases despite the stated objective. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is used naturally in prose: `прикметник`, `займенник`, `присвійний`, `вказівний`, `узгодження`, `дозвіл`, `підручник`, `документ`, `вчителька`, `важливий`. Recommended words also appear: `молодий`, `старший`, `дівчина`, `олівець`. |
| 5. Exercise quality | 9/10 | Marker inventory matches the plan exactly and appears after the relevant teaching. No marker clustering problem. Actual generated YAML logic is not visible here, so only placement/alignment can be judged. |
| 6. Engagement & tone | 7/10 | Too much generic filler: `Learning to quickly distinguish... is a major milestone in your Ukrainian journey` and `This agreement is the core rhythm of the Ukrainian language... soon it will feel completely natural` add warmth but little instructional value in an already over-target module. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly. Markdown is clean, all five activity markers are present, and pipeline word count is 2791, well above the 2000 target. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian as its own system and avoids “like Russian but...” framing in the main teaching flow. The decolonization note is directionally appropriate. |
| 9. Dialogue & conversation quality | 7/10 | The opening lost-and-found dialogue fits the plan well, but conversation quality drops into isolated model sentences, and one line is stilted: `Після того довгого дня ми просто хотіли швидко спати.` |

## Findings
- [Linguistic accuracy] [SEVERITY: critical]  
Location: `Feminine possessive pronouns in the Genitive case take endings that sound like \`-еї\` or \`-ої\`.`  
Issue: This teaches the feminine Genitive ending incorrectly. The forms shown in the same sentence family are `моєї`, `твоєї`, so the relevant ending is `-єї`, not `-еї`.  
Fix: Change `-еї` to `-єї` and phrase it as `take endings like` rather than `sound like`.

- [Plan adherence] [SEVERITY: major]  
Location: plan references `Заболотний Grade 6, §48-49` and `ULP: Ukrainian Adjective Declension`; module text contains 0 mentions of `Заболот`, `ULP`, or `Ukrainian Lessons`.  
Issue: The plan’s references are not cited or integrated anywhere in the lesson.  
Fix: Add one explicit sentence tying the declension patterns to Заболотний §48-49 and the Ukrainian Lessons adjective-declension guide.

- [Plan adherence] [SEVERITY: major]  
Location: objective: `Learner can produce full Genitive noun phrases with adjective + pronoun + noun agreement across all three genders.` Later model phrases are `для моєї старшої сестри`, `біля цього нового міського ринку`, `без того важливого документа`, `для цього нового друга`.  
Issue: The lesson models full multi-word phrases for masculine and feminine, but not for neuter in the culmination section. Neuter appears only earlier in isolated forms such as `нового міста`, `доброго слова`.  
Fix: Add at least one full neuter phrase in the final modeling section, e.g. `без цього важливого слова`.

- [Dialogue & conversation quality] [SEVERITY: major]  
Location: `Після того довгого дня ми просто хотіли швидко спати.`  
Issue: This sounds translated and unnatural as learner model language; `швидко спати` is not idiomatic here.  
Fix: Replace it with `Після того довгого дня ми просто хотіли швидше піти спати.`

- [Pedagogical quality] [SEVERITY: major]  
Location: `Notice how the preposition anchors the entire phrase. Every word that follows it — the pronoun, the adjective, and the noun — falls into the Genitive case in perfect grammatical harmony. This agreement is the core rhythm of the Ukrainian language. It might take some time to get used to changing two or three words instead of just one, but soon it will feel completely natural.`  
Issue: This is motivational filler where the learner needs a procedural shortcut. In a 2791-word module, this space should teach a usable production strategy.  
Fix: Replace the paragraph with a concrete heuristic: change the noun first, then make the pronoun and adjective copy its gender and case.

## Verdict: REVISE
REVISE. There is a critical linguistic teaching error (`-еї`) and several major plan/pedagogy/dialogue issues. Multiple dimensions fall below 9, so this does not meet the PASS gate.

<fixes>
- find: "Feminine possessive pronouns in the Genitive case take endings that sound like `-еї` or `-ої`."
  replace: "Feminine possessive pronouns in the Genitive case take endings like `-єї` or `-ої`."

- find: "This grammatical harmony is called agreement (**узгодження**)."
  replace: "This grammatical harmony is called agreement (**узгодження**). The adjective patterns in this module follow the school-style declension tables in Заболотний Grade 6, §48-49 and the Ukrainian Lessons adjective declension guide."

- find: |
    Ми вчора зустрілися біля цього нового міського ринку. Я нарешті купив ідеальний подарунок для моєї старшої сестри. Вони ніяк не можуть почати працювати без того важливого документа.

    > *We met yesterday near this new city market. I finally bought the perfect gift for my older sister. They cannot start working at all without that important document.*
  replace: |
    Ми вчора зустрілися біля цього нового міського ринку. Я нарешті купив ідеальний подарунок для моєї старшої сестри. Без цього важливого слова речення звучить неприродно. Вони ніяк не можуть почати працювати без того важливого документа.

    > *We met yesterday near this new city market. I finally bought the perfect gift for my older sister. Without this important word, the sentence sounds unnatural. They cannot start working at all without that important document.*

- find: "Після того довгого дня ми просто хотіли швидко спати."
  replace: "Після того довгого дня ми просто хотіли швидше піти спати."

- find: "Notice how the preposition anchors the entire phrase. Every word that follows it — the pronoun, the adjective, and the noun — falls into the Genitive case in perfect grammatical harmony. This agreement is the core rhythm of the Ukrainian language. It might take some time to get used to changing two or three words instead of just one, but soon it will feel completely natural."
  replace: "Notice how the preposition anchors the entire phrase. A practical shortcut is to change the noun first, then make the pronoun and adjective copy its gender and case. This turns a long phrase into a sequence of small, reliable steps."
</fixes>