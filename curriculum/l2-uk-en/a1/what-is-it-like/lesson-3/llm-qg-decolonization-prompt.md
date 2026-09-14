{"review_model": "claude-opus-4-8", "reviewer": "claude-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of lesson 3. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure, no named narrator, marked attributed quotations with Resources entries, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Який? Яка? Яке?", "sections": ["Діалоги", "Який? Яка? Яке?"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Прикметники", "sections": ["Прикметники"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Підсумок", "sections": ["Підсумок"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 3}], "items_min_exempt": [], "proper_names": []}

You are reviewing one quality dimension for the generated module below.
Return ONLY the JSON object described in the response format. Do not ask for
clarification, do not summarize the prompt, and do not emit prose outside the
JSON object.

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


# Lesson Contract v4 — published lessons under a module landing (#7994)

> **History:** DRAFT v3 — signed off by Codex + Gemini in `architecture` channel
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

## 1. Published unit and source artifacts (v4)

V4 applies to curriculum upgrades: the **lesson** is the published unit under a
module landing. Option A emits `site/src/content/docs/{level}/{slug}/index.mdx`
and `{slug}/{n}.mdx`. Every lesson retains the four tabs described below. The
landing carries objectives, lesson cards and linked unions of vocabulary, practice
and resources; previous/next links advance by lesson. The final lesson closes the
module. Existing unsplit V7 modules continue to use the v3 single-page shape.

The canonical output level is `a1`; the previous edition is archived unchanged
at `a1-v1` with `base_level: a1`. Plans stay in `plans/a1/`. Production stays
untouched. A deterministic `lessons.yaml` assigns original sections and activities
before writing. The upgrade input is the existing module's four artifacts and
immutable plan. No wiki packet or new plan is authored. Source lesson files live
in `{level}/{slug}/lesson-{n}/`; only the map is pipeline-owned. Every original
paragraph remains verbatim in its assigned lesson (stress/whitespace normalization
only), and every original activity retains its payload and stable identity.

Each 60-minute lesson has at least 550 prose tokens and ten activities (4–6 inline,
6–9 workbook). The complete pilot split has at least 2000 prose tokens. Original
short-item exemptions are explicit in the map. Vocabulary is allocated once across
lessons and accumulates in published tabs and learner state. Stress annotation runs
after review; correctness, not just mark presence, is checked against the oracle.
No named narrator or self-introduction; people are named only inside dialogues.
Quotations are visibly attributed and listed in Resources. Added A1 Ukrainian
passages of at least three sentences have side-by-side English support.

Schema and exact acceptance: [Phase 1 spec](epics/curriculum-upgrade-phase1-spec.md).
The existing immersion exposure allocation remains a blocking residual documented
there; v4 does not silently change current thresholds.

### Legacy v3 artifact history

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


Shared module contract path: `scripts/build/contracts/module-contract.md`.

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete evidence from the generated
content. Return a machine-readable mapping with `score`, `evidence`, and
`verdict` for this one dimension.

The Generated Content block below is the only reviewable module text. Do not
read local files, follow filesystem paths, or use module text obtained from any
other checkout/session as evidence. Tools may be used for linguistic/source
verification, but not to replace the generated artifacts embedded in this
prompt.

Assigned dimension: decolonization

## Scope — JUDGMENT ONLY, do NOT re-litigate deterministic gates

Deterministic gates already ran before you. Treat their verdicts as ground
truth and do not score them again. The deterministic floor includes
(non-exhaustive): word counts, plan adherence, vesum_verified vocabulary
coverage, textbook grounding, immersion ratios, AI-slop patterns, activity
schema + types + props, formatting standards, `forbidden_words`
(SEVERE_RUSSIANISMS hard list), and `engagement_floor` (callout minimums +
META_NARRATION zero-tolerance ban).

Your job in this LLM dim is the residual judgment that regex cannot make.

## Level Calibration — do not mis-score intended scaffolding

Apply the level contract before scoring any dimension:

- A1: English scaffolding is expected and often substantial. Do NOT penalize
  English task support, English grammar terminology, or line-level glosses when
  they support a Ukrainian-first teaching move. Penalize only English-led
  lecture prose that replaces the Ukrainian anchor, or internal writer/reviewer
  scaffolding that leaked into learner-facing content.
- A2: easy Ukrainian should be the default body voice, with decreasing English
  support for first-introduction grammar, safety clarifications, and concise
  glosses. Do not demand B1-style Ukrainian-only prose, but flag English
  paragraphs that take over the lesson.
- B1/B2/C1/C2: learner-facing prose should be Ukrainian-led. English support is
  exceptional, local, and justified; English-led sections are evidence against
  tone, naturalness, and pedagogy.
- Seminars: use advanced Ukrainian teaching voice. English leakage, generic
  inspirational language, or school-textbook simplification is evidence against
  tone/naturalness unless the plan explicitly requires a bilingual artifact.

For `decolonization` specifically:

- `engagement`: does the prose actually *hold attention*? The gate already
  confirmed callout count + META_NARRATION absence; you assess whether the
  callouts carry real pedagogy vs filler, whether the tone is warm vs
  bureaucratic, whether direct-address phrases (e.g. `Notice the soft sign
  in **писатися**`) are content-anchored vs generic, whether dialogue feels
  human vs robotic. Score the *quality* of engagement, not its presence —
  presence is the gate's job.
- `pedagogical`: does the sequencing actually teach? Are examples
  illuminating? Does each concept earn the next? The gate confirmed word
  budgets and section presence; you assess whether the pedagogy *works*.
  Source-pedagogy failures are in scope even when the plan/wiki asked for
  them: REVISE or REJECT any grammar module that promotes a metaphor,
  discourse heuristic, activity label, or writer-created grouping into a
  grammar taxonomy unless Ukrainian textbook/corpus evidence explicitly
  supports that framing. Do not reward plan adherence when the upstream
  plan/wiki itself appears pedagogically unsupported. For example, a lesson
  may use "background/foreground" as an optional writing heuristic after
  aspect is taught, but if it asks learners to classify every verb as
  `тло`/`подія` as though those are textbook grammar categories, flag
  `unsupported_taxonomy_frame` and score the pedagogical dim below PASS.
  Likewise, if a module teaches impersonal/no-subject forms, examples and
  activities must preserve the no-subject property; adding an ordinary subject
  noun to the target pattern is a pedagogical grammar error, not harmless
  context.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-NO-SCAFFOLDING-LEAKS`: REJECT writer-side scaffolding leaks.
    Writer-side scaffolding never appears in module body. Forbidden in
    published markdown: panel IDs (`P1`, `P2`, ...), Krok-N labels
    (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest
    (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names.
    The module is a finished lesson, not a writer's worksheet.
  - Mirrors `#R-NO-CHILDREN-PRIMARY-QUOTES`: REJECT `>` blockquotes from
    textbooks at Grade 1, 2, or 3 levels in the published module body. Grade
    1-3 RAG hits can still ground lexical choices, but do not surface as
    quoted material. Default: NO blockquote unless it pedagogically advances
    the lesson AND comes from an adult-appropriate source (Grade 7+, adult
    literature, Антоненко-Давидович, style guides). Adult A1 learners are
    not reading children's primers; reject `Захарійчук, Grade 1, p.24` as
    lesson prose.
  - Mirrors `#R-GRAMMAR-TERMS-A1`: REJECT A1 English explanations that avoid
    the rule: Use proper grammatical terminology in English explanations.
    The accepted terms are **noun**, **verb**, **adjective**, **adverb**,
    **pronoun**, **reflexive**, **conjugation**.
    REJECT folksy paraphrase (`a thing`, `an action`, `a word for`,
    `a doing-word`, `the X-form of Y`) in lieu of grammar terms.
  - Mirrors `#R-CLEAN-TABLES`: REJECT bold-everywhere tables. Tables: bold
    ONLY the target Ukrainian forms; pronoun columns (`я`, `ти`, ...),
    English headers, and English glosses remain in regular weight. REJECT
    conjugation tables teaching a present-tense paradigm that omit `ви` or
    `вони` from the FULL set of person/number rows: **я / ти /
    він,вона,воно / ми / ви / вони** (six rows). Vocabulary tables stay
    two-column unless a third column adds essential teaching value (e.g.,
    stress mark, IPA).
