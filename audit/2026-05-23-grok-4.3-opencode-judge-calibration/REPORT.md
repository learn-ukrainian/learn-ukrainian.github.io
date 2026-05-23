# Grok 4.3 Russianism judge calibration — 2026-05-23 19:41 UTC

Model: `xai/grok-4.3` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **83.3%** |
| Precision (sev≥2) | 90.9% |
| Recall (sev≥2) | 62.5% |
| **F1 (sev≥2)** | **74.1%** |
| tp / fp / fn | 10 / 1 / 6 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **xai/grok-4.3** | **74%** | **91%** | **62%** | **83%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | issues_found | ✗ | 1 | 8.3 |
| `cal_clean_short_prose` | clean | clean | ✓ | 0 | 9.2 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 6.9 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 5.9 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 2 | 9.5 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 1 | 13.1 |
| `cal_dirty_workplace` | issues | issues_found | ✓ | 1 | 16.8 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 2 | 20.0 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 9.9 |
| `cal_debatable_next_steps` | issues | clean | ✗ | 0 | 11.8 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 10.7 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 12.2 |
