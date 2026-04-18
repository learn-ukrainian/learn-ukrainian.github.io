# Session Handoff — 2026-04-18 noon (post-/clear)

**You are starting cold. The user just `/clear`-ed.** This file is what `/api/session/current?format=markdown` serves; the boot flow below is the cheap path.

## Cold-start (do this FIRST, before anything else)

```bash
curl -s http://localhost:8765/api/state/manifest          # ~1 KB index, hashes
curl -s http://localhost:8765/api/rules?format=markdown   # only if rules.hash changed
curl -s http://localhost:8765/api/orient                  # always-fresh, per-section TTL
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
```

You're already reading `/api/session/current` — don't re-fetch unless the manifest hash differs from `2b9390f388…` (current as of writing). **Do NOT** read `CLAUDE.md`, `claude_extensions/rules/*.md`, or this file directly via the filesystem on cold start — those are the source of truth the endpoints serve, the API has hash-based 304 cache, and direct reads burn ~75 KB for ~778 B of warm-cache value.

## State of the world (as of 2026-04-18 12:16 CEST)

- **All work pushed.** `origin/main == HEAD`. 0 commits ahead. Working tree clean.
- **Monitor API stable.** Restart-loop fixed (`services.sh` had a race; flock-equivalent + port-free wait + bind check now in place). `/api/orient` cold call ≈ 480 ms. Validated under 6 parallel `restart api`.
- **No active background work.** No Codex workers running, no Gemini reviews in flight, Claude inbox empty.
- **Last live process check**: `api PID 15895` on port 8765 (uptime ~3 h since the last restart-loop bug recovery).

## What this session shipped (10 commits, all pushed)