- `naturalness`: does Ukrainian read as native? The gate confirmed VESUM +
  russianism shadow; you assess flow, register, idiom, grammar government, and
  collocation. This is a linguistic-quality review, not a vibes review.
  Actively search for:
  - calqued or evasive passives where native Ukrainian would use an active,
    impersonal, or result-state construction;
  - wrong government/prepositions (for example, prefer `чекати на когось/щось`
    where a bare English-style object such as `чекайте номер` sounds calqued);
  - wrong verb choice for ordinary Ukrainian collocations (`відчинити/зачинити`
    for doors/windows, `відімкнути/замкнути` for lock/unlock actions,
    `прийняти препарат/ліки` rather than drinking medicine, etc.);
  - anthropomorphic or model-translated metalanguage (`форма просить`,
    `застереження каже`, `правило хоче`) unless quoted as a deliberate learner
    mnemonic;
  - unnatural nominalizations, bureaucratic phrasing, literal English/Russian
    sentence architecture, or register shifts that a Ukrainian editor would
    rewrite even if every surface form passes VESUM.
  If you find two or more concrete native-style Ukrainian defects in generated
  Ukrainian prose, score naturalness below PASS even when deterministic gates
  passed. Name the defect type in `rubric_mapping` and quote the exact offending
  phrase.
- `decolonization`: is the lesson teaching Ukrainian **on its own terms**?
  The gate confirmed forbidden_words.

  **Anchoring principle: teaching codified Ukrainian to learners of a
  historically depressed language IS the substantive decolonization act.**
  Do NOT score 9.0+ as requiring extra anti-colonial rhetoric piled on top
  of clean canonical teaching. That would politicize grammar lessons
  without adding pedagogical value. The scoring anchor differs by module
  type:

  **Topic-neutral modules (grammar, vocabulary basics, phonetics):**
  9.0+ baseline if all three apply when learner-facing contrast is explicitly authorized;
  if contrast is deferred for foundational modules, baseline is still possible when (a), (c), and strict anti-Russian-as-reference execution are present.
  (a) Ukrainian-canonical vocabulary throughout (e.g. `сніданок` not
  `завтрак`, `рушник` not `полотенце`, `одягатися` not `одіватися`) —
  using VESUM/Pravopys-2019 codified forms, not Russified or surzhyk
  approximations.
  (b) If the module is authorized for learner-facing bad-form contrast,
  include at least one bad-form contrast marker pair
  (`<!-- bad -->завтрак<!-- /bad -->` → `сніданок`) where learners are
  likely to encounter the Russified form.
  If no contrast is authorized, this point is satisfied through clear absence-only
  decolonization: no Russian-as-reference framing, no raw bad-form insertion, and
  full VESUM/Pravopys-2019 form coverage.
  (c) Grammar and morphology presented on Ukrainian terms — VESUM /
  Pravopys-2019 as the authority — NOT scaffolded through "like Russian
  but..." or cross-language similarity as the entry point. One brief
  stance line (e.g. "Ukrainian routine words are short and practical")
  is a bonus but NOT a requirement to clear 9.0.

  **Topic-loaded modules (history, biography, literature, culture, war,
  politics):** higher bar because the topic demands it. 9.0+ requires
  substantive framing: explicit Russification / imperial-framing /
  Soviet-euphemism rejection where relevant. A history module that says
  "Civil War" instead of "Українська революція 1917-1921" or "Soviet
  famine" instead of "Holodomor / genocide", a bio module that uses
  Russian-imperial transliteration of a Ukrainian figure's name, or a
  literature module that frames Ukrainian writers as "regional Russian
  literature" — these fail decolonization regardless of vocabulary
  cleanliness.

  **REVISE territory (<9.0):**
  - Leans on Russian to explain Ukrainian ("the Russian equivalent
    would be...") as the primary scaffolding.
  - Uses Russified vocabulary unmarked (no bad-form contrast).
  - Presents Ukrainian as derivative of Russian.
  - For topic-loaded content, omits substantive framing the topic demands.

  **REJECT territory (<7.0):**
  - Uses Russocentric periodization or Soviet euphemisms uncritically.
  - Treats Russian-imperial sources as authoritative on Ukrainian subjects.

  When you score, name the module's TYPE explicitly (topic-neutral vs
  topic-loaded) in your reasoning and apply the corresponding anchor.
  A morning-routine grammar module scoring 8.5 because the rubric was
  read as demanding more rhetoric than the topic supports is a
  reviewer-protocol failure under this anchor.
- `tone`: is the teacher's voice consistent and warm? The gate caught
  META_NARRATION; you assess everything else about register.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-SINGLE-VOICE-A1`: REJECT mid-module register shifts (English
    -> Ukrainian metalanguage -> preachy imperative -> casual paraphrase).
    The module must have one teacher voice across the whole module: warm,
    clear, direct ("you" / "your"). REJECT third-person framing of the
    learner (`the student`, `студента`, `the reader`, `учня`).
  - Mirrors `#R-AUDIENCE-LANGUAGE-A1`: REJECT grammar-translation lectures
    at A1/A2. The module must teach Ukrainian through Ukrainian with English
    as a receding scaffold: Ukrainian term first, em-dash gloss after
    (`прокидаюся — I wake up`), `<DialogueBox uk="..." en="..." />` with a
    Ukrainian-only `uk` turn, Ukrainian-only comprehension/recall content, a
    named persona or named characters, and no foreigner-textbook anti-patterns
    such as transliteration tables, "X sounds like Y in English", "the student
    must learn", or English topic-sentence openers.

A dim score that re-states what a deterministic gate already enforced is a
reviewer-protocol failure. Cite something the gate cannot see.

## Writer Obligation Context — same source material the writer saw

Use these blocks as context when judging the residual quality dimension. Do
not turn this into a new scoring dimension and do not re-run the deterministic
wiki coverage gate; the point is to know what the writer was obligated to
teach while applying the existing `decolonization` rubric.

### Wiki Obligations Manifest

```json
{
  "slug": "what-is-it-like",
  "wiki_path": "/home/ops/learn-ukrainian/wiki/pedagogy/a1/what-is-it-like.md",
  "phonetic_format_reference": [
    "Spoken target in `[...]` single-character square brackets, not Unicode look-alikes",
    "Pair written and spoken form in close lexical proximity (same sentence or adjacent bullet)",
    "Copy >=1 textbook example verbatim when the wiki provides one"
  ],
  "sequence_steps": [
    {
      "id": "step-1",
      "obligation_id": "step-1",
      "category": "sequence_steps",
      "summary": "Крок 1."
    },
    {
      "id": "step-2",
      "obligation_id": "step-2",
      "category": "sequence_steps",
      "summary": "Крок 2."
    },
    {
      "id": "step-3",
      "obligation_id": "step-3",
      "category": "sequence_steps",
      "summary": "Крок 3."
    },
    {
      "id": "step-4",
      "obligation_id": "step-4",
      "category": "sequence_steps",
      "summary": "Крок 4."
    },
    {
      "id": "step-5",
      "obligation_id": "step-5",
      "category": "sequence_steps",
      "summary": "Крок 5."
    },
    {
      "id": "step-6",
      "obligation_id": "step-6",
      "category": "sequence_steps",
      "summary": "Крок 6."
    }
  ],
  "l2_errors": [
    {
      "id": "err-1",
      "obligation_id": "err-1",
      "category": "l2_errors",
      "summary": "Use Він добрий студент."
    },
    {
      "id": "err-2",
      "obligation_id": "err-2",
      "category": "l2_errors",
      "summary": "Use Це гарний хлопець."
    },
    {
      "id": "err-3",
      "obligation_id": "err-3",
      "category": "l2_errors",
      "summary": "Use Яке твоє ім'я?"
    },
    {
      "id": "err-4",
      "obligation_id": "err-4",
      "category": "l2_errors",
      "summary": "Use Вона читає цікаву книжку."
    },
    {
      "id": "err-5",
      "obligation_id": "err-5",
      "category": "l2_errors",
      "summary": "Use Моя мамалига смачна."
    },
    {
      "id": "err-6",
      "obligation_id": "err-6",
      "category": "l2_errors",
      "summary": "Use Це моя синя ручка."
    }
  ],
  "phonetic_rules": [],
  "decolonization_bans": [
    {
      "id": "ban-1",
      "obligation_id": "ban-1",
      "category": "decolonization_bans",
      "summary": "Під час навчання українських прикметників абсолютно неприпустимо спиратися на пояснення через російську мову, використовувати російськомовні терміни, фонетичні аналогії чи кальки [S3]."
    },
    {
      "id": "ban-2",
      "obligation_id": "ban-2",
      "category": "decolonization_bans",
      "summary": "По-перше, уникайте порівнянь звуків в українських прикметникових закінченнях із російськими."
    },
    {
      "id": "ban-3",
      "obligation_id": "ban-3",
      "category": "decolonization_bans",
      "summary": "По-друге, уникайте використання лексичних кальок з російської у виборі прикметників."
    },
    {
      "id": "ban-4",
      "obligation_id": "ban-4",
      "category": "decolonization_bans",
      "summary": "По-третє, звертайте увагу на слова спільного роду (староста, листоноша, сирота, замазура), які часто викликають труднощі в англомовних учнів."
    },
    {
      "id": "ban-5",
      "obligation_id": "ban-5",
      "category": "decolonization_bans",
      "summary": "Особлива і безкомпромісна увага до прикметників на позначення кольорів національної символіки: Державний Прапор України є виключно синьо-жовтий."
    }
  ],
  "external_resources": []
}
```

