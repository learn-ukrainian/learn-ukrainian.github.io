Module,Score,Verdict,Deterministic Audit,Activity/Vocab Coverage,Ready Human Review?
M22 `parenthetical-expressions`,9/10,B+,PASS,10 workbook / 0 inline; 32 vocab,Yes
M23 `multi-clause-sentences`,9/10,B+,PASS,11 workbook / 0 inline; 30 vocab,Yes
M24 `kharchuvannia-i-kukhnia`,9/10,B+,PASS,11 workbook / 0 inline; 43 vocab,Yes
M25 `correlative-constructions`,9/10,B+,PASS,10 workbook / 0 inline; 35 vocab,Yes
M26 `emphasis-and-inversion`,9/10,B+,PASS,11 workbook / 0 inline; 38 vocab,Yes

Module,Notes
M22 `parenthetical-expressions`,Strong parenthetical-expression module with 99.9% immersion and 96% richness. Claude Opus 4.8 initially found two blockers; spelling and essay-answer length were fixed before merge, and follow-up review passed. Score held at 9 for non-blocking section-balance/recycling/advisory notes.
M23 `multi-clause-sentences`,Strong multi-clause syntax module with 100% immersion and 99% richness. Claude Opus 4.8 found no blockers; non-blocking notes were fixed before merge. Score held at 9 for conservative post-build polish risk and large style/editing section balance.
M24 `kharchuvannia-i-kukhnia`,Strong food and kitchen communication module with 99.9% immersion, 96% richness, 43 vocabulary items, and validated activity coverage. Claude Opus 4.8 review passed; score held at 9 for retained non-blocking section-balance warnings.
M25 `correlative-constructions`,Strong correlative-constructions module with 99.6% immersion and 99% richness. Claude Opus blocker review passed with no merge-blocking issues. Score held at 9 for minor deterministic advisory false positives around correlative forms.
M26 `emphasis-and-inversion`,Strong emphasis and inversion module with 100% immersion and 99% richness. Claude Opus read-only blocker review passed; non-blocking activity answer-key/correction-span nits were fixed before merge. Score held at 9 for residual section-balance/advisory notes.

Module,Raw Word Count,Activities,Vocabulary,Audit Words,Immersion,Richness
M22 `parenthetical-expressions`,5509,10 workbook / 0 inline,32,4927/4000,99.9%,96%
M23 `multi-clause-sentences`,5881,11 workbook / 0 inline,30,5640/4000,100.0%,99%
M24 `kharchuvannia-i-kukhnia`,4753,11 workbook / 0 inline,43,4191/4000,99.9%,96%
M25 `correlative-constructions`,4822,10 workbook / 0 inline,35,4360/4000,99.6%,99%
M26 `emphasis-and-inversion`,4633,11 workbook / 0 inline,38,4120/4000,100.0%,99%

Module,Reviewer,Result
M22 `parenthetical-expressions`,Claude Opus 4.8 blocker review + follow-up,Initial two blockers fixed; follow-up PASS with no unresolved blockers.
M23 `multi-clause-sentences`,Claude Opus 4.8 blocker review,PASS; no blockers. Non-blocking notes fixed before merge.
M24 `kharchuvannia-i-kukhnia`,Claude Opus 4.8 blocker review,PASS; no merge blockers.
M25 `correlative-constructions`,Claude Opus blocker review,PASS; no merge-blocking issues found.
M26 `emphasis-and-inversion`,Claude Code model alias `opus` read-only blocker review,PASS; no blockers. Non-blocking activity nits fixed before merge.

Module,PR,Merge Commit,Telemetry Run
M22 `parenthetical-expressions`,#3845,`a8b1ce10d1e274905e7634456d0364c07f0d2a36`,`b2-m22-parenthetical-expressions-pr3845`
M23 `multi-clause-sentences`,#3847,`fdfbcc526e5953963089a8d9b35256169e805682`,`b2-m23-multi-clause-sentences-pr3847`
M24 `kharchuvannia-i-kukhnia`,#3850,`58e69bb1e9d7645c30d517e1e30d78eab6fbf394`,`b2-m24-kharchuvannia-i-kukhnia-pr3850`
M25 `correlative-constructions`,#3853,`14d2e5ae4ad3108a2284b59e3b6514be45cd5a52`,`b2-correlative-constructions-codex-b2-m25-correlative-constructions-20260626`
M26 `emphasis-and-inversion`,#3854,`456f5307e81e9a6cf65ece9678607bdb7ad8692f`,`b2-emphasis-and-inversion-codex-b2-m26-emphasis-and-inversion-20260626`
