## Linguistic Scan
- `[CRITICAL]` Section `Де, куди, звідки — місце`: `Театр, куди ми вчора купили квитки, відомий на всю країну.` The module has just taught that `куди` is for movement toward a destination, but this clause uses `купили`, not a motion verb.
- `[CRITICAL]` Same section: `The third important relative pronoun indicates the initial starting point or place of origin.` This mislabels `звідки` (and the `де/куди/звідки` set) as a pronoun. VESUM tags them as `adv:pron:int:rel`, and textbook results in the repo describe `де, куди, звідки` as `сполучні слова`.
- No Russianisms, Surzhyk forms, paronym confusions, or Russian letters `ы э ё ъ` found.

## Exercise Check
- 5 activity markers are present, matching the 5 `activity_hints` in the plan.
- Placement is appropriate: `fill-in` follows the `який/яка/яке/які` teaching block, `quiz` follows `де/куди/звідки`, `match-up` follows the sentence-combining model, `true-false` follows the error discussion, and `unjumble` closes the module.
- Markers are spread through the module rather than clustered at the end.
- No inline DSL exercise blocks are present, so answer-logic/distractor quality is not auditable from this draft alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All three planned sections and all 5 activity types are present, but the off-plan block `Finally, there is a very common, natural alternative... "що"` introduces grammar outside the stated objectives, and the common-errors treatment does not model the plan’s explicit wrong-gender error (`Хлопець, яке` search: 0). |
| 2. Linguistic accuracy | 6/10 | `Театр, куди ми вчора купили квитки...` misuses `куди` with `купили`, and `The third important relative pronoun...` wrongly classifies `звідки`. |
| 3. Pedagogical quality | 7/10 | The `Ріелтор` / `Покупець` opening gives a solid PPP-style lead-in and there are many examples, but the `що` detour and the wrong part-of-speech label blur the target grammar set. |
| 4. Vocabulary coverage | 9/10 | Required plan vocab appears naturally in prose: `який/яка/яке/які`, `де`, `куди`, `звідки`, `означальний`, `описувати`, `речення`; recommended items `котрий`, `затишний`, `знаходитися`, `стояти` also appear. |
| 5. Exercise quality | 9/10 | Marker count matches the plan and placement is logically sequenced after teaching points. No visible inline exercise logic is wrong in the provided draft. |
| 6. Engagement & tone | 8/10 | The voice is mostly teacherly and concrete, but `Таке речення звучить набагато природніше і показує ваш високий рівень володіння мовою.` is promotional rather than instructional. |
| 7. Structural integrity | 8/10 | All H2 headings are present and the pipeline word count is safely above target, but the learner-facing artifact `<!-- VERIFY -->` remains in the prose. |
| 8. Cultural accuracy | 9/10 | No Russocentric framing or cultural inaccuracies detected; examples stay within Ukrainian usage and context. |
| 9. Dialogue & conversation quality | 8/10 | The named `Ріелтор` / `Покупець` dialogue is relevant and natural enough, but it is brief and the rest of the module is mostly expository. |

## Findings
- `[Linguistic accuracy] [SEVERITY: critical]`
  Location: `Театр, куди ми вчора купили квитки, відомий на всю країну.`
  Issue: `куди` is being taught as the connector for movement toward a destination, but this clause uses `купили`, not a motion verb. The example contradicts the rule it is supposed to illustrate.
  Fix: Replace the sentence with a true motion example, e.g. `Театр, куди ми вчора пішли, відомий на всю країну.` and update the translation accordingly.

- `[Linguistic accuracy] [SEVERITY: critical]`
  Location: `The third important relative pronoun indicates the initial starting point or place of origin.`
  Issue: `звідки` is not a pronoun here. VESUM marks `де/куди/звідки` as adverbial forms (`adv:pron:int:rel`), and the textbook material in the repo treats them as `сполучні слова`.
  Fix: Change `relative pronoun` to `relative word` or `relative adverb`.

- `[Plan adherence] [SEVERITY: major]`
  Location: `Finally, there is a very common, natural alternative that you will hear native speakers use constantly... you can often use the short, invariant word "що".`
  Issue: The plan scope is `який/яка/яке/які`, `де/куди/звідки`, plus `котрий` as recommended vocabulary. This paragraph adds a new alternative system and tells learners it can replace the target forms, which muddies the A2 focus.
  Fix: Remove this `що` paragraph and its examples.

