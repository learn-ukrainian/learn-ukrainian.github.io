# Grok 4.3 Russianism judge calibration — 2026-05-23 19:40 UTC

Model: `xai/grok-4.20-multi-agent-0309` via Hermes OAuth (`api.x.ai/v1`)
Cases: 12 (from `eval/russianism/calibration-cases.jsonl` on `origin/pr-2006`)

## Aggregate

| Metric | Value |
|---|---:|
| Case accuracy | **58.3%** |
| Precision (sev≥2) | 0.0% |
| Recall (sev≥2) | 0.0% |
| **F1 (sev≥2)** | **0.0%** |
| tp / fp / fn | 0 / 0 / 16 |

## Reference leaderboard (2026-05-15, n=12)

| Judge | F1 | Precision | Recall | Case acc |
|---|---:|---:|---:|---:|
| claude-opus-4-7 | 86% | 79% | 94% | 100% |
| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |
| gpt-5.5 | 78% | 90% | 69% | 83% |
| **xai/grok-4.20-multi-agent-0309** | **0%** | **0%** | **0%** | **58%** |

Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `origin/pr-2006` for the prior 3 judges.

## Per-case breakdown

| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |
|---|---|---|:---:|---:|---:|
| `cal_clean_greeting` | clean | judge_error | ✗ | 0 | 2.2 |
| `cal_clean_short_prose` | clean | judge_error | ✗ | 0 | 2.2 |
| `cal_clean_travel` | clean | judge_error | ✗ | 0 | 2.1 |
| `cal_clean_workplace` | clean | judge_error | ✗ | 0 | 2.3 |
| `cal_dirty_email_calques` | issues | judge_error | ✓ | 0 | 2.3 |
| `cal_dirty_medical` | issues | judge_error | ✓ | 0 | 2.6 |
| `cal_dirty_workplace` | issues | judge_error | ✓ | 0 | 2.3 |
| `cal_dirty_meetup` | issues | judge_error | ✓ | 0 | 2.2 |
| `cal_dirty_register` | issues | judge_error | ✓ | 0 | 2.3 |
| `cal_debatable_next_steps` | issues | judge_error | ✓ | 0 | 2.3 |
| `cal_clean_with_lure` | clean | judge_error | ✗ | 0 | 2.2 |
| `cal_dirty_business_meeting` | issues | judge_error | ✓ | 0 | 2.2 |
