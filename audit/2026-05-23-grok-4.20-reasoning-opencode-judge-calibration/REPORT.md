# Grok 4.3 Russianism judge calibration — 2026-05-23 19:47 UTC

Model: `xai/grok-4.20-0309-reasoning` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **100.0%** |
| Precision (sev≥2) | 100.0% |
| Recall (sev≥2) | 75.0% |
| **F1 (sev≥2)** | **85.7%** |
| tp / fp / fn | 12 / 0 / 4 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **xai/grok-4.20-0309-reasoning** | **86%** | **100%** | **75%** | **100%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | clean | ✓ | 0 | 25.9 |
| `cal_clean_short_prose` | clean | clean | ✓ | 0 | 30.1 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 23.5 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 42.6 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 2 | 53.5 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 1 | 56.2 |
| `cal_dirty_workplace` | issues | issues_found | ✓ | 2 | 43.0 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 2 | 71.7 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 40.4 |
| `cal_debatable_next_steps` | issues | issues_found | ✓ | 1 | 43.9 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 46.7 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 27.6 |
