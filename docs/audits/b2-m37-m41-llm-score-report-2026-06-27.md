Module,Score,Verdict,Deterministic Audit,Activity/Vocab Coverage,Ready Human Review?
M37 `register-business-ukrainian`,9/10,B+,PASS,10 workbook / 0 inline; 45 vocab,Yes
M38 `register-formal-written`,9/10,B+,PASS,10 workbook / 0 inline; 49 vocab,Yes
M39 `tradytsii-i-zvychai`,9/10,B+,PASS,10 workbook / 0 inline; 52 vocab,Yes
M40 `register-literary-ukrainian`,9/10,B+,PASS,16 workbook / 0 inline; 49 vocab,Yes
M41 `register-public-discourse`,9/10,B+,PASS,12 workbook / 0 inline; 49 vocab,Yes

Module,Notes
M37 `register-business-ukrainian`,Strong business Ukrainian register module 5217 raw words, 10 workbook activities, 45 vocabulary items, 99% richness. Agy/Gemini review passed no unresolved blockers. Score held at 9 for conservative post-build polish risk around dense business-register coverage.
M38 `register-formal-written`,Strong formal written register module 4059 raw words, 10 workbook activities, 49 vocabulary items, 99% richness. Agy/Gemini review passed no unresolved blockers. Score held at 9 for compact scope and non-blocking polish risk.
M39 `tradytsii-i-zvychai`,Strong traditions and customs communication module 4621 raw words, 10 workbook activities, 52 vocabulary items, 99% richness. Agy/Gemini review passed no unresolved blockers. Score held at 9 for cultural-density polish risk suitable for human review.
M40 `register-literary-ukrainian`,Strong literary-register module 6162 raw words, 16 workbook activities, 49 vocabulary items, 99% richness. Agy/Gemini blocker review passed 10/10 and style review scored 9.5 across dimensions. Score held at 9 for dense literary coverage and human-polish reserve.
M41 `register-public-discourse`,Strong public-discourse/media-register module 4240 raw words, 12 workbook activities, 49 vocabulary items, 99% richness. Agy/Gemini review found two wiki-authority issues; both were fixed and verification passed 10/10 with 0 unresolved findings. Style review scored 9.0 overall. Score held at 9 for remaining non-blocking UA-GEC advisory notes.

Token Telemetry,Status
M37-M41 module telemetry,persisted per module PR; M41 `b2-m41-pr3899` persisted with `status: merged`, `swarm_used: false`, `swarm_label: none`, and `token_source: unavailable`.

Independent Review Evidence,Scope
PR #3893,M37 Agy/Gemini independent review pass
PR #3895,M38 Agy/Gemini independent review pass
PR #3896,M39 Agy/Gemini independent review pass
PR #3898,M40 Agy/Gemini independent review pass; style score 9.5
PR #3899,M41 Agy/Gemini review/fix verification pass; style score 9.0