### Implementation Map Contract

```text
Manifest obligations: 17.
Each row below is a pre-resolved slot the writer MUST fill at the artifact indicated by `artifact`, located by `location_hint`, populated using `treatment_template` as the structural blueprint.

- obligation_id: ban-1  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Підсумок
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-2  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-3  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-4  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-5  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: err-1  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Він добрий студент.
    expected_error_value: Він є добрий студент.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-2  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Це гарний хлопець.
    expected_error_value: Це гарна хлопець.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-3  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Яке твоє ім'я? (або: Як тебе звати?)
    expected_error_value: Який твоє ім'я?
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-4  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Вона читає цікаву книжку.
    expected_error_value: Вона читає цікавий книжку.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-5  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Моя мамалига смачна.
    expected_error_value: Моя мамалига смачний.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-6  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Це моя синя ручка.
    expected_error_value: Це мій синій ручка.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: step-1  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Запитання який? та базова ідентифікація
  treatment_template:
    required_claim: Крок 1. Запитання який? та базова ідентифікація Спершу вводимо питальні слова який? яка? яке? які? та демонструємо їхнє узгодження з іменниками, формуючи стійкі лексичні блоки . Учень має зрозуміти, що англійське незмінне what kind of в українській мові має чотири форми . Доречно використовувати максимально прості, життєві контексти: Який це борщ? Які це макарони? .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-2  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Тверда група прикметників (Називний відмінок)
  treatment_template:
    required_claim: Крок 2. Тверда група прикметників (Називний відмінок) Після розуміння запитань, вводимо найпоширеніші прикметники твердої групи (закінчення -ий, -а, -е, -і) . Демонструємо їх на контрастних прикладах з уже відомими іменниками: великий м’яч, велика кімната, велике відро . Учні практикують підстановку закінчень залежно від роду іменника . На цьому етапі слід уникати винятків.
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-3  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §М'яка група прикметників (Називний відмінок)
  treatment_template:
    required_claim: Крок 3. М'яка група прикметників (Називний відмінок) Коли тверда група засвоєна автоматично, обережно вводимо прикметники м'якої групи (закінчення -ій, -я, -є, -і) . Пояснюємо це не як "зовсім інші слова", а як слова з м'яким звуком перед закінченням, наводячи базові приклади: синій шарф, синє небо . Підручник для 4 класу пропонує порівнювати відмінкові закінчення твердої та м'якої груп, що є корисною аналітичною вправою і для дорослих учнів .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-4  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Прикметники в множині
  treatment_template:
    required_claim: Крок 4. Прикметники в множині Наступним етапом є узгодження прикметників у множині . Підкреслюємо важливу деталь: у множині робиться узагальнення, і для чоловічого, і для жіночого, і для середнього роду використовується закінчення -і (рідше -ї для м'якої групи) . Ця уніфікація значно спрощує завдання для англомовних учнів на ранньому етапі .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-5  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Синтаксична роль та позиція в реченні
  treatment_template:
    required_claim: Крок 5. Синтаксична роль та позиція в реченні Демонструємо, що прикметник зазвичай стоїть перед іменником (цікаву книжку), але також може виступати іменною частиною присудка без дієслова-зв'язки (Вона дуже активна жінка), уникаючи англійської кальки з обов'язковим дієсловом to be .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-6  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Якісні та відносні прикметники (Оглядово)
  treatment_template:
    required_claim: Крок 6. Якісні та відносні прикметники (Оглядово) Наприкінці рівня А1 учні лише поверхово ознайомлюються з різницею між прикметниками, що позначають ступінь ознаки (якісні: великий, смачний), та тими, що вказують на відношення (відносні: український, вчорашній) . Це створює ґрунт для майбутнього вивчення ступенів порівняння на рівні А2 .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num

```

The Tier-1 audits below (A through I, expanded in this rebuild) feed evidence
into specific dims as labeled. Audit F (activity split) → pedagogical +
engagement. Audit G (corpus access) → all dims, weighted strongest for
pedagogical (out-of-level citations are mostly a pedagogical problem). Audit H
(student-aware) → pedagogical + engagement + naturalness. Audit I (audit-line
integrity) → all dims, as a meta-signal that the writer was honest with itself.

A dim scoring high while the audits surface FLAGs is a reviewer-protocol
failure — the dim's rubric must absorb the audit evidence. A dim scoring low
without any audit FLAGs is allowed, but evidence_quotes must justify the score
from the residual rubric alone.

## Reasoning checklist (do this before scoring)

Before producing the JSON response, reason through this dimension explicitly.
If the model supports extended thinking (Claude, Gemini, GPT-5.5), use it
for these four steps. Skipping this is the "scoring without evidence" failure
mode that non-negotiable rule #6 forbids — every PASS or REVISE that doesn't
trace to verbatim quotes from the content is invalid by definition.

1. **List 3 specific evidence quotes from the Generated Content related to
   `decolonization`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the residual-judgment rubric for
   `decolonization`** (see scope section above; deterministic checks already ran).
   Is this quote evidence FOR the dimension being satisfied, or evidence
   AGAINST? A quote that just confirms a deterministic-gate criterion is
   not residual evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `decolonization` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.

Quote-copy discipline: copy/paste exact substrings from Generated Content. Do
not normalize spelling, repair grammar, add or drop prepositions, change case
endings, translate, or smooth punctuation inside quoted evidence. If a sentence
is long, quote the shortest exact offending span instead of reconstructing the
whole sentence from memory. A finding is invalid if the `quote` string does not
appear in the generated artifacts exactly or via harmless whitespace
normalization.

Do not assign a score below 8 unless `rubric_mapping` names at least one
grounded residual defect and `findings` includes a quote from the Generated
Content for that defect. If all three evidence quotes are evidence FOR the
dimension and no concrete residual defect is present, the score must be at
least 8.

If you find concrete defects, emit structured `findings` entries and canonical
`issue_ids`. Use these issue IDs when they apply:

The examples in the issue-ID definitions below are canary examples and label
definitions, not evidence from the module. Do NOT copy them into `evidence`,
`evidence_quotes`, `quote`, `rubric_mapping`, or `findings` unless the exact
same string appears in the Generated Content artifacts. A finding whose quote
comes from this instruction block instead of the generated artifacts is a
reviewer-protocol failure and will be discarded/retried.

- `AWKWARD_PASSIVE_RESULT_STATE`: calqued/evasive passive or result-state
  wording such as `застосунок має бути відкритий` where a native Ukrainian
  editor would use an active, impersonal, or clearer state construction.
- `UNNATURAL_ANTHROPOMORPHISM`: model-translated metalanguage such as
  `форма просить`, `застереження каже`, or `правило хоче`.
- `UKRAINIAN_GRAMMAR_CALQUE`: Ukrainian grammar/naturalness calque, unnatural
  explanatory metalanguage, or reviewer-like paraphrase in learner-facing
  prose, such as `будь обережний, щоб небажаний результат не стався`.
- `ENGLISH_LEAKAGE`: English-led learner-facing prose that violates the level
  calibration above. Do not use this for allowed A1/A2 glosses or scaffolding.
- `AI_LEAKAGE`: model persona, scratchpad, refusal, draft, or self-correction
  text leaked into learner-facing content.
