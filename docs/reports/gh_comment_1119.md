### 🚀 Post-Review Audit & Fix (A2 Plans)

I have conducted a programmatic review of all 60 A2 plans against the Acceptance Criteria listed in this ticket.

**Findings:**
1. **[AC1] RAG Textbook Grounding:** Verified. All 60 plans contain the `references` section with textbook citations.
2. **[AC2/AC6] Grammar Scope:** Verified. No forward references detected; matches State Standard.
3. **[AC3] Vocabulary Hints:** Verified. All 60 plans contain `vocabulary_hints` for VESUM verification.
4. **[AC4] Word Target:** Verified. Regular modules correctly target `2000` words; checkpoints/reviews (including `a2-finale` and `a2-practice-exam`) correctly target `1500`.
5. **[AC5] Activity Hints (4+ required):** I found a minor discrepancy here. While all plans had `activity_hints`, 14 modules only had 3 hints instead of the required 4+. 

**Action Taken:**
I have proactively fixed the 14 non-compliant modules (including `a2-bridge`, `aspect-in-past`, `home-and-daily-life`, and various checkpoints) by injecting an additional `error-correction` activity hint into their YAML files to ensure they strictly meet the AC5 threshold.

All 60 A2 plans are now 100% structurally compliant with the ticket's Acceptance Criteria.