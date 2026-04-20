# Session Handoff — 2026-04-20 08:45 local (post-#1340-close, pre-Codex-thermal-dispatch)

User requested handoff before dispatching Codex on #1363. Good time — current state is clean (no in-flight commits, no running processes, all decisions captured), and the next discrete action is a single dispatch the next session can fire in one command.

## TL;DR — what to do on pick-up

One command to run, then watch:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Implement #1363 per the convergent design in the issue body. \
   Architecture is locked by tri-agent discussion 7282658d2584 — \
   do NOT redesign. Single commit, --mode danger, reference issue." \
  --task-id issue-1363 --mode danger
```

That's it. Codex turnaround ~1-2h. While Codex works, decide whether to **resume cold encode now (without thermal awareness, machine stays warm)** or **wait for #1363 to ship and resume with thermal protection**. My recommendation in the previous round was wait — see "Cold encode" section below.

## What landed this session

### Closed: #1340 (`refactor(wiki): drop hard CEFR-grade filter + tighten diagnostic`)

Two commits, one closed issue, one ADR.

| Commit | What |
|---|---|
| `ae56349e9` | Removed `_TRACK_GRADE_RANGES` from `scripts/wiki/sources_db.py` (2 call sites + dict). Rewrote `scripts/wiki/diagnostics/retrieval_playback.py`: OCR soft-hyphen normalization, token-set `{"all_of": [...]}` matcher, pre-normalized variants, scaled PASS threshold. Updated 3 test files to assert the new architecture. |
| `2c0b8ab30` | Codex adversarial-review fixes: centralized threshold semantics (`PASS_THRESHOLD` for bake-off + `VERDICT_BOTTLENECK_THRESHOLD` for diagnosis, both scaled), narrowed `milozvuchnist` → `milozvuchnist_v_to_w_gloss` (was being satisfied by Grade 10 §23 stylistics — exact scope leak), deleted dead `any_of_groups` doc, promoted track→grade decision to **ADR-007** (`docs/architecture/adr/adr-007-no-hard-grade-filter-for-cefr-retrieval.md`). |

Empirical impact (a1/sounds-letters-and-hello playback):

| State | Modern coverage | Verdict |
|---|---|---|
| Pre-#1340 | 3/10 | retrieval_bottleneck |
| Post-#1340 + Codex fixes | 7/9 (≈78%, threshold 8/9 ≈89%) | writer_bottleneck |

47/47 wiki tests pass. Ruff clean.

### New issues filed

- **#1350** — Bright Kids YT ingestion + listening-anchor schema (deferred). User has free-tier ULP YT (already ingested via closed #1151) and free Bright Kids YT (NOT ingested — channel handle pending). User has commercial ULP PDFs (link-only).
- **#1351** — Rank-order regression test for pedagogical-grade-appropriate retrieval. Codex's architectural finding: current diagnostic treats Grade 9/10 chunks as A1 wins; need a primer-vs-theory rank-order metric. ADR-007 forbids re-introducing the hard SQL gate, so the fix has to be a soft prior at rerank time.
- **#1363** — **Thermal-aware MLX encoding** (this session's open task). Convergent design from tri-agent thread `7282658d2584`. Ready to dispatch Codex.

## #1363 context (read before dispatching)

User question: "can we make this process cpu heat aware? macbook air has no cooling." User explicitly wanted **smart not reactive** — find balance between progress and cooling. Asked for input from others ("maybe others have some idea as well").

I ran `ab discuss architecture` with claude+gemini+codex, max 2 rounds. **Both Gemini and Codex ended at `[AGREE]`** on the design captured in the #1363 issue body. (My local Claude bot failed with a CLI parse error mid-discussion — bridge bug, doesn't affect substance; Gemini and Codex covered the ground.)

**Key design decisions (locked, do not redesign):**

| Question | Answer | Why |
|---|---|---|
| Primary thermal signal | `NSProcessInfo.processInfo.thermalState` via Python `ctypes` → Objective-C runtime | Zero deps, no sudo, no Swift shim |
| Control point | Micro-batch loop in `dense_rerank.py:227-246`, NOT shard loop | Shards too coarse — `plan_shard_groups` can yield one giant shard |
| Backoff trigger | `Serious`/`Critical` only (NOT `Fair`) OR sustained ms/token regression | Apple Silicon runs `Fair` as normal operating state |
| Batch-size modulation | Drop. Sleep-only modulation. | `_sorted_token_batches` pre-computes the entire batch plan; resizing mid-shard requires re-planning, not worth complexity |
| Telemetry | Per-epoch JSONL: `{rows, tokens, encode_s, ms_per_token, tier, thermal_state, sleep_s}`. Normalize by tokens, not rows. | Current shard-boundary events too coarse to tune; row-normalized would misread long texts as thermal slowdowns |
| State persistence | None (`--resume` already stateless via manifest diffing) | Persist logs not controller state |
| `powermetrics` | Drop. | Requires sudo. |

## Cold encode status (KILLED 08:44)

**State:** dead. SIGINT sent to PID 38320, KeyboardInterrupt logged cleanly.

| Metric | Value at kill |
|---|---|
| Elapsed before kill | ~5h |
| `modern_literary` | 92 shards committed / 77,900 rows / **~73% of 107,436** target |
| `external` | done (4 shards, 2,398 rows) |
| `textbook_sections` | done (1 shard, 5,276 rows) |
| `archaic` | **never started** |
| `wikipedia` | **never started** |
| Log | `/tmp/cold-encode.log` (10,502 bytes, full event trace) |

**Resume command (when you're ready):**

```bash
.venv/bin/python -u scripts/wiki/cold_encode.py --all-corpora --resume 2>&1 \
  | tee -a /tmp/cold-encode.log
