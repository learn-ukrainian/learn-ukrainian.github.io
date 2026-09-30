# #9233 retrieval judging rubric

## Frozen v5 rubric

usable quotation = an authentic Ukrainian sentence or short passage a lesson can quote to show the point (not a bare definition, not archaic literary syntax); usable exercise = a task whose stems an A1–A2 adult learner could do after light adaptation (not native-L1 parsing drills). Primers: a sentence counts only if it shows the queried point, not merely contains a matching word. School `ukrmova` (grades 5–11, L1): rules and examples count, L1-only analysis drills do not. ULP bilingual notes: judged on their Ukrainian items; English explanation alone is not a quotation.

## Label schema and judge instructions

For every supplied `(query_id, item_id)`, return exactly one JSON object with these fields:

```json
{
  "query_id": "G3-001",
  "item_id": "the item_id from the blind pool",
  "usable_quotation": false,
  "usable_exercise": true,
  "usable_example": false,
  "reason": "One short sentence tied to the queried point and the chunk."
}
```

Use JSON booleans. Give a single-line reason. Judge only the query and Ukrainian chunk text supplied in the blind file. Do not search sources or infer an arm. Evaluate each label independently:

- `usable_quotation`: apply the frozen quotation rule above.
- `usable_exercise`: apply the frozen exercise rule above.
- `usable_example`: mark true only when the chunk gives an authentic example that directly demonstrates the queried point; a matching word without demonstration is false.

Do not infer usability from subject identity, title, grade, or another judge's decision. The two judges label the identical shuffled pool independently. The primary scoring rule is strict: a label is positive only when both judges say true. The sensitivity rule is lenient: a label is positive when either judge says true. Report Cohen's kappa per label; if either is below 0.6, revise the rubric and relabel before drawing a conclusion.

## Anchored examples copied from real chunks

These brief excerpts are from redistributable school textbook chunks in the evaluation corpus. They illustrate the rubric only; judge the actual pooled chunk in context.

- Query: `коли пишемо апостроф`. Chunk `1-klas-bukvar-zaharijchuk-2025-2_s0096`, source `1-klas-bukvar-zaharijchuk-2025-2`: “Спостерігай за вимовою приголосних звуків перед я, ю, є, ї.” This is an example of a quotation that directly shows the queried point.
- Same query and chunk: “Випиши з тексту п’ять слів з апострофом.” This is an example of an exercise stem; judge actual suitability against the A1–A2 adult learner rule, not the imperative alone.

The quoted strings above were copied from the corresponding live `textbooks` row (`title=Сторінка 99`). They were not reconstructed or newly authored.
