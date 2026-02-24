**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Strictly avoided using forbidden activity types (select, translate, true-false are NOT listed in the allowed types prompt for a2 track constraints). Replaced them with allowed types (quiz, group-sort, match-up, fill-in) while maintaining the 12 activity density requirement. Carefully stripped all Ukrainian angular quotes «» from YAML values to prevent colons breaking the parser. Ensured cloze has exactly 10 blanks and unjumble words arrays contain only strings.
**Proposed Tooling Fix**: N/A