```

`--resume` is stateless via manifest diffing — picks up at the next un-committed shard automatically. Lost work is bounded to whatever was in-flight at kill time (≤ one shard, ~100s of compute).

**Recommendation: WAIT for #1363 to ship before resuming.** Reasoning:
- Machine has been hot for 5+ hours. Cooling needs ~30 min minimum.
- Resuming now (no thermal awareness) means another 3-4h of heat soak through `archaic` + `wikipedia`.
- #1363 turnaround ~1-2h. Wait ~2h, resume thermally-aware, finish remaining ~25% + `archaic` + `wikipedia` cooler.
- Total wall-clock similar; thermal profile dramatically better.

## Other open threads (not blocking)

- **#1350** Bright Kids YT — needs the channel handle from user before any work. Architectural: schema extension for `listening_anchor` field per B1+ module + license-posture column for `external_resources.yaml`.
- **#1351** Rank-order test — architectural follow-up from #1340. Codex flagged that Grade 9/10 chunks satisfying A1 concepts is a real residual risk; the fix is a soft prior at dense-rerank time. Not urgent; has empirical evidence to act on but no user pain yet.

## Decisions still pending from earlier in session (carried over)

These were surfaced but not resolved:

1. **D1 from roadmap** (L1-UK integration path): A (unpark l2-uk-direct) / B (new l1-uk/) / C (shadow mode under l2-uk-en/, Claude rec). Not blocking immediately.
2. **A2 metalanguage word_target inconsistency**: 3 plans at 4000 vs 3 plans at 2000, all same A2.9 bridge phase. My rec: all 6 → 3000. ~5 min fix.
3. **Feedback feature question**: user asked about building learner feedback; Claude recommended GH-issue pointer, not feature build. User seemed aligned but not finalized.

## Operational lessons captured this session

1. **`ps aux | grep` is unreliable in this shell.** The shell aliases `ps` to `procs` (Rust), which doesn't accept the `aux` syntax compatibly. **Use `/bin/ps` explicitly or `lsof <file>` to find a process.** The original handoff's "no process in `ps aux` grep but shards keep appearing — don't kill" was the same alias surprise. Mid-session, I called the cold encode "DEAD" twice on the empty-grep evidence, both times it was alive (PID 38320). User caught it. Don't repeat.
2. **Pre-commit hook runs ruff + a 22-test smoke set automatically on commit** — no need to remind.
3. **Bridge channel `discuss` failed for Claude with `unknown option '--- context: shared'`** — passes context as a flag accidentally. File a bridge bug if it recurs; for now Gemini/Codex round-robin still works.

## Recent commits (this session + prior)

```
2c0b8ab30 fix(wiki): apply Codex review of #1340 + ADR-007 (#1340)
ae56349e9 refactor(wiki): drop hard CEFR-grade filter + tighten #1340 diagnostic (#1340)
2c99191a9 docs(session-state): handoff at #1340 FAIL + grade-filter rethink
3704d2f2f fix(wiki): resolve search_sources re-entrant deadlock + MLX thread-safety
0566cae2d feat(diagnostics): add modern_dense strategy + #1340 comparison report (#1340)
83dc10279 test(wiki): stress + fault-injection tests, ADR-006 revision (#1348 stage-d)
45432e7db feat(sources): ship #1337 schema + extraction for textbook parent sections
```

23 commits ahead of origin/main. Push when convenient.

## Name-privacy policy (locked, carried over)

Never use real person names in anything that lands on public GitHub (issue bodies, comments, commit messages, PR descriptions, committed docs). Session-state files that stay local-only may use names.