- `[Plan adherence] [SEVERITY: major]`
  Location: `English speakers often make three common mistakes when forming relative clauses in Ukrainian...`
  Issue: The plan explicitly calls for a wrong-gender-agreement warning (`Хлопець, яке = WRONG`), but the module never gives a concrete wrong-gender counterexample; search for `Хлопець, яке` returns 0.
  Fix: Add a short wrong-gender example such as `Хлопець, яке прийшов вчора.` — WRONG, followed by the correct form with `який`.

- `[Structural integrity] [SEVERITY: minor]`
  Location: `**Книжка, яка вона цікава.** — *The book, which it is interesting.* (<!-- VERIFY --> WRONG)`
  Issue: `<!-- VERIFY -->` is a stray authoring artifact left in learner-facing content.
  Fix: Remove the HTML comment.

- `[Engagement & tone] [SEVERITY: minor]`
  Location: `Таке речення звучить набагато природніше і показує ваш високий рівень володіння мовою.`
  Issue: This sounds self-congratulatory rather than instructional.
  Fix: Replace it with a concrete learning benefit, e.g. that the structure helps combine ideas more naturally.

## Verdict: REVISE
REVISE. The module is structurally salvageable, but it contains two critical language-teaching errors (`куди` misuse and wrong grammatical labeling), plus major scope drift away from the plan.

<fixes>
- find: |-
    Парк, куди ми ходимо гуляти кожної неділі, дуже великий. Це новий ресторан, куди вони планують піти на вечерю. Місто, куди він завтра їде у відрядження, знаходиться далеко звідси. Театр, куди ми вчора купили квитки, відомий на всю країну.

    > *The park where we go for a walk every Sunday is very large. This is a new restaurant where they plan to go for dinner. The city where he is going on a business trip tomorrow is located far from here. The theater where we bought tickets yesterday is famous all over the country.*
  replace: |-
    Парк, куди ми ходимо гуляти кожної неділі, дуже великий. Це новий ресторан, куди вони планують піти на вечерю. Місто, куди він завтра їде у відрядження, знаходиться далеко звідси. Театр, куди ми вчора пішли, відомий на всю країну.

    > *The park where we go for a walk every Sunday is very large. This is a new restaurant where they plan to go for dinner. The city where he is going on a business trip tomorrow is located far from here. The theater where we went yesterday is famous all over the country.*
- find: |-
    The third important relative pronoun indicates the initial starting point or place of origin.
  replace: |-
    The third important relative word indicates the initial starting point or place of origin.
- find: |-
    Finally, there is a very common, natural alternative that you will hear native speakers use constantly. Instead of matching the gender and number every single time, you can often use the short, invariant word "що". In the Nominative and Accusative cases, this little word can replace the longer connector. It never changes its form, making it incredibly easy to use in everyday conversation. It makes your speech sound flowing and natural without having to pause and think about grammar endings.

    Це Євген, що працює зі мною в офісі. Це м'ясо, що ми купили на ринку.

    > *This is Yevhen, who works with me in the office. This is the meat that we bought at the market.*
  replace: ""
- find: |-
    Skipping the connector word will confuse your listener. Second, avoid using redundant pronouns. Sometimes learners try to combine the relative pronoun with a personal pronoun, resulting in incorrect sentences.
  replace: |-
    Skipping the connector word will confuse your listener. Second, avoid wrong gender agreement: **Хлопець, яке прийшов вчора.** is wrong, because **хлопець** needs **який**. Third, avoid using redundant pronouns. Sometimes learners try to combine the relative pronoun with a personal pronoun, resulting in incorrect sentences.
- find: |-
    **Книжка, яка вона цікава.** — *The book, which it is interesting.* (<!-- VERIFY --> WRONG)
  replace: |-
    **Книжка, яка вона цікава.** — *The book, which it is interesting.* (WRONG)
- find: |-
    Таке речення звучить набагато природніше і показує ваш високий рівень володіння мовою.
  replace: |-
    Таке речення звучить набагато природніше і допомагає поєднати дві думки в одне висловлення.
</fixes>