- `PATH_LEAKAGE` / `INTERNAL_LEAKAGE`: filesystem paths, source paths,
  internal gate names, or debug artifacts leaked into learner-facing content.
- `SEMINAR_REGISTER_PATHOS`: seminar prose that drifts into motivational,
  generic, propagandistic, or wrong-register pathos instead of advanced
  Ukrainian teaching voice.

For each finding, include at minimum `issue_id`, `quote`, `severity`, and
`explanation`. Leave `issue_ids` empty when no concrete defect applies.

## Tier-1 verification audit (do this during evidence search)

Сибір case study (May 2026): an unhardened reviewer let two fabricated
citations and a fused Shevchenko line pass on the writer's first try.
Run this audit on every quote / citation / claim in the Generated Content
that touches dimension `decolonization`. The audit feeds the evidence list above:
unverified items become FLAG strings in your evidence and weigh the score
down, not silent passes.

A. **Source-attribution audit (all dims).** For every dictionary / style-guide / author cited in the Generated Content, use the single-call primitive `mcp__sources__verify_source_attribution(source, claim)` where `source` ∈ {`grinchenko_1907`, `esum`, `sum11`, `antonenko_davydovych`, `literary`, `heritage`, `wikipedia`, `style_guide`}. Verdict `discusses=false` → FLAG `unverified citation`, treat as score-against. The compose-pattern (calling `search_definitions` / `search_style_guide` / `search_grinchenko_1907` / `query_pravopys` / `search_esum` separately) is acceptable only when you need to inspect specific evidence chunks beyond the boolean verdict; for the audit pass itself, the single-call primitive is mandatory.

B. **Quote verification (all dims).** For every authored quote attributed to a literary source, call `mcp__sources__verify_quote(author, text)`. Required: `matched=true` AND `best_confidence ≥ 0.85`. Verdict false or confidence below threshold → FLAG `fabricated quote`. The tool detects fused composites (two real sources stitched into one attributed line) by returning `matched=false` with non-zero near-misses — flag those as `fused quote`. The compose-pattern (`mcp__sources__search_literary` + grep) is forbidden for this audit; use `verify_quote` exclusively.

C. **Sovietization flag (decolonization, naturalness).** When the content
   draws from `search_definitions` (СУМ-11) for politically loaded
   headwords (`ленін*`, `більшовик*`, `радянськ*`, `соціалістичн*`,
   `партійн*`, `національн*`, `школа`, `шлях`, `прапор`), apply
   heightened scrutiny. The result row's `sovietization_risk` field
   (0/1/2) is ground truth; until it is wired through the writer, fall
   back to the keyword regex above. Soviet framing reproduced into the
   module without paraphrase or correction → FLAG
   `soviet-framed definition unsupervised`.

D. **Modern Ukrainian + heritage-defense audit (naturalness, decolonization).** Flag historical / Old East Slavic / Russian-shadow / pre-Pravopys-2019 forms presented as modern Ukrainian. Also flag the opposite error: authentic Ukrainian archaisms, historisms, or dialectisms mislabeled as Russianism/surzhyk/calque without VESUM/check_modern_form plus historical/etymological/source-context verification. Authentic non-standard forms must carry `[Archaism]`, `[Historism]`, or `[Dialectism]`, a modern standard equivalent, and a brief heritage note. Missing tag/equivalent → FLAG `untagged heritage form`; false Russianism claim → FLAG `heritage form misclassified`.

Reviewers verifying a heritage flag MUST themselves call `mcp__sources__search_heritage` (or `mcp__sources__search_slovnyk_me` for a slovnyk.me-only check) before sustaining or rejecting a heritage claim. A reviewer evidence_quote that asserts heritage status without a tool-grounded citation is a reviewer-protocol failure.
When reviewing a writer heritage claim, verify that slovnyk.me citations use canonical `dictionary_slug` values from `scripts/wiki/slovnyk_me.py` and that merged `search_heritage` citations name `source_family`, `source`, and `classification` when no `dictionary_slug` is present. If the writer cites no raw tool-result excerpt, or if your own `search_heritage` call returns empty, treat the claim as unresolved rather than accepting a heritage or Russianism label.

E. **Reinforce rule #6.** Every claim pairs (i) a verbatim quote from the
   content and (ii) a specific MCP-grounded verification or an explicit
   absence-of-verification flag. A `PASS` with no grounded evidence is a
   reviewer-protocol failure.

F. **Source-pedagogy audit (pedagogical dim; grammar modules).** Verify that
   the lesson's named teaching frame is a source-backed way to teach the
   grammar, not just an attractive model-generated metaphor. Search the
   textbook/corpus layer for the key Ukrainian terms in the module's grammar
   frame and compare the results to the generated task labels. If sources
   support the underlying grammar but not the module's taxonomy, flag
   `unsupported_taxonomy_frame`. If the plan/wiki introduced the unsupported
   frame, still flag it; do not treat "the writer followed the plan" as
   evidence for pedagogy. Heuristics are allowed only when clearly labeled as
   heuristics and not drilled as grammar categories. For impersonal/no-subject
   material, verify that target examples remain subjectless; a subject noun in
   the target pattern is `impersonal_subject_intrusion`.

G. **Activity split audit (pedagogical, engagement).** The writer is
contracted to emit two complementary activity sets per `ACTIVITY_CONFIGS[A1]`:
INLINE (light, theory-time checks anchored via `<!-- INJECT_ACTIVITY: act-N -->`)
and WORKBOOK (substantive, after-lesson drill, no INJECT marker). For A1:
INLINE 4-6 / WORKBOOK 6-9 (10 total). For A2: INLINE 4-6 / WORKBOOK 8-11
(12 total). For B1-core/B2-core/C1-core: INLINE 5-7 / WORKBOOK 11-15
(16 total). For C2: INLINE 4-5 / WORKBOOK 8-10 (12 total).

The writer is required to emit a self-audit line
`<activity_split_audit>level=A1 inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
before the artifact fences. Locate this line and verify:

1. The line is PRESENT. Missing → FLAG `activity_split_audit_missing`
   (counts as evidence-against this dim).
2. The reported `inline_n` matches the actual count of
   `<!-- INJECT_ACTIVITY: act-N -->` markers in `module.md`.
3. The reported `workbook_n` matches `len(activities.yaml) - inline_n`.
4. Both counts fall within the level's allowed ranges per §"Corpus Access" of
   the writer prompt.

If the writer's self-audit reports `split_valid=true` BUT the actual counts
violate the range, that is a worse failure than `split_valid=false` (a writer
lying in its own audit). FLAG `activity_split_audit_lied`.

Pedagogical consequence to score against: INLINE activities that are too
long/substantive (item count > 3, multi-paragraph rubrics) break their "fast
theory check" purpose; WORKBOOK activities that are too trivial (single-item
quizzes, no discrimination depth) break their drill purpose. Score the
BALANCE-vs-PURPOSE not just the count.

H. **Corpus-access audit (all dims).** The writer is gated to a level-specific
corpus surface per the Corpus Access (level-gated) table in `linear-write.md`.
Verify the writer did not cite out-of-level sources:

- **a1/a2 textbook scope**: only Grades 1-4 (a1) or 1-5 (a2) source files
  allowed in citations. A `Караман Grade 10` citation in an a1 module is OUT
  OF SCOPE. FLAG `out_of_level_textbook`.
- **a1/a2 literary scope**: only children's literature, folk songs,
  fairy-tale openings, iconic phrases. A Stus / Khvylovy / Zabuzhko /
  Pidmohylny quote in an a1/a2 module is a register break. FLAG
  `out_of_level_literary`. (The curated-tag filter — F1 — is not yet built;
  rely on author/work register judgment.)
- **a1/a2 external scope**: only `ulp_blogs`, `ulp_youtube`,
  `pohribnyi_pronunciation` from `search_external`. Citations from
  `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs`
  at a1/a2 are out of scope. FLAG `out_of_level_external`.
- **b1+/seminars**: full corpus allowed; only flag if the writer claims a
  source NOT in our corpus at all (fabrication, separate failure class covered
  by audits A-B).

For ANY out-of-level citation, the quote may STILL be factually correct but the
register/source choice is wrong for the learner level. Score this as
PEDAGOGICAL evidence-against, not as a fabrication.

I. **Student-aware audit (pedagogical, engagement, naturalness).** The writer
is given a `(This is the first module — no prior learner knowledge.)` block listing cumulative_vocabulary +
known_grammar from prior modules. Verify the writer:

1. **Did not re-explain already-taught grammar.** If the learner-state lists
   "Genitive case endings -а/-я" as known_grammar and this module derives the
   rule from scratch in 200+ words, FLAG `re_explained_known_grammar`. Brief
   reference (`як ти бачив у модулі 7`) is fine; a full re-derivation is not.

2. **Did not introduce unknown vocabulary without inline gloss.** Scan
   `module.md` prose for Ukrainian content words. For any word that is (a) NOT
   in cumulative_vocabulary, (b) NOT in this module's `vocabulary.yaml`, (c)
   NOT a proper noun / Latin borrowing, and (d) NOT introduced with inline
   italic gloss `*(translation)*`, FLAG `unknown_vocab_unscaffolded`.

3. **Foreshadowing pattern visible.** If new lemmas appear in prose BEFORE
   their `vocabulary.yaml` entry, they should carry inline gloss at first
   mention. Absence of gloss on first mention = `missing_foreshadowing_gloss`.

4. **Stacked vocab-level check evidence.** For non-plan lemmas the writer
   introduced, check the `<plan_reasoning>` for `<vocab_level_check>` nodes.
   Missing for a non-plan lemma = `unverified_vocab_introduction`.

5. **Intentional repetition is signposted.** If the module repeats a
   learner-facing concept, skill, or activity family from earlier modules,
   the prose should explicitly frame it as review, reuse, or deeper practice
   before asking the learner to do it again. Good patterns: "You already
   practiced X in Module N; now use it for Y", "Quick review: X. New step:
   Y", or "This is the same X, but the task is harder because Y." If the
   repeated concept appears as if new, FLAG `unsignposted_repetition`.

Pedagogical score: respecting the learner's prior knowledge is what makes the
module BUILD instead of REPEAT. Naturalness score: scaffolded vocabulary
introduction reads as a real teacher's voice; un-introduced vocab feels like a
textbook dump.

J. **Pre-emit audit-line integrity (all dims).** The writer is required to
emit three machine-readable audit lines BEFORE the artifact fences, in order:

1. `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[...]</implementation_map_audit>`
   (per #2094)
2. `<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`
   (per #2095)
3. `<activity_split_audit>level=A1 inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
   (per the just-merged Activity Types section)

