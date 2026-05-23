# Grok 4.3 Russianism judge calibration — 2026-05-23 18:28 UTC

Model: `openrouter/qwen/qwen3.7-max` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **66.7%** |
| Precision (sev≥2) | 100.0% |
| Recall (sev≥2) | 37.5% |
| **F1 (sev≥2)** | **54.5%** |
| tp / fp / fn | 6 / 0 / 10 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **openrouter/qwen/qwen3.7-max** | **55%** | **100%** | **38%** | **67%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | issues_found | ✗ | 0 | 12.0 |
| `cal_clean_short_prose` | clean | clean | ✓ | 0 | 5.8 |
| `cal_clean_travel` | clean | clean | ✓ | 0 | 7.1 |
| `cal_clean_workplace` | clean | clean | ✓ | 0 | 7.0 |
| `cal_dirty_email_calques` | issues | issues_found | ✓ | 2 | 9.4 |
| `cal_dirty_medical` | issues | issues_found | ✓ | 1 | 7.9 |
| `cal_dirty_workplace` | issues | clean | ✗ | 0 | 14.6 |
| `cal_dirty_meetup` | issues | issues_found | ✓ | 0 | 15.5 |
| `cal_dirty_register` | issues | issues_found | ✓ | 1 | 9.0 |
| `cal_debatable_next_steps` | issues | clean | ✗ | 0 | 9.3 |
| `cal_clean_with_lure` | clean | issues_found | ✗ | 0 | 12.1 |
| `cal_dirty_business_meeting` | issues | issues_found | ✓ | 2 | 12.4 |
