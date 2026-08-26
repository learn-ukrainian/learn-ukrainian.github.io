# OPERATOR ADDENDUM (read now — same PR)

Operator follow-up 2026-08-26: **also cover OpenRouter API and DeepSeek API prepaid/pay-as-you-go accounts, not subscriptions.**

These are **not** 5h/weekly/monthly allotment bars. They are **credit/balance** accounts.

## OpenRouter

- `GET https://openrouter.ai/api/v1/key` with `Authorization: Bearer $OPENROUTER_API_KEY` (inference key).
  Fields: `usage`, `usage_daily`, `usage_weekly`, `usage_monthly`, `limit`, `limit_remaining`, `limit_reset`.
- Optional `GET https://openrouter.ai/api/v1/credits` only if a management key is already in env (do not invent one). Remaining ≈ `total_credits - total_usage`.
- UI: remaining USD/credits + daily/weekly/monthly **usage** (not a fake % of a Cursor-style pool). `NEED_PROBE` if no key.

## DeepSeek (first-party `api.deepseek.com`, LOCAL-ONLY)

- `GET https://api.deepseek.com/user/balance` Bearer `$DEEPSEEK_API_KEY` (or the env the DeepSeek adapter already documents).
- Response: `is_available`, `balance_infos[].currency/total_balance/granted_balance/topped_up_balance`.
- UI: total balance + currency + available yes/no. Not a subscription %.

## Rules

- Keys **only** from env / existing opencode config. Never print or persist secrets. Never commit keys.
- Separate section on `/routing.html`: **API accounts** (openrouter, deepseek) vs **Subscriptions** (cursor/claude/…).
- Same 5–10 min cache, GET cache-only.
- Missing key → `NEED_PROBE`, never $0.
- Still no CodexBar subprocess.

Include both in this PR if you have not pushed yet.
