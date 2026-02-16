**Phase**: Phase 6: Green Team Review
**Step**: Full review
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Identified that the LLM hallucinated IPA symbols using Cyrillic characters (e.g., 'л' instead of 'l'), which is a common failure pattern in some models.
**Proposed Tooling Fix**: Add an automated check to the audit script to detect Cyrillic characters inside IPA square brackets.
