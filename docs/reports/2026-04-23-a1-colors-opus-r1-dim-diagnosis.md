# a1/colors Opus R1 — three-dim root-cause diagnosis (#1449)

> **Status:** diagnostic only. No code, prompt, plan, wiki, or writer-rule
> change proposed for merge in this PR. The report is the decision
> substrate for the next dispatch.
>
> **Author:** Claude Opus 4.7 @ xhigh · 2026-04-23
> **Scope:** residual writer-quality gap on `a1/colors` after #1447
> (canonical anchors) and #1448 (tokenizer fix) land.

---

## 0. Up-front note: dim-name reconciliation

The dispatch brief reports a 9-dim review with these failing scores:
Actionable 3.0, Naturalness 4.0, Honesty 4.0.

The artifacts on this branch (including
`curriculum/l2-uk-en/a1/orchestration/colors/review-structured-r1.yaml`
and `curriculum/l2-uk-en/a1/orchestration/colors/v6-review-prompt.md`)
use a different 9-dim schema:

| Brief dim (failing) | Closest actual-review analogue | Actual score |
|---|---|---|
| **Actionable 3.0** | Pedagogical quality | 4/10 |
| **Naturalness 4.0** | Engagement & tone | 3/10 |
| **Honesty 4.0** | Dialogue & conversation quality *(see §3.3)* | 5/10 |

Two brief-described patterns are fully evidenced in this branch's module
+ review artifacts (code-switched pseudo-Ukrainian English; teaching
beats leaking to student text). A third (fabricated textbook citations
— "Vashulenko Grade 2 жовтий м'яч/зелений листок" etc.) is **not
present** in this branch's `colors.md`; the only textbook citation in
the module is `Bolshakova Grade 2 p.38`, which is authentic and traces
to the plan's `references:` block + `v6-skeleton-prompt.md:135`.

The diagnosis below treats the three failing dims named in the brief as
the **pedagogical quality / engagement-and-tone / dialogue-quality
triad** that failed in the real review, and anchors every claim to
evidence present on this branch. If the brief's dim names come from a
separate, un-checked-in Opus review run with a different schema, the
mapping above is where to start the reconciliation.

---

## 1. Executive summary (200 words max)

**All three failing dims share one dominant root cause: the contract
generator feeds the writer a `required_terms` list that is 80%
grammatical-scaffolding Ukrainian (e.g. `для`, `мові`, `активно`,
`вчимо`, `пару`, `такий`, `поділених`, `типами`), and the writer —
doing exactly what contract-compliance asks of it — stuffs those
tokens into English narrative sentences.**

- **Pedagogical quality 4/10** — primarily caused by the
  `required_terms` pipe forcing Ukrainian function words into
  English exposition, which degrades teach-then-practice flow into
  pidgin; secondary cause: plan teaching-beats written in Ukrainian
  prose that the writer lifts near-verbatim into student text.
- **Engagement & tone 3/10** — primarily caused by the same
  `required_terms` pipe (code-switched voice never sounds like a
  teacher); secondary cause: no positive teacher-voice constraint in
  the section prompts compensating for it.
- **Dialogue & conversation quality 5/10** — unrelated to
  `required_terms`; primary cause is a plan `dialogue_situations`
  specification that contains English framing metadata which the
  writer rendered literally as English narration between Ukrainian
  turns.

One fix (fix the contract generator) closes two dims; the third
needs a small plan-authoring-convention nudge.

---

## 2. Attribution framework

For each dim I attribute the low score to one or more of:

- **plan** — the plan YAML (`curriculum/l2-uk-en/plans/a1/colors.yaml`)
- **wiki** — the locked wiki brief (`wiki/pedagogy/a1/colors.md`)
- **prompt** — the section-write prompts (`v6-chunk-XX-prompt.md`) and
  `v6-review-prompt.md`
- **corpus** — retrieval quality via `wiki-excerpts.yaml` / sources MCP
- **writer-rule** — rules/gates enforced by the build pipeline
  (contract generation, chunk builder, audit gates)

Every attribution cites a specific line/file.

---

## 3. Per-dim analysis

### 3.1 Pedagogical quality (Actionable) — 4/10

