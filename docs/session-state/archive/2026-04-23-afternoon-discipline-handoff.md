# Session Handoff — 2026-04-23 afternoon (wiki + module writer discipline)

> User was away ~2 hours; I built a working solution for "correct wiki
> writing prompt for Gemini with Codex" + "proper module writing and
> reviewing prompt" as asked, tested + committed + pushed + opened PR.

## What you come back to — **6 PRs waiting for your merge**

| # | Title | Status |
|---|---|---|
| **1447** | **feat(discipline): canonical-anchor registry + citation-bound prompts for module and wiki writers** | THE wiki+module discipline PR. **Single-commit, 143 tests green.** Read its body carefully. |
| 1446 | feat(quality): review-and-lock how-many wiki + plan | Scale-lock batch |
| 1445 | Backfill wiki source attribution metadata (#1435) | Codex delivered its own PR this time (good) |
| 1444 | feat(quality): review-and-lock what-is-it-like wiki + plan | Scale-lock batch |
| 1443 | feat(quality): review-and-lock things-have-gender wiki + plan | Scale-lock batch |
| 1442 | fix(wiki): strip Gemini MCP warning + collapse duplicate generated_by_model | Landed on main by me (Codex didn't push) |

**Merge order recommendation** when you return:
1. **#1447 first** (wiki+module discipline — every subsequent wiki compile benefits)
2. #1442 (cosmetic MCP warning strip — also benefits compiles)
3. #1445 (backfill — after #1447 the discipline is in place so backfill writes clean metadata)
4. #1443 / #1444 / #1446 (scale-locks — independent, any order)

## Main work delivered — PR #1447 (the big one)

Fixes both failure classes surfaced today:

- **«блакитний» for flag** (a1/colors #1431 v2 smoke) — decolonization-critical
  factual hallucination
- **`[S6]`/`[S7]` phantom citations** (b2/academic-writing) — writer invents
  citation IDs past actual retrieval count

Both are LLM-drift-back-to-pre-training-mid-output failures. Prompt discipline
(80% fix) + mechanical post-pass validator (remaining 20%) plugs the gap.

**What landed:**
- `data/canonical_anchors.yaml` — 18 shared anchors (flag, trident, anthem,
  capital, currency, papa/тато, «фамілія», Kiev/Kyiv, Holodomor dates, current
  president/PM, literary canon safe vs excluded, etc.)
- `scripts/wiki/discipline.py` — mechanical validators + strip/flag repair +
  prompt block renderers (Ukrainian writer / English reviewer)
- **All 4 wiki writer prompts** get `{citation_discipline}` +
  `{canonical_anchors}` — the writer is now told explicitly "only cite [S1]..[SN]"
  and given the canonical-anchor table
- Wiki compile pipeline auto-repairs after write (strips phantom citations,
  flags forbidden anchor phrases with `<!-- VERIFY -->`)
- **Module contract §7a** — full canonical-anchors contract
- Module writer prompt + Factual/Honesty/Language reviewer prompts inject the
  anchor block
- 47 new tests (40 discipline + 7 pin)

**Important caveats (documented in the PR body):**
- Does NOT turn on fix-loop wiki review — still shadow mode. Separate PR worth
  doing next.
- Does NOT repair already-compiled wikis — that's #1445 (now unblocked).
- Does NOT verify live MCP-retrieved chunks — deeper RAG integration, another
  PR.

## Other delivered this session

- **#1439 merged** — #1434 compiler attribution fix (B2 wiki compile now
  possible). You merged it when I asked.
- **#1442** — compile-strip-mcp Codex delivery finalized by me (Codex pattern:
  completed work but didn't commit).
- **Default writer switched on main** — `claude-tools` (Opus). Commit
  `5e2afbd092`. Any new A1 module build = Opus writer + Codex reviewer.

## Running dispatches

- `scale-how-many-review-and-lock` (Claude) — likely finishing; PR #1446
  already exists, may have been opened mid-run
- **All other dispatches completed and have open PRs** above

Monitor `bx9efxhre` still armed on stale task list. Can be safely stopped.

## a1/colors Opus rebuild — **stopped failing, not on disk anymore**

I fired `v6_build.py a1 10 --writer claude-tools` earlier at user's direction
("yes rerun it"). Opus started writing, but hit the `Contract compliance
FAILED` event repeatedly (5–7 violations each round). Dispatch appears to
have terminated. Module state is pre-verify complete, no `colors.md` written
yet on main. Needs a fresh rebuild once PR #1447 lands so the writer prompt
includes the canonical anchors.

**Cause of Opus failure (speculative — need to inspect the contract-compliance
report):** likely that Opus is hitting a rule the Gemini-tuned contract writer
didn't enforce (e.g., word-budget overflow handling, section coverage). This
is a separate issue from the discipline PR — worth a focused look tomorrow.

## A1 lock progress

- **14/55 locked** after this afternoon's merges
- 3 more in PR queue (things-have-gender, what-is-it-like, how-many) →
  17/55 once you merge #1443 / #1444 / #1446

Next slugs in sequence order if you want to keep the scale-lock train moving:
`this-and-that`, `many-things`, `i-have-i-dont-have`, `i-want-i-can`, ...

## Open architectural questions for you

1. **Pipeline module writer is now Opus by default** but `colors` failed
   contract-compliance 5+ times on it. Before scaling module builds, worth
   understanding whether the contract rules are Gemini-shaped (over-specified
   for Opus) or whether Opus is genuinely failing real requirements. Read
   `curriculum/l2-uk-en/a1/orchestration/colors/contract-compliance-write-r*.yaml`.

2. **Wiki dim-review is still shadow mode** — with the discipline PR landed,
   the next leverage point is turning on the real fix-loop (4 dims,
   2 rounds). PR-sized work, maybe 1h.

3. **#1286 review transport** worktree still has uncommitted code (partial fix
   — AC 4-5 unmet). Worth deciding: commit partial, or wait for Codex 0.122.0
   upstream fix.

## What I'd recommend you do first on return

1. **Merge #1447** (the discipline PR). That unblocks everything wiki-side.
2. **Re-fire a1/colors build** with Opus writer to validate the new writer
   prompt actually reduces the «блакитний» class of hallucination.
3. **Merge the 5 other open PRs** in the order above.
4. **Then** kick off B2 wiki compile batch if you want the backlog to move:
   `compile.py --track b2 --all --force`. Post-#1447 articles will emit
   `discipline_pass` / `discipline_repair` events per compile.

## Services + environment (unchanged from morning handoff)

- api:8765, sources MCP:8766, starlight:4321 — all healthy
- `GEMINI_AUTH_MODE=subscription` still set in user shell
- Gemini ladder: flash → 3.1-pro optimistic → 2.5-pro emergency (my mid-day
  edit + revert landed it back at 3.1-pro → flash → 2.5-pro per your
  correction)

---

## LATE FIND (post-handoff) — PR #1448 tokenizer bug

While investigating why a1/colors Opus rebuild kept failing contract
compliance, I traced it to a **Unicode normalization bug in
`scripts/build/phases/wiki_compressor.py::_tokenize`**. NFKD decomposes
`й` → `и + U+0306` and `ї` → `і + U+0308`; stripping ALL combining marks
turned every Ukrainian token ending in й/ї into a non-word:

- `білий` → `білии`
- `жовтий` → `жовтии`
- `блакитний` → `блакитнии`
- `країна` → `краина`

These corrupted tokens were written to plan `factual_anchors`,
contract-compliance then demanded them literally, and Opus (writing
correct Ukrainian) could never satisfy the check.

**Fixed in PR #1448.** 10 new tests. The fix preserves U+0306/U+0308
then recomposes via NFC. Separate PR from #1447 for clean blast-radius
narrative.

**Merge priority updated:**

1. **#1448** (tokenizer bug — unblocks every future module build)
2. **#1447** (wiki+module writer discipline)
3. #1442 (compile-strip MCP warning)
4. #1445 (attribution backfill)
5. #1443 / #1444 / #1446 (scale-locks)

After merging #1448, the a1/colors rebuild with `--writer claude-tools`
should stop looping on impossible anchor matches and actually complete.
Worth re-firing as the real v2 smoke test — if it passes, the AI-only
pipeline viability question flips YES under (Opus writer + Codex
reviewer + canonical anchors + clean tokenizer).
