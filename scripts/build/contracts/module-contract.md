<!-- version: 1.0.0 | updated: 2026-04-23 | GH #1431 -->
# Module Contract — Shared Reference for Writer and Reviewer

> **Purpose.** This document is the single source of truth for what a
> Ukrainian-language module must satisfy. The writer's job is to produce
> content that satisfies it; the per-dimension reviewer's job is to
> score against it. Neither side may import criteria from outside this
> document. Neither side may penalize or skip behavior this document
> explicitly allows.
>
> When the contract conflicts with a hard-coded rule in a prompt
> template, the contract wins. Prompt templates are views; this is the
> model.

## How the contract is specialized per module

Every build specializes this contract with three per-module artifacts:

1. **Plan YAML** at `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` —
   section order, word budgets, teaching beats, required vocabulary.
2. **Shared contract YAML** rendered as `{CONTRACT_YAML}` in both
   writer and reviewer prompts — the plan's section contract, activity
   obligations, dialogue acts, factual anchors, banned error patterns.
3. **Level-immersion policy** from `scripts/config.py`
   `IMMERSION_POLICIES[{level}]` — the band-specific scaffolding rule
   for the module's number within its level (e.g. `a1-m07-14`).

The three together — this document, the plan, and the level policy —
form the complete contract for a single module. The writer and each
per-dim reviewer see all three.

## §1 Level contract — scaffolding language (binding)

**Authority:** `scripts/config.py` `IMMERSION_POLICIES[{level}]`.

The immersion band for the current module sets a quantitative target
(e.g. 10–38 % Ukrainian for `a1-m07-14`) AND a qualitative role for
each language. The band rule is injected verbatim into writer and
reviewer prompts as `{IMMERSION_RULE}`.

**Writer side.** Match the band's target and language roles. If the
band says "English carries the explanation, Ukrainian appears in
examples / dialogues / vocabulary anchors," do exactly that. Do NOT
translate Ukrainian explanatory prose from the wiki brief into the
module — the brief's language and the module's scaffolding language
are independent.

**Reviewer side.** Score scaffolding language ONLY against the band's
target and roles. English-dominant prose at A1 early bands is
contractually correct, not a defect. Score <8 on a language-related
dimension ONLY if:

- the module falls OUTSIDE the band's quantitative target (too much
  Ukrainian at A1, or too little Ukrainian at B1+); OR
- Ukrainian examples are translated into English in their anchor role
  (Ukrainian examples must stay Ukrainian at every level); OR
- scaffolding-language roles are mixed chaotically (paragraphs
  zig-zag between full Ukrainian and full English in the same
  section).

**Reviewer must NOT penalize:** English explanatory prose between
Ukrainian examples at A1, English task instructions at A1/A2, or
short English glosses after Ukrainian dialogue turns at A1.

## §2 Section contract — cover every item

**Authority:** plan YAML `teaching_beats.sections[*].teaching_beats`
and `section_contract.covers` when present.

Each section lists the items it MUST cover, a word budget (typically
`{target: 300, min: 270, max: 330}`), and an ordered activity
obligation chain.

**Writer side.** Every item in the section's covers/beats list MUST
appear in that section's prose. Do NOT silently defer an item to a
later section — that is the #1431 `Кольори` failure (contract promised
12 colors, writer delivered 6 + синій and pushed the rest to Section
3).

When the 270–330 budget cannot fit every contracted item at readable
density, emit a structured overflow block at the end of the section:

```
<section_overflow>
section: "Кольори"
reason: 12 colors + hard/soft split exceeds 330 words at A1 density.
items_needing_more_budget:
  - "блакитний color introduction (was deferred)"
  - "compound shade формулу (темно-/світло-)"
proposed_budget_delta: "+60 words"
</section_overflow>
```

The convergence loop treats `<section_overflow>` as a plan-revision
signal (plan-authoring bug, not writer bug) — not a review failure.
The writer still covers every item; the block documents that the
budget constraint fought the coverage constraint.

**Reviewer side.** Score plan-adherence against whether every covered
item appears in its section. An explicit `<section_overflow>` block
in the writer output is a POSITIVE honesty signal — do NOT penalize
it. Penalize ONLY silent deferrals (an item listed in Section N's
contract that was moved to Section N+1 without overflow disclosure).

## §3 Dialogue contract — corpus-grounded or nothing

**Authority:** plan YAML `dialogue_acts[*]` when present, plus
`mcp__sources__search_sources` over `textbook_sections` +
`ukrainian_wiki` + ULP.

When a section's contract includes dialogue (the section is `Діалоги`,
`Dialogues`, or any section whose contract lists a `dialogue_acts`
entry), the writer MUST ground the dialogue in the corpus before
drafting. Concrete protocol:

