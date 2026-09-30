# Usage probe recordings

Recorded 2026-09-30T07:33:16.877869Z directly from the existing native probes' credential sources.
These are allowlisted quota projections of provider responses, not hand-authored
formatter snapshots. Account identifiers, credit IDs, descriptions, CLI text,
and credential material were excluded before persistence. No reset was redeemed.

Reference: [CodexBar v0.69.0](https://github.com/steipete/CodexBar/tree/48ded68da6932a4fe5de9037d06c4ac48bd36e90).

- `codex.json`: GET `/backend-api/wham/usage`; `credits.balance` and rate windows.
- `codex_resets.json`: GET `/backend-api/wham/rate-limit-reset-credits`;
  `available_count`, `credits[].status` and `expires_at`. See
  `Sources/CodexBarCore/Providers/Codex/CodexOAuth/CodexOAuthUsageFetcher.swift`
  and `Sources/CodexBarCore/CreditsModels.swift` for expiry filtering.
- `claude.json`: GET `/api/oauth/usage`; scoped `limits[]` with
  `kind=weekly_scoped`, `group=weekly`, `percent`, `resets_at`, and
  `scope.model.display_name=Fable`. See `ClaudeScopedWeeklyLimitMapper.swift`.
- `agy.json`: native `/usage` command; `command.data.groups[]`, separate
  Gemini and Claude/GPT groups, `buckets[].window`, `remaining_fraction`, and
  `reset_time`. See `AntigravityStatusProbe.swift`.

Tests freeze observation time and derive zero, missing, expired and malformed
cases from these recordings. Those mutations are synthetic edge cases.
