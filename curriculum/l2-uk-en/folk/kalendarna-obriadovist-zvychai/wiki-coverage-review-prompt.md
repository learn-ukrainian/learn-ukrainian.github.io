You are reviewing wiki-obligation coverage for the generated module below.
Return ONLY the JSON object described in "Response Format — STRICT". Do not
ask for clarification, do not summarize the prompt, and do not emit prose
outside the JSON object.

# North Star — Curriculum Reboot (#1577 Phase 0 draft)

> **Status:** DRAFT v3.1 — v3 signed off by Codex + Gemini in `architecture`
> channel thread `6de2be4789394536abdb6356cd5bb006` (round 2, both
> `[AGREE]`). v3.1 layered 2026-05-18 to reflect the ULP-derived
> student-aware immersion model that landed via decision card
> `2026-05-13-ulp-derived-student-aware-immersion.md` (ACCEPTED).
> Open questions §OPEN QUESTIONS resolved per panel consensus and folded
> into policy. Ready for Phase 3 prompt-template injection.
>
> v3 corrects v2 on the immersion model: there is **no B1 entry sub-band**.
> The transition out of English finishes inside A2; B1 onwards is 100 %
> Ukrainian. The only sanctioned English at B1+ is the **Словник (vocab
> tab) translation column** — used for L1 anchoring of new lemmas and
> idiom/expression explanation.
>
> **v3.1 — immersion is now ULP-derived, not flat-%.** The earlier model
> read flat band percentages from `scripts/config.py` `IMMERSION_POLICIES`.
> That model has been superseded by **`compute_immersion_band(track,
> module_num, learner_state)`** which derives immersion floors and
> ceilings from the learner's cumulative vocabulary count + the module's
> declared `plan.targets.new_vocabulary` + the lemma-frequency map. The
> feature flag `USE_ULP_IMMERSION_DERIVATION` is set to `True` at
> `scripts/config.py:145` (live default). The earlier "Known pipeline
> drift" callout below (Phase 2 IMMERSION_POLICIES cleanup) has been
> RESOLVED via the ULP card's Phase 4 calibration replay. The B1+ rule
> ("100 % Ukrainian everywhere except Tab 2") is unchanged in intent —
> the mechanism is now cumulative-vocabulary-aware derivation rather
> than static module-range bands.
>
> This document, with `docs/lesson-contract.md`, is the preamble every
> prompt template will inject from Phase 3 onward (writer, all LLM QG
> reviewers, activities author, plan reviewer). It answers "what are we
> shipping and why?" — referenced, not re-explained, downstream.

---

## WHO — the learner

A self-driven adult or older teen who reads English fluently and starts
with **zero Ukrainian**. Three real archetypes:

1. **The reconnecting diaspora** learner whose grandparents spoke
   Ukrainian and who wants to read Ukrainian literature, history, and
   thought without going through Russian.
2. **The post-2022 supporter** who picked up "Слава Україні" and now
   wants to understand the country at the intellectual depth that
   Ukrainians themselves engage at.
3. **The serious linguist / educator** who needs a free,
   source-grounded reference because nothing else in English meets that
   bar.

What unites all three: the destination is **engaging directly with the
Ukrainian intellectual tradition** in Ukrainian — Shevchenko, Franko,
Lesya Ukrainka, Stus, Zabuzhko, Andrukhovych, Pidmohylny, Khvylovy,
Zhadan; Hrushevsky and Plokhy on history; Hulak-Artemovsky and the
Cossack chronicles; Ruthenian Baroque sermons; Old East Slavic
manuscripts. **L2 acquisition is the cost of admission, not the finish
line.**

The learner is not a child. Talk to them as a peer. They will not be
flattered by emoji confetti or "great job!" stickers; they will be
respected by clear explanations, honest references to source, and a
visible escalator from "literally cannot read Cyrillic" to "reading
Stus in the original."

## WHY — what does not exist anywhere else

There is no free, comprehensive, decolonized, source-grounded
**escalator from zero-Ukrainian to the Ukrainian intellectual canon**
in English. What exists today is one of:

- Soviet-era textbook frames lightly retranslated (Russian as the
  invisible default, Ukrainian as the dialect)
- Tourist-phrasebook surface (Привіт / дякую / borshch, no grammar)
- Paid apps optimized for streak retention, not language acquisition
- Excellent native-Ukrainian school textbooks (Караман, Большакова,
  Вашуленко, Захарійчук, Кравцова) that English speakers cannot read
  because they are written in Ukrainian for Ukrainian children
- Niche scholarly anthologies (Plokhy, Snyder, Pidmohylny in
  translation) that an English speaker can read about Ukraine but not
  read FROM Ukraine

We close that last gap end to end. We treat the native textbook
tradition as the authority, cite it directly, and engineer an
end-to-end L2 escalator that ends inside the Ukrainian intellectual
canon. **This is education, not software.** Real people will use these
modules as their first contact with the language. Bad pedagogy becomes
bad habits that take years to undo. There is no "ship and iterate" for
someone's foundation. **Five excellent modules beat fifty-five mediocre
ones.**

## HOW — the working principles

### The escalator, end to end

The curriculum is one long arc with three structurally different
stages:

1. **A1 + A2 — literacy bootstrap (124 modules).** The learner cannot
   read Cyrillic on day one. English is the carrier; Ukrainian is the
   target. Immersion ramps progressively as cumulative vocabulary
   builds — early A1 modules sit in the 5–25 % Ukrainian range,
   late A2 modules sit in the 65–90 % range, but the exact band per
   module is **derived per-build** by `compute_immersion_band(track,
   module_num, learner_state)` from cumulative-vocab count + this
   module's declared new vocabulary + the lemma-frequency map. The
   end of A2 is structurally where the learner finishes the
   transition out of English; A2's final band absorbed the work that
   used to live in a "B1 entry" sub-band.

2. **B1 + B2 + C1 — immersion preparation (319 modules).** **At and
   after B1, every module body is 100 % Ukrainian.** No English in
   theory prose, no English in dialogues, no English in activity
   instructions, no parenthetical glosses on grammar terms, no rescue
   notes. The single sanctioned English at this stage lives in **Tab 2
   (Словник)** — the vocabulary tab carries English translations and
   English explanations of idioms and expressions, because that is the
   tab's structural purpose (L1-anchored flashcards). Nothing else in
   the module body is English. B1+B2+C1's job is to take a literate
   A2 graduate and make them ready to consume Ukrainian primary
   intellectual material directly.