Verify ALL THREE lines are present, parseable, and report values consistent
with the artifacts. Any missing line = the writer has failed the protocol;
FLAG `audit_line_missing` with the missing line name. Any line whose claim
doesn't match the artifacts = FLAG `audit_line_inconsistent`.

These audits exist BECAUSE the writer is doing self-grading; the reviewer's
job here is to cross-check that the self-grading matches reality. A green audit
line on broken content is a more serious failure than a red audit line on
broken content (the writer is lying to its own audit).

Return the review object conforming to this authoritative JSON Schema (qg_schema.py, dimension profile). Use empty arrays for no findings/items and null only where the schema permits it.

```json
{
  "type": "object",
  "properties": {
    "score": {
      "type": "number",
      "minimum": 0,
      "maximum": 10
    },
    "evidence": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_quotes": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "rubric_mapping": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "issue_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "issue_id": {
            "type": "string",
            "minLength": 1
          },
          "quote": {
            "type": "string",
            "minLength": 1
          },
          "severity": {
            "type": "string",
            "minLength": 1
          },
          "explanation": {
            "type": "string",
            "minLength": 1
          },
          "replacement": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ]
          },
          "dimension": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "issue_id",
          "quote",
          "severity",
          "explanation",
          "replacement",
          "dimension"
        ],
        "additionalProperties": false
      }
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "verdict": {
      "type": "string",
      "enum": [
        "PASS",
        "REVISE",
        "REJECT"
      ]
    }
  },
  "required": [
    "score",
    "evidence",
    "evidence_quotes",
    "rubric_mapping",
    "issue_ids",
    "findings",
    "flags",
    "verdict"
  ],
  "additionalProperties": false
}
```

The `flags` array MUST contain any FLAG strings raised during audits A-J that
apply to your assigned dim per the per-dim labeling in §"Scope". An empty array
is fine when no flags fired. The pipeline aggregates flags across dims and
surfaces them in the build telemetry; the writer's self-correction loop reads
them to know what to fix on retry.

## Module Context

- Level: A1
- Module: 9
- Slug: what-is-it-like
- Word target: 550

## Module Size Policy — dossier/evidence-led advisory context (#4801)

- Basis: core_evidence_packet
- Density band: core_pedagogy_standard
- Plan floor words: 550
- Recommended range: 3500-5000
- Advisory ceiling words: 5000
- Expansion permission: source_backed_only
- Status: advisory_ok
- Rule: satisfy objectives and evidence coverage, not a token target; the reviewed plan floor still binds.
- Rule: expand only when added material is source-backed and pedagogically necessary.
- Rule: if grounded material runs out before the floor, emit `<!-- SIZE_POLICY_MISMATCH: plan floor exceeds sourced evidence -->` instead of inventing depth.
- Rule: do not repeat framing, conclusions, transitions, definitions, generic exposition, or uncited interpretation to reach the floor.
Notes:
- Core A1-C2 uses a pedagogy/evidence-packet basis; do not apply seminar dossier ceilings mechanically.
- Reviewer rule: do not fail or pass a module on word count alone; deterministic gates handled the floor.
- Reviewer rule: inspect deterministic repetition evidence and marginal pedagogical value throughout the full size band, not only above the advisory ceiling.
- Reviewer rule: if the module is over the advisory ceiling, decide whether the extra length is source-backed density, necessary pedagogy, or filler/padding; length alone is not a failure.
- Reviewer rule: source-backed density is acceptable evidence; repeated framing, generic exposition, uncited interpretation, and inflated transitions are padding evidence.
Padding diagnostic:
- Status: within_advisory_ceiling
- Over advisory ceiling words: 0
- Repetition status: clear
- Repetition matches: 0
- Review action: no_size_padding_signal; review pedagogy and source use normally

Use this as review context, not as a mechanical word-count gate. Inspect the
deterministic paragraph matches and marginal pedagogical value throughout the
full size band, not only above the advisory ceiling. Source-backed density and
necessary pedagogy remain acceptable even when long. Repeated framing,
conclusions, transitions, definitions, generic exposition, or uncited
interpretation are filler/padding defects when they affect `decolonization`.

## Immersion Rule

STRUCTURAL TARGETS (Phase A placeholders; Phase B calibrates):
- At least N UK dialogue lines (band: 0)
- At least N vocab entries (band: 0)
- At least N UK example sentences in bulleted lists (band: 0)
- No UK-only run longer than K words without inline English support (band: 10)
TARGET: 40-55% Ukrainian. ULP S1 bilingual immersion.
LANGUAGE ROLES:
- PRIMARY POSTURE: Ukrainian-first, example-first teaching with brief receding English support.
- ULP SSOT: follow docs/best-practices/ulp-presentation-pattern.md for the Ohoiko S1 rhythm. The full seven-practice contract is injected only for `letter_module: true` plans.

## Contract YAML

```yaml
sections:
- title: Підсумок
  word_budget:
    target: 300
    min: 270
    max: 330
vocabulary_required:
- який, яка, яке (what kind? — m/f/n)
- великий (big)
- маленький (small)
- новий (new)
- старий (old)
- гарний (nice, beautiful)
- чистий (clean)
- дорогий (expensive)
- дешевий (cheap)
vocabulary_optional: []
source_note: Full plan below is authoritative for points, activity hints, vocabulary,
  and references.
```

## Plan

