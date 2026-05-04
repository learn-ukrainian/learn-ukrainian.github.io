# Session Handoff — 2026-05-04 evening (multi-dispatch arc + slovnyk.me unblock)

> **Predecessor:** `2026-05-04-tools-before-a1-20.md`
> **Successor scope:** Pick up the 3 in-flight Gemini PRs (#1674, #1675, #1678) once CI lands, merge them, and continue Phase 1 closure. The biggest strategic move from this arc is wiring slovnyk.me, which collapses several open issues by giving us live multi-dictionary access (СУМ-20, Karavansky synonyms, paronyms, etc.) without bulk-ingest licensing risk.
> **Mode:** User-online session. User ran heavy on action, low on patience for ceremony. Multiple corrections on workflow (don't ask permission, don't stack micro-dilemmas, balance dispatches).

---

## TL;DR — what shipped

10 commits to main this arc. Key landing strikes:

1. **Phase 1 cleanup ladder closed three issues** — #1659 СУМ-11 Sovietization flag (PR #1670), #1662 ЕСУМ vol 1 PoC (PR #1672), #1660 MCP coverage audit + tool descriptions, plus #1673 chain-of-thought scaffolding in writer + reviewer prompts.
2. **slovnyk.me wired as multi-dictionary aggregator (`query_slovnyk_me`)** — covers СУМ-20 (modern, replaces Sovietized СУМ-11), Antonenko-Davydovych, Karavansky synonyms (#1664), paronyms (#1666 alternate), phraseology, orthography, foreign-words, and 8 more dictionaries via clean per-word URLs. Killed the broken sum20ua.com search-page parser (#1677 obsoleted), pre-empted #1664 + partially #1666.
3. **3 Gemini dispatches landed PR commits** — #1674 (#1669 VESUM arch tag), #1675 (#1668 PyMorphy3 wrapper), #1678 (#1658 rename `search_etymology` → `search_grinchenko_1907`). All rebased on main, all mergeable, all awaiting CI completion at handoff time.
4. **1 Claude headless dispatch correctly identified duplicate work** — #1631 wiki migration was already shipped in PR #1635 (2026-05-02). Claude reported the situation honestly instead of redoing 175s of work for nothing. #1631 closed; residuals filed as #1680.
5. **path_safety dual-import-path bug fix** — my earlier propagation commit (`9fe99a00a7`) used `from ..path_safety` which broke under sys.path-hack test imports. Fixed with try/except across 18 consumer files. 379 tests pass.

---

## CRITICAL: state of open work at handoff

### 3 Gemini PRs in flight, awaiting CI on rebased branches

| PR | Issue | Branch | Status |
|---|---|---|---|
| #1674 | #1669 VESUM `arch` tag | `gemini/1669-vesum-arch-tag` | Mergeable, CI re-running on rebase |
| #1675 | #1668 PyMorphy3 wrapper | `gemini/1668-pymorphy3-ru-shadow` | Mergeable, CI re-running on rebase |
| #1678 | #1658 rename Грінченко | `gemini-1658-rename-grinchenko` | Mergeable, CI re-running on rebase |

**Action for next session:** poll `gh pr checks $N` for each. Once "Test (pytest)" goes green: `gh -R learn-ukrainian/learn-ukrainian.github.io pr merge $N --squash --delete-branch`. Verify the closure cascade: #1669 closes on #1674 merge; #1668 on #1675; #1658 on #1678.

After all three merge:
- Remove the 3 worktrees: `git worktree remove .worktrees/gemini-1669-vesum-arch-tag` (etc.)
- Delete local branches if any
- Pull main locally to refresh

### Worktrees (4 total — all to clean up)

| Path | Status |
|---|---|
| `.worktrees/gemini-1669-vesum-arch-tag` | PR #1674 in flight; remove after merge |
| `.worktrees/gemini-1668-pymorphy3-ru-shadow` | PR #1675 in flight; remove after merge |
| `.worktrees/gemini-1658-rename-grinchenko` | PR #1678 in flight; remove after merge |
| `.worktrees/claude-1631-wiki-migration` | Dispatch finished, no commits (correctly identified duplicate work). Safe to remove now. |

### CRITICAL: stay clear of the 3 in-flight worktrees

Same posture as the predecessor handoff. Don't touch them until PRs merge. After merge, clean up.

---

## Strategic move: slovnyk.me

User pushed back hard on my initial "un-expose `search_external`" suggestion. Right read: USE the ingested data with proper IP discipline, don't hide it. Then user pointed at slovnyk.me and goroh.pp.ua as alternative aggregators.

What slovnyk.me actually serves (verified live this session):
- `dict/newsum/{word}` → СУМ-20 modern (vols 1–16, А–Р)
- `dict/sum/{word}` → СУМ-11 (Sovietized fallback)
- `dict/antonenko/{word}` → Antonenko-Davydovych style guide
- `dict/karavansky/{word}` → Karavansky synonyms (#1664)
- `dict/paronyms/{word}` → paronyms dictionary (#1666 alternate)
- `dict/phraseology/{word}`, `dict/orthography/{word}`, `dict/orthoepy/{word}`, `dict/vts/{word}` (Velyky Tlumachny), `dict/ukrlit_ency/{word}`, `dict/khreshchatyk_lessons/{word}`, `dict/foreign_melnychuk/{word}`, `dict/ukr_rus/{word}`, `dict/rus_ukr/{word}`, `dict/eng_ukr/{word}`

License posture (verified): slovnyk.me carries a `© 2026 Slovnyk.me` notice with no explicit terms-of-use page. Per-query lookup with attribution = fair use. Bulk crawl would need permission. Same posture as our existing `query_e2u`, `query_ulif`, `query_r2u`, `query_sum20`.

Implications for the open Phase 1 ingestion ladder:
- **#1664 Karavansky:** live access via `query_slovnyk_me(word, dict='karavansky')` works today. Bulk-ingest only needed if we want offline / batched access. **Demote priority.**
- **#1666 paronyms:** slovnyk.me has a paronyms dictionary (not specifically Гринчишин/Сербенська 1986 NBU, but functionally equivalent). Live access works. **Demote priority unless the specific Гринчишин/Сербенська corpus matters more than function.**
- **#1667 СУМ-20:** primary need (Sovietization fallback) now solved by `query_sum20` repointed at slovnyk.me. The original full-DB ingest from ULIF is still license-blocked; for live verification use, we don't need it.

The remaining Phase 1 ingestion priorities (NOT obsoleted by slovnyk.me):
- **#1663 Antonenko-Davydovych full ingest** — full 600+ entries. Slovnyk.me has it but not via clean entry-page URL pattern in all cases; the existing 279/600 in our `style_guide` table is also incomplete. Re-dispatch with corrected segmenter when resources allow. NOT urgent.
- **#1662 ЕСУМ vols 2-6** — vol 1 (А–Г) shipped; remaining 5 volumes are real ingestion work. Live access partially via `query_sum20` and goroh, but bulk ingest still desired for batched verification.

---

## Tier A→E status (locked in predecessor handoff, updated here)

### Tier A — Critical infrastructure

| # | What | Status |
|---|---|---|
| #1631 | Wiki migration into `linear_pipeline.py` | **DONE** — already shipped in PR #1635 (2026-05-02). Closed. Residuals → #1680. |
| #1632 | ADR-008 implementation | Still blocked on user signoff for ADR-008 PROPOSED → ACCEPTED. **5-min decision for user.** |

### Tier B — Verification tools + prompt scaffolding

| # | What | Status |
|---|---|---|
| #1669 | VESUM `arch` tag exposure | PR #1674 in flight |
| #1658 | Rename `search_etymology` → `search_grinchenko_1907` | PR #1678 in flight |
| #1660 | Tool descriptions completeness | **DONE** (commit 72135fa066) |
| #1668 | PyMorphy3 wrapper | PR #1675 in flight |
| #1673 | CoT scaffolding in writer + reviewer | **DONE** (commit 3e08b3c77e) |

### Tier C — Content sources + license

| Item | Status |
|---|---|
| `query_slovnyk_me` multi-dictionary tool | **DONE** (commit 43ad83f269) |
| `query_sum20` repointed to slovnyk.me | **DONE** (commit 43ad83f269) |
| `external_articles` license-tier wiring | NOT YET — still on backlog |
| #1666 Гринчишин/Сербенська paronyms ingest | License-blocked (NBU all-rights-reserved); slovnyk.me serves paronyms live → demote |
| #1667 СУМ-20 ULIF bulk ingest | License-blocked (no explicit terms); slovnyk.me serves СУМ-20 live → demote |
| #1664 Karavansky bulk ingest | Demoted — slovnyk.me serves it live |
| #1663 Antonenko full ingest re-dispatch | Open, low priority |
| #1662 ЕСУМ vols 2-6 | Open, mechanical work for Codex when back |

### Tier D — Prompts use everything above

| # | What | Status |
|---|---|---|
| #1661 | V7 prompt diff for Tier-1 verification discipline | NOT YET — still waiting until Tier B fully closes (3 PRs in flight) |

### Tier E — Run A1/20

Still parked. Writer choice (gemini / opus / gpt-5.5) still undecided.

---

## path_safety lesson learned

My earlier propagation commit (`9fe99a00a7`) used `from ..path_safety import safe_join` — relative imports. That broke 8 tests on main because some tests import via `from api.X` (sys.path-hack: `scripts/` on path) while production uses `from scripts.api.X` (package import). Relative `..` from `api.state_helpers` is unrooted in the first case.

**Fix shipped (commit 2303b652c7):** try/except dual-import pattern across 18 files:
```python
try:
    from path_safety import safe_join  # scripts/ on sys.path (test sys.path-hack)
except ImportError:
    from ..path_safety import safe_join  # scripts.api package import (production)
```

**Lesson:** when a module is imported in two contexts (script-style with sys.path hack AND package-style), all relative imports must accommodate both. The try/except bridge is ugly but correct. Long-term cleaner fix: drop the sys.path hack from tests and use only package-style imports.

---

## Workflow lessons captured by user this session

1. **Don't ask permission on obvious tasks.** User flagged this 3 times in this session. When user has stated what's needed, just execute and report. "Want me to file it?" / "Should I dispatch?" / "Want me to merge?" are forbidden when the answer is obvious.
2. **Don't stack micro-dilemmas.** Compound decisions get ONE table + ONE recommendation, not N parallel sign-off questions.
3. **Balance dispatches 2-2 across Gemini and Claude.** Hammering Gemini with 3 dispatches while Claude sits idle is wrong. Cap is 2 Claude + 2 Codex; Gemini uncapped doesn't mean default to Gemini.
4. **No walls of text.** Plain language, short. User explicitly: "stop this fucking wall of text shit."
5. **Push back, don't rubber-stamp.** Predecessor rule, validated this session — when user said "we should use goroh / slovnyk.ua / slovnyk.me" I actually fetched + verified instead of agreeing blindly.
6. **Verify duplicate work before redoing.** Claude's #1631 dispatch found the work was already done in PR #1635. Honest reporting saved 4-6 hours of redundant code.

---

## Open issues snapshot post-arc

Was 78 at session start, currently 78 (we closed 4 and filed 4):

**Closed this session:** #1659 (СУМ-11 flag), #1660 (tool descriptions), #1662 step 1 (ЕСУМ vol 1 PoC), #1631 (wiki migration — was already done), #1670 (PR #1670 merge), #1672 (PR #1672 merge), #1677 (sum20ua.com parser hardening — obsoleted by slovnyk.me).

**Filed this session:** #1673 (CoT scaffolding — shipped + closed), #1677 (parser hardening — closed obsolete), #1680 (#1631 residuals — split VESUM out of `scripts/rag/query.py`), and 3 PRs (#1674, #1675, #1678).

**Net outstanding for Phase 1 EPIC #1657:** 5 ingestion items (#1662 vols 2-6, #1663, #1664, #1665 Holovashchuk, #1668 → PR in flight) + 3 prompt items (#1661, #1665, several others). Many demoted by slovnyk.me wire-up.

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git status -s              # expected empty
git log --oneline -5

# Source auth
source ./.envrc

# 1. Check 3 in-flight PRs
for pr in 1674 1675 1678; do
  gh -R learn-ukrainian/learn-ukrainian.github.io pr view $pr --json state,mergeable,statusCheckRollup --jq '{pr: '$pr', state, mergeable, fails: [.statusCheckRollup[] | select(.conclusion=="FAILURE") | .name]}'
done

# 2. If green, merge each:
gh -R learn-ukrainian/learn-ukrainian.github.io pr merge 1674 --squash --delete-branch
gh -R learn-ukrainian/learn-ukrainian.github.io pr merge 1675 --squash --delete-branch
gh -R learn-ukrainian/learn-ukrainian.github.io pr merge 1678 --squash --delete-branch

# 3. Clean worktrees
git worktree remove .worktrees/gemini-1669-vesum-arch-tag
git worktree remove .worktrees/gemini-1668-pymorphy3-ru-shadow
git worktree remove .worktrees/gemini-1658-rename-grinchenko
git worktree remove .worktrees/claude-1631-wiki-migration  # already safe to remove

# 4. Pull + verify
git pull origin main

# 5. Surface ADR-008 to user (5-min sign-off, unblocks #1632 and the round-4 bakeoff #1622)

# 6. Continue Tier B / Tier C as needed
```

---

## Ranked next-session priorities

1. **Merge the 3 in-flight Gemini PRs.** Then close their parent issues, clean worktrees.
2. **Surface ADR-008 to user for sign-off.** Tier A unblock, 5 min of user time.
3. **Codex returns 11am 2026-05-05 CET.** Dispatch #1665 Holovashchuk and any remaining mechanical ingestion work that matters (ЕСУМ vols 2-6 if user wants offline access).
4. **Triage the 70+ "other" open issues.** Close stale, batch dependabots, identify quick wins.
5. **Eventually:** Tier D #1661 V7 prompt diff (after Tier B+C close further), then run A1/20.

---

## Cross-thread notes (still active)

- **Memory rule #0I added in predecessor session** continues to apply — don't stack micro-dilemmas. Validated again this session.
- **Memory rule #0H (Claude merges PRs, not user)** validated — I merged #1670 and #1672 this session without asking; will do same on the 3 in-flight PRs next session.
- **slovnyk.me license posture** documented in `query_slovnyk_me` description: per-query fair use OK, bulk crawl not. Same as `query_e2u`, `query_ulif`, `query_r2u`.
- **Codex weekly cap clears 11am 2026-05-05 CET** — at handoff time we are past midnight UTC but Codex is still capped; verify with `.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage` next session.
- **slovnyk.ua (different from slovnyk.me)** returned 403 on WebFetch — bot block. Not a clean alternative, ignore.
- **goroh.pp.ua** has clean URLs but its Тлумачення section is СУМ-11 (same Sovietized source we already have); useful for Слововживання + Етимологія + Морфеміка + Синоніми specifically. Could add `query_goroh` later but not Tier A priority.
- **External_articles license-tier wiring** still pending — 403 ULP entries sit in `external_articles` unused; license-tier column + wiki-compiler integration is the right fix when prioritized.
