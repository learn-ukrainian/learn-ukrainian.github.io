# Grok 4.3 Russianism judge calibration — 2026-05-15 21:44 UTC

Model: `grok-4.3` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **75.0%** |
| Precision (sev≥2) | 90.0% |
| Recall (sev≥2) | 56.2% |
| **F1 (sev≥2)** | **69.2%** |
| tp / fp / fn | 9 / 1 / 7 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **grok-4.3** | **69%** | **90%** | **56%** | **75%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | clean | ✓ | 0 | 14.2 |
| `cal_clean_short_prose` | clean | issues_found | ✗ | 1 | 25.2 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 10.3 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 8.5 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 2 | 39.9 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 2 | 30.6 |
| `cal_dirty_workplace` | issues | clean | ✗ | 0 | 20.0 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 1 | 14.1 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 12.2 |
| `cal_debatable_next_steps` | issues | clean | ✗ | 0 | 16.6 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 19.3 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 11.5 |
