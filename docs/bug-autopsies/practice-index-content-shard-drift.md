# Practice mode: index-vs-content-shard drift opens a stuck 0/N session

**Issue**: #6734 (residual, after #6741) · **Date**: 2026-08-14

## What broke

Live QA: A1 **Пароніми** opened a session reading **0/8** — a nonzero planned
total with zero exercises ever served, no way forward except leaving the page.
#6741 had already fixed the *cross-level* variant of this bug for **Синоніми**
(idle counts leaking A2+ synonym lemmas into the A1 badge). This was a
different variant of the same failure class that #6741's fix did not cover.

## Why

`site/src/components/LexiconPractice.tsx` plans a session from
`sessionScopeIndexForMode()`, which trusts only the **declared** `.modes`
flag baked into the lightweight `practice-index.{level}.json` shard at build
time. Content-shard-backed modes (paronym, synonym, heritage) additionally
require a matching per-lemma row in their own dedicated shard
(`practice-paronym.{level}.json`, etc.), loaded separately by `ensureDeck()`.

Nothing cross-checked the two. If a lemma's index entry declares
`modes: ['paronym']` but the paronym content shard has no row for that lemma
(a stale/partial republish, or two shards published at different times), the
planner counts the index-declared lemma as real (`plannedTotal > 0`) while
`selectNextPracticeItem()` finds zero actual candidates
(`maps.paronym.get(lemmaId) ?? []` silently yields nothing). The learner gets
a session frame with a nonzero counter and no exercise, forever.

`deck.paronym?.length === 0` was checked for the *fully-empty-shard* case
(shows a "still being prepared" message) but that check is on the array's
overall length, not on whether the array covers the *specific* lemmas the
index scoped in — so a partially-populated content shard (nonzero length,
wrong lemmas) skips that message too and falls through to a contradictory
"All caught up!" screen while the progress pill still reads `0/N`.

## Prevention

Added `withLoadedModeContent()`: cross-references the declared-eligible index
scope against the deck's actually-loaded per-lemma content array for any
mode backed by a dedicated content shard (paronym/synonym/heritage) before
treating an item as playable. Applied at all three places a session's real
item count is decided: the `autoStart` effect, the `selection` memo, and
`beginSession`'s guard. A declared-but-contentless lemma is now dropped from
the plan, so `plannedTotal` reflects real content and the existing
empty-mode message (`practice.modeNoExercises` / the mode's own "still being
prepared" state) fires instead of a stuck `0/N` session.

Regression tests reproduce the exact index/content mismatch and mutation-check
clean (revert the fix → tests fail on `0/1` instead of `0/0`):
`site/tests/unit/LexiconPractice.test.tsx` — "#6734 residual" tests.

Not fixed here: the idle mode-card badge still shows the declared (possibly
stale) count, since idle only fetches the lightweight index shard by design
(no per-mode content fetch until a session starts). The defense is in
refusing to *open* a broken session, not in idle-time badge honesty — doing
the latter would mean eagerly fetching every content shard on every level
switch, a real cost/architecture tradeoff outside this fix's scope.
