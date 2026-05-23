# Grok 4.3 Russianism judge calibration — 2026-05-23 20:47 UTC

Model: `composer-2.5` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **66.7%** |
| Precision (sev≥2) | 66.7% |
| Recall (sev≥2) | 75.0% |
| **F1 (sev≥2)** | **70.6%** |
| tp / fp / fn | 12 / 6 / 4 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **composer-2.5** | **71%** | **67%** | **75%** | **67%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | issues_found | ✗ | 1 | 56.0 |
| `cal_clean_short_prose` | clean | issues_found | ✗ | 1 | 39.5 |
| `cal_clean_travel` | clean | issues_found | ✗ | 1 | 44.1 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 35.7 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 3 | 54.5 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 2 | 92.7 |
| `cal_dirty_workplace` | issues | json_parse_error | ✓ | 0 | 49.9 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 2 | 37.0 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 43.1 |
| `cal_debatable_next_steps` | issues | issues_found | ✓ | 1 | 56.4 |
| `cal_clean_with_lure` | clean | issues_found | ✗ | 1 | 82.2 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 4 | 101.8 |