```yaml
activity_hints:
- focus: 'Додайте правильне закінчення прикметника: нов__ книга, велик__ стіл, чист__
    вікно'
  items: 10
  type: fill-in
- focus: 'З''єднайте прикметники-антоніми: великий ↔ маленький'
  items: 6
  type: match-up
- focus: Який/яка/яке? Оберіть правильне питальне слово.
  items: 6
  type: quiz
- focus: Опишіть кімнату, використовуючи подані іменники та прикметники
  items: 6
  type: fill-in
- focus: Типові адʼєктивні суржикові пари — оберіть нормативну форму (1:1 mirror of
    wiki "Типові помилки L2", усі 9 пар)
  items:
  - Цей суп дуже {смачний|вкусний}.
  - У мене є {жовтий|жолтий} олівець.
  - У сусідки {чорний|черний} кіт.
  - Прапор {червоний|красний}, а не білий.
  - Це {поганий|плохий} фільм.
  - Це {правильна|вірна} відповідь на запитання.
  - Дай мені, будь ласка, {будь-який|любий} олівець.
  - Сергій — {розумний|умний} хлопчик.
  - Тарас — {лінивий|ленивий} учень.
  type: fill-in
changelog:
- changes:
  - 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (worked
    example: at-the-cafe / PR #1412).'
  - Added Surzhyk-drill fill-in activity mirroring the wiki "Типові помилки L2" table
    1:1 (all 9 wiki pairs as quiz items — closes the wiki-plan drift gap completely).
  - Added new objective for recognising adjective-specific Surzhyk pairs (mirrors
    at-the-cafe pattern of pairing decolonization vocabulary with an explicit objective).
  - Added wiki back-reference to references[] (LOCKED 2026-04-23).
  - Added lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes)
    per the rubric convention.
  date: '2026-04-23'
  version: 1.3.0
connects_to:
- a1-010 (Кольори)
content_outline:
- points:
  - 'Самоперевірка: Яке закінчення має прикметник чоловічого роду? (-ий/-ій). Жіночого?
    (-а/-я). Середнього? (-е/-є). Опишіть свою кімнату трьома реченнями, використовуючи
    прикметники.'
  section: Підсумок
  words: 300
dialogue_situations:
- motivation: Запитання Який/яка/яке? зі словами книга(f), атлас(m), фото(n), плакат(m),
    листівка(f)
  setting: 'На книжковому ярмарку вихідного дня — розглядаємо книги, карти та плакати.
    Описуємо предмети: новий атлас (m), цікава книга (f), старе фото (n), великий
    плакат (m), маленька листівка (f). НЕ сумки чи меблі.'
  speakers:
  - Тарас
  - Софія
focus: grammar
grammar:
- Узгодження прикметника з іменником у називному відмінку (закінчення -ий/-а/-е)
- Питальні слова який/яка/яке/які
- Пари прикметників-антонімів як стратегія розширення словникового запасу
- Сполучник «а» (протиставлення) та «і» (поєднання)
level: A1
lifecycle: locked
module: a1-009
objectives:
- Навчитися узгоджувати прикметники з іменниками в роді (лише в називному відмінку)
- Вміти ставити запитання за допомогою слів який/яка/яке
- Описувати предмети та кімнати, використовуючи поширені пари прикметників
- Будувати описові речення, поєднуючи іменники з попереднього модуля «Речі мають рід»
  з прикметниками з цього модуля
- Впізнавати типові адʼєктивні суржикові пари (вкусний → смачний, жолтий → жовтий,
  черний → чорний, красний → червоний, плохий → поганий, вірний → правильний, любий
  → будь-який, умний → розумний, ленивий → лінивий)
pedagogy: PPP
phase: A1.2 [Мій світ]
prerequisites:
- a1-008 (Речі мають рід)
references:
- notes: 'Правило: Прикметник має такий рід, як іменник, з яким він зв''язаний.'
  title: Пономарова Grade 3, p.98
- notes: Вправи на узгодження прикметників, завдання на опис кімнати.
  title: Вашуленко Grade 3, p.128-131
- notes: Authoritative pedagogical brief — see Step 5 "Межа A1" callout (oblique-case
    scope), the writer-note pinning the three permitted A1 adj formats, and the "Типові
    помилки L2" table (9 verified adjective-specific Surzhyk / calque / paronym pairs).
  title: 'Wiki: pedagogy/a1/what-is-it-like (LOCKED 2026-04-23)'
register: розмовний
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md
  template (worked example: at-the-cafe / PR #1412). See PR body for the wiki-side
  gap closure (lifecycle metadata, Типові помилки L2 table, writer-scope tightening)
  and the plan-side findings (no Russianisms in prose, no calques in vocab_hints,
  no plan-internal contradictions; the one drift gap — no plan-side hook for the wiki''s
  adjective Surzhyk table — was closed by adding a fill-in activity mirroring the
  table 1:1). Lifecycle marker convention per the rubric doc.'
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-what-is-it-like
sequence: 9
slug: what-is-it-like
subtitle: Великий стіл, нова книга — опис предметів
title: Який він?
version: 1.3.0
vocabulary_hints:
  recommended:
  - поганий (bad)
  - брудний (dirty)
  - світлий (light, bright)
  - темний (dark)
  - а (and/but — contrast)
  - але (but)
  required:
  - який, яка, яке (what kind? — m/f/n)
  - великий (big)
  - маленький (small)
  - новий (new)
  - старий (old)
  - гарний (nice, beautiful)
  - чистий (clean)
  - дорогий (expensive)
  - дешевий (cheap)
word_target: 550

```

## Generated Content

## module.md

# Підсумок

У цьому підсумковому уроці ви закріпите всі знання про прикметники та опис предметів:
- **Питальні слова** — ask **який? / яка? / яке? / які?** with any noun;
- **Узгодження роду** — accurately match adjective endings (**-ий / -а / -е / -і**);
- **Пари ознак** — use descriptive pairs (**великий / маленький**, **новий / старий**, **чистий / брудний**);
- **Опис простору** — build natural sentences to describe a room, desk, or fair.

Повторення попередніх уроків — retrieval from Lessons 1 and 2:
У перших двох уроках ви дізналися, що іменник завжди визначає рід і закінчення прикметника:
- чоловічий рід (він): **новий стіл**, **старий атлас**, **великий плакат**;
- жіночий рід (вона): **нова книга**, **гарна листівка**, **чиста кімната**;
- середній рід (воно): **нове фото**, **велике вікно**, **чисте дзеркало**;
- множина (вони): **нові книги**, **гарні речі**, **старі фото**.

Також ви навчилися поєднувати ознаки за допомогою сполучника **і** (**новий і чистий**), протиставляти два предмети сполучником **а** (**стіл новий, а стілець старий**) та додавати уточнення через **але** (**маленька, але світла**).

## Підсумок

Оглядово: **якісні: великий, смачний** name qualities, while
**відносні: український, вчорашній** connect a noun to a place, language, or
time. You do not need the theory yet. You only need safe phrases:

- **Добрий день.**
- **смачна кава**
- **українська мова**
- **рідні люди**
- **популярний музикант**
- **активна жінка**
- **талановитий композитор**

<!-- INJECT_ACTIVITY: act-301 -->

Послухайте підсумкову розмову про опис речей — listen to a concluding conversation about describing things:

> **Тарас**: Софіє, подивись, яка гарна листівка!
> **Софія**: Так, листівка дуже гарна і чиста.
> **Тарас**: А ця книга? Яка вона?
> **Софія**: Це нова і цікава книга.
> **Тарас**: А цей атлас? Який він?
> **Софія**: Атлас старий, але дуже цікавий.
> **Тарас**: А фото біля книги? Яке воно?
> **Софія**: Воно маленьке, але гарне і чисте.

Продовження розмови — the conversation continues:

> **Тарас**: А де твоя стара лампа?
> **Софія**: Ось вона, лампа стара, але світла.
> **Тарас**: Яка чиста і світла кімната!
> **Софія**: Дякую, тут новий стіл і чисте вікно.
> **Тарас**: А це смачний суп?
> **Софія**: Так, це дуже смачний суп.
> **Тарас**: Це правильний вибір!
> **Софія**: Ти дуже розумний друг.

Розбір нових реплік — breakdown of lines:

| Українська | English support |
| --- | --- |
| **Софіє, подивись, яка гарна листівка!** | Sofia, look, what a nice postcard! |
| **Так, листівка дуже гарна і чиста.** | Yes, the postcard is very nice and clean. |
| **Це нова і цікава книга.** | This is a new and interesting book. |
| **Атлас старий, але дуже цікавий.** | The atlas is old, but very interesting. |
| **Воно маленьке, але гарне і чисте.** | It is small, but nice and clean. |
| **Ось вона, лампа стара, але світла.** | Here it is, the lamp is old, but bright. |
| **Яка чиста і світла кімната!** | What a clean and bright room! |
| **Дякую, тут новий стіл і чисте вікно.** | Thank you, here is a new table and a clean window. |
| **Так, це дуже смачний суп.** | Yes, this is a very tasty soup. |
| **Це правильний вибір!** | This is a correct choice! |
| **Ти дуже розумний друг.** | You are a very smart friend. |

<!-- INJECT_ACTIVITY: act-302 -->

