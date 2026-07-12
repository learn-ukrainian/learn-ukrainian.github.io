# Core semantic post-build review prompt

Semantic prompt version: `1.0.0`

Apply this only to A1-C2 core tracks, after the common prompt.

- Calibrate language, grammar scope, scaffolding, activity demand, and teaching
  sequence to the resolved CEFR level and module position.
- Preserve A1 English scaffolding. From A2 onward never recommend increasing
  English or lowering Ukrainian immersion; use the repository's current banded
  policy rather than remembered thresholds.
- Verify grammar explanations and examples against Ukrainian sources. Check
  agreement, government, aspect, case, word order, stress, and register where
  relevant.
- Evaluate whether examples precede abstraction, practice follows introduced
  material, and activities use only knowledge available to the learner.
- Compare plan objectives and required vocabulary with prose and activities,
  but do not invent hard counts or headings not supplied by current policy.
- Set `claim_coverage.status` to `not_applicable` unless the module makes
  factual claims that require explicit verification; then use `complete` or
  `incomplete` and report the counts.
