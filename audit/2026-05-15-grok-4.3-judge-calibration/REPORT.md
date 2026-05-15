# Grok 4.3 Russianism judge calibration — 2026-05-15 21:21 UTC

Model: `grok-4.3` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **75.0%** |
| Precision (sev≥2) | 80.0% |
| Recall (sev≥2) | 75.0% |
| **F1 (sev≥2)** | **77.4%** |
| tp / fp / fn | 12 / 3 / 4 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **grok-4.3** | **77%** | **80%** | **75%** | **75%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | clean | ✓ | 0 | 15.4 |
| `cal_clean_short_prose` | clean | issues_found | ✗ | 2 | 16.3 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 12.8 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 11.5 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 4 | 12.3 |
| `cal_dirty_medical` | issues | clean | ✗ | 0 | 18.0 |
| `cal_dirty_workplace` | issues | issues_found | ✓ | 3 | 20.5 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 2 | 28.5 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 17.4 |
| `cal_debatable_next_steps` | issues | clean | ✗ | 0 | 13.3 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 22.7 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 11.2 |
