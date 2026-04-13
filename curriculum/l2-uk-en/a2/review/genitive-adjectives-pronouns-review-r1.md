## Linguistic Scan
- Critical case error: `Я вчора отримав важливого листа від цього нового вчителя.` Here `отримав` takes Accusative; with an inanimate masculine noun this must be `важливий лист`, not `важливого листа`.
- Critical usage claim: the box that says `Never use «їх» for possession!` is false as an absolute rule. VESUM confirms both `їх` and `їхній` exist, and Антоненко-Давидович notes that `їх` can function possessively while modern usage often prefers `їхній` for clarity: https://www.ukrlib.com.ua/books/printit.php?page=32&tid=4002

## Exercise Check
Markers present: `fill-in-genitive-adjectives`, `quiz-possessive-pronouns`, `match-up-nom-to-gen`, `fill-in-demonstratives-full-phrases`, `error-correction-genitive-agreement`.

All 5 plan activities have a corresponding marker, and each marker appears after the relevant teaching block. No inline DSL exercise logic is present in the supplied content, so there is no answer-key logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The 3 planned H2 sections are all present and the 5 activity markers match the plan, but section 1 says `For masculine and neuter adjectives...` and then models only `нового підручника`, `важливого документа`, `синього олівця` rather than giving a clean neuter adjective+noun phrase. |
| 2. Linguistic accuracy | 5/10 | Critical error in `Я вчора отримав важливого листа...`; critical false absolute in `Never use «їх» for possession!`. |
| 3. Pedagogical quality | 7/10 | The module has a PPP shape and plenty of examples, but `The natural Ukrainian word order always places...` overstates a flexible syntax, and some prose is filler instead of rule+example. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary appears naturally in prose: `прикметник`, `займенник`, `присвійний`, `вказівний`, `узгодження`, `дозвіл`, `підручник`, `документ`, `вчителька`, `важливий`; recommended items also appear. |
| 5. Exercise quality | 9/10 | All planned exercise types are represented by markers and placed after the relevant teaching sections. |
| 6. Engagement & tone | 6/10 | Repeated filler such as `This skill allows you to be precise and specific in everyday situations.` and `This makes the language very melodic.` adds words without adding instruction. |
| 7. Structural integrity | 10/10 | All sections are present and ordered correctly; pipeline word count is 2778, above target; markers and markdown are clean. |
| 8. Cultural accuracy | 6/10 | The `їх/їхній` “Decolonization Check” turns a usage preference into a false prohibition, which is linguistically and culturally misleading. |
| 9. Dialogue & conversation quality | 8/10 | The opening uses named speakers and a plausible lost-and-found setting tied to the grammar target. |

## Findings
[Linguistic accuracy] [SEVERITY: critical]  
Location: `Я вчора отримав важливого листа від цього нового вчителя.`  
Issue: `отримав` requires Accusative; for an inanimate masculine noun that is `важливий лист`, not Genitive `важливого листа`.  
Fix: Change it to `Я вчора отримав важливий лист від цього нового вчителя.`

[Linguistic accuracy] [SEVERITY: critical]  
Location: `A very common mistake (and a direct Russianism) is using the unchanging personal pronoun «їх»... Never use «їх» for possession!`  
Issue: This is false as an absolute rule. `Їх` can function possessively in Ukrainian; beginner teaching may prefer `їхній` for clarity, but possessive `їх` is not automatically a Russianism.  
Fix: Rewrite the box as a usage note that recommends `їхній` in learner production without banning possessive `їх`.

[Plan adherence] [SEVERITY: major]  
Location: section 1 paragraph beginning `For masculine and neuter adjectives, the hard stem ending is \`-ого\`.`  
Issue: The explanation promises masculine and neuter coverage, but the immediate models are only masculine phrases.  
Fix: Add explicit neuter models such as `нового міста` and `синього моря`.

[Pedagogical quality] [SEVERITY: major]  
Location: `The natural Ukrainian word order always places the demonstrative pronoun first...`  
Issue: `always` teaches an absolute syntactic rule where Ukrainian actually has flexible word order.  
Fix: Reframe it as the common neutral beginner pattern, not the only possible order.

[Engagement & tone] [SEVERITY: minor]  
Location: `This skill allows you to be precise and specific in everyday situations.` / `This makes the language very melodic.`  
Issue: These are filler lines; they increase length without teaching grammar.  
Fix: Replace them with concise, concrete guidance or delete them.

## Verdict: REVISE
Critical linguistic findings make this unshippable as-is, even though the structure, vocabulary coverage, and exercise placement are solid.

<fixes>
- find: "Я вчора отримав важливого листа від цього нового вчителя."
  replace: "Я вчора отримав важливий лист від цього нового вчителя."
- find: "If the adjective belongs to the soft group, the ending softens to `-ього`. The word «синій» (dark blue) changes to «син**ього**», as in «без синього олівця»."
  replace: "If the adjective belongs to the soft group, the ending softens to `-ього`. The word «синій» (dark blue) changes to «син**ього**», as in «без синього олівця» or «біля синього моря». Neuter nouns follow the same pattern as masculine ones: «нового міста», «доброго слова»."
- find: "The natural Ukrainian word order always places the demonstrative pronoun first, followed by any **присвійний** (possessive) pronoun or descriptive **прикметник** (adjective), and finally the noun itself."
  replace: "A common neutral Ukrainian word order places the demonstrative pronoun first, followed by any **присвійний** (possessive) pronoun or descriptive **прикметник** (adjective), and finally the noun itself."
- find: "This skill allows you to be precise and specific in everyday situations."
  replace: "This lets you describe missing objects more precisely."
- find: "This makes the language very melodic."
  replace: "This keeps the phrase grammatically consistent."
- find: |
    :::info
    **Decolonization Check: "Their" is «їхній»**
    A very common mistake (and a direct Russianism) is using the unchanging personal pronoun «їх» (them) to mean "their", as in ❌ «їх проблеми» (their problems) or ❌ «без їх друга». In standard Ukrainian, "their" is always the declining pronoun **їхній**. You must say ✅ «їхні проблеми» and, in the Genitive, ✅ «без їхнього друга». Never use «їх» for possession!
    :::
  replace: |
    :::info
    **Usage Note: «їхній» for Clarity**
    For beginner production, it is best to prefer the declining possessive pronoun **їхній**: «їхній друг», «їхні проблеми», «без їхнього друга». The form «їх» also exists in Ukrainian and can function possessively in some styles, so it is better not to call every possessive «їх» a Russianism. In this module, teach learners to use **їхній** because it declines clearly and avoids ambiguity.
    :::
</fixes>