:::tip
Пам'ятайте про узгодження — remember the agreement rule:
Іменник завжди обирає закінчення прикметника. Якщо іменник жіночого роду (**кімната**, **лампа**), прикметник має закінчення **-а** (**чиста кімната**, **стара лампа**). Якщо іменник середнього роду (**вікно**, **фото**), використовуйте закінчення **-е** (**чисте вікно**, **гарне фото**).
:::

<!-- INJECT_ACTIVITY: act-303 -->

Now make your own three-line room description. Keep it short:

```text
Це моя кімната.
Вона маленька, але гарна.
У мене є новий стіл і стара лампа.
```

Support after the Ukrainian lines:

| Українська | English support |
| --- | --- |
| **Це моя кімната.** | This is my room. |
| **Вона маленька, але гарна.** | It is small, but nice. |
| **У мене є новий стіл і стара лампа.** | I have a new table and an old lamp. |

Then change one noun and one adjective:

- **стіл** -> **телефон**: **новий телефон**
- **книга** -> **листівка**: **гарна листівка**
- **вікно** -> **фото**: **старе фото**

<!-- INJECT_ACTIVITY: act-304 -->

A good final check is to cover the ending and ask two questions. First, what
gender is the noun? Second, is the noun one thing or many things? If the noun is
**стіл**, your answer is **який?** and **-ий**. If it is **книга**, your
answer is **яка?** and **-а**. If it is **фото**, your answer is **яке?** and
**-е**. If it is **книги**, your answer is **які?** and **-і**. This small
routine is more useful than memorizing a large table before you can use the
phrases.

<!-- INJECT_ACTIVITY: act-305 -->

Workbook practice will make the pattern automatic: choose the right question
word, finish the adjective ending, match opposites, describe a room, and repair
the adjective traps.

### Підсумок модуля

Підіб'ємо підсумки всього модуля — module summary:
- **Чотири форми запитання**: використовуйте **який?** (чоловічий рід), **яка?** (жіночий рід), **яке?** (середній рід) та **які?** (множина).
- **Базові закінчення**: тверда група має чіткі закінчення **-ий**, **-а**, **-е**, **-і** у називному відмінку.
- **Природний зв'язок слів**: в українській мові прикметник може стояти перед іменником (**нова книга**) або після нього (**книга нова**) без зайвого дієслова **є**.
- **Точні описи**: поєднуйте протилежні ознаки за допомогою сполучників **і**, **а**, **але**.

Вітаємо з успішним завершенням модуля! Тепер ви впевнено володієте основними моделями опису предметів українською мовою.


## activities.yaml

inline:
- id: act-301
  type: match-up
  title: Узгодження прикметників
  instruction: З'єднайте прикметник із відповідним іменником за родом.
  pairs:
  - left: цікавий
    right: атлас
  - left: цікава
    right: книга
  - left: цікаве
    right: фото
  - left: смачний
    right: суп
  - left: чиста
    right: кімната
  - left: чисте
    right: вікно
- id: act-302
  type: fill-in
  title: Форми прикметників
  instruction: Оберіть правильне закінчення або слово для кожного речення.
  items:
  - sentence: У мене є нов__ стіл.
    answer: ий
    options:
    - ий
    - а
    - е
    explanation: Стіл — чоловічий рід, тому новий стіл.
  - sentence: Це дуже гарн__ листівка.
    answer: а
    options:
    - а
    - ий
    - е
    explanation: Листівка — жіночий рід, тому гарна листівка.
  - sentence: На столі лежить стар__ фото.
    answer: е
    options:
    - е
    - ий
    - а
    explanation: Фото — середній рід, тому старе фото.
  - sentence: Моя кімната маленька, ___ світла.
    answer: але
    options:
    - але
    - який
    - яка
    explanation: Сполучник але вказує на протиставлення чи уточнення.
  - sentence: Це нов__ і корисний атлас.
    answer: ий
    options:
    - ий
    - а
    - е
    explanation: Атлас — чоловічий рід, тому новий атлас.
  - sentence: Тут стоїть стар__ лампа.
    answer: а
    options:
    - а
    - ий
    - е
    explanation: Лампа — жіночий рід, тому стара лампа.
- id: act-303
  type: group-sort
  title: Розподіл за родами
  instruction: Розподіліть словосполучення за родами іменників.
  groups:
  - label: Чоловічий рід (Він)
    items:
    - смачний суп
    - правильний приклад
  - label: Жіночий рід (Вона)
    items:
    - цікава книга
    - стара лампа
  - label: Середній рід (Воно)
    items:
    - чисте вікно
    - гарне фото
- id: act-304
  type: quiz
  title: Обери точний опис
  instruction: Оберіть правильний варіант опису предмета.
  items:
  - prompt: Який атлас?
    options:
    - text: новий атлас
      correct: true
    - text: нова атлас
      correct: false
    - text: нове атлас
      correct: false
    explanation: Атлас — іменник чоловічого роду.
  - prompt: Яка кімната?
    options:
    - text: чиста кімната
      correct: true
    - text: чистий кімната
      correct: false
    - text: чисте кімната
      correct: false
    explanation: Кімната — іменник жіночого роду.
  - prompt: Яке вікно?
    options:
    - text: велике вікно
      correct: true
    - text: великий вікно
      correct: false
    - text: велика вікно
      correct: false
    explanation: Вікно — іменник середнього роду.
  - prompt: Який суп?
    options:
    - text: смачний суп
      correct: true
    - text: смачна суп
      correct: false
    - text: смачне суп
      correct: false
    explanation: Суп — іменник чоловічого роду.
  - prompt: Яка листівка?
    options:
    - text: гарна листівка
      correct: true
    - text: гарний листівка
      correct: false
    - text: гарне листівка
      correct: false
    explanation: Листівка — іменник жіночого роду.
  - prompt: Яке фото?
    options:
    - text: цікаве фото
      correct: true
    - text: цікавий фото
      correct: false
    - text: цікава фото
      correct: false
    explanation: Фото — іменник середнього роду.
- id: act-305
  type: odd-one-out
  title: Знайди зайве
  instruction: Знайдіть словосполучення, яке відрізняється за граматичним родом.
  items:
  - options:
    - text: цікава книга
      correct: false
    - text: чиста кімната
      correct: false
    - text: смачний суп
      correct: true
    - text: стара лампа
      correct: false
    explanation: Смачний суп — чоловічий рід, інші словосполучення — жіночого роду.
  - options:
    - text: новий стіл
      correct: false
    - text: великий плакат
      correct: false
    - text: старий атлас
      correct: false
    - text: чисте вікно
      correct: true
    explanation: Чисте вікно — середній рід, інші словосполучення — чоловічого роду.
  - options:
    - text: гарне фото
      correct: false
    - text: велике ліжко
      correct: false
    - text: нова листівка
      correct: true
    - text: чисте дзеркало
      correct: false
    explanation: Нова листівка — жіночий рід, інші словосполучення — середнього роду.
  - options:
    - text: розумний хлопчик
      correct: false
    - text: лінивий учень
      correct: false
    - text: правильний приклад
      correct: false
    - text: активна жінка
      correct: true
    explanation: Активна жінка — жіночий рід, інші словосполучення — чоловічого роду.
  - options:
    - text: чиста кімната
      correct: false
    - text: стара лампа
      correct: false
    - text: новий телефон
      correct: true
    - text: гарна листівка
      correct: false
    explanation: Новий телефон — чоловічий рід, інші словосполучення — жіночого роду.
  - options:
    - text: старе ліжко
      correct: false
    - text: новий атлас
      correct: true
    - text: цікаве фото
      correct: false
    - text: велике вікно
      correct: false
    explanation: Новий атлас — чоловічий рід, інші словосполучення — середнього роду.
