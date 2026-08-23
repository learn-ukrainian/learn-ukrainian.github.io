# Fleet agent eyes

**Status:** CTO LOCKED 2026-08-23  
**Audience:** Watch Desk, SRE hosts, CTO, ITSEC  
**Scope:** Token-cheap fleet session awareness. Public repo only — no infra IPs, SSH hosts, or private topology.

This charter is the standing watch order. It does not authorize new architecture, a new control plane, or loading raw session bodies into watcher models.

## Purpose

Keep a human or coordinator seat aware of live fleet work without spending frontier tokens on raw Codex/Claude/Gemini rollouts. Authoritative state stays where it already lives: Monitor leases, GitHub, Fleet Comms, and the body-free Entire projection. Shell digests are a cheap tail, not a memory system.

## Ladder (use in this order)

1. **Monitor / leases** — occupancy, observer presence, and lease rows. Live work is what Monitor says is live.
2. **GitHub + Fleet pulses** — issues, PRs, CI, and Fleet Comms receipts. Disposition and review state are here.
3. **Entire (non-authoritative, ADR-018)** — first `GET /api/ops/entire-context/status` and `GET /api/ops/entire-context/search` on Monitor, then the local `entire_context` CLI (`status`, one bounded `search`). Native Entire only after a green private preflight. Never `--raw-transcript`. Entire locates; it does not own task state.
4. **Shell digests** — `scripts/ops/digest_codex_rollout.py` keyword extract from jsonl tails. No LLM.
5. **Screen last** — attach to a live terminal only when the four cheaper rungs are insufficient.

Do not skip to a lower rung because a higher rung is quieter than expected. Absence of a pulse is not proof of idle.

## Hard rules

- **Never load raw rollouts into watcher models.** Tails stay on disk; models see the keyword digest or a verified Entire locator, not `rollout-*.jsonl`.
- **Entire-before-digest.** Run ladder step 3 before step 4 on any non-trivial watch. Digest is the fallback when Entire/Monitor already said the cheap facts.
- **No Grok Bot full-session ingest.** Grok Bot is coordinator / external QA observer only. It must not be fed full session transcripts, rollout files, or digest dumps as a standing corpus.
- **Standing watches live on Watch Desk.** Heavy AI stays on VPS / Codex / substitute implement seats. The coordinator does not become a second orchestrator by ingesting sessions.
- **OPSEC.** Public tree and public PRs contain no host coordinates, SSH aliases, raw IPs, or private topology. Local digest files are gitignored artifacts.

## Owners

| Role | Owns |
| --- | --- |
| **Watch Desk** | Standing watches. Reads Monitor, pulses, Entire locators, then digests. Does not ingest raw rollouts. |
| **SRE** | Runs the digester on hosts. Env, cron/systemd (or equivalent), disk hygiene for `logs/agent-digests/`. |
| **CTO** | This script and this charter. Changes require a new lock, not a silent edit. |
| **ITSEC** | OPSEC: no IPs, SSH hosts, private topology, or session-body export into public or watcher-model context. |

## Shell digest

Keyword extract only. No LLM. Runnable as a script:

```bash
DIGEST_LABEL=local \
DIGEST_REPO="$HOME/projects/learn-ukrainian" \
python3 scripts/ops/digest_codex_rollout.py
```

| Env | Default |
| --- | --- |
| `DIGEST_LABEL` | `local` |
| `DIGEST_ROOTS` | `~/.codex/sessions:~/.claude/projects:~/.gemini/tmp:~/.config/gemini` |
| `DIGEST_REPO` | `~/projects/learn-ukrainian` |
| `DIGEST_MAX` | `12` |

Behavior: glob `**/rollout-*.jsonl` and `**/*.jsonl`, sort mtime newest first (rollout name is tie-break only — do not rank an old Codex rollout over a newer Claude/other jsonl), tail last 500 lines, keep material keywords, drop AGENTS.md / cold_start / rules-load noise, write `logs/agent-digests/<label>-latest.md`, refresh `logs/agent-digests/index.md`, print the output path plus `bytes= sources= label=`.

Those files are local artifacts. They are gitignored and must not be committed.

## Acceptance checklist

Use this before calling a watch or a digest change done:

- [ ] Digest is keyword extract only (no LLM, no raw-rollout paste into a watcher model).
- [ ] `logs/agent-digests/` remains untracked; script and this charter stay tracked.
- [ ] Output contains no infra IPs, SSH hosts, or private topology.
- [ ] Entire-before-digest: Monitor `/api/ops/entire-context` and `entire_context` CLI were consulted before the shell digest on a non-trivial watch.
- [ ] Native Entire, if used, followed the private preflight; `--raw-transcript` was not used; ADR-018 remains non-authoritative.
- [ ] Grok Bot did not ingest a full session, rollout, or digest corpus. It coordinates only.
- [ ] Standing watch is on Watch Desk; heavy generation/review stayed on VPS / Codex / substitute seats.

## Non-goals

- Not a Foundry, Sources, occupancy, or private-infra change.
- Not a replacement for Monitor leases, Fleet Comms, GitHub, or formal review.
- Not Entire-as-memory and not a public checkpoint export.
- Not permission to wire Grok Bot (or any watcher model) to session tails.