1. Extract the dialogue situation from `dialogue_acts[].setting` and
   `function` (e.g. `"На квітковому ринку — Якого кольору?"`).
2. Call `mcp__sources__search_sources` with a Ukrainian query biased
   toward the scenario (e.g. `"діалог на ринку квіти кольори"`).
3. Take the top 2–3 hits from `textbook_sections` or `ukrainian_wiki`
   as anchors. Match their register. Re-use their common turn-taking
   phrases (Добрий день, Дякую, Будь ласка, Скажіть, будь ласка, …).
4. If the search yields zero hits, emit a `<!-- VERIFY -->` marker
   against the dialogue and mark the uncertainty explicitly rather
   than inventing.

**Writer side.** Do NOT invent Ukrainian dialogue from scratch when
the corpus has real A1 scenarios. Invented A1 dialogue at A1 density
is the #1431 Dialogue dim failure.

**Reviewer side.** Score dialogue authenticity against corpus match
when the contract has `dialogue_acts`. Stiff, interrogation-style,
or English-narrated dialogue is a defect. A dialogue with one or two
corpus-matched turn-taking phrases is PASS-level even if the rest is
writer-composed.

## §4 Pedagogical voice contract — allow-list and block-list

**Human-normal textbook phrases — ALLOWED (reviewer must NOT penalize):**

These are standard L2 textbook-teacher register. They appear in
Bolshakova, Zakharyjchuk, Vashulenko, Avramenko textbooks. They are
content-anchored, not vacuous:

- "You have learned..."
- "Now it's time to..."
- "Let's review..."
- "In this module..."
- "By the end of this lesson..."
- "Here's how to..."
- "Try this now..."
- "Notice that..."
- "Look at..."
- "Read aloud..."

**Vacuous filler — BANNED (writer must NOT produce, reviewer MAY penalize):**

These are content-free. They inflate word count without teaching:

- "Great job!", "Don't worry, it's easy!", "You're doing amazing!"
  (generic praise — the Cheerleader)
- "In this section, we will explore..." followed by nothing specific
  (the Announcer — note: "In this module..." + a specific teaching
  point IS allowed; the banned pattern is the empty transition)
- "This is a very important concept that you will use frequently in
  your daily life." (no specific teaching — the Filler)
- Repeated boilerplate across more than one section

**Distinguishing test.** An opener is ALLOWED if the next clause
teaches something specific to Ukrainian (a word, a sound, a pattern,
a rule). It is BANNED if the next clause is empty framing without
Ukrainian anchor.

Example ALLOWED: "You have learned that hard-group colors follow
-ий / -а / -е. Now compare soft-group синій: -ій / -я / -є."

Example BANNED: "You have learned a lot in this section. Great job!"

## §5 Honesty contract — VERIFY is a positive signal

**Authority:** `scripts/build/phases/v6-write.md` Rule #11.

The writer MUST flag uncertain claims with `<!-- VERIFY: {claim} -->`.
This is a positive honesty signal — the reviewer scores its presence
positively, not negatively, on the honesty axis.

**Writer side.** When the plan, brief, or pre-training disagree with
each other on a word, stress, rule, or example, surface the
disagreement with a VERIFY marker. Do not silently pick the version
that "feels right."

**Reviewer side.** Zero VERIFY markers in a module that has a
genuine plan-vs-authority ambiguity is a honesty-axis defect. One or
two VERIFY markers anchored to specific claims is GOOD. Many VERIFY
markers without specific claims (scattered hedging) is a defect.

## §6 Activity-marker contract

**Authority:** plan YAML `activity_obligations[*]` with `id`, `type`,
`focus`.

**Writer side.** Place `<!-- INJECT_ACTIVITY: {exact_id} -->` markers
in prose, not DSL blocks, not exercises inline. The marker must come
AFTER the teaching prose the exercise tests, not before. If the
contract has N obligations, the writer places N markers.

**Reviewer side.** Score exercise placement against this rule. A
marker placed BEFORE the teaching it tests is a defect (Round-1
colors: `match-up-appearance` placed before appearance collocations
taught). A marker placed AFTER is PASS.

## §7 Forbidden-words contract

**Authority:** `scripts/build/quick_verify.py` `SEVERE_RUSSIANISMS` +
`scripts/build/phases/v6-write.md` forbidden-word table.

The following Russian tokens are hard-banned — the post-write toxic
token scanner fails the build on any hit, even inside dialogue, even
in quoted examples:

| Russian (FORBIDDEN) | Ukrainian (USE THIS) |
|---|---|
| хорошо | добре |
| конечно | звичайно / певна річ |
| спасибо | дякую |
| пожалуйста | будь ласка / прошу |
| ничего | нічого |
| сейчас | зараз |
| тоже | теж / також |
| здесь | тут |
| кот | кіт |
| кон | кін |