workbook:
- id: act-w5
  type: translate
  title: Обери український рядок
  instruction: Choose the Ukrainian sentence that matches the English cue.
  items:
  - source: My room is small but nice.
    options:
    - text: Моя кімната маленька, але гарна.
      correct: true
    - text: Мій кімната маленький, але гарний.
      correct: false
    - text: Моє кімната маленьке, але гарне.
      correct: false
    explanation: Кімната is feminine.
  - source: The table is new and clean.
    options:
    - text: Стіл новий і чистий.
      correct: true
    - text: Стіл нова і чиста.
      correct: false
    - text: Стіл нове і чисте.
      correct: false
    explanation: Стіл is masculine.
  - source: The photo is old.
    options:
    - text: Фото старе.
      correct: true
    - text: Фото стара.
      correct: false
    - text: Фото старий.
      correct: false
    explanation: Фото is neuter in this lesson.
  - source: A cheap postcard
    options:
    - text: дешева листівка
      correct: true
    - text: дешевий листівка
      correct: false
    - text: дешеве листівка
      correct: false
    explanation: Листівка is feminine.
  - source: Good afternoon.
    options:
    - text: Добрий день.
      correct: true
    - text: Добра день.
      correct: false
    - text: Добре день.
      correct: false
    explanation: День is masculine, so the greeting is Добрий день.
  - source: The books are interesting.
    options:
    - text: Книги цікаві.
      correct: true
    - text: Книги цікава.
      correct: false
    - text: Книги цікаве.
      correct: false
    explanation: Plural phrases use цікаві.
- id: act-w6
  type: true-false
  title: Швидка перевірка
  instruction: Decide if the statement is right.
  items:
  - statement: Стіл новий.
    answer: true
    explanation: Стіл is masculine, so новий is correct.
  - statement: Книга нове.
    answer: false
    explanation: Книга is feminine; say Книга нова.
  - statement: Вікно чисте.
    answer: true
    explanation: Вікно is neuter.
  - statement: Який кімната?
    answer: false
    explanation: Кімната is feminine; ask Яка кімната?
  - statement: Кімната маленька, але гарна.
    answer: true
    explanation: Both adjectives agree with кімната.
  - statement: 'В українській можна описати річ без є: Книга цікава.'
    answer: true
    explanation: This no-є present-tense frame is normal.
- id: act-w301
  type: fill-in
  title: Закріплення закінчень
  instruction: Вставте правильну форму прикметника.
  items:
  - sentence: Сергій дуже ___ хлопчик.
    answer: розумний
    options:
    - розумний
    - розумна
    - розумне
    explanation: Хлопчик — чоловічий рід.
  - sentence: Тарас іноді ___, але він старається.
    answer: лінивий
    options:
    - лінивий
    - лінива
    - ліниве
    explanation: Тарас — чоловічий рід.
  - sentence: Це ___ приклад у зошиті.
    answer: правильний
    options:
    - правильний
    - правильна
    - правильне
    explanation: Приклад — чоловічий рід.
  - sentence: На столі стоїть ___ лампа.
    answer: стара
    options:
    - стара
    - старий
    - старе
    explanation: Лампа — жіночий рід.
  - sentence: Це ___ і чистий стіл.
    answer: новий
    options:
    - новий
    - нова
    - нове
    explanation: Стіл — чоловічий рід.
  - sentence: У кімнаті є ___ і гарне вікно.
    answer: чисте
    options:
    - чисте
    - чистий
    - чиста
    explanation: Вікно — середній рід.
- id: act-w302
  type: unjumble
  title: Склади речення
  instruction: Розставте слова у правильному порядку, щоб утворити речення.
  items:
  - words:
    - Це
    - моя
    - маленька
    - кімната.
    sentence: Це моя маленька кімната.
    explanation: Це моя маленька кімната.
  - words:
    - Стіл
    - новий
    - і
    - чистий.
    sentence: Стіл новий і чистий.
    explanation: Стіл новий і чистий.
  - words:
    - У
    - мене
    - є
    - стара
    - лампа.
    sentence: У мене є стара лампа.
    explanation: У мене є стара лампа.
  - words:
    - Це
    - дуже
    - цікава
    - книга.
    sentence: Це дуже цікава книга.
    explanation: Це дуже цікава книга.
  - words:
    - Стіл
    - новий,
    - а
    - стілець
    - старий.
    sentence: Стіл новий, а стілець старий.
    explanation: Стіл новий, а стілець старий.
  - words:
    - Кімната
    - маленька,
    - але
    - гарна.
    sentence: Кімната маленька, але гарна.
    explanation: Кімната маленька, але гарна.
- id: act-w303
  type: match-up
  title: Іменник та ознака
  instruction: Поєднайте предмет із відповідним описом.
  pairs:
  - left: новий стіл
    right: чистий
  - left: маленька кімната
    right: світла
  - left: велике вікно
    right: чисте
  - left: старий атлас
    right: корисний
  - left: гарячий суп
    right: смачний
  - left: нова книга
    right: цікава
- id: act-w304
  type: error-correction
  title: Виправ помилки в родах
  instruction: Знайдіть і виправте помилку в узгодженні роду.
  items:
  - sentence: Це нова атлас.
    error: нова
    answer: новий
    options:
    - новий
    - нова
    - нове
    explanation: Атлас — чоловічий рід, тому новий атлас.
  - sentence: У мене є цікавий книга.
    error: цікавий
    answer: цікава
    options:
    - цікава
    - цікавий
    - цікаве
    explanation: Книга — жіночий рід, тому цікава книга.
  - sentence: Тут стоїть старий лампа.
    error: старий
    answer: стара
    options:
    - стара
    - старий
    - старе
    explanation: Лампа — жіночий рід, тому стара лампа.
  - sentence: Це гарний фото.
    error: гарний
    answer: гарне
    options:
    - гарне
    - гарний
    - гарна
    explanation: Фото — середній рід, тому гарне фото.
  - sentence: Стіл нова і чиста.
    error: нова і чиста
    answer: новий і чистий
    options:
    - новий і чистий
    - нова і чиста
    - нове і чисте
    explanation: Стіл — чоловічий рід.
  - sentence: Вікно великий і світлий.
    error: великий і світлий
    answer: велике і світле
    options:
    - велике і світле
    - великий і світлий
    - велика і світла
    explanation: Вікно — середній рід.
- id: act-w305
  type: group-sort
  title: Сортування за ознаками
  instruction: Розподіліть прикметники за групами ознак.
  groups:
  - label: Розмір і вік
    items:
    - великий
    - маленький
    - старий
  - label: Якість і оцінка
    items:
    - гарний
    - поганий
    - смачний
  - label: Світло і стан
    items:
    - чистий
    - світлий
    - темний


## vocabulary.yaml

- lemma: стара
  translation: old, feminine
  pos: adj
  usage: Лампа стара.
- lemma: гарна
  translation: nice, beautiful, feminine
  pos: adj
  usage: Листівка гарна.
- lemma: гарне
  translation: nice, beautiful, neuter
  pos: adj
  usage: Вікно гарне.
- lemma: чиста
  translation: clean, feminine
  pos: adj
  usage: Кімната чиста.
- lemma: чисте
  translation: clean, neuter
  pos: adj
  usage: Вікно чисте.
- lemma: цікавий
  translation: interesting, masculine
  pos: adj
  usage: Це цікавий атлас.
- lemma: цікава
  translation: interesting, feminine
  pos: adj
  usage: Це цікава книга.
- lemma: цікаве
  translation: interesting, neuter
  pos: adj
  usage: Це цікаве фото.
- lemma: смачний
  translation: tasty, masculine
  pos: adj
  usage: Це смачний суп.
- lemma: правильний
  translation: correct, masculine
  pos: adj
  usage: Це правильний приклад.
- lemma: розумний
  translation: smart, masculine
  pos: adj
  usage: Сергій розумний.
- lemma: лінивий
  translation: lazy, masculine
  pos: adj
  usage: Учень лінивий.


## resources.yaml

- title: Пономарова 3 клас — Узагальнення знань про прикметник
  source: 'Пономарова К. І. Українська мова та читання: підруч. для 3 кл. — с. 98-102'
  notes: Підсумкові вправи на узгодження прикметників з іменниками та самоперевірку.
- title: Прикметники і прислівники — Adjectives and Adverbs in Ukrainian
  url: https://www.ukrainianlessons.com/adjectives-and-adverbs/
  notes: Ukrainian Lessons overview of adjective agreement and descriptive patterns
    for review.
- title: 'Dobra Forma: Adjectives (Gender and Number in Nominative)'
  url: https://opentext.ku.edu/dobraforma/chapter/16-1/
  notes: Open textbook practice and summary exercises for nominative adjective forms.
- title: Adjectives & Adverbs Chart
  url: https://www.ukrainianlessons.com/adjectives-adverbs-chart/
  notes: Reference chart for learners summarizing adjective endings across genders.


## Task

Review the assigned dimension `decolonization` and return the required JSON object now.
No preamble, no markdown, no questions.
