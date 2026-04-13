## Linguistic Scan
- Grammar fact error in section 1: `You can start a sentence with «тому що» when directly answering a question, but you should avoid starting a sentence with «бо».` This reverses the plan’s point about `бо`-clause position; SУМ-11 describes `бо` as usually standing at the start of the subordinate clause and sometimes after its first word.
- Grammar fact error in section 2: `Для вашого рівня краще завжди уникати такої подвійної конструкції... або «хоча», або «але».` School-textbook data explicitly allows a fronted concessive clause followed by `а/але/проте/зате/однак`, so this is not a blanket error rule.

## Exercise Check
- Inventory: 5/5 planned markers are present.
- Issue: 3 marker IDs are malformed and do not cleanly match the plan hints:
`match-up-match-two-halves-of-sentences-with-with`,
`unjumble-reorder-words-to-form-correct-compound-sentences-with-and`,
`group-sort-sort-conjunctions-into-vs-vs`.
- Placement is otherwise broadly after relevant teaching: 2 markers after `Хоча...`, 1 mid-section in `Складносурядне речення...`, 2 at the end of section 3.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All three planned H2 sections appear, required vocabulary is present, and references are named, but the plan point about `бо` position is reversed by `you should avoid starting a sentence with «бо»`, and 3 activity IDs are malformed. |
| 2. Linguistic accuracy | 6/10 | Critical grammar-teaching error: `Для вашого рівня краще завжди уникати такої подвійної конструкції` mislabels `Хоча..., але...` as wrong; the `бо` positioning rule is also overprescriptive/inaccurate. |
| 3. Pedagogical quality | 7/10 | There are many examples and a clear PPP-like flow, but section 2 spends core teaching space on a false prohibition instead of teaching the simpler A2 default as a preference. |
| 4. Vocabulary coverage | 9/10 | Required `тому що, бо, хоча, але, проте, однак, причина, сполучник, складне речення, тому` all appear; recommended `допуст, зате, навпаки, незважаючи на` also appear in prose. |
| 5. Exercise quality | 5/10 | All 5 planned activity types are marked, but 3 IDs are malformed (`with-with`, `with-and`, `vs-vs`), which risks broken injection or mismatched generated exercises. |
| 6. Engagement & tone | 7/10 | The teacher voice is warm, but filler such as `мають дуже красиву інтонацію` and `чудовий природний ритм` adds sentiment more than instruction. |
| 7. Structural integrity | 8/10 | All planned H2 headings are present and the pipeline word count is 2861, but malformed `INJECT_ACTIVITY` placeholders remain as source artifacts. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms and explicitly defends `бо` as native Ukrainian; no Russia-centered framing problem was found. |
| 9. Dialogue & conversation quality | 8/10 | The opening dialogue matches the plan situation and uses target conjunctions naturally, but the conversational material is brief relative to the expository prose. |

## Findings
- [PLAN ADHERENCE] [SEVERITY: critical]
Location: Section `Чому? Тому що... / Бо...` — `You can start a sentence with «тому що» when directly answering a question, but you should avoid starting a sentence with «бо».`
Issue: This contradicts the plan’s positional point for `бо` and teaches an overstrict rule.
Fix: Replace it with a note that `бо` usually stands at the start of the dependent clause and can also appear after the first word of that clause.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: Section `Хоча...` — `Студенти часто кажуть: «Хоча він втомився, але він працював». Для вашого рівня краще завжди уникати такої подвійної конструкції.`
Issue: This teaches a false grammar rule. Textbook data explicitly allows concessive clauses followed by `але/проте/зате/однак`; at A2 you can prefer the simpler pattern, but you cannot label the other pattern categorically wrong.
Fix: Rephrase this as a stylistic/level recommendation, not a prohibition.

- [EXERCISE QUALITY] [SEVERITY: major]
Location: Marker block after `Хоча...` and section 3 — `<!-- INJECT_ACTIVITY: match-up-match-two-halves-of-sentences-with-with -->`, `<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-compound-sentences-with-and -->`, `<!-- INJECT_ACTIVITY: group-sort-sort-conjunctions-into-vs-vs -->`
Issue: These IDs are truncated/malformed and do not cleanly correspond to the plan hints.
Fix: Replace them with full, specific IDs that preserve the missing semantic parts.

- [ENGAGEMENT & TONE] [SEVERITY: minor]
Location: `В українській мові речення з цим сполучником мають дуже красиву інтонацію.` and `Цей новий текст має чудовий природний ритм. Він чудово показує причину, контраст і кінцевий результат.`
Issue: These lines are generic praise rather than instruction.
Fix: Replace them with more neutral, information-bearing wording.

## Verdict: REVISE
REVISE because the module contains two critical grammar-teaching errors and three malformed exercise placeholders. That fails the severity gate even though coverage and structure are otherwise solid.

<fixes>
- find: "You can start a sentence with «тому що» when directly answering a question, but you should avoid starting a sentence with «бо»."
  replace: "You can start a sentence with «тому що» when directly answering a question. In a longer complex sentence, «бо» usually stands at the start of the dependent clause, and it can also appear after the first word of that clause."
- find: "Важливо пам'ятати одну критичну річ про цю граматику. Студенти часто кажуть: «Хоча він втомився, але він працював». Для вашого рівня краще завжди уникати такої подвійної конструкції. Використовуйте у своєму реченні тільки один сполучник — або «хоча», або «але»."
  replace: "Важливо пам'ятати одну річ про цю граматику. Для рівня A2 найпростіше будувати речення без додаткового протиставного сполучника: «Хоча він втомився, він продовжив працювати». Водночас у реальних українських текстах трапляються й конструкції на зразок «Хоча він втомився, але він працював», тож це не граматична помилка, а стилістичний варіант."
- find: "It is important to remember one critical thing about this grammar. Students often say: \"Although he was tired, but he worked.\" For your level, it is better to always avoid such a double construction. Use only one conjunction in your sentence — either \"although\" or \"but\"."
  replace: "It is important to remember one thing about this grammar. At A2, the clearest default pattern is to build the sentence without an extra contrast conjunction: \"Although he was tired, he continued to work.\" At the same time, Ukrainian texts do also contain patterns like \"Although he was tired, but he worked\", so this is not a grammatical error but a stylistic variant."
- find: "<!-- INJECT_ACTIVITY: match-up-match-two-halves-of-sentences-with-with -->"
  replace: "<!-- INJECT_ACTIVITY: match-up-match-two-halves-of-sentences-prychyna-with-naslidok-dopust-with-rezultat -->"
- find: "<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-compound-sentences-with-and -->"
  replace: "<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-compound-sentences-with-tomu-shcho-bo-and-khocha -->"
- find: "<!-- INJECT_ACTIVITY: group-sort-sort-conjunctions-into-vs-vs -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort-sort-conjunctions-into-prychyna-vs-dopust-vs-protystavlennia -->"
- find: "В українській мові речення з цим сполучником мають дуже красиву інтонацію."
  replace: "В українській мові речення з цим сполучником мають характерну інтонацію."
- find: "Цей новий текст має чудовий природний ритм. Він чудово показує причину, контраст і кінцевий результат."
  replace: "Цей новий текст звучить природніше й чітко показує причину, контраст і кінцевий результат."
</fixes>