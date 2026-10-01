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

The blind pool exposes only item IDs and text; chunk IDs, source identity and arm membership are kept in the separate sealed key. Do not infer usability from subject identity, title, grade, or another judge's decision. The two judges label the identical shuffled pool independently. The primary scoring rule is strict: a label is positive only when both judges say true. The sensitivity rule is lenient: a label is positive when either judge says true. Report Cohen's kappa for all three labels; if either decision label (`usable_quotation` or `usable_exercise`) is below 0.6, revise the rubric and relabel before drawing a conclusion.

## Anchored examples copied from real chunks

These brief excerpts are from redistributable school textbook chunks in the evaluation corpus. They illustrate the rubric only; judge the actual pooled chunk in context.

- Query: `коли пишемо апостроф`. Chunk `1-klas-bukvar-zaharijchuk-2025-2_s0068`, source `1-klas-bukvar-zaharijchuk-2025-2`: “Ось вона — твоя сім’я!” This is a usable quotation in its apostrophe-teaching passage: a short authentic sentence demonstrates the spelling before я in сім’я.
- Query: `коли пишемо апостроф`. Chunk `1-klas-bukvar-zaharijchuk-2025-2_s0096`, source `1-klas-bukvar-zaharijchuk-2025-2`: “Випиши з тексту п’ять слів з апострофом.” This is an exercise instruction, not a usable quotation: it gives no sentence demonstrating an apostrophe word. Mark `usable_quotation=false`.
- Same query and chunk: “Випиши з тексту п’ять слів з апострофом.” This is an example of an exercise stem; judge actual suitability against the A1–A2 adult learner rule, not the imperative alone.

The quoted strings above were copied from the identified live `textbooks` rows; only line wrapping is folded. They were not reconstructed or newly authored.

## Query re-freeze after branch review

G3-141 uses `коли слово змінюється` in place of temporal `при зміні слова`, following Антоненко-Давидович, «При чи за?», pp. 117–118 (style-guide entry and indexed book prose). VESUM attests all ten words of the revised query (`vesum:549b64685592733e140fa5e50ca35d29e388e4017bf7a43c007e84c972e4d193`). G3-136 is `term` because its string occurs verbatim in a corpus chunk. The re-frozen set has 144 queries: 131 paraphrase and 13 term.

G3-005 `представитися` is unchanged. The driver reported VESUM attestation, reconfirmed in this fix round; this round also checked Russian shadow (no match), the style-guide index (no result), and indexed «Як ми говоримо» prose (no result). The style-guide index is partial, and indexed-text absence is not a linguistic verdict.

G3 file SHA-256: `152391220a5db3fd7ad4b48795d47a844bd223ad912d87dcaf6e12f10764fa53`. This supersedes the v5 item 6 hash only for the two explicitly ordered edits; it does not authorize model compute.
