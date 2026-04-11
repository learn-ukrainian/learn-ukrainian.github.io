## Linguistic Scan
One critical linguistic error found: the use of "написаний автором лист" as a positive example of a passive participle with an instrumental agent, which is a Russian calque and contradicts the module's own later rules. All other Ukrainian forms (including "масмедіа", "канцелярит", and the explanations of calques) are correct and verified.

## Exercise Check
All activity markers from the plan's `activity_hints` are present, correctly formatted, and logically placed after the relevant pedagogical sections:
- `<!-- INJECT_ACTIVITY: group-sort-vs-vs -->` tests the three types of passive immediately after they are introduced.
- `<!-- INJECT_ACTIVITY: style-choice-active-passive -->` and `<!-- INJECT_ACTIVITY: reading-passive-ident -->` are placed after the stylistic rules are explained.
- `<!-- INJECT_ACTIVITY: error-correction-passive -->` and `<!-- INJECT_ACTIVITY: instrumental-usage-fill -->` correctly follow the "Culture of Speech" section where the rules against instrumental agents are taught.
- An additional `<!-- INJECT_ACTIVITY: passive-transformation-task -->` is present at the end of the synthesis section, which is a helpful expansion on the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Required textbooks (Караман, Авраменко, Глазова) and State Standard references from the plan are not cited in the text. Word count is 3697, below the 4000-word target. |
| 2. Linguistic accuracy | 7/10 | Critical error: uses "написаний автором лист" as an example of a correct passive participle, which is a Russian calque (instrumental agent with participle) and contradicts the module's own later rules. |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of the "three whales" of passive voice, but the contradictory example of "написаний автором" undermines the otherwise strong pedagogical flow. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (здійснюватися, довкілля, доцільно, моніторинг, etc.) are integrated smoothly and naturally. |
| 5. Exercise quality | 10/10 | All required exercise types are covered by markers and placed appropriately after the relevant theory sections. |
| 6. Engagement & tone | 9/10 | Good use of metaphors ("детектив заходить до кімнати", "три кити") and professional tone, avoiding gamified cliches. |
| 7. Structural integrity | 8/10 | Word count (3697) is below the 4000-word target. All H2 headings from the plan are present and well-structured. |
| 8. Cultural accuracy | 10/10 | Effectively highlights the decolonial aspect of preferring active voice over the Soviet bureaucratic passive. Uses authentic Ukrainian folklore examples. |
| 9. Dialogue & conversation quality | 8/10 | The dialogue between Oleg and Mariia is functional and demonstrates the transition from informal to formal, but is quite brief. |

## Findings

[Linguistic accuracy] [critical]
Location: `Наприклад: «Це написаний автором лист» *(This is a letter written by the author)* або «Ми живемо у нещодавно збудованому будинку»`
Issue: Passive participles with an instrumental agent ("написаний автором") are considered Russian calques in Ukrainian. This also directly contradicts the module's later rule that the instrumental case is categorically forbidden for living agents.
Fix: Change to a non-agentive instrumental indicating a tool/instrument (знаряддя), such as "написаний олівцем".

[Plan adherence] [major]
Location: General content
Issue: The plan required citing several textbooks (Караман, Авраменко, Глазова) and the State Standard, but none are mentioned in the prose.
Fix: Add a paragraph summarizing these references to improve plan adherence and simultaneously increase word count.

[Structural integrity] [major]
Location: General content
Issue: The word count is 3697, which is below the 4000-word target.
Fix: Insert an additional paragraph discussing the textbook references to address the missing plan points and increase the word count.

## Verdict: REVISE
The module is exceptionally well-written, engaging, and clearly explains a difficult concept. However, it contains a critical linguistic contradiction in the first section ("написаний автором лист") that accidentally teaches a Russian calque as correct, completely undermining the module's core rule against instrumental agents. Additionally, it misses the required textbook references and falls short of the word count target. Applying the exact fixes will correct the error and add the missing references.

<fixes>
- find: "Наприклад: «Це написаний автором лист» *(This is a letter written by the author)* або «Ми живемо у нещодавно збудованому будинку»"
  replace: "Наприклад: «Це написаний олівцем лист» *(This is a letter written in pencil)* або «Ми живемо у нещодавно збудованому будинку»"
- insert_after: "(написано пером), але ніколи — для живої особи."
  text: "\n\nОкрім того, якщо ви хочете поглибити свої знання, радимо звернутися до класичних шкільних підручників, на які спирається сучасна мовна норма. Зокрема, у підручнику С. Карамана для 10 класу (§75, с. 187; §77, с. 191–193) дуже докладно описано перехід від активного до пасивного стану та розібрано специфіку безособових форм. О. Авраменко у своєму підручнику для 11 класу (§25, с. 81–82) та О. Глазова (11 клас, §21–22, с. 95–97) також приділяють значну увагу подоланню кальок і правильному використанню дієприкметників. Усі ці мовознавчі орієнтири органічно відповідають вимогам Державного стандарту 2024 року (SS 4.1.3.1), який вимагає від випускників уміння свідомо розрізняти та стилістично доречно вживати пасивні та активні конструкції в різних типах текстів."
</fixes>