Reviewer on Language dim: any hit = max 6.0/10.

## §7a Canonical anchors contract — decolonization-critical facts

**Authority:** `data/canonical_anchors.yaml` (shared registry used by
both the module pipeline and the wiki compiler; loaded via
`scripts/wiki/discipline.py::load_canonical_anchors`).

A finite, enumerated set of Ukrainian facts carry state-constitutional
or dictionary authority AND have known LLM failure modes producing
decolonization-harmful alternatives. The registry lists each anchor
with:

- `topic_uk` — what the anchor is about (e.g. "Прапор України")
- `correct` — the canonical form the writer MUST use verbatim (e.g.
  "синьо-жовтий")
- `forbidden[].pattern` — regex(es) for known drift forms the writer
  MUST NOT produce (e.g. "блакитно-жовт" for the flag)
- `forbidden[].reason` — decolonization rationale for the rejection
- `authority` — where the canonical form comes from

**Writer side.** When the module touches a topic covered by an anchor,
the writer must use the `correct` form verbatim. Never paraphrase an
anchor. Never invent alternates. The writer prompt injects a
Ukrainian-language table of all forbidden patterns with rationales
before drafting begins.

**Reviewer side.** The **Factual** and **Honesty** dims REJECT any
module containing a forbidden-pattern match. The **Language** dim
treats a forbidden match as max-6.0 (same as §7 Russianisms). Each
reviewer sees the registry rendered as a "REJECT if matched" list in
English.

**Mechanical enforcement.** After writer output is produced, a
deterministic pass runs `run_discipline_checks` and records any
violations as a `discipline_repair` log event. Anchor violations get
`<!-- VERIFY: ... -->` markers inserted next to the offending phrase
so downstream audits and human review surface them without the
surrounding sentence collapsing.

**Update policy.** Anchors with a `last_verified` field (current
president, current PM) must be re-verified on any state-figure change.
Other anchors (flag, anthem, trident, orthographic pairs) are stable
and do not expire.

**Scope.** This contract applies only to anchors explicitly listed in
the registry. It is not a license to reject any Ukrainian form the
reviewer personally disagrees with — the registry is the authoritative
floor. If a Ukrainian fact is wrong but not in the registry, file a
registry PR; do not REJECT the module on that basis.

## §8 Per-dim reviewer scope

Each per-dim reviewer scores ONE dimension, using ONLY that
dimension's clauses from this contract:

| Dim | Clauses it scores against |
|---|---|
| factual | §5 honesty + factual_anchors in plan YAML |
| language | §7 forbidden words + Ukrainian linguistic quality (VESUM, Правопис 2019) |
| decolonization | cultural framing (out of scope for tuning here; current 2026-04-23 scores are 8.8+) |
| completeness | §2 section contract covers list |
| actionable | §1 scaffolding + §4 pedagogical voice (concrete teaching, not abstract) |
| naturalness | §4 pedagogical voice allow-list/block-list + §1 scaffolding roles |
| plan_adherence | §2 section contract + §6 activity markers placement |
| honesty | §5 honesty + VERIFY markers as positive signal |
| dialogue | §3 dialogue contract (corpus-grounded when `dialogue_acts` present) |

A reviewer that scores OUTSIDE its column imports criteria from
outside the contract and violates this document.

## §9 Dispute protocol

If writer and reviewer disagree on whether a passage satisfies the
contract, the escalation is:

1. Reviewer names the exact clause of this document it believes is
   violated (e.g. "§4 block-list: Great job!").
2. Writer re-reads that clause and either corrects or flags the
   clause as ambiguous with a `<!-- VERIFY: contract §N -->` marker.
3. If the clause is ambiguous, the next plan-revision round treats it
   as a contract-authoring bug and escalates to human review.

Reviewer may NOT cite criteria outside this document (e.g. "LLM-tell
pattern" absent from §4 allow-list/block-list). Writer may NOT ignore
a clause because a prompt template says otherwise — the contract
supersedes templates.

## §10 Test enforcement

`tests/test_contract_reference_sync.py` asserts at CI time that:

- `scripts/build/phases/v6-write.md` references this document by path
- every `scripts/build/phases/v6-review/v6-review-*.md` references
  this document by path
- the Naturalness reviewer carries the §4 allow-list literal
- the per-dim reviewer templates carry `{IMMERSION_RULE}` or its
  calibration clause from §1
- the writer prompt carries the `<section_overflow>` protocol from §2
- the writer prompt carries the dialogue-retrieval mandate from §3

If any of these pin-tests fails, CI fails. Divergence is detected
before a build runs.