| SHA | What | Why it matters |
|---|---|---|
| `3d95e30d4` | API stability — `services.sh` restart race + 7 s wiki orient → 19 ms | Fixed the user-reported "API is crashing" loop (623 restarts in `logs/api.log`) |
| `347686a2b` | `strip_meta` tempered repetition (#1323 round 2) | Resolves Gemini's PARTIAL on `f4c03c12d` — `[^<]*?` was too restrictive |
| `9ba22f571` | session-state log | — |
| `e44fc3711` | (Codex Phase C) Google Drive backup scripts | rclone v1.73.3 installed; **awaiting `rclone config`** |
| `9dbdfcaf1` | Gemini #1324 patches (5 fixes + 3 regression tests) | External corpus — fresh-clone bootstrap, 0-affinity exclusion, double-rank, dedup, FTS pool |
| `735f05987` | session-state log | — |
| `0dd764bd7` | Bridge `--stdout-only` delivery + `is_compiled` file-existence check | **The Phase A 0/9 root cause.** Bridge wasn't writing response to stdout; `is_compiled` ignored disk state. |
| `ef58e0a38` | session-state log | — |
| `4a0c77b55` | Working-tree sweep (192 files) — pipeline artifacts + `--auth` plumb-through | Folded in workflow files, curriculum dispatch jsons, fresh wiki articles, `--auth` flag wiring on `ask-gemini` (test was waiting on this) |
| (this) | Cold-start handoff | — |

Full back-context: `git log --oneline 21d9f4022..HEAD`.

## Open decisions (none in flight, all need user input)

| # | Decision | Default if unsaid |
|---|---|---|
| 1 | **Phase B kickoff?** Module builds via `v6_build.py`. Different pipeline from Phase A — could proceed without re-verifying Phase A. Conservative call: re-run Phase A on 2 slugs first. | Hold for explicit "go Phase B" or "rerun Phase A". |
| 2 | **Merge readiness on #1323 + #1324 round-2 patches?** Both have unit-tested fixes; Gemini hasn't seen the round-2 patches yet. Could queue another re-verify or call them shipped. | Wait for user call (Gemini-quota sensitive; spamming is rude). |
| 3 | **`rclone config` for Phase C activation.** Backup scripts are in place; rclone is installed; no Google Drive remote configured yet. | User must run `rclone config` themselves (OAuth needs browser). |
| 4 | **Watcher restoration?** `com.learn-ukrainian.agent-watcher` LaunchAgent unloaded this session (was respawning a moved script every 10 s for 3+ weeks). Plist backed up at `~/Library/LaunchAgents/com.learn-ukrainian.agent-watcher.plist.disabled-2026-04-18`. To restore, point its `ProgramArguments` at `scripts/tools/agent_watcher.py` and `launchctl bootstrap`. | Leave unloaded unless user wants auto-message-broker draining back. |

## Open coding issues (`gh issue list --state open --limit 5`)

| # | Title |
|---|---|
| 1324 | External articles corpus — re-chunk, enrich schema, MCP expose (5 patches landed; spec at `docs/architecture/external-corpus-spec.md`) |
| 1323 | Migrate wiki sources to sibling YAML files (3 patches landed; round-2 strip_meta patch landed) |
| 1322 | Convergent pipeline — replace heal loop, eliminate `needs-human-review.yaml` (Gemini-approved with patches) |
| 1319 | tooling: unify remaining audit-check sentence splitters to use `cleaners.split_sentences` |
| 1316 | fix(v6): early-literacy review calibration and invalid empty-findings gate |

`/api/issues/map` gives the full grouped view.

## Pipeline pulse

From `/api/orient.pipeline.summary`:
- a1: 33/55 content_done, 31/55 audit_passing, 39/55 reviewed
- a2: 2/69 content_done, 64/69 reviewed (research stage)
- b1: 0/94 content_done, 72/94 reviewed
- everything else (b2, c1+, seminar tracks): research not even started

## Gotchas you need to remember on this cold start

1. **The `_cli.py` `--auth` flag was WIP that I almost shipped twice.** Surfaced via the pre-commit pytest hook (`test_help_includes_model_and_deadline_flags` and `test_handle_ask_gemini_passes_auth_mode`). Now plumbed through `ask-gemini → ask_gemini() → process_and_respond() → runtime_invoke()`. The flag value space is `["auto", "subscription", "api-key", "api"]`.
2. **`is_compiled` semantics changed.** It now AND-checks the on-disk `.md` file. If you patch any code that calls it, do NOT add a separate file-existence check at the call site — the helper handles that already, and a redundant check would lie about state for stale rows that the helper would have purged.
3. **`--stdout-only` semantics clarified.** It now actually writes Gemini's response to stdout (was previously suppressing it AND polluting stdout with bridge progress logging). Wiki review pipeline depends on this. If you change the bridge, run the smoketest:
   ```bash
   printf 'Reply EXACTLY: PARSER_TEST_OK 9.5/10\n' | unset GEMINI_API_KEY GOOGLE_API_KEY && \
     .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini - \
       --task-id smoketest --model gemini-3.1-pro-preview --stdout-only --from claude
   ```
   stdout must contain Gemini's response and nothing else.
4. **`services.sh restart` is now serialized.** A `mkdir`-based lock at `.pids/.restart.lock.d/` prevents the parallel-restarter race that produced 623 wasted uvicorn spawns. If you see that lock dir lingering after a crash, it's safe to delete (the lock is reclaimed automatically when the holder PID is dead).
5. **Wiki was clean-slated on 2026-04-17** (commit `86e84b203`) — 558 articles deleted for full regeneration. 4 articles compiled this session via Phase A (the 4 seminar slugs). Everything else needs re-compile.
6. **Sibling sources YAML.** Wiki articles now live as `wiki/<domain>/<slug>.md` plus `wiki/<domain>/<slug>.sources.yaml`. The migration deleted the legacy `(Source N: ...)` citations from articles and replaced them with `[SN]` tags resolved against the sibling registry. Spec: `docs/architecture/sources-refactor-spec.md`.

## Recent handoff files (deeper context)

- `docs/session-state/2026-04-18-handoff.md` — earlier today's autonomous-plan setup (this file replaces it as the live handoff)
- `docs/session-state/writer-ab-test-plan.md`
- `docs/session-state/2026-04-14-handoff.md`
- `docs/session-state/2026-04-13-recovery-plan.md`

## If something looks wrong on cold start

- API not responding? `./services.sh status` then `./services.sh restart api` (now safe to spam thanks to the lock).
- Tests failing on a file you haven't touched? Don't fix them inline — they're likely the WIP from another worker. Stash + commit only files you authored.
- Stale agent-bridge inbox warnings (`codex has N pending deliveries (oldest XhYm)`)? Those are messages addressed TO codex/gemini, not for you to drain. Ignore on cold start.