#### Pattern

English meta-exposition dominates instruction. Ukrainian learner-target
forms are present as examples, but the *teaching language* itself is
English with Ukrainian grammatical scaffolding tokens welded in,
producing sentences that neither a beginner-English reader nor a
beginner-Ukrainian reader can parse cleanly.

#### Evidence (minimum 3 concrete quotes)

1. **`colors.md:39` (section `## Кольори`, P1)**
   > "Ukrainian has twelve **базових кольорів, поділених за двома
   > типами прикметників**: the **тверда група** (hard group) and the
   > **м'яка група** (soft group). This division follows **такий**
   > самий патерн as adjective agreement from Module 9."
   - What's wrong: the noun phrase "базових кольорів, поділених за
     двома типами прикметників" is a genitive participle construction
     that only makes sense in pure Ukrainian grammar. Sticking it
     inside an English matrix clause ("Ukrainian has twelve …") makes
     the learner parse a Ukrainian genitive string they have zero
     tools for at A1. "такий самий патерн as adjective agreement"
     is ungrammatical in both languages.
   - Reviewer echo:
     `review-structured-r1.yaml:17-19` (Pedagogical quality evidence:
     "dominated by English meta-exposition instead of Ukrainian-first
     teaching flow").

2. **`colors.md:78` (section `## Підсумок`)**
   > "This module covered twelve basic colors and the essential skill
   > of **узгодження кольорів** — matching color adjectives to nouns by
   > gender and number. The agreement follows the same **правилами**
   > you practiced in **модуль 9**…"
   - What's wrong: `правилами` is the Ukrainian instrumental plural of
     `правило`. An A1 learner has never seen the instrumental case.
     Embedding it inside "follows the same **X** you practiced in
     module 9" teaches the string "правилами" as if it were a lemma,
     priming a wrong form. Same for `модуль 9` (nominative) where the
     prepositional `у модулі 9` would be the Ukrainian equivalent —
     but the module meant this to be read as an English noun phrase.

3. **`colors.md:39`**
   > "This division follows такий самий патерн as adjective
   > agreement from Module 9."
   - What's wrong: `такий` is a demonstrative determiner that cannot
     stand alone in Ukrainian without its phrase; splicing it into
     English as if it were a noun is teaching the learner a broken
     collocation.

#### Root-cause attribution

| Cause | Weight | Evidence |
|---|---:|---|
| **writer-rule (contract generator)** | 70% | `scripts/build/phases/plan_contract.py:42-51` — `_extract_terms` pulls up to 8 Cyrillic tokens ≥3 chars from the concatenated teaching-beats with a 6-word stopword list. For section `Кольори` it emitted `[базових, кольорів, поділених, типами, прикметників, Тверда, група, такий]`. For section `Синій ≠ блакитний` it emitted `[українській, мові, для, активно, вчимо, пару, синій, темно-]`. These are surfaced to the writer in the chunk prompt under `required_terms:` (`v6-chunk-02-prompt.md:98-106`, `v6-chunk-03-prompt.md:65-73`). The writer honors them. |
| **plan (teaching-beats style)** | 30% | `plans/a1/colors.yaml:51,63,183-188` — `content_outline` points are written as mixed Ukrainian prose ("Узгодження кольорів за правилами модуль №9", "такий самий патерн, як у модулі №9"). These Ukrainian strings land inside `teaching_beats` in the contract and the writer lifts fragments near-verbatim. Even if `required_terms` were fixed, the writer has a continuing incentive to mirror the Ukrainian prose style of the beats. |

**Not** attributable to wiki (`wiki/pedagogy/a1/colors.md` excerpts are
coherent Ukrainian and the writer isn't lifting them) or corpus
(relevant Bolshakova/Vashulenko chunks are retrieved correctly).
**Not** attributable to the section prompt's explicit instructions —
the prompt actually says "Do not use meta-pedagogical narration"
(`v6-chunk-02-prompt.md:14`), but it does not say anything about
avoiding code-switching, and it hands the writer the `required_terms`
list as a positive obligation.

---

### 3.2 Engagement & tone (Naturalness) — 3/10

#### Pattern

Teacher voice reads as a grammar textbook's specification, not as a
patient guide. Formulaic meta-openers ("This module covered…",
"You have learned…", "Now it is time…") appear in the summary. The
Ukrainian insertions disrupt cadence instead of providing
example-evidence.

#### Evidence

1. **`colors.md:78` (`## Підсумок`, opener)**
   > "**This module covered** twelve basic colors and the essential
   > skill of **узгодження кольорів**…"
   - What's wrong: the exact formulaic opener banned implicitly by
     the contract (`banned_error_patterns: - Meta-narration` —
     `contract.yaml:275`). The writer knows meta-narration is
     banned but its positive obligations override; with eight
     required Ukrainian scaffolding tokens to place and a 270-word
     minimum budget, the cheapest way to land them is formulaic
     English frames.

2. **`colors.md:41` (`## Кольори`, P2 transition)**
   > "Now meet the important exception."
   - What's wrong: canned tutorial voice, no teacher personality, no
     concrete image. The section is about sea-blue vs sky-blue — a
     place where the teacher voice could carry real weight.

3. **`colors.md:88` (`## Підсумок`, self-check item)**
   > "Look around your room and describe three things by color, one
   > adjective each. Say them aloud: «сірий ноутбук», «чорна
   > сумка», «біле ліжко»."
   - What's wrong: even the self-check is mechanical ("one adjective
     each"). Compare to the tone we hit on a1/hey-friend or
     a1/food-and-drink where teacher voice + a ready phrase appears.
     The writer had no positive tone target so defaulted to a spec.

#### Root-cause attribution

| Cause | Weight | Evidence |
|---|---:|---|
| **writer-rule (same contract generator)** | 55% | Same as §3.1 — code-switched voice cannot sound natural. Fixing `_extract_terms` alone will remove the worst disfluencies. |
| **prompt (no positive tone anchor)** | 45% | `v6-chunk-02-prompt.md:3` names the persona ("The Patient Guide") but §§ below give only *negative* style constraints ("Do not use meta-pedagogical narration"). There is no "voice target" block — no sample paragraph of the teacher voice, no tone anchors ("warm, concrete, 1 image per paragraph"). Under pressure from word-count minimums + `required_terms` pressure, the writer falls back to formulaic English. |

**Not** attributable to plan (the plan's `register: розмовний` line at
`plans/a1/colors.yaml:115` is correct intent; it is just not surfaced
in the prompt).

---

### 3.3 Dialogue & conversation quality (Honesty) — 5/10

> Mapping note: I cannot evidence an "Honesty 4.0" fabricated-citation
> finding on this branch. The module's one textbook citation
> (`colors.md:5` — Bolshakova Grade 2 p.38) is authentic and
> traces to the plan (`plans/a1/colors.yaml:117-118`) and the
> skeleton prompt (`v6-skeleton-prompt.md:135`). If the brief's
> Honesty dim was flagging dialogue authenticity rather than source
> fabrication, it maps onto the Dialogue & conversation quality
> score in this branch's review (5/10). I diagnose against that; if
> the user's intent was a true citation-fabrication dim, that dim
> has no evidence on this branch and the mapping needs user input.

#### Pattern

Named speakers and plausible turns exist, but the dialogue sections
are padded with English narration between turns that should be carried
by the Ukrainian itself, and one reply line is stilted.

#### Evidence

1. **`colors.md:23` (before Dialogue 2)**
   > "Ліза picks a party outfit with Дмитро's help. He also asks how
   > to recognize Оля, whom he hasn't met."
   - What's wrong: this is stage direction in English, landed as
     narration rather than unfolding in dialogue. Reviewer flagged
     this pattern (`review-structured-r1.yaml:104-106`: "the section
     is padded with English narration (`Meanwhile, Dmytro and
     Liza…`)" — slightly different wording, same class).

2. **`colors.md:29` (Dialogue 2, Liza's outfit reply)**
   > "**Ліза:** Білий. І сіре пальто, і коричневі черевики."
   - What's wrong: reviewer called this "clipped and robotic"
     (`review-structured-r1.yaml:53-54`); indeed it reads as a
     color-noun list, not a conversational turn. Compare to
     a1/many-things or a1/shopping dialogues where a reply has a
     filler + an emotion + a color.

3. **`colors.md:5` (before Dialogue 1)**
   > "Наталка visits a flower market. The scene draws on a poem
   > about colors (за мотивами вірша про кольори) from Bolshakova's
   > Grade 2 textbook (p. 38)."
   - What's wrong: the citation is authentic, but its placement —
     inline, English, before the dialogue — is stage-direction
     framing. A learner does not need to be told the scene's
     pedagogical provenance; that belongs in a colophon, not the
     narrative.

#### Root-cause attribution

| Cause | Weight | Evidence |
|---|---:|---|
| **plan (`dialogue_situations` spec)** | 60% | `plans/a1/colors.yaml:31-41` — the `setting:` fields for both dialogues are written as **English-friendly stage directions** with parenthetical linguistic metadata ("Описати: чорна сукня (f), білий светр (m)…"). The writer correctly read `setting:` as "render this as framing prose before the dialogue." The plan does not give a turn-by-turn skeleton (speaker→line), only a description of what should happen and which colors must land. |
| **prompt (no dialogue-specific output shape)** | 30% | `v6-chunk-01-prompt.md` for the Діалоги section inherits the generic section prompt; there is no dialogue-specific template like "render as: speaker-line × 5-8, then ≤2 sentences of analytical gloss, no stage directions." |
| **writer-rule (no narration-gate)** | 10% | The audit phase does not have a "dialogue section must be ≥70% dialogue lines" gate. Contract compliance today counts required terms, not conversation density. |

**Not** attributable to corpus (wiki and dialogue exemplars are fine),
wiki (the locked wiki brief does not prescribe stage-direction
framing).

---

## 4. Cross-dim synthesis

**Two of the three failing dims share one root cause.** Pedagogical
quality and Engagement & tone both fail primarily because the
writer is compelled by the contract to place 8 Cyrillic tokens per
section in an English narrative, and the only grammatically legal way
to do that is code-switching. Fix `_extract_terms` and both dims
will lift meaningfully.

Dialogue & conversation quality fails for a **different** reason
(plan-level `dialogue_situations` shape + no dialogue-output template
in the prompt). This fix is independent and cheaper.

Therefore the decision path is:

1. **One unified fix** for dims 3.1 + 3.2 — touches
   `scripts/build/phases/plan_contract.py` and `v6-chunk-prompt`
   template.
2. **One separate fix** for dim 3.3 — touches the plan-authoring
   convention doc + `dialogue_situations` shape.

---

## 5. Proposed fix

### 5.1 Fix for dims 3.1 + 3.2 — contract generator + prompt voice anchor

**File 1:** `scripts/build/phases/plan_contract.py`

Change the `_extract_terms` function to exclude grammatical
scaffolding and prefer **learner-target vocabulary and fixed
collocations** supplied elsewhere in the plan.

Specifically:

- **Drop** `_extract_terms` as the source of `required_terms` for
  the section contract. It is a fragile heuristic that was always
  going to produce exactly this kind of Goodhart failure: the top-8
  Cyrillic tokens of a Ukrainian sentence are function words.
- **Replace** with explicit extraction from the plan's
  `vocabulary_hints.required` (already curated by the
  curriculum-maintainer to be learner-target) **intersected with**
  the section's teaching-beat text — i.e., "of the required
  vocabulary items, which ones are relevant to this section?"
- **Add** a stopword list of Ukrainian grammatical scaffolding
  (function words, auxiliary verbs, demonstratives, common
  participles) — at minimum: `для, мові, активно, вчимо, пару,
  такий, поділених, типами, мотивами, базових, вірша, групи, варто,
  використовуються` and the 300-ish most frequent Ukrainian
  function words available from VESUM frequency data.
- **Keep** the 8-term limit but source from `must_introduce` +
  `recommended` vocabulary + named collocations in the plan
  (`карі очі`, `русяве волосся`, etc.).

**File 2:** section prompt template (`scripts/build/phases/` or
wherever `v6-chunk-XX-prompt.md` is generated) — add a positive
**voice anchor** block before the contract, e.g.:

```markdown
## Teacher voice (follow this shape)

Write in English as the narrative medium. Ukrainian appears ONLY as:
- bolded inline lexical items with gloss — «синій» (dark blue)
- block-quoted dialogue turns
- example phrases you are explicitly teaching

Do NOT embed Ukrainian grammatical forms (verbs, participles,
function words) inside English sentences. If you feel pulled to
write "follows the same правилами you practiced…", stop — write
"follows the same rules you practiced…" in English and introduce
«правило» separately as a lexical item if it is a teaching target.
```

### 5.2 Fix for dim 3.3 — plan dialogue shape + prompt template

**File 1:** `docs/best-practices/dialogue-situations.md` — add a
convention: `dialogue_situations[].turns:` is the canonical field;
`setting:` is metadata for the writer only and is NOT rendered
as framing prose. Each turn is `{ speaker, ua, en_gloss }`. The
plan for `a1/colors` then gets a turn-list lift for both dialogues,
using the textbook-anchored poem from Bolshakova as the source.

**File 2:** the section prompt for a `type: dialogue` section — add
a template: "Render as: H3 title (optional, Ukrainian), 5–8
speaker-turns in block-quote format, ≤2 sentences of analytical
gloss in English pointing at specific Ukrainian forms from the
dialogue. No narrative framing, no stage directions."

**File 3:** `scripts/audit/checks/` — optional new check
`dialogue_density.py` that counts non-dialogue-line prose in a
dialogue section and caps it at 30%.

### 5.3 Fix attribution summary

| File | Change shape | Dim(s) addressed |
|---|---|---|
| `scripts/build/phases/plan_contract.py:42-51` | `_extract_terms` redesign | 3.1, 3.2 |
| `v6-chunk-XX-prompt.md` template | add "Teacher voice" block | 3.1, 3.2 |
| `docs/best-practices/dialogue-situations.md` | add `turns:` convention | 3.3 |
| `plans/a1/colors.yaml:31-41` | add `turns:` | 3.3 |
| `scripts/audit/checks/dialogue_density.py` (new) | 30% prose cap | 3.3 |

---

## 6. Dispatch-ready follow-up briefs

### 6.1 Brief — contract generator fix (dims 3.1 + 3.2)

Saved separately at `.worktree-briefs/fix-required-terms-extraction.md`
(not created by this diagnostic dispatch; draft body below for the
user to land as a follow-up).

```markdown
# Fix `_extract_terms` in plan_contract — #1449 follow-up

## Context
`scripts/build/phases/plan_contract.py:42-51` emits section
`required_terms` by taking the first 8 Cyrillic tokens ≥3 chars
from concatenated teaching-beats. For the `a1/colors` contract
this produced `[для, мові, активно, вчимо, пару, синій, темно-]`
(section 3) and `[базових, кольорів, поділених, типами,
прикметників, Тверда, група, такий]` (section 2) — function
words and grammatical scaffolding, not learner-target vocabulary.
The writer honors these as hard requirements, producing
code-switched English sentences like "This division follows такий
самий патерн as adjective agreement from Module 9" that wreck the
pedagogy and engagement dims (see
`docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md`).

## Task
Rewrite `_extract_terms` to source from
`plan["vocabulary_hints"]["required"]` + `recommended` +
`content_outline[].points` collocation heuristics (words in
«guillemets» or `code-fences`), NOT from arbitrary Cyrillic
tokens in the prose. Keep the 8-term limit. Add a test fixture
using the colors plan that asserts `required_terms` does not
contain `для`, `мові`, `активно`, `вчимо`, `пару`, `такий`,
`поділених`, `типами`.

## Verify
- Unit test on colors plan passes
- Regenerate `orchestration/colors/contract.yaml` and confirm
  section 2's `required_terms` is ⊂ `{червоний, жовтий, зелений,
  синій, чорний, білий, сірий, блакитний, коричневий, рожевий,
  помаранчевий, фіолетовий, колір}`
- Run smoke on a1/colors end-to-end; verify dim 3 (Pedagogical
  quality) lifts to ≥7 and dim 6 (Engagement & tone) to ≥6

## Agent
Codex — this is pure pipeline code. Do NOT dispatch to Gemini
(content work, wrong tool).
```

### 6.2 Brief — dialogue_situations shape (dim 3.3)

```markdown
# Plan convention: dialogue_situations[].turns — #1449 follow-up

## Context
Dim 3.3 (Dialogue & conversation quality) failed on a1/colors
because the plan's `dialogue_situations[].setting` field was
written as an English stage direction; the writer rendered it
as framing narration before the dialogue. See diagnosis report.

## Task
1. Extend `docs/best-practices/dialogue-situations.md` to define
   `turns:` as a required sibling of `setting:`, with shape
   `[{speaker, ua, en_gloss}]`. `setting:` becomes writer-only
   metadata, never rendered.
2. Update `plans/a1/colors.yaml` to add `turns:` for both dialogues
   (use the textbook-anchored content already in the review/
   module — Bolshakova p.38 flower-market poem; outfit dialogue
   with Дмитро/Ліза).
3. Update `v6-chunk-XX-prompt.md` template: if
   `current_section.dialogue_acts` is non-empty, inject a render
   template requiring block-quote turns + ≤2 gloss sentences.
4. (Optional) Add `scripts/audit/checks/dialogue_density.py`
   capping prose at 30% of dialogue-section body.

## Verify
- a1/colors re-write produces a dialogue section that is ≥70%
  speaker-turn lines
- dim 9 (Dialogue & conversation quality) lifts to ≥8

## Agent
Claude (prompt/plan-authoring work — this is within the core
curriculum-maintainer scope).
```

---

## 7. Prediction

Under the assumption that **#1447 and #1448 have already landed** and
**both proposed fixes (§5.1 and §5.2) are implemented**, here is my
score prediction for a fresh Opus R1 run on `a1/colors`. I am
deliberately **not** optimistic — a reviewer that previously scored
Pedagogical quality 4/10 is calibrated and won't swing to 9/10 just
because code-switching is gone.

| Dim (this-branch schema) | Current | Predicted | Reasoning |
|---|---:|---:|---|
| Plan adherence | 5 | 7 | Still loses some points on section-level word budgets unless a separate fix lands. |
| Linguistic accuracy | 8 | 9 | #1448 kills the tokenizer-corruption class; minor orthographic slips may remain. |
| Pedagogical quality | 4 | 7 | Code-switching gone → teach-then-practice flow readable; still not brilliant without corpus uplift for A1. |
| Vocabulary coverage | 7 | 8 | Better `required_terms` surface learner-target items, writer hits them. |
| Exercise quality | 8 | 8 | Unchanged; the activity-order fix is orthogonal. |
| Engagement & tone | 3 | 6 | Natural English teacher voice lifts this, but "Patient Guide" style isn't positively anchored enough to get 8+. |
| Structural integrity | 8 | 8 | Unchanged. |
| Cultural accuracy | 9 | 9 | Already a strength; unchanged. |
| Dialogue & conversation quality | 5 | 8 | `turns:` plus dialogue-density gate lifts this meaningfully. |

**Overall:** 6.1 → **~7.8**. MIN (current = 3) → predicted **6**.
That is **still below** the 8.0-per-dim publish threshold — so the
module will need one more R2 correction pass, but it should escape
`REJECT` / `plan_revision_request` terminal and reach an R2 that can
heal to publish.

If the prediction looks too pessimistic, the variable most likely
underestimated is Pedagogical quality (if the corpus uplift from the
locked wiki is bigger than I'm crediting, 7 could go to 8).

---

## 8. What this diagnostic does NOT claim

- **I did not verify** that the brief's "Honesty 4.0" dim maps to
  Dialogue & conversation quality in this branch's review. If the
  user's review run used a schema where Honesty explicitly scored
  fabrications, that dim has no supporting evidence on this branch
  (the only textbook citation is authentic) and the mapping needs
  user input.
- **I did not test** the proposed fix. §5 is design, not
  implementation; the follow-up briefs in §6 are what get
  dispatched.
- **I did not verify** my prediction empirically. §7 is a calibrated
  bet, not a measurement.

---

## 9. Appendix — `required_terms` ⇒ module-text mapping (evidence log)

For the user to spot-check attribution. Each row: a token emitted by
`_extract_terms` + the module sentence it landed in.

| Section | Emitted term | Module line | Exact quote |
|---|---|---|---|
| Діалоги | `Вибір` | `colors.md:3` | "### Діалог 1 — **Вибір** букета…" |
| Діалоги | `букета` | `colors.md:3` | "### Діалог 1 — Вибір **букета**…" |
| Діалоги | `квітковому` | `colors.md:3` | "…на **квітковому** ринку" |
| Діалоги | `ринку` | `colors.md:3` | "…на квітковому **ринку**" |
| Діалоги | `мотивами` | `colors.md:5` | "…за **мотивами** вірша про кольори…" |
| Діалоги | `вірша` | `colors.md:5` | "…мотивами **вірша** про кольори…" |
| Кольори | `базових` | `colors.md:39` | "Ukrainian has twelve **базових** кольорів…" |
| Кольори | `кольорів` | `colors.md:39` | "…базових **кольорів**, поділених…" |
| Кольори | `поділених` | `colors.md:39` | "…кольорів, **поділених** за двома…" |
| Кольори | `типами` | `colors.md:39` | "…за двома **типами** прикметників…" |
| Кольори | `прикметників` | `colors.md:39` | "…типами **прикметників**: the тверда група…" |
| Кольори | `Тверда` | `colors.md:78` | "**Тверда** група (the hard group)…" |
| Кольори | `група` | `colors.md:39, 41, 78` | "…the тверда **група**…" |
| Кольори | `такий` | `colors.md:39` | "This division follows **такий** самий патерн…" |
| Синій ≠ бл. | `українській` | `colors.md:59` | "В **українській** мові для рівня A1…" *(inside `:::info` Ukrainian block — properly placed here)* |
| Синій ≠ бл. | `мові` | `colors.md:59` | "В українській **мові** для рівня A1…" *(same, OK placement)* |
| Синій ≠ бл. | `для` | `colors.md:59` | "В українській мові **для** рівня A1…" *(same, OK)* |
| Синій ≠ бл. | `активно` | `colors.md:59` | "…ми **активно** вчимо цю пару…" *(OK — inside the Ukrainian info block)* |
| Синій ≠ бл. | `вчимо` | `colors.md:59` | "…ми активно **вчимо** цю пару…" *(OK here)* |
| Синій ≠ бл. | `пару` | `colors.md:59` | "…активно вчимо цю **пару**…" *(OK here)* |
| Синій ≠ бл. | `синій` | `colors.md:54-72, pervasive` | (legitimate learner-target) |
| Підсумок | `Узгодження` | `colors.md:78` | "…essential skill of **узгодження** кольорів…" |
| Підсумок | `кольорів` | `colors.md:78` | "…**кольорів** — matching color adjectives…" |
| Підсумок | `правилами` | `colors.md:78` | "The agreement follows the same **правилами** you practiced…" |
| Підсумок | `модуль` | `colors.md:78` | "…in **модуль** 9, now applied…" |
| Підсумок | `Тверда` | `colors.md:78` | "**Тверда** група (the hard group) includes…" |
| Підсумок | `група` | `colors.md:78` | "…hard **група** includes eleven…" |
| Підсумок | `червоний` | `colors.md:78` | "**червоний** стіл, червона книга…" |
| Підсумок | `стіл` | `colors.md:78` | "червоний **стіл**, червона книга…" |

**Observation:** in section 3 (Синій ≠ блакитний), the writer solved
the `required_terms` obligation cleverly by wrapping the function-word
demands inside a dedicated Ukrainian `:::info` block with an English
gloss below it — which is acceptable pedagogy. In sections 2 and 4,
the writer had fewer degrees of freedom (prose only, no info-box
escape hatch) and degraded to code-switching. This is consistent with
the attribution: writers under `required_terms` pressure will
code-switch by default; giving them a structural escape (info block)
partly rescues the dim but does not help where structure-less prose
is required.

---

*End of report — 2026-04-23, Claude Opus 4.7 @ xhigh.*
