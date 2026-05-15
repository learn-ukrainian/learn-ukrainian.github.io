# Grok 4.3 Russianism judge calibration — 2026-05-15 21:25 UTC

Model: `grok-4.3` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **91.7%** |
| Precision (sev≥2) | 84.6% |
| Recall (sev≥2) | 68.8% |
| **F1 (sev≥2)** | **75.9%** |
| tp / fp / fn | 11 / 2 / 5 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **grok-4.3** | **76%** | **85%** | **69%** | **92%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | issues_found | ✗ | 1 | 29.2 |
| `cal_clean_short_prose` | clean | clean | ✓ | 0 | 6.8 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 7.7 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 8.6 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 2 | 21.4 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 1 | 25.6 |
| `cal_dirty_workplace` | issues | issues_found | ✓ | 1 | 34.5 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 2 | 15.6 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 22.1 |
| `cal_debatable_next_steps` | issues | issues_found | ✓ | 2 | 13.1 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 19.1 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 15.2 |
