# Grok 4.3 Russianism judge calibration — 2026-05-23 19:07 UTC

Model: `openrouter/deepseek/deepseek-v4-pro` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **91.7%** |
| Precision (sev≥2) | 100.0% |
| Recall (sev≥2) | 62.5% |
| **F1 (sev≥2)** | **76.9%** |
| tp / fp / fn | 10 / 0 / 6 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **openrouter/deepseek/deepseek-v4-pro** | **77%** | **100%** | **62%** | **92%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | clean | ✓ | 0 | 27.1 |
| `cal_clean_short_prose` | clean | clean | ✓ | 0 | 47.2 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 36.0 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 32.1 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 3 | 68.5 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 1 | 138.4 |
| `cal_dirty_workplace` | issues | clean | ✗ | 0 | 69.1 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 1 | 42.1 |
| `cal_dirty_register` | issues | issues_found | ✓ | 2 | 61.0 |
| `cal_debatable_next_steps` | issues | issues_found | ✓ | 1 | 76.2 |
| `cal_clean_with_lure` | clean | clean | ✓ | 0 | 66.8 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 52.5 |
