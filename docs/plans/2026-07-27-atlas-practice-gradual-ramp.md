# Plan of record (DRAFT for advisors): Atlas + Practice gradual ramp

**Status:** DRAFT — needs advisor review (Sol + Fable) before infra/process lock
**Date:** 2026-07-27
**Epic:** #4387 (Word Atlas + Practice Hub)
**Operator ask:** gradual expansion schedule; know **when** infra must change; whether to ramp; path to server-side LLM later; **static for now**
**Author seat:** interim atlas driver (Grok) — architecture draft for advisors, not a solo lock

---

## 1. Product north star

| Horizon | Learner experience |
| --- | --- |
| **Now** | Browse a large Word Atlas; practice a smaller high-quality pool |
| **Near** | Curated decks (Alona / course) feel complete; CTA works for those words |
| **Mid** | Most “everyday” atlas words are practiceable; banner becomes rare |
| **Far** | **Practice any public atlas word** — static pool covers the head, long-tail may use server assist |

**Non-negotiables (already decided):**
- Static-first practice (offline-capable shards)
- Quality gates over coverage vanity
- Rights-aware examples (no fake sentences, no textbook exercise traps)
- CODE decides word validity (VESUM / triage), not LLM dictionary judgment
- Non-commercial permanent project

**Answer: should we ramp?**
**Yes — gradually.** Not “add everything tomorrow.” Ramp is how we reach “any word” without melting static size budgets or shipping junk drills.

---

## 2. Two systems, one core

```text
SOURCES → LEXICAL CORE (lemmas / senses / attestations / rights)
              │
     ┌────────┴────────┐
     ▼                 ▼
  ATLAS SITE      PRACTICE BUILDER (eligibility → CEFR shards)
  (look up)       (drill only if in pool — today)
     │                 │
     └────────┬────────┘
              ▼
         LEARNER APP
              │
              ▼ later
    “any word” = pool ≈ atlas  OR  on-demand cards from same core
```

| Metric (2026-07-27, tool-backed) | Value |
| --- | --- |
| Atlas articles (`data/atlas.db`) | ~17.4k |
| Practice pool (union A1–C1 lemmaIds) | ~4.9k |
| Alona v5 active seed | ~1.0k (not-in-VESUM skipped) |
| Practice lexemes gzip budget / level | 180 KB gzip / 1.6 MB raw (headroom today) |

Banner **“Not in the practice pool yet”** = not in `practice-index.*`, **not** “empty atlas page.”
Example: `інвалідність` is a rich A2 atlas entry with morphology; it is simply out of the practice pool.

---

## 3. Eligibility stack (what “practiceable” means)

A lemma is practiceable only if it clears **mode-appropriate** gates (existing `generate_practice_deck` / PRACTICE-HUB-SPEC spirit):

| Layer | Requirement |
| --- | --- |
| **Identity** | Stable lemma id / slug; preferably VESUM-linked |
| **Gloss** | Learner-usable EN (or UK) meaning |
| **CEFR anchor** | Level or course anchor (estimate OK if labeled) |
| **Mode data** | Stress for stress drills; verified paradigm for case; pairs for synonym/paronym; **example + rights** for cloze |
| **Quality** | No surzhyk junk, no derived-only debris, no ambiguous cloze |

**Ramp rule:** expand only what passes gates. Prefer empty mode shard over bad cards.

---

## 4. Phased schedule (calendar targets, not hard SLAs)

Assumes fleet capacity + one focused atlas driver; slip dates, not quality.

### Wave 0 — Foundation (done → finishing) · through ~2026-08

