# EPIC — Alignment-Pipeline Runtime Contracts

**Origin:** [`docs/architecture/2026-04-23-alignment-pipeline-audit.md`](../architecture/2026-04-23-alignment-pipeline-audit.md)
**Status:** open. Tracking GH issue: `#TBD` (set on creation).
**Gating relationship:** peer of EPIC #1365 (two-track build rollout). Cannot scale A1→C2 safely until this EPIC's Phase 0–2 land.

---

## Phase 0 — Land queued work (operational, no new issues)

- Merge open PRs in order: **#1448 → #1447 → #1442 → #1445 → #1443 / #1444 / #1446**. Rationale documented in 2026-04-23 afternoon handoff.
- Push diagnostic worktree branches and open review PRs:
  - `.worktrees/claude-1449-colors-dim-diagnostics` → PR closing #1449
  - `.worktrees/claude-1450-gemini-wiki-writer-diagnostic` → PR closing #1450
- Comment on supersede candidates: #1268, #1277, #1288, #1322 (all rewrite-block plumbing; outcome depends on Phase 2-C decision).
- Comment on #1434 with the #1450 Fix-1 brief; relabel dispatch-ready.
- Update `claude_extensions/rules/pipeline.md` to reflect `main`'s writer default (`claude-tools`). Deploy with `npm run claude:deploy`.
- Update `memory/MEMORY.md` with the two behavioral lessons from the audit §8.
- Autopsies: `docs/bug-autopsies/alignment-contracts.md` + 3 INDEX one-liners.

## Phase 1 — Runtime alignment contract (highest leverage)

| # | Title | Agent | Key files |
|---|---|---|---|
| P1-A | Alignment manifest hash contract — compose + stamp | Codex | `scripts/build/` (new `alignment_manifest.py`), callers |
| P1-B | Sidecar freshness invariant — refuse reuse on hash mismatch | Codex | `scripts/build/v6_build.py:3207`, `scripts/build/module_memory.py:293-316` |

**Exit criteria:** no phase consumes an artifact stamped with a stale hash. Unit tests prove mismatch → rebuild. Manifest includes: plan hash, sources hash, template hashes, canonical-anchor hash, tokenizer version, threshold snapshot, active decisions subset.

## Phase 2 — Collapse split-brain configuration

| # | Title | Agent | Key files |
|---|---|---|---|
| P2-A | Unify thresholds — single exported table | Codex | `scripts/audit/config.py`, `scripts/config.py`, `scripts/build/v6_build.py:112` |
| P2-B | Migrate wiki review to per-dim + MIN | Codex | `scripts/wiki/compile.py:623-639`, wiki review prompt |
| P2-C | Decision-vs-code parity — kill-or-revert rewrite strategies | Claude (decision) + Codex (code) | `docs/decisions/` (new ADR), `scripts/build/convergence_loop.py:595-607` |

**P2-C supersedes** #1268, #1277, #1288, #1322. One architectural decision closes four issues. Decision owner: human; drafted by Claude.

## Phase 3 — Pipeline + plan mechanism fixes (highest pedagogical impact)

| # | Title | Agent | Key files |
|---|---|---|---|
| **#1434** | Fix `_search_sections_fts5` missing `corpus` key — #1450 Fix 1 (existing issue, relabeled) | Codex | `scripts/wiki/sources_db.py:315-322` |
| P3-A | Fix `_extract_terms` + add Teacher-voice prompt anchor — #1449 §5.1 | Codex | `scripts/build/phases/plan_contract.py:42-51`, `v6-chunk-XX-prompt.md` template |
| P3-B | `dialogue_situations[].turns:` convention + render template + density audit — #1449 §5.2 (rolls in #1199) | Claude | `docs/best-practices/dialogue-situations.md`, `plans/a1/colors.yaml`, `scripts/audit/checks/dialogue_density.py` (new) |
| P3-C | `compiler._format_sources` — strip S-prefix, disambiguate chunk label — #1450 Fix 2a | Codex | `scripts/wiki/compiler.py:281-287` |

**P3-B rolls in** #1199 (B2+C1 plan regen — same `dialogue_situations` + budget class).

## Phase 4 — Invariant tests (turn classes of drift into CI failures)

| # | Title | Agent |
|---|---|---|
| P4-A | Citation resolution invariant — every `[S\d+]` resolves to `sources.db` | Codex |
| P4-B | Unicode round-trip golden corpus — extends #1448 tokenizer fix | Codex |
| P4-C | Post-processor mutation-class invariant — stress annotator may only add marks | Codex |
| P4-D | Plan immutability pre-commit hook — no in-place edit without `.bak` + version bump | Codex |
| P4-E | Rules deployment invariant — CI fails if `diff claude_extensions/rules/ .claude/rules/` non-empty | Codex |
| **#1351** | Rank-order test for pedagogical-grade retrieval — existing issue, already a Phase 4 fit | (existing) |

## Phase 5 — Resume delivery (only after Phase 0–4 stable)

1. Re-fire `a1/colors` after P3-A + P3-B land. Expected: MIN crosses 8 on Pedagogical + Engagement; ≤1 R2 correction pass.
2. Second vertical slice: `i-want-i-can` (dialogue-heavy; stresses P3-B).
3. Scale-lock cadence on remaining A1 slugs: no module ships that didn't consume an alignment manifest.

---

## Dedup map (existing issues)

| Existing | Disposition |
|---|---|
| #1434 | **Active** — dispatch with #1450 Fix-1 brief (Phase 3) |
| #1199 | **Roll into P3-B** — same `dialogue_situations` + word-budget class |
| #1351 | **Link as P4 candidate** — already an invariant test |
| #1268 | **Comment + supersede-pending-P2C** — rewrite-block plumbing |
| #1277 | **Comment + supersede-pending-P2C** — rewrite-block plumbing |
| #1288 | **Comment + supersede-pending-P2C** — rewrite-block plumbing |
| #1322 | **Comment + supersede-pending-P2C** — rewrite-block plumbing |
| #1395 | Unrelated — stale-worktree operator endpoint |
| #1398 | Unrelated — Gemini `--effort` wiring |
| #1365 EPIC | **Peer/gating** — add cross-link |

## Ordering rationale

- **Phase 0 before everything.** The 7 queued PRs are prerequisites; the tokenizer fix (#1448) in particular is load-bearing for any alignment verification.
- **Phase 1 before Phase 3.** P1-A + P1-B prevent Phase 3 fixes from being masked by stale sidecars on `a1/colors` rebuild.
- **Phase 2-C decision before Phase 4-E.** Kill-or-revert the rewrite contradiction before adding a CI test that enforces decisions — otherwise the test would fire on merge day one.
- **Phase 3 in parallel with Phase 4.** Once Phase 1 is green, P3 (mechanism fixes) and P4 (invariants) are independent and can dispatch concurrently.
- **Phase 5 resumes delivery.** No scale-lock or new module build until Phase 0–2 are green.

## Cost estimate

| Phase | Effort | Owner |
|---|---|---|
| 0 | ~1 h operational | User (merges), Claude (pushes + comments) |
| 1 | 2–3 days | Codex |
| 2 | 2 days | Codex + Claude (decision) |
| 3 | 2 days | Codex + Claude |
| 4 | 2 days | Codex |
| 5 | ongoing | Claude orchestrator |

Total: ~9 working days to full runtime-contract discipline, after which module scale-lock resumes on a safer basis.
