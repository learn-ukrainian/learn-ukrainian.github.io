Module,Score,Verdict,Deterministic Audit,Activity/Vocab Coverage,Ready Human Review?
M58 `numeral-declension-time-dates`,9/10,B+,PASS,6 workbook / 5 inline; 40 vocab,Yes
M59 `numeral-declension-compound-numbers`,9/10,B+,PASS,5 workbook / 5 inline; 32 vocab,Yes

Module,Repair Score Notes
M58 `numeral-declension-time-dates`,Re-scored after PR #3988 learner-quality repair. The module now teaches time/date numeral forms with table-first scaffolding, decision rules, inline checks, and workbook consolidation instead of workbook-only practice. Hermes/DeepSeek v4 Pro independent review returned PASS / mergeable with only minor findings, all fixed before merge. Score remains 9/10 because the content is review-ready but dense numeral/date coverage still deserves human polish before release.
M59 `numeral-declension-compound-numbers`,Re-scored after PR #3988 learner-quality repair. The module now teaches compound, collective, and fractional numeral forms with table-first scaffolding, inline checks, and workbook consolidation. Normative instrumental forms for `вісімсот` are handled as `вісьмастами / вісьмомастами`, while `восьмистами` appears only as an error form. Hermes/DeepSeek v4 Pro independent review returned PASS / mergeable with only minor findings, all fixed before merge. Score remains 9/10 because the content is review-ready but dense numeral paradigms still deserve human polish before release.

Evidence,Result
Content repair PR,#3988 merged as `7db34d0526ae51958e0feceb0e59adfafbbc5f28`
External review,Hermes / DeepSeek v4 Pro PASS / mergeable; two minor findings fixed before merge
Local validation,M58/M59 MDX generation, activity validation, vocab validation, module audits, source markdownlint, git diff check, site build, and rendered-output smoke passed
Rendered-output smoke,No raw `**` and no `INJECT_ACTIVITY` on repaired B2 module routes
Scoring disposition,Keep both modules at 9/10 B+ and ready for human review; do not promote to A/A+ until human polish confirms learner experience