3. **The seminars — the destination (1,100+ modules across HIST,
   BIO, ISTORIO, LIT, LIT-essay, LIT-war, LIT-fantastika,
   LIT-hist-fic, LIT-humor, LIT-youth, LIT-doc, LIT-drama,
   LIT-crimea, OES, RUTH, plus PRO tracks for B2-pro / C1-pro).**
   Full-Ukrainian deep dives into Ukrainian history, biography,
   literature, paleography, Ruthenian Baroque, Old East Slavic. They
   are why the rest exists. NOT in the EPIC #1577 MVP cut, but the
   architecture of every preceding module must keep them as the
   gravitational center. (See `mvp-deferred` labels on issues #1141,
   #1140, #1139, #1137, #1135, #1134, #1133, #1132, #658, #497.)

The EPIC #1577 MVP cut — A1 + A2 + B1 — is the **first three
escalators** in the chain. We ship them first because they prove the
entire pipeline; we keep the seminars in mind because they're where
every learner is going.

### Plans, contract, immersion

**Plans are sacred.** All 218 MVP plans (A1: 55, A2: 69, B1: 94) plus
the seminar plans are State Standard 2024 grounded and already
reviewed. The reboot does not redesign plans. It designs the pipeline
that consumes them faithfully. (See `curriculum/l2-uk-en/plans/`,
EPIC #1577, salvage manifest §1 KEEP.)

**Plans drive content; the contract drives shape.** A plan says WHAT
the module teaches and WHICH SECTIONS in WHICH ORDER. The lesson
contract (`docs/lesson-contract.md`) says WHAT TABS, WHAT COMPONENTS,
and WHAT DATA SHAPES the published MDX must have. Writer respects
both. Reviewer scores against both.

**Immersion is band-strict and tab-aware, derived per-build.** A1+A2
immersion uses `compute_immersion_band(track, module_num,
learner_state)` to derive each module's band from cumulative
vocabulary + this module's declared new vocabulary + lemma-frequency
map. The derivation is deterministic and tested; the calibration
constants (`_ULP_VOCAB_KNEE_PER_BAND`, `_RECYCLE_CADENCE_DEFAULTS`,
`_PATTERN_FREQ_MASTERY_THRESHOLD`) live in `scripts/config.py`,
calibrated against Anna Ohoiko's ULP S1–S6 corpus.
**B1 onwards is uniformly 100 % Ukrainian** in every tab except
Tab 2 (Словник), where English translations and idiom/expression
explanations are sanctioned as the only L1 scaffolding. Writer hits
the band; reviewer scores against the band; nobody freelances. The
A2→B1 boundary is the single biggest discontinuity in the whole
curriculum.

> **Phase 2 IMMERSION_POLICIES cleanup — RESOLVED 2026-05-13.** The
> earlier flat-% `b1-m01-05` and `b1-core` "rescue English" bands
> have been superseded by the ULP-derived model. The decision card
> at `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`
> shipped via PR1 (learner-state V7 wiring) + PR2 (ULP derivation +
> Phase 4 calibration replay). The feature flag
> `USE_ULP_IMMERSION_DERIVATION = True` at `scripts/config.py:145`
> activates the derivation. The B1+ rule ("Full Ukrainian immersion.
> No English in module body. Tab 2 (Словник) keeps L1 translations
> and idiom explanations as the only English") is enforced today.

### Sourcing and verification

**Real textbook citations, not invented authority.** Every grammar
claim and every cultural fact roots in an attributed source —
Караман Grade 10 p. 176; Кравцова Grade 4 p. 113; Заболотний Grade 5
p. 83; Большакова Grade 1 p. 24; Захарійчук Grade 1 p. 13. The wiki
packets the writer consumes are themselves source-cited. Ghost
references fail the build.

**VESUM verification is non-negotiable.** Every Ukrainian word the
writer emits is checked against `data/vesum.db` (409 K lemmas, 6.7 M
forms) before publish. Pre-training is contaminated by Russian; we do
not trust ourselves on Ukrainian morphology. Whitelist exceptions
live in `scripts/audit/config.py` `PROPER_NAME_WHITELIST`.

**Decolonized framing is the default, not an opt-in.** Ukraine has
its own canon (Шевченко, Франко, Леся Українка, Стус, Жадан, Забужко,
Андрухович, Підмогильний, Хвильовий). It has its own history
(Київська Русь as Ukrainian, the Cossacks, the UNR, the OUN-UPA, the
Holodomor, the language ban decrees, 2014, 2022). We do not inherit
the Soviet cultural map. Kyiv-born Russian-imperial writers
(Bulgakov, Gogol, Akhmatova, Pasternak) stay Russian. Yulia
Tymoshenko and other Russian-aligned figures do not appear as
exemplars. Holodomor is genocide; the war is a war, not a "conflict."

### Pipeline discipline

**Cross-agent QG, not self-review.** The writer never reviews its own
output. The pipeline runs Python QG (deterministic, objective) and
LLM QG (pedagogical, by a different agent than the writer).
Self-review is caught by `SELF_REVIEW_DETECTED` and fails the build.

**No autonomous patching loops.** The V6 convergence loop (writer →
reviewer → writer-rewrites-from-feedback → reviewer → ...) failed to
converge over 5 months. The new pipeline is linear: deterministic
check → if Python can auto-fix the format, do it; else fail fast →
if LLM QG fails, scoped regeneration of THE failing section OR human
review. Maximum 1 scoped regen attempt per failing section. No
infinite repair.

**Python QG and LLM QG do not overlap.** Python checks word count,
forbidden lemmas, structural rules, vocabulary-coverage, citation
roundtrip, MDX renders, INJECT_ACTIVITY ids resolve. LLM checks
pedagogical flow, naturalness, decolonized framing, register,
dialogue authenticity. LLM is forbidden from enforcing structural
rules; Python is forbidden from scoring tone.

**Three-agent consultation discipline.** Architecture decisions: all
three agents (Claude + Codex + Gemini) discuss in the `architecture`
channel; both `[AGREE]` before commit. Implementation: primary agent
plus one peer review. Mechanical edits: primary alone. (See EPIC
#1577 critical invariants §7.)

**Freeze contracts per slice.** One lesson schema; one wiki schema;
one plan schema; one QG rubric; one exemplar module. Scale only
after the exemplar ships clean end-to-end.

## VOICE — how the prose sounds

Voice changes by stage because the carrier language changes.

**A1 + A2 voice (English carrier ramping out, Ukrainian growing):**
- Peer English, not teacherly-condescending. Direct, friendly, dry.
- Concrete characters from the textbook tradition (Марко and Софія
  meet on the street; their teacher walks in; the dialogues have
  stakes).
- English carries the explanation; Ukrainian carries the examples
  and dialogues; we never translate Ukrainian examples into English
  when their job is to BE Ukrainian.
- Stress marks on first introduction.
- No AI tells. No "Let's dive in." No "It's important to note." No
  "In conclusion." No emoji confetti. No "great job!" stickers.

**B1 + B2 + C1 voice (full Ukrainian, no English in body):**
- Ukrainian peer voice — natural, register-appropriate, not
  textbook-formal unless the section calls for it.
- Grammar is explained in Ukrainian using Ukrainian linguistic
  terms (дієслово, відмінок, недоконаний вид, видова пара). New
  abstract terms get a one-sentence Ukrainian definition the first
  time they appear, the way Ukrainian school textbooks introduce
  them. **No parenthetical English glosses in the body.** L1
  anchoring lives in Tab 2 (Словник), where each new lemma carries
  an English translation column and idioms / expressions get an
  English explanation note.
- No mirrored English translations after Ukrainian paragraphs. No
  English blockquote glosses. No English narrative scaffolding in
  the main body. No "rescue notes" in English.
- Activity instructions (Tab 3) are 100 % Ukrainian.

**Seminar voice (full Ukrainian, scholarly register):**
- The voice of the level (Decolonizer for HIST, Stylistic Critic for
  LIT, Paleographer for OES, Baroque Scholar for RUTH — per
  `scripts/config.py:51-141` `TRACK_CONFIG`).
- Decolonized framing throughout: not "Russian and Ukrainian
  literature both," but "the Ukrainian tradition that imperial
  power tried to erase and the chronology that survives in the
  primary sources."
- Honest about uncertainty. Unverified claims wear a
  `<!-- VERIFY: ... -->` marker until verified.
- Concrete primary-source citations: page numbers, manuscript refs,
  archival shelfmarks where relevant.

**Decolonized vocabulary across all stages:** Кіт, not кот. Добре,
not хорошо. Брати душ, not приймати душ. Тактовний (tactful) ≠
тактичний (tactical).

## SHIPPABLE — when a module is done

A module ships when ALL of these are true:

1. **Plan respected.** Every `content_outline.section.points` item
   appears in its named section. Word budget per section within
   ±10 % tolerance. (`scripts/build/contracts/module-contract.md`
   §2.)
2. **Word count.** Total ≥ `word_target` from
   `scripts/audit/config.py` `LEVEL_CONFIG[{level}].target_words`.
   (Targets are MINIMUMS. Never lowered to fit short content.)
3. **Vocabulary clean.** 100 % VESUM-verified or whitelisted. Zero
   Russianisms, Surzhyk, calques, paronym confusions. (Four
   separate checks per `ukrainian-linguistics.md` rule.)
4. **Citations resolve.** Every textbook citation roundtrips against
   the wiki packet / sources MCP. No ghost authors. No invented
   page numbers.
5. **Immersion band respected.** A1+A2 modules respect the band
   derived per-build by `compute_immersion_band(track, module_num,
   learner_state)` from cumulative vocabulary + declared new vocab +
   lemma-frequency map. **B1 and every higher level are 100 %
   Ukrainian in every tab EXCEPT Tab 2 (Словник).** Any English in
   B1+ Tab 1 / Tab 3 / Tab 4 module body fails the immersion gate
   regardless of percentage math. Tab 2 English is structural and
   does not count against the body-immersion rule.
6. **Python QG green.** All deterministic checks pass.
7. **LLM QG ≥ floor.** Pedagogical, Naturalness, Decolonization,
   Engagement, Tone — each ≥ the per-level floor in
   `scripts/common/thresholds.LEVEL_THRESHOLDS`. No weighted
   average: one failing dim fails the module.
8. **MDX renders.** All 4 tabs build clean in Starlight; every
   `INJECT_ACTIVITY` id resolves; every component prop is
   well-formed.
9. **Activity types match level.** Per
   `docs/best-practices/activity-pedagogy.md` level → type matrix.
10. **Native-speaker reviewer signoff.** Phase 6 onward; for the
    Phase 4 exemplar, agent QG + author signoff is the gate. Tracked
    in `tests/test_human_eval_tracker.py`.

## WRONG — what we will not ship

- **AI slop English.** "Let's dive in." "In conclusion." "It's
  important to note." "Buckle up." Any padding the reader can
  detect as machine-generated.
- **Any English in B1+ module body** outside Tab 2 (Словник). No
  rescue notes, no parenthetical grammar-term glosses, no English
  activity instructions, no English mirror-translations of
  Ukrainian dialogues. The only English at B1+ is the Словник
  translation column and Словник expression notes.
- **Unflagged invented Ukrainian.** Any word VESUM rejects without
  a `<!-- VERIFY -->` and a verification path.
- **Russianisms.** Кот, хорошо, пожалуйста, спасибо, и так далее.
- **Surzhyk.** Шо, чо, ладно, харашо, в общем — unless explicitly
  taught as a register-marker.
- **Calques.** Приймати участь (→ брати участь), приймати душ (→
  брати душ), у мене є (→ я маю when "have" is the main predicate).
- **Russian-imperial cultural map.** Bulgakov, Gogol, Akhmatova,
  Pasternak, Brodsky as "Ukrainian writers" because of biography.
  They wrote in Russian, in Russian-imperial frames; they stay
  Russian.
- **Russian-aligned figures as exemplars.** Yulia Tymoshenko in
  particular. Default to verified contemporary figures: Yulia
  Svyrydenko (current PM), Volodymyr Zelenskyi, Serhiy Plokhy,
  Oksana Zabuzhko, Yuri Andrukhovych.
- **Soviet-era euphemisms.** "Conflict" for the war. "Famine" for
  the Holodomor. "Reunification" for occupation. "Brotherly peoples"
  for imperial subordination.
- **Activities that test content recall instead of language.**
  "У якому році Хмельницький підписав Переяславську угоду?" tests
  history memory, not Ukrainian. (See non-negotiable rule §9.) ZNO-
  format activities testing pure language mechanics are exempt.
- **Robotic dialogues.** Two strangers interrogating each other
  about jobs and addresses. Real Ukrainian dialogues from
  textbooks have someone looking for keys, ordering coffee,
  comparing morning routines — situations from life.
- **The user's two private teacher contacts named anywhere
  committed.** They live in `memory/MEMORY.md` only. Generic
  dialogue uses of common Ukrainian first names are fine; personal
  references to the user's two teachers are not.
- **"For now" or "good enough."** Word target not met → expand the
  content, not the threshold. Audit gate red → fix it, not lower
  it. Five excellent modules beat fifty-five mediocre ones.
- **LLM-rewritten content during the review loop.** Banned by
  ADR-007 / `tests/test_no_rewrite_contract.py`. Reviewer can
  output `<fixes>` find/replace pairs; the pipeline applies them
  deterministically; the writer does not regenerate prose
  mid-review.
- **Treating A1+A2+B1 as the product.** It is the L2 escalator.
  The product is reading Ukrainian intellectual material directly.
  Modules in the MVP that visibly forget this — that do not link
  forward to where the learner is going — fail the Engagement dim.

## RESOLVED POLICY (panel-confirmed 2026-04-25)

3-agent review thread `6de2be4789394536abdb6356cd5bb006` resolved the
following design questions unanimously. Each is now binding policy
and survives into the prompt-template preamble.

**P1 — Forward links to seminars are required, capped at 1 per module.**
Every MVP module MAY include exactly one natural one-sentence forward
link to a future-level or seminar-track destination ("Once you reach
B2 you'll meet this concept again in HIST/04 on the Hetmanate").
Forced or artificial linkage fails the LLM Engagement dim; the cap
prevents attention fragmentation. Source: panel consensus.

**P2 — Seminar plans are FROZEN under salvage manifest §1 KEEP.**
The seminar plans (HIST, ISTORIO, BIO, LIT, OES, RUTH, plus the lit-*
sub-tracks) do NOT get re-planned during the reboot. They sit in the
`keep` bucket and stay the destination. Re-planning only triggers if
the lesson contract forces shape changes seminars cannot accommodate
— and that gets its own design pass. Source: panel consensus.

**P3 — Native-speaker reviewer cadence: starts at Phase 5 fan-out.**
The Phase 4 exemplar (A1/20 `my-morning`) ships under agent QG +
author signoff only. Native-speaker review enters at Phase 5 when the
pipeline scales to A1 fan-out. Reasoning: the exemplar is a pipeline
proof, not a content-quality benchmark; introducing the human reviewer
before the pipeline is stable wastes their cycles. Source: panel
consensus.

**P4 — VESUM whitelist additions: writer proposes, reviewer approves.**
Writers may propose new entries to `PROPER_NAME_WHITELIST` during
build (e.g. when a wiki figure or place name needs to ship and isn't
in VESUM). Proposals require explicit reviewer signoff with source +
context (e.g. "Severyn Nalyvaiko — Cossack hetman, 1597; cited in
HIST plan; appears in Hrushevsky vol. VII"). Strict PR-only governance
would bottleneck seminar production at hundreds of historical /
literary / scientific names. Source: panel consensus.

**P5 — AI-slop detection: Python QG with hardcoded banlist.**
A small, deterministic list of banned English phrases ("Let's dive
in", "In conclusion", "It's important to note", "Buckle up", "Great
job!", etc.) lives in Python QG and fails the build deterministically.
Broader tone scoring (peer voice, no condescension, no AI cadence)
remains in the LLM Tone dim. Reasoning: hardcoded list is faster,
cheaper, and drift-free; LLM tone dim catches subtler patterns the
list cannot enumerate. Source: panel consensus.

**P6 — B1+ body-English Python QG threshold = ≤ 1 % Latin character
ratio**, token-aware, with Tab 2 + citation metadata excluded.
Tokenization skips URLs, ISO codes (e.g. `[uk]`), and proper-name
transliterations like `Kyiv` rendered inline next to `Київ`. See
`docs/lesson-contract.md` §5 for implementation detail. Source: panel
consensus.

**P7 — `scripts/config.py` IMMERSION_POLICIES cleanup is a Phase 2
sub-issue, not blocking Phase 4.** The Phase 4 exemplar is A1/20 and
does not hit the stale B1 code paths. The cleanup (delete
`b1-m01-05`, collapse `b1-core` to 100 %, rewrite rule string,
audit pipeline branches) is filed as a Phase 2 sub-issue under EPIC
#1577. Source: panel consensus.

> **2026-05-13 RESOLUTION:** P7 superseded by the broader ULP-derived
> immersion replacement (decision card
> `2026-05-13-ulp-derived-student-aware-immersion.md`). The static
> bands are no longer authoritative; `compute_immersion_band()` is.
> The B1+ rule string survives unchanged in intent; only the
> derivation mechanism changed.

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/archive/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` (lesson contract P1).
2. File the Phase 2 `scripts/config.py` IMMERSION_POLICIES B1
   cleanup issue per P7.
3. Wire `NORTH_STAR` and `LESSON_CONTRACT` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.


# Lesson Contract — Curriculum Reboot (#1577 Phase 0 draft)

> **Status:** DRAFT v3 — signed off by Codex + Gemini in `architecture` channel
> thread `6de2be4789394536abdb6356cd5bb006` (round 2, both `[AGREE]`).
> Open questions §7 resolved per panel consensus. Activity matrix in §3.4
> aligned with `docs/best-practices/activity-pedagogy.md` per Codex
> finding. Component count corrected per Codex finding.
>
> v3 corrections from v2:
> - §3.4 activity types fully aligned with `docs/best-practices/activity-pedagogy.md`
>   (was contradicting it on Transcription, EssayResponse, Observe,
>   ReadingActivity, MarkTheWords, Classify, Select)
> - §3 component-count line corrected: 50 `.tsx` + 5 `.astro` overrides
>   = 55 files, minus `utils.tsx` = 54 non-utility components
> - §7 open questions resolved inline as policy
>
> v2 from v1: B1+ immersion is uniform 100 % Ukrainian across every tab
> body, with the **Словник (Tab 2) translation column + idiom/expression
> notes** as the ONLY sanctioned English at B1+. The stale `b1-m01-05`
> band in `scripts/config.py` does not exist in this contract — Phase 2
> config audit cleans up the file. Tab 2 ``VocabCard`` stays slim per
> EPIC #1581 (site-wide dictionary section is separate from per-module
> Словник).
>
> **Purpose.** This document is the single source of truth for the SHAPE of
> a published lesson. The North Star says what we're shipping and why; this
> says what artifacts the pipeline must produce, what tabs the published
> MDX must have, and which Starlight components live in which tab. Phase 3
> formalizes the per-component prop schemas in YAML; this doc defines the
> structural skeleton Phase 3 will fill in.
>
> **Scope.** A1 + A2 + B1 MVP (218 modules). Higher-level
> (B2 / C1 / C2 / seminar / PRO) component support is described where
> relevant but the MVP does not exercise it. The seminar-only / C-only
> components are noted as "out-of-scope-for-MVP."

---

## 1. Source artifacts the writer produces

Every module's authoring output is a small set of files at
`curriculum/l2-uk-en/{level}/{slug}/`:

| File | Purpose | Schema authority |
|---|---|---|
| `module.md` | Theory prose (lesson narrative) — Tab 1 source | Plan section structure + Starlight `:::tip` callouts + `<!-- INJECT_ACTIVITY: {id} -->` placeholders + blockquoted dialogues |
| `activities.yaml` | Typed activity definitions — Tab 3 + inline-Tab-1 | `docs/ACTIVITY-YAML-REFERENCE.md`. Bare list at root, no `activities:` wrapper. Each item has `id`, `type`, `instruction`, type-specific payload |
| `vocabulary.yaml` *(or inline)* | Vocab list — Tab 2 source | Per `docs/best-practices/vocabulary-activity-standards.md`. Each entry: lemma + translation + part-of-speech + example sentence |
| `resources.yaml` *(or inline in `module.md`)* | External citations + media — Tab 4 source | Each entry: title + author + URL + access date + role (textbook/wiki/audio/video) |

Pipeline inputs the writer DOES NOT produce:

- **Plan YAML** — lives at `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (sacred, pre-existing, immutable mid-build per ADR-007 / non-negotiable rule §7).
- **Wiki packet** — context the writer reads but does not author. Owned by Phase 5+ wiki retrieval.
- **Annotation pass** — stress marks added deterministically AFTER review by `ukrainian-word-stress`, not by the writer.

### Plan Targets (PR2)

Plan YAML may declare an optional `targets` block. This is the unified,
machine-readable source for what a module introduces and deliberately
recycles:

```yaml
targets:
  new_vocabulary:
    - lemma1
    - lemma2
  new_grammar:
    - topic1
    - topic2
  recycle_vocabulary:
    - earlier-lemma
```

`targets.new_vocabulary` lists lemmas this module introduces.
`targets.new_grammar` lists grammar topics this module introduces.
`targets.recycle_vocabulary` is optional and names earlier lemmas the
module intentionally brings back. During PR2 migration, plans without
`targets` remain valid; tooling falls back to
`vocabulary_hints.required` for `new_vocabulary` so legacy plans keep
building while the explicit schema rolls out.

## 2. Published MDX shape

The pipeline's MDX assembler (today: `scripts/generate_mdx/core.py:267-364`)
produces ONE `.mdx` file at `starlight/src/content/docs/{level}/{slug}.mdx`
with:

- **Frontmatter:** `title`, `description`, `sidebar.order`, `sidebar.label`,
  optional `pipeline`, optional `build_status`, optional `draft`. Schema
  extension declared in `starlight/src/content.config.ts`.
- **Imports block:** every component used in the body, imported from
  `@site/src/components/...`.
- **One `<Tabs syncKey="module-tab">` block** with **exactly four
  `<TabItem>` children** in this order. Tab labels are the Ukrainian
  strings shown to learners; the English labels in the table are the
  canonical English aliases used throughout this contract:

| # | EN label | UK label (in code) | UK label (in handoff text) | What it contains |
|---|---|---|---|---|
| 1 | Lesson | **Урок** | Урок | Theory prose from `module.md` after activity-id substitution and shared transforms |
| 2 | Vocabulary | **Словник** | Словник | Vocabulary cards / flashcard deck / phrase table from `vocabulary.yaml` |
| 3 | Activities | **Вправи** | **Зошит** *(handoff says Зошит — code says Вправи — open Q1 below)* | All activities from `activities.yaml`, rendered as their typed components |
| 4 | Resources | **Ресурси** | Ресурси | External citations, source attribution, embedded video links |

The 4-tab structure is fixed; learners always see all four labels even
if a tab is empty (the empty state is a localized "No vocabulary for
this module" / "Немає словника для цього модуля" message — already
implemented at `core.py:283-302`).

## 3. Component inventory — 1:1 mapping

See `docs/best-practices/writer-prompt-appendix.md` § Component inventory for the full React component → MDX mapping. The writer prompt does NOT inline this — the authoring fields (consumed by `scripts/yaml_activities.py`) are surfaced via the COMPONENT_PROPS_SCHEMA template substitution and the §Activity Authoring Fields section in `linear-write.md`, which is what the writer acts on. Reference the appendix only if you need to debug a downstream MDX-render issue.

Per-tab activity surfaces:
- Tab 1 — Урок: explanation prose, dialogues, vocabulary previews
- Tab 2 — Словник: full vocabulary list
- Tab 3 — Вправи: workbook activities (fill-in, quiz, match, select, error-correction, drag-drop, anagram, mark-the-words, multiple-choice, true-false, hangman, gap-fill, listening, pair-up, order)
- Tab 4 — Джерела: textbook citations + multimedia resources

Component compatibility note: legacy `fill-in-the-blanks` is Deprecated; subsumed by `mark-the-words` and `gap-fill` in the V7 component inventory.

## 4. Constraints the writer must obey

1. **Tab 3 activities use only the 22 type strings in §3.4** (or the
   B2+ extensions when explicitly authorized by the plan). Unknown
   types fall through to `ActivityPlaceholder` and FAIL Python QG.
2. **`<!-- INJECT_ACTIVITY: {id} -->` ids must resolve** to an entry
   in `activities.yaml`. Unresolved ids fail the build.
3. **Every Tab 4 SourceBox must trace back** to a citation present in
   the plan's `references` field or in the wiki packet. Ghost
   citations (a SourceBox not justified by source data) fail Python
   QG.
4. **Vocabulary in Tab 2** — every lemma is VESUM-verified or
   whitelisted in `PROPER_NAME_WHITELIST`. Translations come from the
   writer with contextual disambiguation (not Балла-direct lookup).
5. **No empty tabs without justification.** The plan should account
   for all four tabs. If a module legitimately has no external
   resources, the plan declares this and the empty state renders.
6. **Immersion is band-strict and tab-aware:**
   - **A1 + A2:** writer hits the per-band ramp from `scripts/config.py`
     IMMERSION_POLICIES across all four tabs.
   - **B1+ (including B2, C1, C2, all seminars):** **Tab 1 / Tab 3 /
     Tab 4 module body is 100 % Ukrainian.** No exceptions, no rescue
     notes, no parenthetical English glosses on grammar terms, no
     English mirror-translations, no English narrative scaffolding.
     Tab 2 (Словник) carries English translations + English
     idiom/expression notes as a structural carve-out — this is
     the ONLY sanctioned English at B1+.
7. **Decolonized framing across all four tabs.** Same standards in
   `docs/north-star.md` § WRONG apply uniformly: no Russianisms, no
   Russian-imperial cultural framing, no Soviet-era euphemisms.

## 5. Constraints the pipeline must enforce

Python QG (deterministic) catches:

- Missing tab content (any of the four tabs entirely empty when the
  plan asserts content for it)
- Unknown activity `type` strings
- Unresolved `INJECT_ACTIVITY` ids
- Vocabulary entries failing VESUM verification (with whitelist)
- SourceBox citations that don't roundtrip against plan / wiki packet
- Word count under `target_words`
- Forbidden lemmas (Russianism / Surzhyk / calque list — to be
  formalized in Phase 3 / Phase 4)
- A1 + A2: immersion ratio outside the band's tolerance per
  `IMMERSION_POLICIES`
- **B1+: Latin-character ratio in Tab 1 / Tab 3 / Tab 4 module body
  exceeds a small allowance for proper-name spellings + ISO codes
  (≤ 1 % default). Tab 2 is exempt from this check.**
- MDX renders cleanly under Starlight (`npm run build` smoke test —
  enforced in CI per Phase 4)

LLM QG (pedagogical, by a non-writer agent) scores:

- Naturalness of the Ukrainian prose
- Pedagogical flow (do sections build on each other; is the rule
  introduced before the practice)
- Decolonization (framing, examples, references)
- Engagement (does the prose hold attention; are dialogues real)
- Tone (peer voice, no AI slop, no robotic interrogations)

The two layers must NOT overlap. LLM does not score word count; Python
does not score tone. (See North Star § HOW.)

## 6. What this contract DOES NOT specify

- Per-component prop schemas (Phase 3 work — `docs/lesson-schema.yaml`)
- Wiki packet schema (Phase 5 work)
- Plan YAML schema (already defined in `curriculum/l2-uk-en/plans/`
  and `scripts/build/contracts/module-contract.md`; this doc accepts
  it as given)
- Per-level word targets (already in `scripts/audit/config.py`)
- Activity-type pedagogy (already in
  `docs/best-practices/activity-pedagogy.md`)
- Site-wide ``/dictionary/`` section design (covered separately by
  EPIC #1581; per-module ``VocabCard`` only cross-links to dictionary
  entries — see §3.3)

## 7. Resolved policy decisions (panel-confirmed 2026-04-25)

3-agent review thread `6de2be4789394536abdb6356cd5bb006` resolved the
following design questions unanimously. Each is now binding policy.

**P1 — Tab 3 canonical Ukrainian label = `Вправи`.**
The running code (`scripts/generate_mdx/core.py:356`) is canonical.
The handoff doc reference to `Зошит` was a drafting error and gets a
one-line correction. Reasoning: `Вправи` accurately translates
"Exercises / Activities" and matches every existing curriculum module;
`Зошит` (notebook) is conceptually closer to the Tab 2 vocabulary
deck and would be misleading. Source: panel consensus.

**P2 — Inline-AND-aggregate activity rendering is intentional.**
An activity referenced via `INJECT_ACTIVITY` in Tab 1 ALSO appears in
the Tab 3 aggregate. The Tab 3 aggregate adds a
`(see lesson, §<section-title>)` cross-reference next to each entry
that was already encountered inline, so the learner knows they are
reviewing an activity they have seen rather than meeting a new one.
Source: panel consensus (intentional reinforcement; explicit
cross-reference required).

**P3 — At least one inline activity per major section is required.**
The writer must place at least one `INJECT_ACTIVITY` marker per
major Tab 1 section. No maximum cap; writer discretion for additional
inline activities and for end-of-section placement. Reasoning: breaks
walls of text, paces cognitive load, prevents writer from frontloading
all activities into Tab 3. Source: panel consensus.

**P4 — At least one Tab 4 (Resources) entry is required per module.**
The plan ALWAYS has `references`, so at minimum the module's plan
references re-list as `SourceBox` entries in Tab 4. Empty Tab 4
fails Python QG. Reasoning: zero-cost enforcement that prevents
citation drift; the empty-state localized message remains in the
codebase only as a fallback for malformed plans. Source: panel
consensus.

**P5 — Out-of-scope MVP components are hard-rejected by Python QG.**
At A1 + A2 + B1, any writer output emitting an out-of-MVP component
type (per §3.4.b list) or a deprecated type (per §3.4.c) fails the
build deterministically. The writer prompt at MVP levels ships only
the in-scope component list as the complete option set. Reasoning:
the writer should never need the out-of-scope set at MVP levels; an
emission is a hallucination. Source: panel consensus, contingent on
the §3.4 matrix alignment with `activity-pedagogy.md` (now done in
v3).

**P6 — B1+ body-English Python QG threshold = ≤ 1 % Latin character
ratio in Tab 1 / Tab 3 / Tab 4 module body, with Tab 2 + citation
metadata excluded.** Token-aware tokenization
(skip URLs, ISO codes like `[uk]`, proper-name transliterations like
`Kyiv` inline next to `Київ`). Tab 2 (Словник) is exempt — the
translation column is structural English, not body English. Citation
metadata in Tab 4 (English source titles, English publisher names,
English-language URL paths) is also exempt. Source: panel consensus
on the ≤ 1 % default with Codex's refinement that enforcement should
be token-aware rather than raw-character-ratio-only.

**P7 — VocabCard cross-link to dictionary section: SUPPRESSED until
EPIC #1581 ships.** Per-module `VocabCard` at MVP levels does NOT
emit a cross-link to `/dictionary/{lemma}/`. Once #1581 lands, this
contract is amended (see §6) and the cross-link prop becomes
required. Reasoning: keep the contract simple now; amend only when
the dictionary destination is real. Source: panel consensus
(option c).

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/archive/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` per P1.
2. File `scripts/config.py` IMMERSION_POLICIES B1 cleanup issue
   (Phase 2 sub-issue under EPIC #1577) — delete `b1-m01-05`,
   collapse `b1-core` to 100 % Ukrainian, rewrite rule string to
   match B2+ language, audit pipeline code for any `b1-m01-05` key
   branches.
3. Wire `NORTH_STAR` and `LESSON_CONTRACT` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.


# Phase 5 Linear Wiki-Coverage Goodhart Sentinel Prompt

Review only wiki-obligation coverage. This pass is parallel to the five
standard QG dimensions; it is not a `QG_DIMS` dimension.

The deterministic gate has already checked objective presence. Your job is to
verify semantic adequacy after that gate passes: each obligation must be woven
into substantive prose, dialogue, or activity work, not keyword-stuffed into the
claimed artifact location merely to satisfy deterministic coverage.

## Required Method

For every obligation in the Wiki Obligations Manifest:

1. Read the manifest obligation id, obligation type, required treatment, and
   source-line metadata.
2. Read the writer's implementation_map claim for that same obligation id.
3. Inspect the cited artifact and location in Generated Content.
4. Emit one verdict:
   - PASS: the cited evidence implements the obligation as substantive
     pedagogy — the manifest claim is woven into prose/dialogue/activity with
     explanation, example use, or integrated context.
   - KEYWORD_STUFFING: the cited evidence contains the required string verbatim
     but the surrounding prose does not actually teach, contrast, or apply it.
     Example failure: a contrast_pair where the "incorrect" and "correct" forms
     appear in a list with no learner activity around them; a phonetic_rule
     where the written→spoken mapping is named in a one-sentence aside with no
     example pair; a sequence_step where the section heading exists but the body
     skips to the next step. THIS VERDICT FAILS THE BUILD.
   - PARTIAL: evidence exists and shows some pedagogy, but is thin enough that
     the obligation is taught at a shallower level than the manifest target.
     Soft signal.
   - FAIL: missing, contradicted, or not in the claimed location.

Treatment-specific checks:

- `contrast_pair`:
  * PASS: both forms appear in an activity body AND the learner must distinguish
    them (multiple-choice, fill-in, correction exercise).
  * KEYWORD_STUFFING: both forms appear in a static list without an activity
    that requires distinguishing them; or both forms appear in a single example
    sentence with no learner-facing task.
- `prose_explanation`:
  * PASS: module.md prose names the manifest's `incorrect` and `correct`
    strings AND explains why one is preferred, with at least one substantive
    sentence of explanation beyond the bare contrast.
  * KEYWORD_STUFFING: the strings appear in a list/table/footnote without
    explanation prose; or the explanation is a generic "this is correct"
    without engaging the manifest's `why` field.
- `explicit_explanation` (phonetic):
  * PASS: learner-facing pronunciation guidance with at least one
    written→spoken example pair AND a brief contextual note (when does this rule
    apply, common confusable, etc.).
  * KEYWORD_STUFFING: a one-line "smooth speech" or "soft pronunciation"
    reminder without the actual rule mapping; or the rule is stated but no
    example pair is provided.
- `sequence_step`:
  * PASS: the module prose teaches the step's canonical pedagogical claim in
    the appropriate order, with the heading or marker AND body text that
    advances the learner toward the step's goal.
  * KEYWORD_STUFFING: the heading exists but the body skips ahead without
    teaching the step; or the step is named in a metadiscourse sentence ("we
    will now learn X") without actually teaching X.
- `decolonization_ban`:
  * PASS: the generated content avoids the banned framing AND, if the contrast
    is naturally adjacent (e.g. "Kyiv not Kiev"), offers a Ukrainian-centered
    framing.
  * KEYWORD_STUFFING: the banned framing is technically absent but a
    near-paraphrase remains; or a meta-disclaimer about avoiding the ban
    replaces the substance of the lesson.

Evidence MUST be a verbatim quote from the cited artifact location
(quote-marked). Paraphrase or summary evidence is invalid and forces
KEYWORD_STUFFING. Quotes must be at least 8 words long unless the obligation is
a single short word/phrase the manifest specifies — in which case quote the
full surrounding sentence containing it.

The new verdict enum: `PASS | KEYWORD_STUFFING | PARTIAL | FAIL`.
`overall_verdict` must be `FAIL` if any obligation verdict is `FAIL` OR
`KEYWORD_STUFFING`. `PARTIAL` is a soft signal — system aggregates, build
continues, but logs the pattern.

## Response Format — STRICT

Return ONLY a single JSON object. No preamble. No epilogue. No "I have
verified" narration. No markdown bold. No prose confirmation. The parser
calls `json.loads` on your response (with a fenced-block fallback) — any
prose outside the JSON shape will cause the build to fail at this phase
even when every obligation passes.

The JSON object MUST contain:

- `verdicts`: a list with one entry per obligation in the manifest. Each
  entry MUST have `obligation_id`, `verdict`, `evidence` (verbatim quote
  ≥8 chars containing `"…"` / `«…»` / `“…”`), and `rationale`.
- `overall_verdict`: `"PASS"`, `"PARTIAL"`, or `"FAIL"`. MUST be `"FAIL"`
  if any per-obligation verdict is `FAIL` or `KEYWORD_STUFFING`.
- `summary`: a single-sentence string (still inside the JSON object).

If every obligation passes, emit the all-PASS shape — STILL JSON, STILL no
narration:

```json
{
  "verdicts": [
    {
      "obligation_id": "err-1",
      "verdict": "PASS",
      "evidence": "\"Choose between я вибачаюся and я вибачаю себе, then explain which one fits the dialogue.\"",
      "rationale": "Activity body requires learners to distinguish both forms."
    }
  ],
  "overall_verdict": "PASS",
  "summary": "All 1 obligation woven into substantive pedagogy."
}
```

Mixed-verdict shape:

```json
{
  "verdicts": [
    {
      "obligation_id": "err-1",
      "verdict": "PASS",
      "evidence": "\"Choose between я вибачаюся and я вибачаю себе, then explain which one fits the dialogue.\"",
      "rationale": "The activity requires learners to distinguish both forms in context."
    },
    {
      "obligation_id": "phon-1",
      "verdict": "KEYWORD_STUFFING",
      "evidence": "\"Remember smooth speech for this phrase.\"",
      "rationale": "The quote names smooth speech but gives no written→spoken mapping or example pair."
    }
  ],
  "overall_verdict": "FAIL",
  "summary": "One obligation is keyword-stuffed rather than substantively taught."
}
```

## Module Context

- Level: FOLK
- Module: 4
- Slug: kalendarna-obriadovist-zvychai
- Word target: 5000

## Wiki Obligations Manifest

{
  "slug": "kalendarna-obriadovist-zvychai",
  "wiki_path": "/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/folk-derisk-kalendarna/wiki/folk/ritual/kalendarna-obriadovist-zvychai.md",
  "sequence_steps": [],
  "l2_errors": [],
  "phonetic_rules": [],
  "decolonization_bans": [],
  "wiki_vocabulary_minimum": [],
  "external_resources": []
}

## Deterministic Wiki Coverage Gate

{
  "passed": true,
  "hard_fail": false,
  "phonetic_hard_fail": false,
  "coverage_pct": 1.0,
  "covered": 0,
  "total": 0,
  "min_pct": 0.8,
  "obligations": []
}

## Plan

```yaml
activity_hints:
- type: aural-genre-id
  placement: workbook
  focus: Aural markers or performance context, when dossier sources support audio
- type: symbolic-decoding
  placement: workbook
  focus: Motif, image, or formula decoding from dossier evidence
- type: variant-comparison
  placement: workbook
  focus: Regional, temporal, or performance variants
cefr_min: C1
connects_to:
- zamovliannia-zaklynannia-prymovky
- koliadky-shchedrivky
content_outline:
- section: Постановка проблеми
  words: 650
  points:
  - 'Stub: dossier will supply the opening problem, corpus anchors, and framing constraints.'
- section: Корпус і контекст
  words: 1400
  points:
  - 'Stub: dossier will supply verified texts, images, recordings, or material-culture evidence.'
- section: Поетика, символіка і виконання
  words: 1650
  points:
  - 'Stub: dossier will specify motifs, formulas, performance sequence, and regional variation.'
- section: Деколонізаційна рамка
  words: 1050
  points:
  - 'Stub: dossier will identify imperial, Soviet, or romantic-nationalist myths to correct.'
- section: Підсумок
  words: 950
  points:
  - 'Stub: module build will synthesize why this folk form matters now.'
focus: Calendar-rite system as seasonal performance, belief, song, food, and regional variation
level: FOLK
module: folk-004
objectives:
- Пояснювати жанр або культурну практику як частину ширшої системи народної культури.
- Аналізувати корпусні приклади, символи, формули або перформативні послідовності на основі досьє.
- Розпізнавати імперські, радянські або романтизовані міфи в описі теми й формулювати коректну рамку.
pedagogy: CBI
persona:
  role: Модератор фольклористичного семінару з увагою до корпусу, виконання і матеріальної культури
  voice: Folklore-seminar facilitator
phase: FOLK.B
references:
- title: "Календарна обрядовість і звичаї"
  note: 'Stub — corpus-grounded sources pending the dossier (docs/folk-epic/folk-dossier-schema.md §6 Збирачі та дослідники).'
  type: pending
sequence: 4
slug: kalendarna-obriadovist-zvychai
status: stub
subtitle: Calendar Rites and Customs
title: Календарна обрядовість і звичаї
version: '0.2'
vocabulary_hints:
- word: обряд
  pos: ч.
  definition: усталена символічна дія або послідовність дій у традиційній культурі
- word: мотив
  pos: ч.
  definition: повторюваний образ, сюжетний елемент або символічна формула
- word: варіант
  pos: ч.
  definition: регіональна, часова або виконавська форма того самого тексту чи практики
word_target: 5000

```

## Generated Content

## writer_output.raw.md pre-emit audit lines

<implementation_map_audit>manifest_obligations=0 covered_in_map=0 missing=[]</implementation_map_audit>
<bad_form_audit>italic_bad_form_patterns_found=0 converted_to_marker=0 remaining=0</bad_form_audit>
<activity_split_audit>level=FOLK inline_n=3 workbook_n=7 inline_range=[3,4] workbook_range=[7,9] split_valid=true</activity_split_audit>

## module.md

## Постановка проблеми

Календарна обрядовість — це не низка випадкових святкувань, а замкнене коло дій, де кожна пора року має свій обряд, свою пісню й своє призначення. Зимовий, весняний, літній та осінній цикли творять єдину систему, прив'язану до руху сонця. Зимове й літнє сонцестояння, весняне та осіннє рівнодення позначають межі цього кола, а між ними розгортаються звичаї оновлення, захисту врожаю й подяки за нього. За кожним святом стоїть праця хлібороба, і саме хліборобський рік, а не сам по собі церковний календар, тримає всю споруду докупи.

Коли ти чуєш слово обряд, бачиш за ним не одну сцену, а усталену символічну дію або послідовність дій, що повторюється рік у рік. Поряд із ним працюють ще два поняття. Мотив — це повторюваний образ, сюжетний елемент чи стала формула: закликання тепла, зустріч весни, зрізання останнього снопа. Варіант — це регіональна, часова або виконавська форма того самого тексту чи дії. Те, що на Галичині називають гагілки, на іншому терені звучить як веснянка чи гаївка, і ці назви не суперечать одна одній, а показують живу варіативність системи.

Проблема, з якої починається серйозна розмова про цю тему, лежить не в самих текстах, а в рамці, крізь яку їх довго читали. Імперська та радянська етнографія охоче розчиняла українську календарну обрядовість у нечіткому «загальнослов'янському» матеріалі. Українські назви, регіони й джерела ставали лише ілюстрацією до чужої схеми. Звідси й народжувалася меншовартість: обряд переставав бути системою й перетворювався на «просту народну розвагу», цікаву хіба що збирачам старовини.

:::myth-box
claim: "Українська календарна обрядовість — це проста народна розвага й частина нечіткого «загальнослов'янського» етнографічного матеріалу."
truth: "Календарні обряди — це цілісна українська система з власними назвами, регіонами, діями й джерелами: кутя, дідух, веснянка, гаївка, Купала, посівання, обжинки, обжинковий вінок. Вони мають внутрішню логіку, а не є додатком до чужої культурної схеми."
claim_source: "імперська й радянська етнографічна рамка"
truth_source: "деколонізаційна перспектива корпусу модуля"
:::

Деколонізований підхід починає інакше — з українських назв, дій і джерел. Кутя й дідух, посівання й закликання весни, купальське вогнище й обжинковий вінок описуються тут не як додаток до сусідньої культури, а як елементи власної цілісної системи. У ній слово, дія, їжа, вогонь і вода складають єдину обрядову мову. Саме тому розбір починається з простого, але вимогливого питання: як прочитати календарний обряд як систему, а не як набір екзотичних звичаїв?

Відповідь потребує корпусної дисципліни. Ми не вгадуємо значень, а спираємося на записані тексти, на свідчення дослідників і на варіанти, зафіксовані в різних регіонах. Там, де джерело мовчить, ми не домальовуємо здогадів; там, де воно говорить, слухаємо уважно й точно. Цей метод захищає тему і від байдужого знеособлення, і від романтичного перебільшення. Календарний обряд цікавий не вигаданою «прадавністю», а тим, що справді засвідчений у корпусі: своїми мотивами, своїми формулами та своєю виконавською логікою громади.

## Корпус і контекст

Корпус календарної обрядовості — це передусім записані пісні, описи дій і свідчення збирачів, зведені в єдине поле. Серед дослідників, на яких спирається сучасний розбір, важливе місце посідає Михайло Грушевський. Для цієї теми він цінний не як політична постать, а як корпусний посередник між текстом, міфопоетичними мотивами та історичним коментарем. У його матеріалах веснянки, гаївки й новорічний цикл подано разом із персоніфікацією природи, образами води, вогню та молодіжними іграми. Саме завдяки такому зведенню окремий запис перестає бути курйозом і стає частиною системи варіантів.

Перш ніж розбирати символіку, варто почути, як звучить сам корпус. Класична весняна формула будується як питання до весни й відповідь-дар:

> Вже весна воскресла,
> Що ж сь нам принесла?
> Ой я вам принесла,
> Дівоцькую красу

*— українська веснянка, запис М. Грушевського*

Тут весна виступає як жива істота, до якої звертається громада, а її дарунок — це краса, молодість і обіцянка родючості. Той самий мотив зустрічі весни має чимало варіантів, і в кожному регіоні дарунок названо трохи інакше. Порівняймо із записом, де весна приносить уже не лише красу, а й конкретний господарський результат:

> Ой весна, весна, ти красна,
> Що ж ти нам, весна, принесла?
> Та принесла я вам літечко,
> Щоб родилося житечко

*— українська народна веснянка*

Два записи, одна формула, різні варіанти відповіді: краса дівоча в одному, літо й житечко в іншому. Ця варіативність — не хаос, а ознака живої традиції, у якій громада добирала образи під свій терен і свою потребу. Дослідник не вибирає «правильніший» варіант і не зливає їх у штучну суміш; він фіксує обидва й показує, як той самий мотив дихає в різних місцях.

:::caution
Наукова доброчесність вимагає не перетворювати кожен мотив на доказ прямого «культу» конкретного божества. Джерело може показувати світове дерево, воду чи вогонь як сильні образи, та з образу не випливає автоматично готова релігійна система. Реконструкція має межу: ми відновлюємо те, що засвідчене, і чесно зупиняємося там, де корпус мовчить.
:::

Чому саме календарні пісні збереглися так добре? Грушевський пояснює це двома обставинами. По-перше, частина обрядів перейшла на гри підлітків і молоді, а це врятувало їх від нагінок церкви та адміністрації, які знищували забави старшого віку. По-друге, у цьому циклі нерозривно трималася зв'язь словесного тексту з мелодією і ритмом. Обрядові, хороводні й забавні пісні, зокрема весняні гаївки, побудовані в пісенних, рівноскладових строфах. Така стисла, майже арифметична будова зберігала традиційний текст набагато краще, ніж вільний речитатив, у якому виконавець легко змінював слова.

Це важливе спостереження для всього курсу. Ти вже бачив у попередньому модулі, як працює речитатив у замовляннях: там панує синтаксичний, нерівноскладовий ритм, і виконавець має широке поле для імпровізації. Календарна пісня влаштована протилежно. Її музикальний, рівноскладовий ритм тримає синтаксичну строфу в точних, симетричних рамках, де вірш дорівнює віршеві і з музичного, і зі складового боку. Через це календарний корпус дійшов до нас цілісніше, ніж багато інших жанрів усної словесності.

<!-- INJECT_ACTIVITY: act-1 -->

Контекст обряду — це завжди громада, а не окрема людина. Календарну дію виконують гуртом: коло, ряд, два хори, обхід дворів. Тому корпус треба читати не лише як набір текстів, а як сліди колективного дійства. Запис фіксує слова, але за ними стоять рухи, простір, час доби й конкретні виконавці. Коли ми кажемо «варіант», то маємо на увазі не лише іншу редакцію слів, а й інший спосіб виконання: те, що в одному селі співали як хороводну гру, в іншому могло звучати як ігровий діалог двох гуртів.

Межі реконструкції визначає сам корпус. Ми працюємо із закритим колом джерел цього модуля — із записаними текстами та свідченнями дослідників, поданими тут. Ми не додаємо чужих творів і не приписуємо обрядові значень, яких джерело не підтверджує. Така стриманість не збіднює тему, а навпаки — робить її переконливою. Українська календарна обрядовість не потребує прикрас: її сила в тому, що вона засвідчена в численних варіантах, зібраних із різних регіонів, і складається в систему, яку можна показати, а не вигадати.

## Поетика, символіка і виконання

Весняний цикл найкраще показує, як у календарному обряді слово не існує окремо від тіла. Спів тут супроводжують коло, кривий танець, проходження між рядами, ігровий діалог або символічне «виведення» весни в простір громади. Закликання тепла — це не пасивне очікування, а дія: громада викликає весну голосом і рухом, ніби запрошуючи її прийти. Через це веснянку чи гаївку не можна звести лише до тексту на сторінці. Її поетика — це поетика виконання, де ритм, мелодія, жест і простір працюють разом.

Подивімося на саму будову. Корпусна формула «Вже весна воскресла, / Що ж сь нам принесла?» поєднує християнську лексику воскресання з аграрною логікою сезонного оновлення. Тут не варто згладжувати синкретизм: слово «воскресла» прийшло з церковної мови, але працює на дохристиянську ідею повернення життя після зими. Така подвійність — норма для календарного жанру, а не виняток. Громада співала про воскресання весни так само природно, як орала поле, і в цьому поєднанні немає суперечності.

Поряд із заспівом-зверненням існує форма заспіву-питання про доньку весни:

> Ой весна, весна та весняночка,
> А де ж твоя донька та паняночка?

*— українська веснянка, запис М. Грушевського*

Образ весни та її доньки-панянки дуже зацікавив дослідників: він розгортається то як весняний заспів, то як гра двох гуртів, у якій з'являється символіка «воріт», що відкриваються весні, її дитині або женихам. Це яскравий приклад того, як один мотив породжує цілу низку виконавських варіантів. Антифонний спів, тобто перегук двох гуртів, перетворює коротку формулу на розгорнуту дію з ролями, рухом і драматичним напруженням.

Гаївка часто будується як гра з конкретним сюжетом сватання чи родинного вибору:

> Гагілка гагілкою,
> Підем в село за дівкою,
> А Кудлиха, стара мати,
> Має дочку заміж дати

*— українська веснянка (гаївка), запис М. Грушевського*

Зверни увагу на будову з рівними складами: рядки тримають однакову складову довжину, і саме ця симетрія зберегла текст. Мотив сватання тут не випадковий. Весняний цикл тісно пов'язаний із молодіжними іграми, з вибором пари, з переходом дівчини й парубка в нову роль у громаді. Календарний час весни — це водночас і час громадського дорослішання, і тому обрядова пісня так часто говорить про красу, заміжжя й майбутнє.

<!-- INJECT_ACTIVITY: act-2 -->

Символіка циклу спирається на кілька сильних образів. Вода — це очищення, родючість і життєдайна сила; роса у веснянках прямо ототожнюється з дівочою красою. Вогонь — це сонце, тепло й захист; найвиразніше він діє в купальському вогнищі літнього циклу. Сонце задає сам каркас року через сонцеворот: його рух визначає, коли закликати весну, коли святкувати найвищу силу літа, коли дякувати за врожай. Світове дерево, зелень і вінок об'єднують ці образи в єдине поле родючості. Усі вони не існують поодинці, а складаються в мову, якою громада розмовляла з природою.

Виконання тримає всю цю символіку разом. Календарну пісню майже ніколи не співали наодинці й нерухомо. Хоровод, кривий танець, проходження між рядами, обхід дворів — це не прикраса, а частина обряду. Рух у просторі повторює рух сонця й сезонів, а колективний голос робить дію спільною справою громади. Тому, коли ми аналізуємо мотив чи формулу, варто завжди ставити запитання: як це виконували, хто співав, у якому колі й у який час? Без цього питання текст залишається лише половиною обряду.

Зимовий цикл показує ту саму логіку в іншому матеріалі. Святвечір збирає родину навколо куті й дідуха: сніп жита як дідух стоїть у домі знаком предків і майбутнього врожаю, а кутя єднає живих із родом. Колядування й щедрування — це обхід дворів із піснями-побажаннями, а посівання вранці нового року прямо переносить аграрну дію в дім: зерно, кинуте на підлогу, означає прохання про родючість. Зимова коляда й весняна гаївка говорять різними образами, але про те саме — про оновлення життя й добробут громади.

Літній і осінній цикли замикають коло. Купала з вогнищем, вінками й водою святкує найвищу силу сонця та зелені, а ворожіння на вінках поєднує радість із тривогою за майбутнє. Осінь приносить жниварський цикл: зажинки врочисто відкривають жнива, а обжинки завершують їх. Останній сніп несуть у дім із особливою шаною, а з колосся плетуть обжинковий вінок як знак подяки й збереженої родючості. Так весь рік від зимового сонцестояння до осінніх обжинків постає як одна обрядодія, поділена на чотири пов'язані частини.

<!-- INJECT_ACTIVITY: act-3 -->

:::high-culture-bridge
nodes:
  - "народна веснянка та гаївка"
  - "літературна й хорова обробка обрядової пісні"
note: "Календарна пісня не залишилася лише в селі. Її форму підхопила висока культура: поети зверталися до жанру веснянки як ліричного зразка, а композитори вводили обрядову пісню в хоровий і концертний репертуар. Цей рух від громадського кола до сцени найкраще спростовує міф про «просту розвагу»: те, що жило в обряді, стало частиною модерної української культурної циркуляції."
:::

## Деколонізаційна рамка

Імперські й радянські рамки часто знеособлювали українську календарну обрядовість, розчиняючи її в нечіткому «загальнослов'янському» або суто «етнографічному» матеріалі. Механізм цього знеособлення простий і небезпечний. Спершу український обряд позбавляють власної назви й регіону. Далі його подають як локальний варіант чужої, ширшої схеми. Нарешті він стає безіменною ілюстрацією, з якої легко зробити висновок про культурну вторинність. Так народжується меншовартість — відчуття, ніби своя традиція є лише блідою копією сусідньої.

Деколонізований підхід руйнує цей ланцюг із першого кроку. Він починає з українських назв, регіонів, дій і джерел. Кутя, дідух, веснянка, гаївка, Купала, посівання, обжинки, обжинковий вінок і останній сніп описуються як елементи української системи, а не як додаток до чужої культурної схеми. Це не риторичний жест, а методологічна вимога. Коли ти називаєш обряд його власним іменем і вказуєш регіон та запис, він перестає бути «матеріалом взагалі» й повертає собі конкретність. Конкретність — найкращий захист від знеособлення.

Перший міф, який треба виправити, — що календарний фольклор є «простою народною розвагою». Насправді корпус показує складну систему з власним ритмом, символікою та виконавською логікою. Розвага й обряд тут не протилежні: гра підлітків була водночас і забавою, і способом передати традицію. Саме тому, що обряди перейшли на молодіжні ігри, вони й збереглися, коли суворіші форми зникали під тиском церкви та влади. Назвати це «лише розвагою» означає не помітити, як працює механізм передання культури.

Другий міф — що українські цикли є просто місцевою версією загальнослов'янської спадщини. Спільне коріння справді існує, і це нормально для споріднених народів. Та спільність походження не скасовує окремості системи. Українська веснянка з її образом весни-панянки, українська гаївка з її іграми «воріт», український обжинковий вінок і дідух мають власні назви, власні регіональні варіанти й власний корпус записів. Деколонізація тут означає не вигадування унікальності, а просту наукову точність: описувати своє своїми словами та своїми джерелами.

Третій міф приходить з протилежного боку — це романтичне перебільшення. Спокусливо перетворити кожен образ на доказ прямого «культу» давнього божества й реконструювати цілий пантеон із кількох пісенних рядків. Але це така сама помилка, як і знеособлення, лише з іншим знаком. Романтизований опис підмінює корпус фантазією й зрештою робить тему вразливою: її легко спростувати, бо вона спирається на здогад, а не на свідчення. Деколонізаційна рамка вимагає тверезості. Ми показуємо синкретизм там, де він є, фіксуємо варіанти, називаємо дослідників і чесно окреслюємо межу реконструкції.

Через це робота з джерелами тут підпорядкована строгому правилу. Ми цитуємо лише ті тексти, що засвідчені в корпусі цього модуля, і не додаємо сторонніх творів, назв чи дат. Така стриманість — не обмеження, а сила деколонізованого методу. Українська календарна обрядовість не потребує ні імперського «загального тла», ні романтичних прикрас. Їй досить власних назв, власних регіонів і власних записів, щоб постати як повноцінна, внутрішньо логічна система. Завдання дослідника — не прикрасити її, а точно показати те, що вже є.

## Підсумок

Календарна обрядовість постає не як купа звичаїв, а як єдина система, у якій рік ділиться на чотири пов'язані цикли. Зимовий цикл збирає родину навколо куті й дідуха та обходить двори з колядою і щедрівкою. Весняний цикл закликає тепло веснянками й гаївками та поєднує спів із рухом громади. Літній цикл святкує найвищу силу сонця купальським вогнищем, вінками й водою. Осінній цикл дякує за врожай зажинками й обжинками, останнім снопом і обжинковим вінком. Сонцеворот тримає це коло, а праця хлібороба наповнює його змістом.

Три поняття, з якими ти працював, відчиняють будь-який із цих циклів. Обряд показує усталену дію або послідовність дій. Мотив указує на повторюваний образ чи формулу: зустріч весни, роса-краса, останній сніп. Варіант відкриває географію та історію традиції, бо той самий мотив звучить по-різному на Галичині, Волині чи Слобожанщині. Разом ці ключі дають змогу читати календарну пісню системно, а не як випадкову екзотику. Вони ж захищають від двох крайнощів — байдужого знеособлення й романтичного перебільшення.

Чому ця тема важлива саме нині? Тому що деколонізація культури починається з точних описів. Поки українські обряди залишалися безіменним «загальнослов'янським матеріалом», їх легко було привласнити або знецінити. Щойно ми називаємо кутю кутею, гаївку гаївкою, обжинки обжинками й показуємо їхні варіанти за записами дослідників, система повертає собі голос. Це і є практична робота з пам'яттю: не гасло, а уважне читання корпусу.

Календарний обряд також показує живу тяглість культури. Те, що колись виконувала громада в колі, перейшло на молодіжні ігри, потім у записи збирачів, а далі — у літературу й хоровий спів. Веснянка стала і предметом наукового аналізу, і ліричним зразком, і концертним номером. Ця циркуляція від села до сцени — найкращий доказ, що перед нами не «проста розвага», а форма, здатна жити в багатьох середовищах і не втрачати сенсу.

Метод, яким ми користувалися, лишається однаковим для всіх циклів. Спершу слухаємо корпус і цитуємо засвідчене. Далі описуємо мотив і його варіанти, не зливаючи їх у штучну суміш. Потім ставимо питання про виконання: хто співав, у якому колі, в який час доби й року. Нарешті окреслюємо межу реконструкції й зупиняємося там, де джерело мовчить. Цей шлях поєднує наукову доброчесність із повагою до традиції.

Ти вже бачив у попередньому модулі, як працюють замовляння з їхнім речитативним ритмом і прямим зверненням до сил природи. Календарна пісня — це інший полюс тієї самої усної культури: співовий, рівноскладовий, громадський. А наступний крок веде до колядок і щедрівок, де зимовий цикл розгортається у власну багату систему побажань і обходів. Так окремі жанри складаються в одну карту української обрядовості, і кожен новий цикл уточнює загальну картину.

:::tip
Щоб не плутати чотири цикли, тримайся руху сонця: зима дає кутю й дідуха, весна — закликання й гаївки, літо — купальське вогнище й воду, осінь — обжинки й останній сніп. Чотири пори — чотири дії: зберегти, закликати, святкувати, подякувати.
:::

Найважливіше, що варто винести: українська календарна обрядовість самодостатня. Їй не потрібне чуже «тло», щоб мати значення, і не потрібні романтичні прикраси, щоб бути цікавою. Її цінність — у точно засвідченій системі мотивів, варіантів і виконавських форм, зібраних із власних регіонів і власних джерел. Назвати це своїми іменами — і є та робота, заради якої ми читаємо корпус.

## Як читати цикл крізь три ключі

Три поняття — обряд, мотив і варіант — це не сухі терміни, а робочі ключі, якими відмикається будь-який сезонний цикл. Обряд — це усталена дія або послідовність дій, що має своє місце в річному колі: Святвечір з кутею, закликання весни, купальське вогнище, зрізання останнього снопа. Він не випадковий і не одноразовий; його повторюваність і є тим, що робить його обрядом, а не просто подією. Коли ти бачиш дію, яка повертається рік у рік у тому самому часі й з тією самою метою, перед тобою саме обряд, а не випадкова забава.

Мотив працює на іншому рівні. Це повторюваний образ або стала формула, що мандрує від тексту до тексту: зустріч весни, роса як дівоча краса, ворота, що відчиняються весні, останній сніп, який несуть у дім із шаною. Один обряд може тримати кілька мотивів, а той самий мотив здатний переходити з весняного циклу в осінній, змінюючи вбрання, але зберігаючи внутрішнє ядро. Саме тому мотив зручно простежувати крізь увесь рік: він показує, що цикли пов'язані між собою, а не стоять окремими острівцями.

Варіант відкриває географію та історію. Те, що на Галичині звуть гаївкою чи гагілкою, деінде звучить як веснянка; та сама формула зустрічі весни в одному записі дарує красу, а в іншому — літо й житечко. Дослідник не вибирає «правильніший» варіант і не зливає всі редакції в одну штучну суміш. Він фіксує кожен запис із його місцем і показує, як живий мотив дихає по-різному в різних теренах. Варіативність — не зіпсованість традиції, а доказ її життя.

Разом ці три ключі дають змогу читати календарну пісню системно. Обряд відповідає на питання «що роблять», мотив — «який образ повторюється», варіант — «де і як саме це звучить». Коли всі три питання поставлено разом, окремий запис перестає бути курйозом і стає вузлом у мережі. Ця мережа й є та система, про яку йшлося від самого початку: не низка екзотичних звичаїв, а зв'язне поле дій, образів і регіональних форм.

## Слово, дія і простір

Календарну пісню майже ніколи не співали наодинці й нерухомо, і це принципово для розуміння жанру. Текст на сторінці — лише половина обряду; друга половина — рух, простір і час. Хоровод, кривий танець, проходження між рядами, обхід дворів, ігровий діалог двох гуртів — усе це не прикраса до слів, а їхнє продовження. Коли громада закликає весну, вона робить це голосом і тілом водночас: спів кличе тепло, а рух у колі ніби накреслює саме коло року.

Простір обряду має значення. Весняні гаївки часто виконували на вигоні, біля церкви чи на леваді — там, де громада збиралася відкрито. Зимовий обхід дворів вів пісню від хати до хати, перетворюючи все село на сцену. Купальське дійство тяжіло до води й вогню, до берега річки чи галявини. Місце не було випадковим: воно входило в обряд так само, як слова й мелодія, і змінити його означало змінити сам зміст дії.

Час доби та року тримає всю конструкцію. Посівання чинять саме вранці нового року, бо ранок — це початок; купальське вогнище палять у найкоротшу ніч, бо саме тоді сонце на вершині сили; останній сніп несуть наприкінці жнив, бо він замикає працю. Обряд прив'язаний до руху сонця не метафорично, а буквально: сонцеворот задає, коли яку дію виконувати, і саме тому хліборобський рік, а не церковний календар сам по собі, тримає всю споруду докупи.

Через це аналітик мусить завжди ставити чотири питання до кожного запису: що співали, хто співав, у якому колі та просторі й у який час. Без них текст залишається німим. Із ними навіть короткий рядок розгортається в повноцінну обрядову дію, у якій слово, тіло, простір і час працюють як одне ціле. Саме така цілісність і робить календарну пісню обрядом, а не просто текстом.

## Синкретизм як норма жанру

Календарна пісня вільно поєднує образи різного походження, і це не вада, а закон жанру. Формула «Вже весна воскресла» бере слово з церковної мови воскресання, та вживає його для дохристиянської ідеї повернення життя після зими. Громада не відчувала тут суперечності: вона співала про воскресання весни так само природно, як орала поле. Спроба «очистити» такий текст від одного з шарів зруйнувала б саме те, що робить його живим документом культури.

Цей синкретизм має глибоку логіку. Хліборобський світ потребував мови, якою можна говорити з порами року, із сонцем, водою й землею. Коли прийшло християнство, воно не стерло цю мову, а наклалося на неї: давні свята отримали нові імена й дати, а нові образи ввійшли в старі формули. Тому кутя й дідух стоять поряд із церковним календарем, а купальське вогнище горить біля християнських назв. Дослідник фіксує обидва шари й показує, як вони співіснують, замість того щоб оголошувати один із них «справжнім», а другий «пізнім нашаруванням».

Саме тут деколонізаційна рамка вимагає особливої тверезості. Спокусливо витлумачити кожен синкретичний образ як доказ прямого «культу» давнього божества й вибудувати з кількох рядків цілий пантеон. Але з образу не випливає автоматично готова релігійна система. Світове дерево, роса, вогонь чи вода можуть бути сильними символами й без приписаної їм наперед міфології. Реконструкція має межу, і чесний опис зупиняється там, де закінчується свідчення корпусу.

Отже, синкретизм — це не проблема, яку треба розв'язати, а ознака, яку треба описати. Він показує, що традиція не застигла, а вбирала нове, не втрачаючи власного ядра. Уміння бачити обидва шари водночас і не плутати образ із доктриною — одна з головних навичок, яку дає робота з календарним корпусом. Без цієї навички легко або збіднити текст, або перевантажити його вигаданими значеннями.

## Громада як виконавець

Календарний обряд — це завжди справа гурту, а не окремої людини, і саме колективність визначає його форму. Коло, ряд, два хори, обхід дворів — усе це способи зробити дію спільною. Навіть коли в пісні звучить один голос-заспів, за ним стоїть громада, що підхоплює, відповідає, рухається. Антифонний спів, тобто перегук двох гуртів, прямо вписує діалог у тканину обряду: один гурт питає, другий відповідає, і коротка формула розгортається в розгорнуту дію з ролями та напруженням.

Особливу роль тут відіграє молодь. Грушевський пояснював добру збереженість календарного циклу тим, що частина обрядів перейшла на ігри підлітків і молоді, а це врятувало їх від нагінок церкви та адміністрації, які знищували забави старшого віку. Молодіжна гра була водночас і забавою, і школою традиції: співаючи про сватання, ворота й вибір пари, молодь не лише бавилася, а й засвоювала те місце, яке мала посісти в громаді. Весняний цикл тому так часто говорить про красу, заміжжя й майбутнє — це час громадського дорослішання.

Колективність також пояснює, чому варіант — таке важливе поняття. Кожне село виконувало обряд трохи по-своєму: де співали як хороводну гру, де як ігровий діалог двох гуртів, де додавали місцеві імена й деталі. Це не псування єдиного «правильного» тексту, а природний наслідок того, що носієм традиції була громада, а не книга. Жива пам'ять багатьох людей завжди дає множину редакцій, і саме ця множина робить корпус багатим.

Тому читати запис як слід колективного дійства — не примха, а необхідність. За словами на сторінці стоять рухи, голоси й конкретні виконавці. Коли ми кажемо «варіант», то маємо на увазі не лише іншу редакцію слів, а й інший спосіб виконання. Громада — не тло обряду, а його справжній автор і носій, і саме через неї текст набуває голосу й руху.

## Чому метод важить

Метод, яким описують календарну обрядовість, важить не менше, ніж самі тексти, бо саме він відрізняє науку від здогаду. Перший крок методу — слухати корпус і цитувати лише засвідчене. Ми працюємо із закритим колом джерел: із записаними піснями, описами дій і свідченнями збирачів. Ми не додаємо сторонніх творів, не приписуємо обрядові дат і назв, яких джерело не підтверджує, і не «покращуємо» текст під свою гіпотезу. Там, де корпус мовчить, ми мовчимо разом із ним.

Другий крок — описувати мотив і його варіанти, не зливаючи їх у штучну суміш. Спокуса звести кілька записів до одного «архетипного» тексту велика, але вона нищить саме те, що цінне, — варіативність. Дослідник тримає кожен запис окремо, з його місцем і формою, і показує мережу зв'язків між ними, а не плаский усереднений зразок. Так зберігається і географія, і історія традиції.

Третій крок — ставити питання про виконання. Хто співав, у якому колі, в якому просторі, в який час доби й року? Без цих питань текст залишається половиною обряду. Календарна пісня, на відміну від речитативного замовляння, побудована в пісенних, рівноскладових строфах, де вірш дорівнює віршеві і з музичного, і зі складового боку. Саме ця стисла, майже арифметична будова зберегла традиційний текст набагато краще, ніж вільний речитатив, у якому виконавець легко змінював слова. Отже, форма виконання прямо впливає на те, що взагалі дійшло до нас.

Четвертий крок — чесно окреслювати межу реконструкції. Ми показуємо синкретизм там, де він є, фіксуємо варіанти, називаємо дослідників і зупиняємося там, де закінчується свідчення. Така стриманість не збіднює тему, а робить її переконливою: висновок, що спирається на корпус, важко спростувати, бо він не вигаданий, а показаний. Метод — це і є та дисципліна, що перетворює збірку звичаїв на систему знання.

## Від кола до сцени

Календарна пісня не залишилася замкненою в селі — вона пройшла довгий шлях циркуляції, і цей шлях найкраще спростовує міф про «просту розвагу». Спершу обряд жив у громадському колі, переходив від покоління до покоління в живому виконанні. Потім його почали записувати збирачі, і усне дійство отримало письмову форму, придатну для аналізу. Далі обрядова пісня ввійшла в літературу й хоровий спів: поети зверталися до жанру веснянки як ліричного зразка, а композитори вводили обрядову пісню в концертний репертуар.

Кожен із цих переходів щось зберігав і щось змінював. Запис фіксував слова, але втрачав рух і простір, тому збирач мусив описувати ще й дію, коло, час. Літературна обробка брала образ і ритм веснянки, але переносила їх у нове, авторське середовище. Хорова версія підкреслювала музичний бік, рівноскладову будову, антифонний перегук гуртів. Так один і той самий мотив жив у багатьох середовищах, не втрачаючи свого ядра, — і саме ця здатність жити в різних формах доводить, що перед нами повноцінна культурна форма, а не випадкова забава.

Циркуляція має й деколонізаційне значення. Поки українські обряди залишалися безіменним «загальнослов'янським матеріалом», їх легко було привласнити або знецінити. Щойно веснянка стала водночас і предметом наукового аналізу, і ліричним зразком, і концертним номером із власним іменем та регіоном, вона повернула собі голос у модерній культурі. Рух від громадського кола до сцени — це не відрив від коренів, а продовження життя традиції іншими засобами.

Тому, завершуючи розгляд, варто тримати в голові всю траєкторію: коло громади, зошит збирача, сторінка поета, хорова партитура. Це не чотири різні речі, а одна форма в чотирьох станах. Українська календарна обрядовість зберігає тяглість саме тому, що вміє переходити з одного середовища в інше й щоразу промовляти заново — своїми іменами, своїми образами, своїми записами.

## Чотири дії одного року

Усю систему зручно тримати в пам'яті через чотири дієслова, що відповідають чотирьом порам. Зима — це зберегти: кутя й дідух збирають родину навколо пам'яті про предків і надії на врожай, а сніп жита в домі стоїть знаком тяглості роду. Обхід дворів із колядою та щедрівкою розносить побажання добробуту по всій громаді, а посівання вранці нового року переносить аграрну дію просто в хату. Усе тут спрямоване на те, щоб зберегти життя й рід через найтемнішу пору.

Весна — це закликати. Громада не чекає тепла пасивно, а викликає його голосом і рухом: веснянки й гаївки, хоровод і кривий танець, ігровий діалог двох гуртів. Образ весни-панянки, ворота, що відчиняються, роса як дівоча краса — усе це служить одній меті: повернути життя й родючість після зими. Літо — це святкувати: купальське вогнище, вінки й вода відзначають найвищу силу сонця та зелені, а ворожіння на вінках поєднує радість із тривогою за майбутнє.

Осінь — це подякувати. Зажинки врочисто відкривають жнива, обжинки їх завершують, останній сніп несуть у дім із особливою шаною, а з колосся плетуть обжинковий вінок як знак подяки й збереженої родючості. Зберегти, закликати, святкувати, подякувати — чотири дії, чотири пори, одне коло. Коли ти тримаєш у голові цю просту четвірку, жоден обряд не загубиться, бо кожен знаходить своє місце в русі сонця й у праці хлібороба.


## activities.yaml

- id: act-1
  type: ritual-sequencing
  title: Чотири цикли року
  instruction: Розташуй календарні цикли в порядку руху сонця — від зими до осені.
  items:
  - 'осінній цикл: обжинки й останній сніп'
  - 'зимовий цикл: кутя, дідух і посівання'
  - 'літній цикл: купальське вогнище й вода'
  - 'весняний цикл: закликання тепла, веснянки й гаївки'
  correct_order:
  - 1
  - 3
  - 2
  - 0
  steps:
  - 'зимовий цикл: кутя, дідух і посівання'
  - 'весняний цикл: закликання тепла, веснянки й гаївки'
  - 'літній цикл: купальське вогнище й вода'
  - 'осінній цикл: обжинки й останній сніп'
  model_answer: Правильний порядок — зимовий, весняний, літній, осінній цикл. Він
    повторює рух сонця через сонцестояння й рівнодення та хліборобський рік.
- id: act-2
  type: motif-formula
  title: Формула зустрічі весни
  instruction: Прочитай заспів і визнач повторювану формулу, на якій він побудований.
  text: Вже весна воскресла, / Що ж сь нам принесла? / Ой я вам принесла, / Дівоцькую
    красу
  passage: 'Весняний заспів будує діалог: громада звертається до весни як до живої
    істоти й чекає на дарунок.'
  prompt: Яку повторювану формулу побудовано в цьому заспіві?
  formulas:
  - 'звертання-питання до весни: «Що ж сь нам принесла?»'
  - 'відповідь-дар: «Ой я вам принесла…»'
  answers:
  - діалогічна формула питання й відповіді
  - персоніфікація весни як адресата дії
  model_answer: Заспів побудовано на формулі «питання до весни — відповідь-дар». Весна
    персоніфікована як адресат, а її дарунок (краса, родючість) — повторюваний мотив
    циклу.
- id: act-3
  type: ritual-sequencing
  title: Жниварський цикл
  instruction: Розташуй дії осіннього жниварського циклу в правильному порядку.
  items:
  - 'обжинки: завершення жнив і обжинковий вінок'
  - 'зажинки: урочистий початок жнив'
  - останній сніп несуть у дім
  - 'жнива: основна праця женців у полі'
  correct_order:
  - 1
  - 3
  - 0
  - 2
  steps:
  - 'зажинки: урочистий початок жнив'
  - 'жнива: основна праця женців у полі'
  - 'обжинки: завершення жнив і обжинковий вінок'
  - останній сніп несуть у дім
  model_answer: 'Порядок такий: зажинки відкривають жнива, далі основна праця женців,
    потім обжинки з обжинковим вінком, і останній сніп урочисто несуть у дім.'
- type: variant-comparison
  title: Веснянки, гаївки, гагілки
  instruction: Порівняй три регіональні назви весняних обрядових пісень за поданими
    ознаками.
  prompt: Чим різняться й чим єдині веснянки, гаївки та гагілки як варіанти одного
    жанру?
  variants:
  - веснянки
  - гаївки
  - гагілки
  features:
  - регіон побутування
  - обрядова функція
  - виконавський контекст (коло, гра двох гуртів)
  model_answer: 'Усі три — варіанти весняної обрядової пісні з єдиною функцією: закликати
    весну й тепло. «Веснянка» — ширша, поширена назва; «гаївка» й «гагілки» — регіональні
    форми, зокрема на західних теренах. Виконавчо їх єднають коло, кривий танець та
    ігровий діалог; різняться вони назвою й місцевими редакціями текстів, тобто варіативністю,
    а не суттю.'
- type: motif-formula
  title: Образи родючості
  instruction: Розбери, як весняна пісня пов'язує прихід весни з родючістю.
  text: Ой весна, весна, ти красна, / Що ж ти нам, весна, принесла? / Та принесла
    я вам літечко, / Щоб родилося житечко
  passage: 'Тут дарунок весни — не лише краса, а конкретний господарський результат:
    літо й добрий урожай.'
  prompt: Які мотиви й формули поєднують весну з родючістю в цьому записі?
  formulas:
  - 'дарунок весни: «принесла я вам літечко»'
  - 'мета-побажання: «щоб родилося житечко»'
  answers:
  - мотив весни-дарувальниці
  - аграрна формула прохання про врожай
  model_answer: Пісня будує мотив весни-дарувальниці й завершує аграрною формулою
    прохання про врожай («щоб родилося житечко»). Так весняний цикл прямо пов'язує
    оновлення природи з родючістю поля.
- type: performance
  title: Виконання гаївки
  instruction: Прочитай уголос фрагмент гаївки, дотримуючись ритму з рівними складами.
  fragment: Гагілка гагілкою, / Підем в село за дівкою, / А Кудлиха, стара мати, /
    Має дочку заміж дати
  prompt: Проговори фрагмент так, щоб рядки мали рівні склади й виразний ритм
    обрядової гри.
  self_checklist:
  - рядки мають рівні склади
  - ритм пісенний, а не речитативний
  - збережено архаїчні форми тексту без виправлення
  show_record_button: true
  model_answer: Гаївка має рівні склади; читай її співно, а не як речитатив.
    Архаїчні форми («гагілка», «дівкою») лишаються без змін, бо це цитата корпусу,
    а не сучасна проза.
- type: ritual-sequencing
  title: Свята календарного кола
  instruction: Розташуй обрядові події за порами року — від зими до осені.
  items:
  - 'Купала: вогнище, вінки й вода'
  - 'Святвечір: кутя й дідух'
  - 'обжинки: останній сніп і обжинковий вінок'
  - 'закликання весни: гаївки навесні'
  correct_order:
  - 1
  - 3
  - 0
  - 2
  steps:
  - 'Святвечір: кутя й дідух'
  - 'закликання весни: гаївки навесні'
  - 'Купала: вогнище, вінки й вода'
  - 'обжинки: останній сніп і обжинковий вінок'
  model_answer: Зимовий Святвечір із кутею й дідухом, потім весняне закликання гаївками,
    далі літня Купала з вогнищем і водою, нарешті осінні обжинки з останнім снопом
    і вінком.
- type: essay-response
  title: Деколонізаційна рамка обряду
  instruction: Напиши коротке аналітичне есе на основі поданого матеріалу.
  prompt: Поясни, чому опис української календарної обрядовості як «загальнослов'янського
    матеріалу» знеособлює традицію, і покажи, як деколонізований підхід повертає їй
    конкретність. Спирайся на назви, регіони й джерела.
  min_words: 180
  source_reading: 'Деколонізаційна рамка модуля: знеособлення через втрату назви й
    регіону; деколонізований опис починає з українських назв, дій і джерел.'
  rubric:
  - названо механізм знеособлення (втрата назви, регіону, джерела)
  - наведено конкретні українські назви й цикли
  - розрізнено деколонізацію й романтичне перебільшення
  - висновок спирається на корпус, а не на здогад
  peer_review_guidelines: 'Перевір, чи автор уникає двох крайнощів: байдужого знеособлення
    й романтичної фантазії. Познач місця, де твердження не підкріплене назвою, регіоном
    або джерелом.'
  model_answer: 'Сильне есе показує ланцюг знеособлення: український обряд позбавляють
    назви й регіону, подають як варіант чужої схеми, а потім як безіменну ілюстрацію.
    Деколонізований підхід руйнує цей ланцюг, називаючи кутю, дідух, веснянку, гаївку,
    Купалу, обжинки своїми іменами та вказуючи регіон і запис. Водночас автор застерігає
    проти романтичного перебільшення й тримається меж реконструкції.'
- type: critical-analysis
  title: Межі реконструкції
  instruction: Проаналізуй уривок про збереження календарних пісень і відповідай на
    питання.
  context: Грушевський пояснює, чому весняний цикл зберігся краще за інші жанри усної
    словесності.
  target_text: Обрядові, хороводні й забавні пісні, зокрема весняні гаївки, побудовані
    в пісенних, рівноскладових строфах; така стисла будова зберігала текст краще,
    ніж вільний речитатив.
  source_reading: 'Корпус і контекст модуля: співовий, рівноскладовий ритм проти синтаксичного
    речитативу; перехід обрядів на молодіжні ігри.'
  focus_points:
  - ритмічна будова як чинник збереження
  - роль молодіжних ігор у переданні
  - межа між засвідченим і домисленим
  question: Чому співовий, рівноскладовий ритм зберіг календарний текст краще за речитатив?
  questions:
  - Які дві обставини, за Грушевським, урятували весняний цикл?
  - Де проходить межа між реконструкцією й домислом у цій темі?
  model_answer: 'Рівноскладова, симетрична строфа тримає текст у точних рамках, тож
    виконавець не міг вільно його змінювати, як у речитативі. Перехід обрядів на молодіжні
    ігри сховав їх від нагінок церкви та влади. Межа реконструкції проходить там,
    де корпус мовчить: образ не дорівнює готовому «культу» божества.'
  model_answers:
  - Перша обставина — перехід обрядів на ігри підлітків, що вберегло їх від заборон;
    друга — нерозривна зв'язь тексту з мелодією та рівноскладовим ритмом.
  - 'Межа там, де джерело не підтверджує висновку: ми відновлюємо засвідчене й не
    домальовуємо релігійних систем із кількох рядків.'
- type: comparative-study
  title: Два записи однієї формули
  instruction: Порівняй два записи весняної формули зустрічі весни.
  prompt: Зістав два варіанти формули «що ж нам принесла весна» й покажи, що в них
    спільне, а що варіантне.
  source_a: Вже весна воскресла, / Що ж сь нам принесла? / Ой я вам принесла, / Дівоцькую
    красу
  source_b: Ой весна, весна, ти красна, / Що ж ти нам, весна, принесла? / Та принесла
    я вам літечко, / Щоб родилося житечко
  source_reading: 'Корпус і контекст модуля: один мотив зустрічі весни має багато
    регіональних варіантів дарунка.'
  items_to_compare:
  - звертання до весни
  - формула питання
  - зміст дарунка весни
  criteria:
  - спільна структура питання-відповіді
  - відмінність у дарунку (краса / літо й врожай)
  - ознаки регіональної варіативності
  task: Випиши спільну формулу обох записів і поясни, чим різняться відповіді-дарунки.
  model_answer: 'Обидва записи мають спільну формулу «звертання до весни — питання
    про дарунок — відповідь». Різниться зміст дарунка: у першому це дівоча краса,
    у другому — літо й добрий урожай («житечко»). Ця різниця показує живу регіональну
    варіативність одного мотиву, а не дві окремі пісні.'


## vocabulary.yaml

- lemma: обряд
  translation: rite, ritual
  pos: ч.
  usage: Кожен обряд має усталену послідовність дій.
- lemma: мотив
  translation: motif, recurring image
  pos: ч.
  usage: Мотив зустрічі весни повторюється в багатьох піснях.
- lemma: варіант
  translation: variant, regional form
  pos: ч.
  usage: Той самий текст має кілька регіональних варіантів.
- lemma: звичай
  translation: custom, tradition
  pos: ч.
  usage: Посівання — давній новорічний звичай.
- lemma: цикл
  translation: cycle
  pos: ч.
  usage: Весняний цикл починається із закликання тепла.
- lemma: сонцестояння
  translation: solstice
  pos: с.
  usage: Зимове сонцестояння позначає межу циклу.
- lemma: рівнодення
  translation: equinox
  pos: с.
  usage: Весняне рівнодення відкриває новий сезон.
- lemma: сонцеворот
  translation: solar turning point
  pos: ч.
  usage: Сонцеворот тримає коло календарних обрядів.
- lemma: кутя
  translation: kutia (ritual grain dish)
  pos: ж.
  usage: На Святвечір родина сідає до куті.
- lemma: дідух
  translation: didukh (ritual sheaf)
  pos: ч.
  usage: Дідух стоїть у домі як знак предків.
- lemma: святвечір
  translation: Christmas Eve (Holy Supper)
  pos: ч.
  usage: Святвечір збирає всю родину разом.
  notes: 'Як назва свята пишеться з великої літери: Святвечір.'
- lemma: коляда
  translation: carol (winter ritual song)
  pos: ж.
  usage: Коляда лунає під час обходу дворів.
- lemma: колядування
  translation: carolling (rite of carolling)
  pos: с.
  usage: Колядування — це обхід дворів із піснями.
- lemma: щедрування
  translation: shchedruvannia (New-Year ritual singing)
  pos: с.
  usage: Щедрування супроводжує щедрівка.
- lemma: закликання
  translation: calling, invocation (of spring/warmth)
  pos: с.
  usage: Закликання тепла відкриває весняний цикл.
- lemma: гагілки
  translation: hahilky (regional spring songs)
  pos: мн.
  usage: На західних теренах веснянки звуть гагілки.
  notes: Уживається переважно в множині; регіональний варіант поряд із гаївками.
- lemma: хоровод
  translation: round dance
  pos: ч.
  usage: Гаївку часто співають у хороводі.
- lemma: русалії
  translation: rusalii (early-summer rite week)
  pos: мн.
  usage: Русалії пов'язані з пізнім весняним циклом.
- lemma: купальський
  translation: of Kupala
  pos: прикм.
  usage: Купальське вогнище горить улітку.
- lemma: вогнище
  translation: bonfire
  pos: с.
  usage: Молодь стрибала через купальське вогнище.
- lemma: зажинки
  translation: zazhynky (start-of-harvest rite)
  pos: мн.
  usage: Зажинки врочисто відкривають жнива.
- lemma: обжинки
  translation: obzhynky (harvest-end festival)
  pos: мн.
  usage: Обжинки завершують жниварський цикл.
- lemma: обжинковий
  translation: of the harvest festival
  pos: прикм.
  usage: Обжинковий вінок плетуть з останнього колосся.
- lemma: серп
  translation: sickle
  pos: ч.
  usage: Женці жали ниву серпом.
- lemma: жнива
  translation: harvest (reaping)
  pos: мн.
  usage: Жнива — основна праця женців у полі.
- lemma: врожай
  translation: harvest, crop yield
  pos: ч.
  usage: Обряд просить про добрий врожай.
- lemma: родючість
  translation: fertility (of land)
  pos: ж.
  usage: Вода й зерно символізують родючість.
- lemma: хліборобський
  translation: farming, of the tiller
  pos: прикм.
  usage: Хліборобський рік тримає всю систему обрядів.
- lemma: синкретичний
  translation: syncretic
  pos: прикм.
  usage: Формула воскресання весни — синкретичний образ.
- lemma: персоніфікація
  translation: personification
  pos: ж.
  usage: Персоніфікація весни робить її адресатом пісні.
- lemma: антропоморфний
  translation: anthropomorphic
  pos: прикм.
  usage: Весна постає в антропоморфному образі панянки.
- lemma: солярний
  translation: solar
  pos: прикм.
  usage: Солярний рух задає каркас календарного року.
- lemma: сакральний
  translation: sacred
  pos: прикм.
  usage: Останній сніп має сакральне значення.
- lemma: життєдайний
  translation: life-giving
  pos: прикм.
  usage: Вода — життєдайна сила весняного циклу.
- lemma: обрядодія
  translation: ritual action, rite-act
  pos: ж.
  usage: Цілий рік постає як одна обрядодія з чотирьох частин.
- lemma: знеособлення
  translation: depersonalisation, erasure of identity
  pos: с.
  usage: Імперська рамка вела до знеособлення традиції.
- lemma: реконструкція
  translation: reconstruction
  pos: ж.
  usage: 'Реконструкція має чітку межу: лише засвідчене.'
- lemma: романтизований
  translation: romanticised
  pos: прикм.
  usage: Романтизований опис підмінює корпус фантазією.
- lemma: антифонний
  translation: antiphonal (two-choir)
  pos: прикм.
  usage: Антифонний спів — це перегук двох гуртів.
- lemma: рівноскладовий
  translation: isosyllabic (equal-syllable)
  pos: прикм.
  usage: Рівноскладова строфа зберігає текст краще за речитатив.
- lemma: великодній
  translation: Easter (adj.)
  pos: прикм.
  usage: Великодні ігри належать до весняного циклу.
- lemma: новорічний
  translation: New-Year (adj.)
  pos: прикм.
  usage: Посівання — новорічний звичай.


## resources.yaml

- title: Обрядові та обрядово-календарні пісні — Вікіпедія
  role: wiki
  url: https://uk.wikipedia.org/wiki/Обрядові_та_обрядово-календарні_пісні
  notes: 'Оглядова стаття про календарно-обрядові пісні: зв''язок із порами року,
    звичаями та сільськогосподарськими роботами. Контекст до секцій «Корпус і контекст»
    та «Поетика».'
- title: Веснянки — Вікіпедія
  role: wiki
  url: https://uk.wikipedia.org/wiki/Веснянки
  notes: Стаття про веснянки як старовинні обрядові пісні, пов'язані з початком весни
    та польовими роботами; підтримує розбір весняного циклу й варіантів (гаївки, гагілки).


## Task

Review every obligation in the manifest against the generated content and
return the required JSON object now. No preamble, no markdown, no questions.
