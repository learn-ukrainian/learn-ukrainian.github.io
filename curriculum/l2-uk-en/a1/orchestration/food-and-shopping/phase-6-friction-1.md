**Phase**: Phase 6: Green Team Review
**Step**: Reviewing Vocabulary YAML vs Content
**Friction Type**: INCONSISTENCY
**Raw Error**: Vocabulary file had 20 items, content taught ~35 items.
**Self-Correction**: Manually listed missing items in the review.
**Proposed Tooling Fix**: A script to cross-check bolded Ukrainian words in `.md` against `lemma` fields in `vocabulary/*.yaml` would catch this automatically.
