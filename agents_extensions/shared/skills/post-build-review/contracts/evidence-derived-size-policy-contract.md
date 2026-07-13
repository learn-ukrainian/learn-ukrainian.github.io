# Evidence-derived size-policy contract

Size-policy contract version: `1.1.0`

Consume the existing structured record from
`scripts/audit/module_size_policy_audit.py` and the implementation in
`scripts/build/module_size_policy.py`. Do not duplicate density thresholds in
prompts, track policy, or this contract.

- `word_target` and a valid reviewed `size_policy.floor_words` are deterministic
  floors, not targets to pad toward with unsupported material.
- Enforce floors against authored instructional/expository words. Report
  learner-visible words, quoted primary-source words, excluded markup/directive/
  URL tokens, and the legacy raw whitespace-token count separately. Heading
  text is learner-visible; it is authored outside primary-reading blocks and
  quoted inside them. Markdown markers are not words.
- The recommended range and advisory ceiling express evidence/pedagogical
  pressure. Crossing the ceiling triggers semantic inspection; it is not an
  automatic fail.
- Source-backed density and necessary pedagogy are acceptable. Repeated framing,
  generic exposition, uncited interpretation, and inflated transitions are
  padding evidence.
- Detect repetition only in authored prose paragraphs of at least 40 lexical
  words. Exclude primary-reading blocks, blockquotes, fenced examples, list/
  table activity boilerplate, activity sections, and short recaps. Normalize
  Unicode/case, build five-word shingle sets, and report a pair when it shares
  at least eight shingles and either Jaccard similarity is at least `0.55` or
  shorter-paragraph containment is at least `0.82` with length ratio at least
  `0.70`. Every finding records both line ranges, headings, scores, and shared
  text; source order and fixed score rounding make serialization deterministic.
- If grounded material runs out before the floor, surface a plan-policy mismatch
  instead of inventing depth. `SIZE_POLICY_MISMATCH` never waives the floor; it
  stops automatic expansion and routes the plan to versioned plan review.
- Invalid reviewed policy or missing required dossier evidence blocks automatic
  expansion.
- Sparse dossier classification is not proof of padding, but unsupported sparse
  material cannot trigger automatic expansion. Exceeding an advisory ceiling is
  review information, never an automatic failure.

Oleksandr Bilash is the first exemplar only. Its current range, ceiling,
headings, evidence density, and conclusion belong to its plan/result fixture,
not to BIO or seminar defaults.
