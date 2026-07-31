# Plan of record: Atlas + Practice gradual ramp

**Status:** PLAN OF RECORD — operator sequence confirmed **2026-08-01** (driver: grok-atlas).  
Long-tail **server / 250k delivery** still needs advisor lock when that phase starts (Sol + Fable).  
**Date:** 2026-07-27 (Track T split); **2026-08-01** (operator ramp sequence + ticket board).  
**Epic:** #4387 (Word Atlas + Practice Hub)  
**Mandate board:** #6132 (sub-issues #6134–#6143 and related open tickets)  
**Related:** #4920 (backend / ~250k serving), #6142 (past 20k expand), ULIF #5224 / #5230

---

## 0. Operator ramp sequence (binding)

**Intent (operator, plain language):**

1. Establish a **solid base dictionary** (~**10k** class — honest, enriched-enough core).  
2. **Work out Practice** on that base (multi-mode factory + sessions that feel real).  
3. **Expand atlas ~20k** and **enrich**.  
4. **Expand Practice again** (re-run factory on the larger atlas).  
5. **Iterate** the same loop toward full coverage (~**250k** lemmas — architecture changes for serving; see #4920).

**This is the product growth spine.** Residual tickets (#6064, etc.) are **wire under the spine**, not a substitute for it.

| Stage | Atlas | Practice | Notes |
| --- | --- | --- | --- |
| **S1 — Base dict** | ~10k solid core (or current live base if already larger) | Not yet “done” | Quality over hollow shells |
| **S2 — Practice on base** | Freeze vanity growth if practice is empty | Factory + session variety on existing sources | Prefer empty mode over bad cards |
| **S3 — Expand ~20k + enrich** | Cohort / ULIF / intake (~20.3k cohort file exists) | Re-run factory after enrich | 20k is a **checkpoint**, not the product |
| **S4 — Practice catch-up** | — | Regen shards; thin modes grow from real sources | Ticket board #6134–#6141 |
| **S5 — Iterate to full** | Beyond 20k → toward ~250k | Regen every expand wave | Static-first until #4920-class serving |

### Current position (tool-backed order of magnitude, 2026-08-01)

| Layer | Approx | Implication |
| --- | --- | --- |
| Live public atlas | ~17–18k entries | Already **past a pure 10k freeze** — treat as **base+** |
| 20k cohort list | ~20 323 lemmas | Expand/enrich phase material (#6142) |
| Practice index (sum A1–C1 items) | ~4.8–5k | **Practice lagging atlas** — S2/S4 is the active catch-up |
| Teacher private seed | ~1k package | Track T (parallel homework track) |

**Policy:** Do **not** “collect 250k first.” Do **not** sell residual CEFR crumbs as the product.  
**After every atlas expand wave:** practice factory regen + quality gates.  
**20k is temporary.** **250k needs backend / entry-model serving** (#4920), not infinite static Pages blobs.

### Ticket map (follow GH, not private queues)

| Stage | Primary tickets |
| --- | --- |
| S2/S4 practice factory & modes | #6134 #6136 #6137 #6138 #6139 #6141 #3797 |
| Session / any deck | #6135 #5882 #5718 #6143 |
| Heritage (important **subtask**) | #6140 |
| S3/S5 expand | #6142 #3936 #5230 #5224 |
| Teacher residual wire | #6064 |
| ~250k architecture | #4920 #4378 #4384 |

---

### CRITICAL split (operator 2026-07-27 evening — still binding)

| Track | Scope | Timeline |
| --- | --- | --- |
| **Track T — Teacher homework** | Full **Curated private teacher-lesson v5** list (~1k active seed) in Practice | **Immediate** — parallel to Track A; **not** capped at 50 words |
| **Track A — Atlas-wide ramp** | Grow practice pool toward “any atlas word” (live ~17k→20k→more) | Gradual waves; operator sequence §0 |

A **32–50 gold slice** is only a **factory smoke test**. It must never be treated as the teacher-list delivery.

---

## 1. Product north star

| Horizon | Learner experience |
| --- | --- |
| **Now (Track T)** | Practice the **teacher’s full Curated private teacher-lesson word list** in the app |
| **Now (product)** | Browse a large Word Atlas; practice pool smaller than atlas |
| **Near** | Curated decks feel complete; CTA works for those words |
| **Mid** | Most “everyday” atlas words are practiceable; banner becomes rare |
| **Far** | **Practice any public atlas word** — static pool covers the head; long-tail may use server assist |

**Non-negotiables (already decided):**

- Static-first practice (offline-capable shards)
- Quality gates over coverage vanity
- Rights-aware examples (no fake sentences, no textbook exercise traps)
- CODE decides word validity (VESUM / triage), not LLM dictionary judgment
- Non-commercial permanent project

**Should we ramp the whole atlas (Track A)?**
**Yes — gradually.**

**Should the Curated private teacher-lesson teacher list wait for that ramp?**
**No.** Track T is unblocked homework priority and runs **ahead of** Wave 1–4 calendar language.

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
| Curated private teacher-lesson v5 active seed | ~1.0k (not-in-VESUM skipped) |
| Practice lexemes gzip budget / level | 180 KB gzip / 1.6 MB raw (headroom today) |

Banner **“Not in the practice pool yet”** = not in `practice-index.*`, **not** “empty atlas page.”
Example: `інвалідність` is a rich A2 atlas entry with morphology; it is simply out of the practice pool.

---

## 3. Eligibility stack (what “practiceable” means)

| Layer | Requirement |
| --- | --- |
| **Identity** | Stable lemma id / slug; preferably VESUM-linked |
| **Gloss** | Learner-usable EN (or UK) meaning |
| **CEFR anchor** | Level or course anchor (estimate OK if labeled) |
| **Mode data** | Stress for stress drills; verified paradigm for case; pairs for synonym/paronym; **example + rights** for cloze |
| **Quality** | No surzhyk junk, no derived-only debris, no ambiguous cloze |

**Ramp rule:** expand only what passes gates. Prefer empty mode shard over bad cards.
**Track T rule:** admit full Curated private teacher-lesson list for recognition/practice; cloze only where sentence is clean.

---

## 4. Phased schedule

### Wave 0 — Foundation + **Track T** · **immediate**

| Item | Exit |
| --- | --- |
| Practice hub live | Done |
| Open lexical plan + projection schema | Done |
| Curated private teacher-lesson v5 seed frozen (VESUM skip; no renames) | Done |
| Seed → ADR-017 converter | Done (#5901) |
| Factory smoke 32–50 | Mechanism PR #5905 (smoke only) |
| **Track T: full Curated private teacher-lesson v5 (~1k) in Practice** | **P0 next driver** — homework |

**Infra change?** None. Stay static.
**Do not** bury Track T in “Wave 1 autumn.”

---

### Wave 1 — After Track T · polish

| Milestone | Target | Exit |
| --- | --- | --- |
| W1.a Morphology search v1 | form → lemma | Declined search hits sample pages |
| W1.b Durable enrich cache | #5884 | No silent loss on cleanup |
| W1.c Banner UX | Soften gloss-only vs pool-miss | Clear copy |

**Advisor checkpoint A:** after Track T full Curated private teacher-lesson is live — static still healthy?

---

### Wave 2 — Systematic pool growth · ~months after Track T

| Batch | Source | Order of magnitude |
| --- | --- | --- |
| 2.1 | A1–A2 high-frequency + course | +1–2k |
| 2.2 | B1 core | +1–2k |
| 2.3 | Redistributable examples → cloze | careful |
| 2.4 | Further teacher decks | as admitted |

**Pool target end of Wave 2:** ~**10–15k** practice lemmas.

**Infra triggers (measure monthly):**

| Signal | Threshold (proposal) | Action |
| --- | --- | --- |
| practice-lexemes **gzip** / level | > **150 KB** of 180 KB (~80%) | Split shards before hard fail |
| practice-lexemes **raw** / level | > **1.2 MB** of 1.6 MB | Same |
| Index load (mobile mid) | > **500 ms** | Partition index |
| SSG / hydrate wall | > **30 min** or CI flake | Incremental build |
| Client search jank | agreed MB / UX pain | SQLite-wasm or server search spike |

**Advisor checkpoint B:** first 80% budget hit — Sol/Fable before next +2k batch.

---

### Wave 3 — Toward “most words” · later

| Goal | Approach |
| --- | --- |
| Pool ~20–40k stretch | Batch from atlas.db; fail closed |
| Atlas depth | Phase-2 paced ULIF/wiki; durable caches |
| Cloze | Attestation-backed only |

**Advisor checkpoint C (mandatory before any server):** Sol + Fable (auth, offline, cost, non-commercial hosting).

---

### Wave 4 — Server assist + optional LLM · gated, later

**Still static-first.** Server is additive.

| Capability | Server | LLM (only if approved) |
| --- | --- | --- |
| Long-tail practice cards | Assemble from DB | Optional distractors with gates |
| Cloze rare words | Corpus API first | Only rights-safe + VESUM-checked |
| Search | API if client FTS too big | No |
| Sync / analytics | Accounts + FSRS | No |

**LLM policy (draft):** never on client core path; never decides validity/morphology; default off until checkpoint C.

---

## 5. Operating cadence

| Cadence | Activity |
| --- | --- |
| **Immediate** | Track T full Curated private teacher-lesson practice admission |
| **Weekly** | Curated deck merges after Track T |
| **Biweekly** | Track A pool batches (after Track T) |
| **Monthly** | Infra trigger dashboard |
| **Per wave end** | Advisor checkpoint |

**Fleet:** drivers dispatch workers; cross-family CF on code; Sol/Fable for design locks.
**FLEET-FIRST / NO SOLO** on Grok driver seat (demotion trigger).

---

## 6. Decision cards for advisors (Track A)

| ID | Question | Driver recommendation |
| --- | --- | --- |
| **DC-0** | Confirm Track T full Curated private teacher-lesson is **not** gated by Wave 1–4 calendar? | **Confirm** — homework is immediate |
| **DC-1** | Gradual atlas ramp vs freeze pool ~5k? | **Ramp gradually** after Track T |
| **DC-2** | 80% gzip — split shards vs raise limits? | **Split first** |
| **DC-3** | When design on-demand practice? | After Wave 2 ~10–15k **or** 80% budget |
| **DC-4** | When introduce server? | Only checkpoint C; static default |
| **DC-5** | LLM on server? | **Later, gated**; never validity/morphology |

---

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Confusing Track T with Track A | This section; #5903 comments |
| Coverage vanity → bad drills | Eligibility fail-closed |
| Static budget cliff | 80% triggers; shard v2 |
| Rights regressions | Provenance required |
| Solo driver thrash | FLEET-FIRST seat rules |

---

## 8. Immediate next actions (ordered)

1. **Track T:** full Curated private teacher-lesson v5 (~1029) into Practice — extend #5905 / #5792 (not stop at 40)
2. Local smoke: several Curated private teacher-lesson lemmas → Practice CTA works
3. Banner-rate sample on random non-Curated private teacher-lesson atlas pages
4. Advisor finish on this draft → lock DC-0…DC-5 for Track A
5. Only after Track T: Wave 2 batch 2.1

---

## 9. Related issues / docs

- Umbrella: #4387 · Tracking: #5903 · Plan PR: #5904
- Seed: #5790 · Schema: #5791 · Gold/factory: #5792 · Paste-text: #5882 · Durability: #5884
- Backend later: #4384 · #4920
- Plans: `2026-07-25-atlas-open-lexical-layer.md`, `atlas-entry-model-v1-and-corpus-fill.md`, `PRACTICE-HUB-SPEC.md`

---

## 10. Advisor ask

Review as **architecture / ramp design**, not code nits. Explicitly affirm **DC-0** (teacher list is immediate). Return APPROVE / APPROVE-WITH-CHANGES / BLOCK on DC-0…DC-5.

---

*Draft for advisor consensus. Track T priority is operator-locked; Track A thresholds need advisors + operator GO.*
