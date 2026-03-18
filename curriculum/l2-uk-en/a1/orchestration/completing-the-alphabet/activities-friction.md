**Phase**: Phase 3: Activities + Vocabulary
**Step**: watch-and-repeat item count + classify item count
**Friction Type**: PLAN_GAP
**Raw Error**: Plan requests 10 watch-and-repeat items but only 6 pronunciation videos exist (Ь, Ц, Ч, Щ, Ф, Ґ). Plan requests 8 classify items for Ь words but only 6 Ь-words appear in the lesson content (сіль, день, Львів, мідь, осінь, кінь).
**Self-Correction**: Used all available videos (6) for watch-and-repeat. Used all 6 Ь-words for classify. Both activities meet schema minimums (≥1 for watch-and-repeat, ≥1 per category for classify).
**Proposed Tooling Fix**: Update plan activity_hints to match available resources — watch-and-repeat: 6 items, classify (Ь): 6 items. Alternatively, the plan could add more Ь-words to the content (e.g., тінь, зелень, площадь) to increase classify items.