| Item | Exit |
| --- | --- |
| Practice hub live (static FSRS, CEFR shards) | Done |
| Open lexical plan + inventory + projection schema | Done / landing |
| Alona v5 seed frozen (VESUM skip policy) | Done |
| Seed → ADR-017 converter | Done (#5901) |
| **Gold deck 32–50** through real practice pipeline | **In flight (#5792)** |

**Infra change?** None. Stay static.

---

### Wave 1 — Curated vertical · ~2026-08 → 2026-09

| Milestone | Target | Exit criteria |
| --- | --- | --- |
| W1.a Gold deck | 32–50 lemmas | CTA works; local Astro smoke; provenance on examples |
| W1.b Alona full deck | ~1k seed (ok-sentence first) | `practice-index` membership for deck slug **or** CEFR inject; human smoke |
| W1.c Morphology search v1 | form → lemma aliases | Declined search hits atlas page for sample set |
| W1.d Durable enrich cache | 20k / ULIF (#5884) | No silent loss on cleanup |

**Ramp?** Yes — curated only.
**Infra change?** Still static. Measure: total gzip of practice shards per level after W1.b.

**Advisor checkpoint A:** after W1.b — “Is static still healthy? Cloze quality OK?”

---

### Wave 2 — Systematic pool growth · ~2026-09 → 2026-11

Grow practice pool from atlas enrichment in **measured batches** (not one dump):

| Batch | Source | Target add (order of magnitude) | Notes |
| --- | --- | --- | --- |
| 2.1 | A1–A2 high-frequency + course | +1–2k | Stress + gloss required |
| 2.2 | B1 core | +1–2k | Paradigm verify before case modes |
| 2.3 | Words with redistributable examples | +cloze | Cloze stays rare until quality holds |
| 2.4 | Alona remainder + teacher decks | +as admitted | Privacy until operator GO |

**Pool target end of Wave 2:** ~**10–15k** practice lemmas (still << full atlas).
**Atlas target:** continue Phase-1 local fill; no forced 250k yet.

**Infra triggers (measure monthly):**

| Signal | Threshold (proposal) | Action |
| --- | --- | --- |
| Per-level practice-lexemes **gzip** | > **150 KB** of 180 KB budget (~80%) | Split shards (by letter / mode / sublevel) **before** hard fail |
| Per-level practice-lexemes **raw** | > **1.2 MB** of 1.6 MB | Same |
| Practice index load time (mobile mid) | > **500 ms** parse+index | Partition index; lazy mode shards already help |
| SSG / hydrate wall time | > **30 min** or CI flake | Incremental deck build / cache |
| Atlas search payload (client) | > **agreed MB** or jank | SQLite-wasm path or server search spike |

**Infra change?** Still **static**, but may need **shard layout v2** (mechanical, not backend).
**Advisor checkpoint B:** first time any level hits 80% size budget — Sol/Fable review shard plan **before** next +2k batch.

---

### Wave 3 — Coverage toward “most words” · ~2026-11 → 2027-Q1

| Goal | Approach |
| --- | --- |
| Practice pool ~**20–40k** (stretch) | Batch eligibility from atlas.db; fail closed on quality |
| Atlas depth | Phase-2 paced ULIF/wiki; durable caches mandatory |
| Cloze | Only attestation-backed; never LLM filler on client |

**Should we ramp here?** Only if Wave 2 quality metrics hold (error rates, human spot checks, cloze ambiguity).

**Infra triggers → real architecture change:**

| Signal | Threshold (proposal) | Change |
| --- | --- | --- |
| Static total practice download (all levels learner might pull) | Uncomfortable on 4G / offline package | **Tiered download** (level-only) already; then **server fetch for long-tail modes** |
| Full atlas SSG time / artifact size | Operator pain or CI broken | **On-demand article** or hybrid SSG |
| “Practice any word” demand | Banner rate still high at 40k pool | Design **on-demand practice cards** from atlas.db |
| Accounts / cross-device FSRS | Operator GO | **Practice backend** (#4384) — progressive enhancement |

**Advisor checkpoint C (mandatory):** before any server component — Sol + Fable design review (auth, offline, cost, non-commercial hosting).

---

### Wave 4 — Server assist + optional LLM · 2027+ (gated)

**Still static-first.** Server is additive.

| Capability | Role of server | Role of LLM (only if approved) |
| --- | --- | --- |
| Long-tail practice cards | Assemble gloss+stress+paradigm from DB | Optional: distractor generation with human/auto quality gates |
| Cloze for rare words | Prefer corpus attestation API | LLM only if rights-safe **and** VESUM-checked; never invent dictionary facts |
| Search | Query API if client FTS too big | No |
| Sync / analytics | Accounts + FSRS sync | No |

**LLM policy (binding draft for advisors):**
- Client remains static / deterministic for core decks
- LLM **never** decides word validity or morphology
- LLM **may** assist server-side generation only behind gates + logging
- Default: off until Wave 3 checkpoint C passes

---

## 5. Operating cadence (how we ramp without chaos)

| Cadence | Activity |
| --- | --- |
| **Weekly** | Gold/curated deck merges; practice rebuild for small deltas |
| **Biweekly** | Pool growth batch (size + quality report) |
| **Monthly** | Infra trigger dashboard (budgets, SSG time, banner rate sample) |
| **Per wave end** | Advisor checkpoint (A/B/C) |

**Fleet:** drivers dispatch workers; cross-family CF on code; Sol/Fable for design locks.

---

## 6. Decision cards for advisors

| ID | Question | Driver recommendation |
| --- | --- | --- |
| **DC-1** | Confirm gradual ramp vs freeze practice pool at ~5k? | **Ramp gradually** (Waves 1–2) |
| **DC-2** | Size-budget trigger at 80% gzip — split shards vs raise limits? | **Split first**; raise limits only with measurement |
| **DC-3** | When to design on-demand practice? | After Wave 2 pool ~10–15k **or** 80% budget hit — whichever first |
| **DC-4** | When to introduce server? | Only at Wave 3 checkpoint C; static remains default path |
| **DC-5** | LLM on server? | **Later, gated**; never on client core path; never for validity/morphology |

---

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Coverage vanity → bad drills | Eligibility fail-closed; spot audits |
| Static budget cliff | 80% triggers; shard v2 |
| Rights regressions in examples | Provenance required; textbook exercise filter |
| Double migration of 250k | Schema before mass fill (already policy) |
| Solo driver thrash | FLEET-FIRST / NO SOLO seat rules |

---

## 8. Immediate next 30 days (executable)

1. Land **gold deck (#5792)** — factory proof
2. Expand to **Alona full “ok sentence” subset** as curated practice deck
3. Instrument **banner rate** sample (N random atlas pages: hasPractice true/false)
4. Publish **size-budget dashboard** script (one command → gzip/raw per level)
5. Advisor review of this draft (Sol + Fable) → lock DC-1…DC-5
6. Only then schedule Wave 2 batch 2.1

---

## 9. Related issues / docs

- Umbrella: #4387
- Seed: #5790 · Schema: #5791 · Gold: #5792 · Paste-text: #5882 · Durability: #5884
- Backend (later): #4384 · #4920
- Plans: `docs/plans/2026-07-25-atlas-open-lexical-layer.md`, `docs/plans/atlas-entry-model-v1-and-corpus-fill.md`, `docs/poc/word-atlas/PRACTICE-HUB-SPEC.md`

---

## 10. Advisor ask (copy for Sol / Fable)

Please review as **architecture / ramp design**, not code nits:

1. Is the wave split and **order** right?
2. Are **infra trigger thresholds** sane (too early / too late)?
3. Should Wave 2 pool target be lower/higher than 10–15k?
4. Confirm **static-until-checkpoint-C** and **LLM-only-later-gated**.
5. Any missing trigger (SSG, rights, pedagogy)?

Return: **APPROVE** / **APPROVE-WITH-CHANGES** / **BLOCK**, with explicit edits to DC-1…DC-5.

---

*Draft for advisor consensus. Not operator-locked until advisors + operator GO.*
