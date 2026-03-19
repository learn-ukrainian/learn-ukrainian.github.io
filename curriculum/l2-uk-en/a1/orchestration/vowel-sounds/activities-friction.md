**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: PLAN_GAP
**Raw Error**: group-sort plan specifies 8 items but schema enforces minimum 10 total across groups. Initial generation included юшка in ONE-sound group (incorrect — юшка is word-initial Ю = 2 sounds) and село (has no iotated vowel at all). Caught during self-review.
**Self-Correction**: Moved юшка and їжа to TWO-sounds group (both are word-initial iotated vowels). Removed село entirely. Final split: 8 two-sound + 2 one-sound = 10 total.
**Proposed Tooling Fix**: Add a pre-generation check that compares plan item counts against schema minimums and flags mismatches before content generation begins.