Module,Score,Verdict,Deterministic Audit,Activity/Vocab Coverage,Ready Human Review?
M27 `stylistic-connectors`,9/10,B+,PASS,10 workbook / 0 inline; 32 vocab,Yes
M28 `kupivlia-i-servisy`,9/10,B+,PASS,10 workbook / 0 inline; 46 vocab,Yes
M29 `complex-syntax-ellipsis-parcelling`,9/10,B+,PASS,10 workbook / 0 inline; 45 vocab,Yes
M30 `direct-indirect-speech`,9/10,B+,PASS,12 workbook / 0 inline; 46 vocab,Yes
M31 `checkpoint-syntax-ii`,9/10,B+,PASS,20 workbook / 0 inline; 35 vocab,Yes

Module,Notes
M27 `stylistic-connectors`,Strong stylistic-connectors module with validated activity coverage and 100.0% immersion. Initial independent blockers were fixed before merge; final Agy/Gemini review passed. Score held at 9 for conservative post-fix polish risk and the 32/35 vocabulary soft-target note.
M28 `kupivlia-i-servisy`,Strong shopping/services communication module with 5787/4000 audit words, 46 vocabulary items, and validated consumer-service practice. Initial Agy/Gemini blocker was fixed; follow-up review passed. Score held at 9 for conservative post-build polish risk.
M29 `complex-syntax-ellipsis-parcelling`,Strong ellipsis/parcelling module with 4283/4000 audit words, 100.0% immersion, and 99% richness. Agy/Claude Opus blocker review passed with no unresolved findings. Score held at 9 for conservative advanced-syntax polish risk.
M30 `direct-indirect-speech`,Strong direct/indirect speech module with 12 workbook activities, 46 vocabulary items, and 96% richness. Agy/Claude Opus blocker review passed with no unresolved findings. Score held at 9 for conservative punctuation/transformation polish risk.
M31 `checkpoint-syntax-ii`,Strong Syntax II checkpoint with broad review coverage, 20 workbook activities, 6995/4000 audit words, and 99.9% immersion. Agy/Claude Opus review passed with no unresolved findings. Score held at 9 for checkpoint size and minor non-blocking notes.

Module,Raw Word Count,Activities,Vocabulary,Audit Words,Immersion,Richness
M27 `stylistic-connectors`,5212,10 workbook / 0 inline,32,4880/4000,100.0%,99%
M28 `kupivlia-i-servisy`,6004,10 workbook / 0 inline,46,5787/4000,100.0%,97%
M29 `complex-syntax-ellipsis-parcelling`,4686,10 workbook / 0 inline,45,4283/4000,100.0%,99%
M30 `direct-indirect-speech`,4683,12 workbook / 0 inline,46,4131/4000,100.0%,96%
M31 `checkpoint-syntax-ii`,7247,20 workbook / 0 inline,35,6995/4000,99.9%,99%

Module,Reviewer,Result
M27 `stylistic-connectors`,Agy -> Claude Opus 4.6 initial review; Agy -> Gemini 3.1 Pro High final review,Initial two blockers fixed before merge; final PASS no unresolved blockers.
M28 `kupivlia-i-servisy`,Agy -> Gemini 3.1 Pro High initial and follow-up review,Initial one blocker fixed before merge; follow-up PASS no unresolved blockers.
M29 `complex-syntax-ellipsis-parcelling`,Agy -> Claude Opus 4.6 Thinking blocker review,PASS; no unresolved findings.
M30 `direct-indirect-speech`,Agy -> Claude Opus 4.6 Thinking blocker review,PASS; no unresolved findings.
M31 `checkpoint-syntax-ii`,Agy -> Claude Opus 4.6 Thinking blocker review,PASS; no unresolved findings.

Module,PR,Merge Commit,Telemetry Run
M27 `stylistic-connectors`,#3861,`603c49861af56d8d813d79f4d1e1747a6f58060b`,`b2-stylistic-connectors-codex-b2-m27-stylistic-connectors-20260626`
M28 `kupivlia-i-servisy`,#3862,`6836ffd7e38b96506f6dd986b7ffae8e5e489236`,`b2-kupivlia-i-servisy-codex-b2-m28-kupivlia-i-servisy-20260626`
M29 `complex-syntax-ellipsis-parcelling`,#3863,`56c98bdc2a473ee626e425a33f160bb63e0933ad`,`b2-complex-syntax-ellipsis-parcelling-codex-b2-m29-ellipsis-parcelling-20260626`
M30 `direct-indirect-speech`,#3864,`844928f4e75fbec3e54f5c3ee551c987d2290e60`,`b2-direct-indirect-speech-codex-b2-m30-direct-indirect-speech-20260626`
M31 `checkpoint-syntax-ii`,#3865,`c664961c01c22ce0a0c36a1cc1196d77f311dd70`,`b2-checkpoint-syntax-ii-codex-b2-m31-checkpoint-syntax-ii-20260626`
