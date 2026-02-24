**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Strictly avoided types `true-false`, `group-sort`, and `select` as the prompt template specifically constrained the allowed types to `quiz, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction`. Successfully reformatted target concepts into these allowed types to meet the 10 activities requirement. Ensured `quiz` options matched schema format strictly and `explanation` resided on the `question` level. Handled `error-correction` with all required properties.
**Proposed Tooling Fix**: N/A