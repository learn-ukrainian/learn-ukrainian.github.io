{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of the complete module across all lessons. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Мелодика", "sections": ["Наголос", "Мелодика"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Друк, зошит, голос", "sections": ["Читаємо вголос", "Друк, зошит, голос"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Перевірка", "sections": ["Перевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 1}, {"placement": "inline", "index": 4, "new_id": "act-5", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 3}], "items_min_exempt": [{"id": "act-1", "reason": "4-item original activity preserved from baseline"}, {"id": "act-2", "reason": "4-item original activity preserved from baseline"}, {"id": "act-3", "reason": "3-item original activity preserved from baseline"}, {"id": "act-4", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w6", "reason": "4-item original activity preserved from baseline"}], "proper_names": []}

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

Assigned dimension: engagement

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

For `engagement` specifically:

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
teach while applying the existing `engagement` rubric.

### Wiki Obligations Manifest

```json
{
  "slug": "stress-and-melody",
  "wiki_path": "/home/ops/learn-ukrainian/.worktrees/builds/a1-stress-and-melody-20260914-120044/wiki/pedagogy/a1/stress-and-melody.md",
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
      "summary": "Use Чітка вимова всіх голосних: [молоко́] instead of Редукція ненаголошених: вимовляти «молоко» як [мeлeко́] або [мшва-лшва-ко́]: В англійській ненаголошені склади зводяться до нейтрального звука (schwa)."
    },
    {
      "id": "err-2",
      "obligation_id": "err-2",
      "category": "l2_errors",
      "summary": "Use Наголос на другому компоненті: [кіломе́тр] instead of Наголос на першому складі у запозиченнях: [кі́лометр]: Іншомовні складні іменники на -метр в українській мові мають наголошений другий компонент («сантиме́тр», «кіломе́тр»), за винятком назв приладів («баро́метр») [S7]."
    },
    {
      "id": "err-3",
      "obligation_id": "err-3",
      "category": "l2_errors",
      "summary": "Use Перенесення наголосу: «кни́жка» — «книжки́» instead of Фіксування наголосу в множині: «кни́жка» — «кни́жки»: Англійська мова зберігає наголос кореня при додаванні закінчення -s."
    },
    {
      "id": "err-4",
      "obligation_id": "err-4",
      "category": "l2_errors",
      "summary": "Use Використовувати логічний наголос на значущому слові instead of Завжди наголошувати займенники в реченні: Англомовні можуть надмірно виділяти займенники («Я йду»)."
    },
    {
      "id": "err-5",
      "obligation_id": "err-5",
      "category": "l2_errors",
      "summary": "Use Наголос на суфіксі: [мале́нький] instead of Ігнорування суфікса -еньк-: [ма́ленький]: Прикметниковий пестливий суфікс -еньк- завжди наголошений («мале́нький», «чорне́нький») [S7]."
    },
    {
      "id": "err-6",
      "obligation_id": "err-6",
      "category": "l2_errors",
      "summary": "Use Чіткий наголос за правилом: [одина́дцять] (передостанній), [сімдеся́т] (останній) instead of Вимова числівників на -дцять і -десят із неправильним наголосом: [о́динадцять], [сі́мдесят]: В українській мові у числівниках на -десят наголошений останній склад, а на -дцять — передостанній [S7]."
    },
    {
      "id": "err-7",
      "obligation_id": "err-7",
      "category": "l2_errors",
      "summary": "Use Наголос на другому складі: [була́], [були́] instead of Помилкове наголошення дієслів минулого часу: [бу́ла], [бу́ли]: Англомовні тяжіють до наголосу на першому складі."
    }
  ],
  "phonetic_rules": [],
  "decolonization_bans": [
    {
      "id": "ban-1",
      "obligation_id": "ban-1",
      "category": "decolonization_bans",
      "summary": "Автори модулів повинні пам'ятати, що процес деколонізації освіти включає повну відмову від російськоцентричного порівняльного підходу."
    },
    {
      "id": "ban-2",
      "obligation_id": "ban-2",
      "category": "decolonization_bans",
      "summary": "Уникайте російських еталонів: Категорично заборонено пояснювати український наголос чи мелодику через призму російської фонетики (наприклад, заборонено писати «тут наголос не такий, як у російській» або пояснювати відсутність сильного акання/ікання як «відмінність від російської»)."
    },
    {
      "id": "ban-3",
      "obligation_id": "ban-3",
      "category": "decolonization_bans",
      "summary": "Фонетична чистота і «акання»: Російській мові притаманна сильна якісна редукція («акання» та «ікання» в ненаголошених позиціях)."
    },
    {
      "id": "ban-4",
      "obligation_id": "ban-4",
      "category": "decolonization_bans",
      "summary": "Калькові вітання та формули: Працюючи над ритмікою діалогів, ніколи не використовуйте зросійщені кальки."
    },
    {
      "id": "ban-5",
      "obligation_id": "ban-5",
      "category": "decolonization_bans",
      "summary": "Символічний простір: Для прикладів використання логічного наголосу чи вправ на інтонацію активно використовуйте українські реалії та канонічні формули."
    }
  ],
  "external_resources": []
}
```

### Implementation Map Contract

```text
Manifest obligations: 18.
Each row below is a pre-resolved slot the writer MUST fill at the artifact indicated by `artifact`, located by `location_hint`, populated using `treatment_template` as the structural blueprint.

- obligation_id: ban-1  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-2  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Наголос
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
  subtype: substance_required
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
    expected_correction_value: Чітка вимова всіх голосних: [молоко́]
    expected_error_value: Редукція ненаголошених: вимовляти «молоко» як [мeлeко́] або [мшва-лшва-ко́]
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-2  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Наголос на другому компоненті: [кіломе́тр]
    expected_error_value: Наголос на першому складі у запозиченнях: [кі́лометр]
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-3  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Перенесення наголосу: «кни́жка» — «книжки́»
    expected_error_value: Фіксування наголосу в множині: «кни́жка» — «кни́жки»
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-4  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Використовувати логічний наголос на значущому слові
    expected_error_value: Завжди наголошувати займенники в реченні
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-5  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Наголос на суфіксі: [мале́нький]
    expected_error_value: Ігнорування суфікса -еньк-: [ма́ленький]
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-6  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Чіткий наголос за правилом: [одина́дцять] (передостанній), [сімдеся́т] (останній)
    expected_error_value: Вимова числівників на -дцять і -десят із неправильним наголосом: [о́динадцять], [сі́мдесят]
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-7  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Наголос на другому складі: [була́], [були́]
    expected_error_value: Помилкове наголошення дієслів минулого часу: [бу́ла], [бу́ли]
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: step-1  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Фіксований наголос у базових словах
  treatment_template:
    required_claim: Крок 1. Фіксований наголос у базових словах Почніть із найпростіших та найуживаніших двоскладових і трискладових слів, де наголос не змінюється. Покажіть учням контраст між наголошеним і ненаголошеним складом. Використовуйте знайомі власні назви (Київ, Львів) та базову лексику . Наголошений склад має промовлятися трохи довше, але ненаголошені голосні не редукуються (не перетворюються на шва, як в англійській), а зберігають свою якість, хоча звучать дещо слабше.
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-2  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Рухомий наголос при словозміні
  treatment_template:
    required_claim: Крок 2. Рухомий наголос при словозміні Коли вводиться категорія множини (plurality), необхідно одразу показати, що наголос може «стрибати». Підручники зазначають: іменники в множині здебільшого мають наголос на закінченні («батьки́», «огірки́») . Це також стосується слів із суфіксом -к-, де наголос у множині часто переходить на закінчення: «ка́зка» — «казки́», «кни́жка» — «книжки́» . Автор модуля має спеціально підбирати такі пари для аудіовправ, щоб учні звикали до рухливості українського наголосу.
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-3  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Наголос у системі дієслів
  treatment_template:
    required_claim: Крок 3. Наголос у системі дієслів Під час знайомства з дієсловами теперішнього й минулого часу слід акцентувати увагу на стабільних патернах. Наприклад, дієслово «бути» у майбутньому часі має наголошений перший склад («бу́деш», «бу́демо»), тоді як у минулому часі жіночого і середнього роду та множини він падає на другий склад («була́», «було́», «були́») . Окрему увагу слід приділити дієсловам з наголосом на останньому складі, таким як «нести́» (несла́), «везти́» (везла́), або закінченням «-емо», «-имо» («ідемо́», «мовчимо́») .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-4  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Смислорозрізнювальний наголос (омографи)
  treatment_template:
    required_claim: Крок 4. Смислорозрізнювальний наголос (омографи) Ближче до кінця рівня А1 варто ввести концепцію слів, які пишуться однаково, але звучать по-різному. За допомогою наголосу розрізняються слова (наприклад, «доро́га» як шлях і «дорога́» як прикметник) або форми слів , . Це викликає інтерес у дорослих учнів і формує усвідомлення ваги орфоепічної норми.
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-5  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Варіантне наголошування
  treatment_template:
    required_claim: Крок 5. Варіантне наголошування Як феномен, українська мова має слова з подвійним (варіантним) наголосом. Студентам А1 треба пояснити, що обидва варіанти є правильними, щоб зняти зайвий стрес. До таких слів належать: «за́вжди́», «ма́бу́ть», «по́ми́лка», «алфа́ві́т», «про́сти́й», «та́ко́ж» , , . Вводьте їх як цікаву особливість, але в словнику подавайте той варіант, який найчастіше чути в сучасній літературній мові.
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-6  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Логічний наголос та фразова інтонація
  treatment_template:
    required_claim: Крок 6. Логічний наголос та фразова інтонація Останнім етапом на базовому рівні є робота з інтонацією цілого речення. Навчіть учня зміщувати смисловий акцент (логічний наголос) у реченні за допомогою сили голосу або зміни тону . Поясніть, що в питальних реченнях без питального слова підвищення тону відбувається саме на слові, яке несе логічний наголос.
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
   `engagement`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the residual-judgment rubric for
   `engagement`** (see scope section above; deterministic checks already ran).
   Is this quote evidence FOR the dimension being satisfied, or evidence
   AGAINST? A quote that just confirms a deterministic-gate criterion is
   not residual evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `engagement` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.

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
that touches dimension `engagement`. The audit feeds the evidence list above:
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
- Module: 4
- Slug: stress-and-melody
- Word target: 1200

## Module Size Policy — dossier/evidence-led advisory context (#4801)

- Basis: core_evidence_packet
- Density band: core_pedagogy_standard
- Plan floor words: 1200
- Recommended range: 3500-5000
- Advisory ceiling words: 5000
- Expansion permission: source_backed_only
- Status: over_advisory_ceiling
- Rule: satisfy objectives and evidence coverage, not a token target; the reviewed plan floor still binds.
- Rule: expand only when added material is source-backed and pedagogically necessary.
- Rule: if grounded material runs out before the floor, emit `<!-- SIZE_POLICY_MISMATCH: plan floor exceeds sourced evidence -->` instead of inventing depth.
- Rule: do not repeat framing, conclusions, transitions, definitions, generic exposition, or uncited interpretation to reach the floor.
Notes:
- Core A1-C2 uses a pedagogy/evidence-packet basis; do not apply seminar dossier ceilings mechanically.
- Built module exceeds the advisory ceiling; expansion should be justified by sourced pedagogy.
- Reviewer rule: do not fail or pass a module on word count alone; deterministic gates handled the floor.
- Reviewer rule: inspect deterministic repetition evidence and marginal pedagogical value throughout the full size band, not only above the advisory ceiling.
- Reviewer rule: if the module is over the advisory ceiling, decide whether the extra length is source-backed density, necessary pedagogy, or filler/padding; length alone is not a failure.
- Reviewer rule: source-backed density is acceptable evidence; repeated framing, generic exposition, uncited interpretation, and inflated transitions are padding evidence.
Padding diagnostic:
- Status: over_advisory_ceiling
- Over advisory ceiling words: 2988
- Repetition status: clear
- Repetition matches: 0
- Review action: advisory_review_only; distinguish source-backed density from filler/padding

Use this as review context, not as a mechanical word-count gate. Inspect the
deterministic paragraph matches and marginal pedagogical value throughout the
full size band, not only above the advisory ceiling. Source-backed density and
necessary pedagogy remain acceptable even when long. Repeated framing,
conclusions, transitions, definitions, generic exposition, or uncited
interpretation are filler/padding defects when they affect `engagement`.

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

## ULP Presentation Pattern — letter_module:true full contract
For `letter_module: true` A1/A2 plans, follow all seven Anna Ohoiko practices:
1. EM-DASH GLOSS: UK terms precede EN glosses (`привіт — hello`); never gloss-first.
2. SIDE-BY-SIDE BILINGUAL: narratives of 3+ sentences use UK-left / EN-right aligned rendering.
3. STRESS MARKS: keep plain Ukrainian ready for deterministic stress marking; do not transliterate.
4. DIALOGUE UK-ONLY: Tab 1 dialogues are pure Ukrainian; support follows in `en` props or a table/paragraph.
5. UK-ONLY Q&A: comprehension stems and content options stay Ukrainian; English only in UI affordances.
6. TRANSLATE TO WORKBOOK: EN→UK translation drills belong in workbook practice, never Tab 1 prose.
7. NAMED PERSONA: use a named Ukrainian teacher/persona or characters with real Ukrainian anchors.
Reject transliteration tables, `X sounds like Y in English`, EN-first dialogue glossing, vocab dumps, and abstract `the student must learn` framing.

## Contract YAML

```yaml
sections:
- title: Наголос
  word_budget:
    target: 350
    min: 315
    max: 385
- title: Інтонація
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Читаємо вголос
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Підсумок
  word_budget:
    target: 250
    min: 225
    max: 275
vocabulary_required:
- наголос (stress/accent)
- замок (castle — stress on first syllable)
- замок (lock — stress on last syllable)
- кава (coffee)
- вода (water)
- столиця (capital)
vocabulary_optional: []
source_note: Full plan below is authoritative for points, activity hints, vocabulary,
  and references.
```

## Plan

```yaml
activity_hints:
- focus: Де наголос? Виберіть правильний склад.
  items: 8
  type: quiz
- focus: 'З''єднайте пари слів за наголосом: замок ↔ замок'
  items: 4
  type: match-up
- focus: Твердження, питання чи оклик? Виберіть на основі пунктуації.
  items: 6
  type: quiz
- focus: 'Поставте правильний розділовий знак: Це кава_ Де метро_ Як гарно_'
  items: 6
  type: fill-in
- focus: 'Типові L2-помилки наголосу — оберіть нормативну форму (див. wiki "Типові
    помилки L2 (наголос)"). Формат: `слово {нормативний_наголос|помилковий_наголос}`.'
  items:
  - Це моя {новий|новий} комп''ютер. (adjective ending-stress, R-L1 transfer)
  - Мій дідусь {старий|старий}. (adjective ending-stress, R-L1 transfer)
  - У мене в руці {одинадцять|одиннадцять} гривень. (numeral — stress on `-на-`)
  - Я вивчив {чотирнадцять|чотирнадцять} нових слів. (numeral — stress on `-на-`)
  - У мене болять {гóлови|голови}. (plural — mobile stress, plural is stem-stressed)
  - Мене звати {Марія|Марія}. (feminine -ія name — stress on `-і-`)
  type: fill-in
changelog:
- changes:
  - Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md. Added
    lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes) per the
    convention.
  - 'Fixed internal contradiction in grammar[]: tightened "Три інтонаційні моделі:
    розповідна ↘, питальна ↗, оклична ↘↘" → "…питання без питального слова (так/ні)
    ↗…" (matches the WH-question falling-intonation rule stated elsewhere in the plan
    and in the locked wiki).'
  - 'Fixed intonation inconsistency in Читаємо вголос: `Як справи? ↗` → `Як справи?
    ↘` (applies the plan''s own WH-question rule). Added author-note explaining the
    conversational-register exception so the writer does not silently invert back
    to the "natural" rising contour.'
  - 'Fixed typo: "з модуля модуль №1" → "з модуля №1".'
  - Added stress-transfer-error fill-in activity (6 items) mirroring the new wiki
    "Типові помилки L2 (наголос)" table — covers numerals, adjective ending-stress,
    mobile plural, homograph pairs.
  - Annotated meaning-distinguishing stress pairs directly in vocabulary_hints (замок
    / замок, атлас / атлас, орган / орган — all with stress marks and English glosses).
    Dropped the disputed `мука / мука` flour/torment pair from vocabulary_hints; a
    note in content_outline[0].points[1] flags that the modern standard term for flour
    is `борошно` so the writer does not silently teach a dialectal form.
  - Added одинадцять / чотирнадцять to recommended vocabulary as canonical L2 stress-transfer
    targets.
  - 'Added wiki back-reference to references: (LOCKED 2026-04-23).'
  date: '2026-04-23'
  version: 1.2.0
connects_to:
- a1-005 (Хто я?)
content_outline:
- points:
  - 'Заболотний, 5 клас, с. 73: Українська мова має 38 звуків, і наголос визначає,
    який склад вимовляється голосніше та довше. Наголос є ВІЛЬНИМ — він може падати
    на будь-який склад і РУХОМИМ — може переміщуватися між формами одного слова. Це
    відрізняє його від французької (завжди на останньому) чи чеської (завжди на першому).'
  - 'Наголос змінює значення — реальні пари слів, які зустрінуться учням: замок (castle)
    / замок (lock), атлас (atlas) / атлас (satin), орган (organ of the body) / орган
    (musical instrument), сім''я (family) / сім''я (seed). Неправильний наголос =
    неправильне слово. Ось чому позначки наголосу є важливими. (Примітка до автора:
    пара `мука / мука` — не подавати як "torment/flour"; модерна словникова норма
    для "flour" — `борошно`.)'
  - На письмі позначки наголосу (') ставляться в підручниках і словниках, але НЕ у
    звичайних українських текстах. Учням завжди слід перевіряти наголос на goroh.pp.ua,
    якщо є сумніви.
  - 'Поширені моделі для початківців: Перший склад: мама, тато, ранок, кава, книга.
    Останній склад: вода, зима, рука, метро, кафе. Короткого шляху немає — потрібно
    вивчати наголос для кожного слова окремо.'
  section: Наголос
  words: 350
- points:
  - 'Українська мова використовує інтонацію (мелодику) для розрізнення типів речень.
    Ті самі слова, різна мелодика, різне значення. Твердження: Це кава. ↘ Питання:
    Це кава? ↗ Оклик: Як гарно! ↘↘'
  - 'Питальні слова (хто, що, де, коли) утворюють питання БЕЗ висхідної інтонації:
    Що це? ↘ Де метро? ↘ Але загальні питання (так/ні) завжди мають висхідну інтонацію:
    Це метро? ↗'
  - 'В українській мові речення класифікують за метою висловлювання: розповідні, питальні,
    спонукальні. Будь-яке з них може бути також окличним — це окремий вимір. Для A1
    зосередимося на трьох моделях пунктуації: . для тверджень, ? для питань, ! для
    окликів або наказів.'
  section: Інтонація
  words: 300
- points:
  - 'Читання багатоскладових слів із правильним наголосом: у-кра-їн-ська, фо-то-гра-фі-я,
    ві-дпо-чи-нок. Метод: розділити на склади → знайти наголошений склад → прочитати
    у природному темпі.'
  - 'Практика читання наголошених слів — читати вголос із правильним наголосом: Ки-їв,
    мо-ло-ко, ран-ок, ка-ва, во-да, зи-ма, у-кра-їн-ська. Знайдіть наголошений склад,
    а потім прочитайте все слово в природному темпі.'
  - 'Практика діалогів з використанням вітань з модуля №1: — Привіт! ↘ — Привіт! Як
    справи? ↘ — Добре! А у тебе? ↗ — Добре! ↘ Застосовуйте інтонаційні моделі до вже
    вивчених привітань. УВАГА до автора: `Як справи?` містить питальне слово `як`,
    тому за правилом має спадну інтонацію. У живому розмовному мовленні ця фраза часто
    звучить з висхідною (фатична функція), але для A1 подаємо нормативний спадний
    контур, щоб учень закріпив правило WH-питань.'
  section: Читаємо вголос
  words: 300
- points:
  - 'Самоперевірка: Що таке наголос? Чи може він змінювати значення слова? Наведіть
    приклад. Яку інтонацію ви використовуєте для загальних питань (так/ні)? Для тверджень?
    Прочитайте це вголос: Це аптека? Так, це аптека. Як гарно!'
  section: Підсумок
  words: 250
focus: phonetics
grammar:
- Вільний наголос
- Пари слів, значення яких залежить від наголосу
- 'Три інтонаційні моделі: розповідна ↘, питання без питального слова (так/ні) ↗,
  оклична ↘↘'
- Питальні речення з питальним словом (хто/що/де/коли/як) мають спадну інтонацію,
  як і розповідні
letter_module: true
level: A1
lifecycle: locked
module: a1-004
objectives:
- Розуміти, що український наголос є вільним і може змінювати значення слова
- Правильно ставити наголос у поширених словах рівня A1
- Використовувати висхідну інтонацію для загальних питань (так/ні) і низхідну для
  тверджень
- Читати вголос із природним українським ритмом
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
plan_fixes:
- changes:
  - strip U+0301 from all string values (43 removals)
  date: '2026-04-24'
  trigger: Plan check rejected U+0301 combining acute stress marks in 43 place(s).
    Pipeline adds stress marks deterministically AFTER review; plans must be stress-free.
  version: 1.2.1
prerequisites:
- a1-003 (Спеціальні знаки)
references:
- notes: 38 звуків, наголос. Наголос як вільний і рухомий.
  title: Заболотний Grade 5, p.73
- notes: Інтонація речень — розповідні, питальні, окличні.
  title: Авраменко Grade 5, p.19
- notes: Практика наголосу з числівниками.
  title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
- notes: Authoritative pedagogical brief — see Крок 5 (чотири базові інтонаційні контури
    з прикладовими реченнями) and "Типові помилки L2 (наголос)" (R-L1 + англ. stress-transfer
    drill).
  title: 'Wiki: pedagogy/a1/stress-and-melody (LOCKED 2026-04-23)'
register: розмовний
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md.
  Wiki locked to 9/10 on all 5 dimensions (wiki/.reviews/pedagogy/a1/stress-and-melody-review-LOCKED.md).
  Plan findings: (1) internal contradiction between grammar item 3 "питальна ↗" and
  grammar item 4 "питальні слова не потребують висхідної інтонації" — tightened item
  3 to "питання без питального слова (так/ні) ↗"; (2) Читаємо вголос dialogue marked
  `Як справи? ↗` which contradicts the plan''s own WH-question rule — normalised to
  `↘` with an author-note about the conversational-register exception; (3) typo `з
  модуля модуль №1` → `з модуля №1`; (4) added stress-transfer-error fill-in activity
  mirroring the new wiki "Типові помилки L2 (наголос)" table; (5) added `мука / борошно`
  writer-note to disambiguate the homograph pair''s pedagogical role vs. the modern
  standard term for "flour"; (6) wiki back-reference added to references. See PR body
  for full findings + fixes.'
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-stress-and-melody
sequence: 4
slug: stress-and-melody
subtitle: Наголос змінює значення, інтонація змінює намір
targets:
  new_grammar: []
  new_vocabulary:
  - наголос
  - замок
  - кава
  - вода
  - столиця
  - атлас
  - орган
  - ранок
  - метро
  - фотографія
  - одинадцять
  - чотирнадцять
  recycle_vocabulary: []
title: Наголос і мелодика
version: 1.2.3
vocabulary_hints:
  recommended:
  - атлас (atlas — stress on first syllable; pairs with атлас for meaning-distinguishing
    drill)
  - атлас (satin — stress on last syllable; pairs with атлас)
  - орган (organ of the body — stress on first syllable; pairs with орган)
  - орган (musical instrument — stress on last syllable; pairs with орган)
  - ранок (morning)
  - метро (metro)
  - фотографія (photograph)
  - одинадцять (eleven — stress on `-на-`; classic L2 stress-transfer target)
  - чотирнадцять (fourteen — stress on `-на-`; classic L2 stress-transfer target)
  required:
  - наголос (stress/accent)
  - замок (castle — stress on first syllable)
  - замок (lock — stress on last syllable)
  - кава (coffee)
  - вода (water)
  - столиця (capital)
word_target: 1200

```

## Generated Content

## lesson-1
## module.md

# Наголос і мелодика

**ка́ва. вода́. Це ка́ва? Де метро́?** — stress and sentence melody.

Teacher Oksana starts with a tiny routine: listen, mark, repeat. If you have a
teacher or tutor, let them read one word first. If you are working alone, read
the stress mark first and then say the word slowly.

Today you are not memorizing every stress pattern in Ukrainian. You are
learning why stress matters, how to read words with stress marks, and how to
use three beginner sentence melodies.

By the end, you can:

- explain **на́голос** — word stress;
- read **ка́ва**, **вода́**, **ра́нок**, and **метро́** with the marked syllable
  stronger and a little longer;
- keep Ukrainian vowels clear outside stress;
- recognize pairs where stress changes meaning, such as **за́мок** and
  **замо́к**;
- use falling melody for statements, rising melody for yes/no questions, and
  falling melody for questions with **хто**, **що**, **де**, **коли**, or
  **як**;
- read a short greeting dialogue with Ukrainian rhythm.

:::tip
If you want extra listening support, open [ULP Season 1, Episode 5 —
Pronunciation Trainer](https://www.ukrainianlessons.com/episode5/) from the
Resources tab and copy only short model words.
:::

## Наголос

**ка́ва. вода́. молоко́.** Listen first, then read the marks.

**На́голос** is the syllable you say with more force and a little more length.
In learning materials, this course marks it with an accent: **ка́ва**,
**вода́**, **молоко́**. In ordinary Ukrainian texts, the mark is usually
absent, so you learn stress as part of each new word.

Use this quick pass before the table:

1. Point to the stress mark.
2. Say only the stronger syllable.
3. Say the whole word once.

Ukrainian stress is free. It can fall near the beginning, middle, or end of a
word.

| Model | Read it slowly |
| --- | --- |
| first syllable | **ма́ма**, **та́то**, **ра́нок**, **ка́ва**, **кни́га** |
| final syllable | **вода́**, **зима́**, **рука́**, **метро́**, **кафе́** |
| middle syllable | **столи́ця**, **люди́на**, **одина́дцять** |

There is no useful shortcut for A1 learners. That is normal. Treat stress as
part of the word, just like spelling. When you add a word to your notebook,
add its stress too: **ка́ва**, not just кава.

A second habit matters just as much: do not blur unstressed vowels. In
**молоко́**, the first two **о** sounds stay **о**. They are lighter than the
stressed final **о**, but they stay clear. Read slowly first:
**мо-ло-ко**. Keep every vowel clear, then speed up.

Some Ukrainian words move stress when the form changes. For now, only notice
the idea. **голова́** can become **го́лови** in plural. That is a future
grammar habit, but you can already hear that Ukrainian stress can move.

Stress can also change meaning:

| Pair | English support |
| --- | --- |
| **за́мок** | castle |
| **замо́к** | lock |
| **а́тлас** | atlas |
| **атла́с** | satin |
| **о́рган** | body organ |
| **орга́н** | musical instrument |
| **сі́м'я** | seed |
| **сім'я́** | family |

Do not guess these from spelling alone. Use the stress mark when it is given,
and check a dictionary such as goroh.pp.ua when you are unsure.

:::tip
You already saw **за́мок** and **замо́к**, and you already know **сім'я́**
from Module 3. Here they are reminders, not a new memory load: the mark is
small, but it can carry meaning.
:::

<!-- INJECT_ACTIVITY: act-1 -->

<!-- INJECT_ACTIVITY: act-3 -->

## Мелодика

**Це ка́ва. Це ка́ва? Як га́рно!** — same words can carry different melody.

**Мелодика** is the movement of the voice across a whole sentence. For A1, use
three safe models:

| Sentence type | Model | Voice |
| --- | --- | --- |
| statement | **Це ка́ва.** | falling **↘** |
| yes/no question | **Це ка́ва?** | rising **↗** |
| exclamation | **Як га́рно!** | stronger falling **↘↘** |

The punctuation helps you choose the melody, but your voice must still do the
work.

Now add the most important beginner exception. A question with a question word
usually falls, not rises:

| Question word | Example | Melody |
| --- | --- | --- |
| **що** | **Що це?** | falling **↘** |
| **де** | **Де метро́?** | falling **↘** |
| **як** | **Як спра́ви?** | falling **↘** |
| **хто** | **Хто це?** | falling **↘** |

But a yes/no question rises:

| Yes/no question | Melody |
| --- | --- |
| **Це метро́?** | rising **↗** |
| **Це вода́?** | rising **↗** |
| **А у тебе́?** | rising **↗** |

<!-- INJECT_ACTIVITY: act-4 -->

Logical stress means the important word inside the sentence. Keep this simple
today. In **Це ка́ва?**, the important word is **ка́ва** because you are
checking the object. In **А у тебе́?**, the important part is **тебе́** because
you are turning the question back to the other person.

Keep the explanation Ukrainian-centered. Listen to the Ukrainian words, notice
the stress, and copy the contour.

:::tip
Do not worry if your melody feels slow at first. Slow and clear is the right
A1 target.
:::

Read this short beginner dialogue aloud, listening to the contour of each line:

> Наза́р: Це ка́ва? ↗
> Окса́на: Ні, це вода́. ↘
> Наза́р: А де ка́ва? ↘
> Окса́на: Ось ка́ва. ↘
> Наза́р: Як га́рно! ↘↘

Support after the Ukrainian dialogue:

| Українська | English support | Intonation pattern |
| --- | --- | --- |
| **Це ка́ва?** | Is this coffee? | rising **↗** (yes/no question) |
| **Ні, це вода́.** | No, this is water. | falling **↘** (statement) |
| **А де ка́ва?** | And where is the coffee? | falling **↘** (wh-question with **де**) |
| **Ось ка́ва.** | Here is coffee. | falling **↘** (statement) |
| **Як га́рно!** | How lovely! | stronger falling **↘↘** (exclamation) |

When you practice these lines, pay attention to how punctuation guides your pitch. A question mark with **Це ка́ва?** prompts your voice to go up at the end, while **А де ка́ва?** starts with a question word and drops downward. Statements like **Ось ка́ва.** settle gently downward, and exclamations like **Як га́рно!** finish with an energetic downward plunge.

<!-- INJECT_ACTIVITY: act-2 -->

In the next lesson, we take these two essential skills — placing the stress correctly on every word and choosing the right sentence melody — into longer words and practical reading aloud.


## activities.yaml

inline:
- id: act-1
  type: quiz
  title: Де на́голос
  instruction: Обери склад із позначеним на́голосом.
  items:
  - prompt: 'Читай: ка́ва. Де на́голос?'
    options:
    - text: перший склад
      correct: true
    - text: останній склад
      correct: false
    - text: немає наголосу
      correct: false
    explanation: У слові ка́ва на́голос на ка́.
  - prompt: 'Читай: вода́. Де на́голос?'
    options:
    - text: останній склад
      correct: true
    - text: перший склад
      correct: false
    - text: усі склади однакові
      correct: false
    explanation: У слові вода́ на́голос на да́.
  - prompt: 'Читай: столи́ця. Де на́голос?'
    options:
    - text: середній склад
      correct: true
    - text: перший склад
      correct: false
    - text: останній склад
      correct: false
    explanation: У слові столи́ця на́голос на ли́.
  - prompt: 'Молоко́: що робимо з ненаголошеними голосними?'
    options:
    - text: тримаємо кожен голосни́й чистим
      correct: true
    - text: пропускаємо перший голосни́й
      correct: false
    - text: читаємо кожне о як а
      correct: false
    explanation: Українські ненаголошені голосні залишаються чистими.
- id: act-2
  type: quiz
  title: Вибір мелодики
  instruction: Обери першу модель мелодики речення.
  items:
  - prompt: Це ка́ва.
    options:
    - text: спадна ↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Твердження має спадну мелодику.
  - prompt: Це ка́ва?
    options:
    - text: висхідна ↗
      correct: true
    - text: спадна ↘
      correct: false
    explanation: Так/ні питання має висхідну мелодику.
  - prompt: Де метро́?
    options:
    - text: спадна ↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Питання з де на A1 має спадну мелодику.
  - prompt: Як га́рно!
    options:
    - text: сильніша спадна ↘↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Оклик має сильнішу спадну мелодику.
- id: act-3
  type: quiz
  title: Швидкий контраст
  instruction: Обери коротку англійську підказку.
  items:
  - prompt: за́мок
    options:
    - text: castle
      correct: true
    - text: lock
      correct: false
    explanation: За́мок із наголосом на першому складі — castle.
  - prompt: замо́к
    options:
    - text: lock
      correct: true
    - text: castle
      correct: false
    explanation: Замо́к із наголосом на останньому складі — lock.
  - prompt: сім'я́
    options:
    - text: family
      correct: true
    - text: seed
      correct: false
    explanation: Сім'я́ з фінальним наголосом — family.
- id: act-4
  type: fill-in
  title: Пунктуація і мелодика
  instruction: Обери розділовий знак, який відповідає реченню.
  items:
  - sentence: Це ка́ва_
    answer: .
    options:
    - .
    - '?'
    - '!'
    explanation: Твердження має крапку й спадну мелодику.
  - sentence: Це метро́_
    answer: '?'
    options:
    - '?'
    - .
    - '!'
    explanation: Так/ні питання має знак питання й висхідну мелодику.
  - sentence: Де апте́ка_
    answer: '?'
    options:
    - '?'
    - .
    - '!'
    explanation: Де робить це питанням, але мелодика спадна.
  - sentence: Як га́рно_
    answer: '!'
    options:
    - '!'
    - '?'
    - .
    explanation: Це оклик.
  - sentence: Так, це вода́_
    answer: .
    options:
    - .
    - '?'
    - '!'
    explanation: Це твердження.
workbook:
- id: act-w1
  type: fill-in
  title: Типові помилки наголосу
  instruction: Обери нормативну форму з позначеним наголосом.
  items:
  - sentence: 'новий: ___'
    answer: нови́й
    options:
    - нови́й
    - но́вий
    explanation: У слові нови́й наголос на останній частині.
  - sentence: 'старий: ___'
    answer: стари́й
    options:
    - стари́й
    - ста́рий
    explanation: У слові стари́й наголос на останній частині.
  - sentence: 'одинадцять: ___'
    answer: одина́дцять
    options:
    - одина́дцять
    - о́динадцять
    explanation: Одина́дцять має наголос на -на́-.
  - sentence: 'чотирнадцять: ___'
    answer: чотирна́дцять
    options:
    - чотирна́дцять
    - чоти́рнадцять
    explanation: Чотирна́дцять теж має наголос на -на́-.
  - sentence: 'множина слова голова́: ___'
    answer: го́лови
    options:
    - го́лови
    - голови́
    explanation: 'У цій парі наголос рухається: голова́, але го́лови.'
  - sentence: 'ім''я: ___'
    answer: Марі́я
    options:
    - Марі́я
    - Ма́рія
    explanation: У цьому імені наголос на рі́.
- id: act-w2
  type: match-up
  title: На́голос змінює значення
  instruction: З'єднай наголошене слово з короткою англійською підказкою.
  pairs:
  - left: за́мок
    right: castle
  - left: замо́к
    right: lock
  - left: а́тлас
    right: atlas
  - left: атла́с
    right: satin
  - left: о́рган
    right: body organ
  - left: орга́н
    right: musical instrument
  - left: сі́м'я
    right: seed
  - left: сім'я́
    right: family
- id: act-w101
  type: match-up
  title: Питальні та ключові слова
  instruction: З'єднай українське слово з відповідним значенням.
  pairs:
  - left: хто
    right: who
  - left: що
    right: what
  - left: де
    right: where
  - left: як
    right: how
  - left: коли́
    right: when
  - left: на́голос
    right: word stress
  - left: мело́дика
    right: sentence melody
  - left: склад
    right: syllable
- id: act-w102
  type: quiz
  title: 'Мелодика: спадна чи висхідна?'
  instruction: Визнач правильну інтонаційну модель для кожного речення.
  items:
  - prompt: Це вода́.
    options:
    - text: спадна́ ↘ (твердження)
      correct: true
    - text: висхідна́ ↗
      correct: false
    explanation: Твердження закінчується спадною інтонацією.
  - prompt: Це вода́?
    options:
    - text: висхідна́ ↗ (загальне питання)
      correct: true
    - text: спадна́ ↘
      correct: false
    explanation: Загальне питання (так/ні) має висхідну інтонацію.
  - prompt: Що це?
    options:
    - text: спадна́ ↘ (питальне слово «що»)
      correct: true
    - text: висхідна́ ↗
      correct: false
    explanation: Питання з питальним словом «що» має спадну інтонацію.
  - prompt: Хто це?
    options:
    - text: спадна́ ↘ (питальне слово «хто»)
      correct: true
    - text: висхідна́ ↗
      correct: false
    explanation: Питання з питальним словом «хто» має спадну інтонацію.
  - prompt: А у тебе́?
    options:
    - text: висхідна́ ↗ (зворотне питання)
      correct: true
    - text: спадна́ ↘
      correct: false
    explanation: Зворотне питання «А у тебе?» вимовляється з висхідною інтонацією.
  - prompt: Як спра́ви?
    options:
    - text: спадна́ ↘ (питальне слово «як»)
      correct: true
    - text: висхідна́ ↗
      correct: false
    explanation: Питання з питальним словом «як» за базовим правилом має спадну інтонацію.
- id: act-w103
  type: true-false
  title: Правила українського наголосу
  instruction: Визнач, чи твердження правдиве (правда), чи хибне (неправда).
  items:
  - statement: 'Украї́нський на́голос є рухо́мим і мо́же змі́нювати фо́рму слів (напри́клад:
      голова́ — го́лови).'
    correct: true
    explanation: Наголос в українській мові може переміщуватися у формах слів.
  - statement: Слова́ за́мок і замо́к означа́ють одне́ й те са́ме.
    correct: false
    explanation: 'Наголос розрізняє значення: за́мок — castle, замо́к — lock.'
  - statement: У сло́ві вода́ на́голос па́дає на пе́рший склад.
    correct: false
    explanation: У слові вода́ наголос падає на другий (останній) склад.
  - statement: Пита́ння Що це? за прави́лом ма́є спадну́ інтона́цію ↘.
    correct: true
    explanation: Питання з питальними словами мають спадний контур.
  - statement: Окличне речення Як га́рно! вимовляється зі спадною інтонацією ↘↘.
    correct: true
    explanation: Окличні речення мають виразну спадну мелодику.
  - statement: У сло́ві молоко́ ненаголо́шені зву́ки [о] перетво́рюються на [а].
    correct: false
    explanation: В українській мові ненаголошені звуки [о] вимовляються чітко.
- id: act-w104
  type: fill-in
  title: Розділові знаки та інтонація
  instruction: Доповни речення правильним розділовим знаком.
  items:
  - sentence: Ось гаря́ча ка́ва_
    answer: .
    options:
    - .
    - '?'
    - '!'
    explanation: Це розповідне речення.
  - sentence: Це твоя́ вода́_
    answer: '?'
    options:
    - '?'
    - .
    - '!'
    explanation: Це загальне питання.
  - sentence: Хто це_
    answer: '?'
    options:
    - '?'
    - .
    - '!'
    explanation: Це питання з питальним словом.
  - sentence: Що це_
    answer: '?'
    options:
    - '?'
    - .
    - '!'
    explanation: Це питання з питальним словом.
  - sentence: Як чудо́во_
    answer: '!'
    options:
    - '!'
    - '?'
    - .
    explanation: Це окличне речення.
  - sentence: Так, це метро́_
    answer: .
    options:
    - .
    - '?'
    - '!'
    explanation: Це розповідне речення-відповідь.
- id: act-w105
  type: translate
  title: Переклад термінів
  instruction: Обери правильний переклад для кожного слова.
  items:
  - source: голосни́й
    options:
    - text: vowel
      correct: true
    - text: consonant
      correct: false
    - text: word
      correct: false
    explanation: Голосни́й — vowel.
  - source: мело́дика
    options:
    - text: sentence melody / intonation
      correct: true
    - text: spelling
      correct: false
    - text: accent mark
      correct: false
    explanation: Мело́дика — sentence melody.
  - source: склад
    options:
    - text: syllable
      correct: true
    - text: letter
      correct: false
    - text: sentence
      correct: false
    explanation: Склад — syllable.
  - source: ре́чення
    options:
    - text: sentence
      correct: true
    - text: word
      correct: false
    - text: sound
      correct: false
    explanation: Ре́чення — sentence.
  - source: пита́ння
    options:
    - text: question
      correct: true
    - text: statement
      correct: false
    - text: greeting
      correct: false
    explanation: Пита́ння — question.
  - source: сло́во
    options:
    - text: word
      correct: true
    - text: syllable
      correct: false
    - text: phrase
      correct: false
    explanation: Сло́во — word.


## vocabulary.yaml

- lemma: наголос
  translation: stress / accent
  pos: noun
  usage: Наголос у слові ка́ва.
- lemma: мелодика
  translation: melody / intonation
  pos: noun
  usage: Мелодика речення.
- lemma: склад
  translation: syllable
  pos: noun
  usage: Один склад.
- lemma: наголошений
  translation: stressed
  pos: adjective
  usage: Наголошений склад.
- lemma: ненаголошений
  translation: unstressed
  pos: adjective
  usage: Ненаголошений склад.
- lemma: голосний
  translation: vowel
  pos: adjective / noun
  usage: Голосний звук.
- lemma: слово
  translation: word
  pos: noun
  usage: Слово ка́ва.
- lemma: речення
  translation: sentence
  pos: noun
  usage: Речення має мелодику.
- lemma: питання
  translation: question
  pos: noun
  usage: Це питання.
- lemma: хто
  translation: who
  pos: pronoun
  usage: Хто це?
- lemma: що
  translation: what
  pos: pronoun
  usage: Що це?
- lemma: де
  translation: where
  pos: adverb
  usage: Де метро́?
- lemma: коли
  translation: when
  pos: adverb
  usage: Коли?
- lemma: як
  translation: how
  pos: adverb
  usage: Як спра́ви?
- lemma: кава
  translation: coffee
  pos: noun
  usage: Ка́ва.
- lemma: вода
  translation: water
  pos: noun
  usage: Вода́.


## resources.yaml

- title: Заболотний Grade 5, p.73
  source: Заболотний О. В., Заболотний В. В. Українська мова. 5 клас, с. 73
  notes: 'Plan reference: 38 sounds and stress as the louder/longer syllable; stress
    is free and mobile.'
- title: Авраменко Grade 5, p.19
  source: Авраменко О. М. Українська мова. 5 клас, с. 19
  notes: 'Plan reference: sentence intonation categories and punctuation patterns.'
- title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: 'Plan reference: beginner stress practice with numerals and sentence rhythm.'


## lesson-2
## module.md

# Друк, зошит, голос

У першому уроці ви навчилися розпізнавати наголос і перші моделі мелодики: **ка́ва**, **вода́**, **Це ка́ва?**, **Де метро́?**. In Lesson 1 you learned to recognize stress and initial sentence melodies: **ка́ва** (coffee), **вода́** (water), **Це ка́ва?** (Is this coffee?), **Де метро́?** (Where is the metro?).

Тепер ми переходимо до читання багатоскладових слів, типових пасток наголосу та поєднання друку й письма в зошиті — now we turn to reading multi-syllable words, navigating stress traps, and connecting printed text with notebook writing:
- **Ділити довгі слова на склади та знаходити наголошений склад** — split longer words into syllables and identify the stressed beat (**украї́нська**, **фотогра́фія**, **відпочи́нок**, **столи́ця**);
- **Уникати типових пасток наголосу** — master stress in numerals (**одина́дцять**, **чотирна́дцять**), adjectives (**нови́й**, **стари́й**), and names (**Марі́я**);
- **З'єднувати друк, зошит і голос** — match printed words with handwritten forms in your notebook and read them aloud with natural Ukrainian rhythm.

## Читаємо вголос

**украї́нська. фотогра́фія. відпочи́нок.**

Use this three-step routine for longer words:

1. Split the word into syllables.
2. Find the stressed syllable.
3. Read the whole word in a natural tempo.

Practice:

| Whole word | Stressed part to notice |
| --- | --- |
| **украї́нська** | the **ї́н** part is strongest |
| **фотогра́фія** | the **гра́** part is strongest |
| **відпочи́нок** | the **чи́** part is strongest |
| **одина́дцять** | the **на́** part is strongest |
| **чотирна́дцять** | the **на́** part is strongest |

For the number words below, put stress on **на́**:
**одина́дцять**, **чотирна́дцять**. When you write these in your notebook,
write the full word with the stress mark, then underline only the strong part.

:::tip
For this module, a stress mark is a training wheel. It is not usually printed
in ordinary Ukrainian texts, but it helps your eyes remember the sound until
the word becomes familiar.
:::

Розбиваючи довгі слова на склади, пам'ятайте просту підказку: кожен голосний звук утворює окремий склад. Ukrainian phonetic theory describes this clearly: «Склад — це частина слова, яку вимовляють одним поштовхом видихуваного повітря» (quoted from: Заболотний Grade 5, p. 73). Скільки в слові голосних звуків, стільки й складів.

When reading multi-syllable Ukrainian words, keep every unstressed vowel clear and distinct:
- **у-кра-ї́н-ська** — four syllables, stress on **ї́н**;
- **фо-то-гра́-фі-я** — five syllables, stress on **гра́**;
- **від-по-чи́-нок** — four syllables, stress on **чи́**;
- **сто-ли́-ця** — three syllables, stress on **ли́**.

<!-- INJECT_ACTIVITY: act-201 -->

<!-- INJECT_ACTIVITY: act-202 -->

Read the Ukrainian dialogue first:

```text
О́ля: Приві́т! ↘
Тара́с: Приві́т! Як спра́ви? ↘
О́ля: До́бре! А у те́бе? ↗
Тара́с: До́бре! ↘
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Приві́т!** | Hi! |
| **Як спра́ви?** | How are things? |
| **До́бре!** | Good! |
| **А у те́бе?** | And you? |

Notice two details. **Як спра́ви?** has the question word **як**, so the
beginner model is falling. **А у те́бе?** is a yes/no-style return question, so
it rises.

Now read a second tiny exchange:

```text
О́ля: Це ка́ва. ↘
Тара́с: Це ка́ва? ↗
О́ля: Так, це ка́ва. ↘
Тара́с: Де вода́? ↘
О́ля: Ось вода́. ↘
Тара́с: Як га́рно! ↘↘
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це ка́ва.** | This is coffee. |
| **Це ка́ва?** | Is this coffee? |
| **Так, це ка́ва.** | Yes, this is coffee. |
| **Де вода́?** | Where is the water? |
| **Ось вода́.** | Here is water. |
| **Як га́рно!** | How nice! |

Послухайте розмову Олі та Тараса про подорож і фотографії — listen to Olya and Taras talk about travel and photographs:

> Оля: Привіт, Тарасе! (Hello, Taras!) ↘
> Тарас: Привіт, Олю! Як справи? (Hello, Olya! How are things?) ↘
> Оля: Добре, дякую. А у тебе? (Good, thank you. And you?) ↗
> Тарас: Теж добре. Що це? (Also good. What is this?) ↘
> Оля: Це нова фотографія. (This is a new photograph.) ↘
> Тарас: Це столиця, Київ? (Is this the capital, Kyiv?) ↗
> Оля: Так, це столиця. (Yes, this is the capital.) ↘
> Тарас: Як гарно! А де метро? (How nice! And where is the metro?) ↘
> Оля: Ось метро. (Here is the metro.) ↘
> Тарас: Це чудовий відпочинок! (This is a wonderful rest!) ↘↘
> Оля: Так, відпочинок чудовий! (Yes, the vacation is wonderful!) ↘

Розбір реплік діалогу — breakdown of dialogue lines:

| Українська | English support |
| --- | --- |
| **Привіт, Тарасе!** | Hello, Taras! |
| **Привіт, Олю! Як справи?** | Hello, Olya! How are things? |
| **Добре, дякую. А у тебе?** | Good, thank you. And you? |
| **Теж добре. Що це?** | Also good. What is this? |
| **Це нова фотографія.** | This is a new photograph. |
| **Це столиця, Київ?** | Is this the capital, Kyiv? |
| **Так, це столиця.** | Yes, this is the capital. |
| **Як гарно! А де метро?** | How nice! And where is the metro? |
| **Ось метро.** | Here is the metro. |
| **Це чудовий відпочинок!** | This is a wonderful rest! |
| **Так, відпочинок чудовий!** | Yes, the vacation is wonderful! |

Common traps now become workbook habits:

| Trap | Safer Ukrainian habit |
| --- | --- |
| blurring unstressed vowels in **молоко́** | keep **мо-ло-ко́** clear |
| reading **нови́й** or **стари́й** with early stress | stress the final part |
| keeping stress fixed in **голова́ / го́лови** | notice that stress can move |
| always emphasizing a pronoun | put logical stress on the meaningful word |
| reading **Марі́я** with first-syllable stress | stress the **рі́** part |
| reading **одина́дцять** or **чотирна́дцять** with early stress | stress **на́** |

You do not need to produce all of these words fluently today. You need to
recognize the safer habit and avoid building the wrong one.

<!-- INJECT_ACTIVITY: act-5 -->

## Друк, зошит, голос

**Друк:** **ка́ва**, **вода́**, **молоко́**, **метро́**.

**Зошит:** the same known words written by you, a teacher, or a tutor with the
stress mark preserved.

Recognition comes before fast writing. Match the notebook word to the printed
word, then read it aloud with the stress and melody.

| Друк | Notebook recognition prompt |
| --- | --- |
| **ка́ва** | Which notebook word has stress on the first syllable? |
| **вода́** | Which notebook word has stress on the final syllable? |
| **молоко́** | Which notebook word keeps all three **о** sounds clear? |
| **метро́** | Which notebook word ends with the stressed vowel? |

<!-- INJECT_ACTIVITY: act-203 -->

Коли ви записуєте нові слова в зошит, завжди позначайте наголос олівцем або ручкою. Writing down new vocabulary with explicit stress marks bridges eye recognition and vocal production:
- **Друк** (print) trains your eyes to recognize standard letterforms in textbooks and signs;
- **Зошит** (notebook) builds motor memory as you write out the syllables and place the accent mark;
- **Голос** (voice) activates the acoustic pattern, ensuring that unstressed vowels like [о] in **молоко́** remain unreduced and clear.

Sentence intonation in Ukrainian functions as a unified melody across the whole phrase: «Речення мають інтонаційну завершеність, яка на письмі позначається крапкою, знаком питання або знаком оклику» (quoted from: Авраменко Grade 5, p. 19). Always read whole phrases aloud rather than isolated words.

<!-- INJECT_ACTIVITY: act-204 -->

### Підсумок уроку — Lesson summary

Підіб'ємо підсумки другого уроку — let us summarize what we practiced in Lesson 2:
- **Багатоскладові слова** (multi-syllable words): ділимо слова на склади за кількістю голосних і знаходимо наголошений склад (**украї́нська**, **фотогра́фія**, **відпочи́нок**, **столи́ця**).
- **Числівники та прикметники** (numerals and adjectives): пам'ятаємо наголос на **-на́-** у числівниках (**одина́дцять**, **чотирна́дцять**) та кінцевий наголос у базових прикметниках (**нови́й**, **стари́й**).
- **Триєдність навчання** (the learning triad): поєднуємо друк (**друк**), запис у зошиті (**зошит**) та виразне читання вголос (**голос**).

У наступному уроці ми проведемо фінальну перевірку матеріалу всього модуля, перевіримо всі типи мелодики та підсумуємо результати нашого першого фонетичного курсу.


## activities.yaml

inline:
- id: act-201
  type: quiz
  title: Наголошений склад у довгих словах
  instruction: Визнач наголошений склад у поданому слові.
  items:
  - prompt: украї́нська
    options:
    - text: ї́н
      correct: true
    - text: у́к
      correct: false
    - text: ська́
      correct: false
    explanation: У слові украї́нська наголос падає на склад -ї́н-.
  - prompt: фотогра́фія
    options:
    - text: гра́
      correct: true
    - text: фо́
      correct: false
    - text: фі́
      correct: false
    explanation: У слові фотогра́фія наголошеним є третій склад -гра́-.
  - prompt: відпочи́нок
    options:
    - text: чи́
      correct: true
    - text: ві́д
      correct: false
    - text: но́к
      correct: false
    explanation: У слові відпочи́нок наголос падає на склад -чи́-.
  - prompt: одина́дцять
    options:
    - text: на́
      correct: true
    - text: о́
      correct: false
    - text: дцять
      correct: false
    explanation: У числівнику одина́дцять наголос завжди падає на склад -на́-.
  - prompt: чотирна́дцять
    options:
    - text: на́
      correct: true
    - text: чо́
      correct: false
    - text: дцять
      correct: false
    explanation: У числівнику чотирна́дцять наголос теж падає на склад -на́-.
  - prompt: столи́ця
    options:
    - text: ли́
      correct: true
    - text: сто́
      correct: false
    - text: ця́
      correct: false
    explanation: У слові столи́ця наголошеним є другий склад -ли́-.
- id: act-202
  type: match-up
  title: Поділ на склади та наголос
  instruction: З'єднай слово з його складовою будовою та позначеним наголосом.
  pairs:
  - left: украї́нська
    right: у-кра-ї́н-ська (наголос на -ї́н-)
  - left: фотогра́фія
    right: фо-то-гра́-фі-я (наголос на -гра́-)
  - left: відпочи́нок
    right: від-по-чи́-нок (наголос на -чи́-)
  - left: одина́дцять
    right: о-ди-на́-дцять (наголос на -на́-)
  - left: чотирна́дцять
    right: чо-тир-на́-дцять (наголос на -на́-)
  - left: столи́ця
    right: сто-ли́-ця (наголос на -ли́-)
- id: act-5
  type: fill-in
  title: Типові пастки наголосу
  instruction: Обери нормативну форму з позначеним наголосом.
  items:
  - sentence: Це мій ___ комп'ютер.
    answer: нови́й
    options:
    - нови́й
    - но́вий
    explanation: У слові нови́й наголос наприкінці.
  - sentence: Мій дідусь ___.
    answer: стари́й
    options:
    - стари́й
    - ста́рий
    explanation: У слові стари́й наголос наприкінці.
  - sentence: У мене ___ гривень.
    answer: одина́дцять
    options:
    - одина́дцять
    - о́динадцять
    explanation: Одина́дцять має наголос на -на́-.
  - sentence: Я знаю ___ нових слів.
    answer: чотирна́дцять
    options:
    - чотирна́дцять
    - чоти́рнадцять
    explanation: Чотирна́дцять теж має наголос на -на́-.
  - sentence: 'Множина слова голова́: ___.'
    answer: го́лови
    options:
    - го́лови
    - голови́
    explanation: У цій словниковій парі наголос рухається.
  - sentence: Мене звати ___.
    answer: Марі́я
    options:
    - Марі́я
    - Ма́рія
    explanation: У цьому імені наголос на рі́.
- id: act-203
  type: match-up
  title: Зошит і вимова
  instruction: З'єднай слово з підказкою для правильної вимови.
  pairs:
  - left: ка́ва
    right: наголос на першому складі
  - left: вода́
    right: наголос на останньому складі
  - left: молоко́
    right: три чіткі звуки [о]
  - left: метро́
    right: наголошений голосний [о] в кінці
  - left: ра́нок
    right: наголос на складі ра-
  - left: нови́й
    right: наголошений закінчення -и́й
- id: act-204
  type: quiz
  title: 'Читаємо вголос: ритм і мелодика'
  instruction: Обери правильну інтонацію та характеристику для кожного речення.
  items:
  - prompt: Приві́т! Як спра́ви? ↘
    options:
    - text: спадна інтонація (питальне слово як)
      correct: true
    - text: висхідна інтонація
      correct: false
    explanation: Речення з питальним словом «як» за правилом вимовляється зі спадною
      інтонацією.
  - prompt: До́бре! А у те́бе? ↗
    options:
    - text: висхідна інтонація (зворотне питання)
      correct: true
    - text: спадна інтонація
      correct: false
    explanation: Зворотне питання без питального слова має висхідну інтонацію.
  - prompt: Це ка́ва? ↗
    options:
    - text: висхідна інтонація (загальне питання так/ні)
      correct: true
    - text: спадна інтонація
      correct: false
    explanation: Загальне питання потребує підйому тону вгору.
  - prompt: Так, це ка́ва. ↘
    options:
    - text: спадна інтонація (розповідне твердження)
      correct: true
    - text: висхідна інтонація
      correct: false
    explanation: Розповідне твердження закінчується спадною інтонацією.
  - prompt: Де вода́? ↘
    options:
    - text: спадна інтонація (питальне слово де)
      correct: true
    - text: висхідна інтонація
      correct: false
    explanation: Питання з «де» вимовляється зі спадним рухом голосу.
  - prompt: Як га́рно! ↘↘
    options:
    - text: сильніша спадна інтонація (оклик)
      correct: true
    - text: висхідна інтонація
      correct: false
    explanation: Окличне речення має виразну спадну інтонацію.
workbook:
- id: act-w3
  type: group-sort
  title: Сортуй за наголосом
  instruction: Розподіли кожне слово за позначеним наголошеним складом.
  groups:
  - label: Перший склад
    items:
    - ма́ма
    - та́то
    - ра́нок
    - ка́ва
  - label: Середній склад
    items:
    - столи́ця
    - люди́на
    - одина́дцять
    - чотирна́дцять
  - label: Останній склад
    items:
    - вода́
    - зима́
    - рука́
    - метро́
- id: act-w4
  type: match-up
  title: Друк і зошит
  instruction: З'єднай друковане слово з підказкою в зо́шиті.
  pairs:
  - left: 'друк: ка́ва'
    right: 'зошит: на́голос на першому складі'
  - left: 'друк: вода́'
    right: 'зошит: на́голос на останньому складі'
  - left: 'друк: молоко́'
    right: 'зошит: три чисті звуки о'
  - left: 'друк: метро́'
    right: 'зошит: останній наголошений голосни́й'
- id: act-w201
  type: fill-in
  title: Наголос у числівниках та прикметниках
  instruction: Обери правильне слово з нормативним наголосом.
  items:
  - sentence: Я знаю ___ нових українських слів.
    answer: одина́дцять
    options:
    - одина́дцять
    - два́надцять
    - де́сять
    explanation: У числівнику одина́дцять наголос падає на -на́-.
  - sentence: У нашій групі навчається ___ студентів.
    answer: чотирна́дцять
    options:
    - чотирна́дцять
    - трина́дцять
    - де́сять
    explanation: У числівнику чотирна́дцять наголос падає на -на́-.
  - sentence: Це мій ___ підручник.
    answer: нови́й
    options:
    - нови́й
    - чи́стий
    - до́брий
    explanation: Прикметник нови́й має наголос на останньому складі.
  - sentence: Це наш ___ будинок.
    answer: стари́й
    options:
    - стари́й
    - молоди́й
    - гарне́нький
    explanation: Прикметник стари́й має наголос на останньому складі.
  - sentence: Сьогодні теплий і сонячний ___ .
    answer: ра́нок
    options:
    - ра́нок
    - день
    - ве́чір
    explanation: Слово ра́нок має наголос на першому складі.
  - sentence: Київ — це головна ___ України.
    answer: столи́ця
    options:
    - столи́ця
    - ву́лиця
    - краї́на
    explanation: У слові столи́ця наголошеним є середній склад -ли́-.
- id: act-w202
  type: match-up
  title: Склади та переклад слів
  instruction: З'єднай українське слово з його англійським значенням.
  pairs:
  - left: украї́нська
    right: Ukrainian
  - left: фотогра́фія
    right: photograph
  - left: відпочи́нок
    right: rest / vacation
  - left: одина́дцять
    right: eleven
  - left: чотирна́дцять
    right: fourteen
  - left: столи́ця
    right: capital
- id: act-w203
  type: group-sort
  title: Групування слів за кількістю складів
  instruction: Розподіли слова за кількістю складів.
  groups:
  - label: Два склади
    items:
    - ка́ва
    - вода́
    - ра́нок
    - зима́
  - label: Три склади
    items:
    - столи́ця
    - молоко́
    - люди́на
  - label: Чотири і більше складів
    items:
    - украї́нська
    - фотогра́фія
    - відпочи́нок
    - одина́дцять
- id: act-w204
  type: true-false
  title: Правила вимови та письма
  instruction: Визнач, чи твердження правдиве, чи хибне.
  items:
  - statement: У слові одина́дцять наголос завжди падає на склад -на́-.
    correct: true
    explanation: Усі числівники від 11 до 19 мають наголос на -на́-.
  - statement: Прикметники нови́й і стари́й мають наголос на першому складі.
    correct: false
    explanation: В українській мові прикметники нови́й і стари́й мають наголос на
      закінченні.
  - statement: В українській мові ненаголошені звуки [о] вимовляються чисто й чітко.
    correct: true
    explanation: Українські ненаголошені [о] не редукуються і не переходять в [а].
  - statement: У слові фотогра́фія наголошеним є склад -гра́-.
    correct: true
    explanation: 'Наголос у слові фотогра́фія падає на третій склад: фо-то-гра́-фі-я.'
  - statement: Слово молоко́ має наголос на першому складі.
    correct: false
    explanation: 'У слові молоко́ наголос падає на останній склад: мо-ло-ко́.'
  - statement: Наголос в українській мові може розрізняти значення слів (за́мок і
      замо́к).
    correct: true
    explanation: 'Український наголос є розрізнювальним: за́мок — castle, замо́к —
      lock.'
- id: act-w205
  type: translate
  title: Переклад вивчених слів уроку
  instruction: Обери правильний англійський переклад для кожного українського слова.
  items:
  - source: нови́й
    options:
    - text: new
      correct: true
    - text: old
      correct: false
    - text: hot
      correct: false
    explanation: Нови́й — new.
  - source: стари́й
    options:
    - text: old
      correct: true
    - text: new
      correct: false
    - text: young
      correct: false
    explanation: Стари́й — old.
  - source: відпочи́нок
    options:
    - text: rest / vacation
      correct: true
    - text: work
      correct: false
    - text: study
      correct: false
    explanation: Відпочи́нок — rest / vacation.
  - source: молоко́
    options:
    - text: milk
      correct: true
    - text: water
      correct: false
    - text: coffee
      correct: false
    explanation: Молоко́ — milk.
  - source: голова́
    options:
    - text: head
      correct: true
    - text: hand
      correct: false
    - text: face
      correct: false
    explanation: Голова́ — head.
  - source: метро́
    options:
    - text: metro
      correct: true
    - text: bus
      correct: false
    - text: train
      correct: false
    explanation: Метро́ — metro.


## vocabulary.yaml

- lemma: столиця
  translation: capital
  pos: noun
  usage: Ки́їв — це столи́ця.
- lemma: ранок
  translation: morning
  pos: noun
  usage: До́брий ра́нок!
- lemma: метро
  translation: metro
  pos: noun
  usage: Ось метро́.
- lemma: фотографія
  translation: photograph
  pos: noun
  usage: Це нова́ фотогра́фія.
- lemma: одинадцять
  translation: eleven
  pos: numeral
  usage: Одина́дцять слів.
- lemma: чотирнадцять
  translation: fourteen
  pos: numeral
  usage: Чотирна́дцять гривень.
- lemma: молоко
  translation: milk
  pos: noun
  usage: Холо́дне молоко́.
- lemma: голова
  translation: head
  pos: noun
  usage: Боли́ть голова́.
- lemma: голови
  translation: heads
  pos: noun plural
  usage: Го́лови.
- lemma: українська
  translation: Ukrainian
  pos: adjective
  usage: Украї́нська мова.
- lemma: відпочинок
  translation: rest / vacation
  pos: noun
  usage: Відпочи́нок чудо́вий.
- lemma: новий
  translation: new
  pos: adjective
  usage: Нови́й підручник.
- lemma: старий
  translation: old
  pos: adjective
  usage: Стари́й будинок.
- lemma: гарно
  translation: nicely / beautiful
  pos: adverb
  usage: Як га́рно!
- lemma: Марія
  translation: Maria
  pos: proper noun
  usage: Мене́ зва́ти Марі́я.


## resources.yaml

- title: Заболотний Grade 5, p.73
  source: Заболотний О. В., Заболотний В. В. Українська мова. 5 клас, с. 73
  notes: 'Plan reference: 38 sounds and stress as the louder/longer syllable; stress
    is free and mobile.'
- title: Авраменко Grade 5, p.19
  source: Авраменко О. М. Українська мова. 5 клас, с. 19
  notes: 'Plan reference: sentence intonation categories and punctuation patterns.'
- title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: 'Plan reference: beginner stress practice with numerals and sentence rhythm.'


## lesson-3
## module.md

# Перевірка

У перших двох уроках ви дізналися, що український наголос є вільним і може змінювати значення слова, а мелодика речення визначає його намір: **ка́ва**, **вода́**, **Це ка́ва?**, **Де метро́?**. In the first two lessons you learned that Ukrainian word stress is free and can change meaning, while sentence melody signals the speaker's intent: **ка́ва** (coffee), **вода́** (water), **Це ка́ва?** (Is this coffee?), **Де метро́?** (Where is the metro?).

Тепер ми проводимо фінальну перевірку матеріалу всього модуля — now we conduct the final review of the entire module:
- **Перевірити наголос у смислових парах** — review stress contrasts in semantic pairs (**за́мок / замо́к**, **а́тлас / атла́с**, **о́рган / орга́н**, **сі́м'я / сім'я́**);
- **Закріпити моделі мелодики речень** — consolidate the three beginner sentence melodies: statements (**↘**), yes/no questions (**↗**), and exclamations (**↘↘**);
- **Прочитати підсумковий діалог** — read the final review dialogue with natural Ukrainian rhythm.

## Перевірка

Before you leave the lesson tab, check four things aloud:

- What is **на́голос**?
- Can stress change meaning? Say **за́мок** and **замо́к**.
- Which melody do you use for **Це апте́ка?**
- Which melody do you use for **Де метро́?**

### Наголос змінює значення — Stress changes meaning

В українській мові наголос вільний і рухомий. Ukrainian phonetic theory emphasizes this rule: «Український наголос вільний, тобто він може падати на будь-який склад» (quoted from: Заболотний Grade 5, p. 73). Moving the accent to a different syllable can create a completely different word.

Review the essential meaning-distinguishing pairs from this module:

| Pair | First-syllable stress | Final-syllable stress |
| --- | --- | --- |
| **за́мок / замо́к** | **за́мок** — castle / fortress | **замо́к** — lock (device for closing) |
| **а́тлас / атла́с** | **а́тлас** — atlas (collection of maps) | **атла́с** — satin (smooth fabric) |
| **о́рган / орга́н** | **о́рган** — body organ (heart, lung) | **орга́н** — pipe organ (musical instrument) |
| **сі́м'я / сім'я́** | **сі́м'я** — seed (biological) | **сім'я́** — family |

Look at each pair carefully in context:
- **Ось стари́й за́мок.** — Here is an old castle.
- **Ось міцни́й замо́к.** — Here is a sturdy lock.
- **Це географі́чний а́тлас.** — This is a geographical atlas.
- **Це блиску́чий атла́с.** — This is shiny satin.
- **Се́рце — це важли́вий о́рган.** — The heart is an important organ.
- **У за́лі гра́є вели́кий орга́н.** — A large organ plays in the hall.
- **Мале́ сі́м'я пророста́є навесні́.** — A tiny seed sprouts in spring.
- **Моя́ сім'я́ дру́жна.** — My family is friendly.

<!-- INJECT_ACTIVITY: act-301 -->

### Моделі наголосу в словнику — Stress patterns in vocabulary

When adding new vocabulary to your notebook, group words by where the stress falls:
- **Перший склад** (first syllable): **ма́ма**, **та́то**, **кни́га**, **ка́ва**, **ра́нок**;
- **Останній склад** (final syllable): **зима́**, **рука́**, **кафе́**, **вода́**, **метро́**;
- **Середній склад** (middle syllable): **люди́на**, **столи́ця**, **апте́ка**, **відпочи́нок**.

Remember to keep every unstressed vowel clear: in **молоко́**, do not reduce [о] to [а]. In **зима́**, say the first vowel clearly as [и].

<!-- INJECT_ACTIVITY: act-302 -->

### Мелодика та пунктуація — Melody and punctuation

Sentence intonation directly communicates the speaker's intent: «За метою висловлювання речення поділяють на розповідні, питальні та спонукальні» (quoted from: Авраменко Grade 5, p. 19).

In speech, three pitch contours provide safe, natural models for beginners:

| Sentence type | Punctuation | Melodic contour | Example |
| --- | --- | --- | --- |
| statement (твердження) | period (.) | falling **↘** | **Це апте́ка. ↘** |
| yes/no question (загальне питання) | question mark (?) | rising **↗** | **Це апте́ка? ↗** |
| exclamation (оклик) | exclamation mark (!) | strong falling **↘↘** | **Як га́рно! ↘↘** |
| WH-question (питальне слово) | question mark (?) | falling **↘** | **Де апте́ка? ↘** |

Pay special attention to questions with question words (**хто**, **що**, **де**, **коли́**, **як**). Even though they end with a question mark on paper, your voice falls at the end: **Що це? ↘**, **Де метро́? ↘**, **Як спра́ви? ↘**.

<!-- INJECT_ACTIVITY: act-303 -->

<!-- INJECT_ACTIVITY: act-304 -->

### Читання та діалог — Reading and dialogue

Final reading:

```text
О́ля: Це апте́ка? ↗
Тара́с: Так, це апте́ка. ↘
О́ля: Як га́рно! ↘↘
```

English support after the Ukrainian dialogue:

| Українська | English support |
| --- | --- |
| **Це апте́ка?** | Is this a pharmacy? |
| **Так, це апте́ка.** | Yes, this is a pharmacy. |
| **Як га́рно!** | How nice! |

Ask a native Ukrainian teacher or tutor to listen to one read-aloud from this
module. The feedback target is narrow: stress, clear vowels, and the direction
of the sentence melody.

You can now read a marked Ukrainian word, keep vowels clear, and choose the
first safe melody for a statement or question. Next, Module 5 uses this sound
control when you introduce yourself.

The workbook adds extra practice with the same skills: stress sorting,
stress-transfer repair, quick facts, and word recognition.

Послухайте підсумкову розмову Олі та Тараса — listen to the comprehensive review dialogue between Olya and Taras:

> Оля: Привіт, Тарасе! (Hi, Taras!) ↘
> Тарас: Привіт, Олю! Що це в тебе? (Hi, Olya! What is that you have?) ↘
> Оля: Це нова книга і великий атлас. (This is a new book and a big atlas.) ↘
> Тарас: Це географічний атлас чи блискучий атлас? (Is this a geographic atlas or shiny satin?) ↗
> Оля: Це атлас із мапами! А де мама і тато? (This is an atlas with maps! And where are mom and dad?) ↘
> Тарас: Мама і тато пили каву в кафе. (Mom and dad were having coffee in the cafe.) ↘
> Оля: А де аптека? (And where is the pharmacy?) ↘
> Тарас: Ось аптека біля метро. А що там вдалині — це замок? (Here is the pharmacy near the metro. And what is that in the distance — is that a castle?) ↗
> Оля: Так, це старий замок! (Yes, that is an old castle!) ↘
> Тарас: Як гарно! (How nice!) ↘↘
> Оля: Дуже гарно! (Very nice!) ↘↘

Розбір підсумкового діалогу — breakdown of the final dialogue:

| Українська | English support |
| --- | --- |
| **Привіт, Тарасе!** | Hi, Taras! |
| **Привіт, Олю! Що це в тебе?** | Hi, Olya! What is that you have? |
| **Це нова книга і великий атлас.** | This is a new book and a big atlas. |
| **Це географічний атлас чи блискучий атлас?** | Is this a geographic atlas or shiny satin? |
| **Це атлас із мапами! А де мама і тато?** | This is an atlas with maps! And where are mom and dad? |
| **Мама і тато пили каву в кафе.** | Mom and dad were having coffee in the cafe. |
| **А де аптека?** | And where is the pharmacy? |
| **Ось аптека біля метро. А що там вдалині — це замок?** | Here is the pharmacy near the metro. And what is that in the distance — is that a castle? |
| **Так, це старий замок!** | Yes, that is an old castle! |
| **Як гарно!** | How nice! |
| **Дуже гарно!** | Very nice! |

<!-- INJECT_ACTIVITY: act-305 -->

### Підсумок модуля — Module summary

Підіб'ємо підсумки всього модуля — module summary:
- **Вільний і рухомий наголос**: ви знаєте, що в українській мові наголос може падати на будь-який склад і рухатися у формах слів (**голова́ — го́лови**). Free and mobile stress: you know that Ukrainian stress can fall on any syllable and shift across word forms (**голова́** — **го́лови**).
- **Розрізнення значення за наголосом**: ви розрізняєте смислові пари слів за наголосом (**за́мок — замо́к**, **а́тлас — атла́с**, **о́рган — орга́н**, **сі́м'я — сім'я́**). Distinguishing meaning by stress: you distinguish semantic word pairs by stress (**за́мок** / **замо́к**, **а́тлас** / **атла́с**, **о́рган** / **орга́н**, **сі́м'я** / **сім'я́**).
- **Три інтонаційні моделі**: ви впевнено вживаєте спадну мелодику для тверджень (**Це ка́ва. ↘**), висхідну для загальних питань (**Це ка́ва? ↗**) та сильну спадну для окликів (**Як га́рно! ↘↘**). Three sentence melodies: you confidently use falling melody for statements, rising for yes/no questions, and strong falling for exclamations.
- **Спадний контур питань із питальними словами**: ви пам'ятаєте, що питання зі словами **хто**, **що**, **де**, **коли́**, **як** мають спадну інтонацію (**Де метро́? ↘**, **Що це? ↘**). Falling contour for WH-questions: you remember that questions starting with question words have a falling intonation.
- **Чистота ненаголошених голосних**: ви вимовляєте ненаголошені звуки [о] та [е] чітко, без редукції (**молоко́**, **відпочи́нок**). Clear unstressed vowels: you pronounce unstressed vowels clearly without blurring.
- **Природний ритм читання**: ви вмієте ділити довгі слова на склади та читати короткі діалоги вголос із природним українським ритмом. Natural reading rhythm: you can split long words into syllables and read short dialogues aloud with natural Ukrainian rhythm.


## activities.yaml

inline:
- id: act-301
  type: match-up
  title: Па́ри слів із рі́зним на́голосом
  instruction: З'єднай словосполучення з відповідним значенням.
  pairs:
  - left: стари́й за́мок
    right: old castle (fortress)
  - left: дверни́й замо́к
    right: door lock (device for closing)
  - left: географі́чний а́тлас
    right: geographical atlas (collection of maps)
  - left: блиску́чий атла́с
    right: shiny satin (smooth fabric)
  - left: важли́вий о́рган
    right: vital body organ (heart, lung)
  - left: музи́чний орга́н
    right: musical pipe organ
  - left: мале́ сі́м'я
    right: tiny plant seed
  - left: весе́ла сім'я́
    right: happy family
- id: act-302
  type: quiz
  title: Де на́голос у сло́ві
  instruction: Визнач, на який склад падає наголос.
  items:
  - prompt: ма́ма
    options:
    - text: перший склад
      correct: true
    - text: останній склад
      correct: false
    explanation: У слові ма́ма наголос падає на перший склад.
  - prompt: зима́
    options:
    - text: останній склад
      correct: true
    - text: перший склад
      correct: false
    explanation: У слові зима́ наголос падає на останній склад.
  - prompt: люди́на
    options:
    - text: середній склад
      correct: true
    - text: перший склад
      correct: false
    - text: останній склад
      correct: false
    explanation: У слові люди́на наголос падає на середній склад.
  - prompt: кни́га
    options:
    - text: перший склад
      correct: true
    - text: останній склад
      correct: false
    explanation: У слові кни́га наголос падає на перший склад.
  - prompt: рука́
    options:
    - text: останній склад
      correct: true
    - text: перший склад
      correct: false
    explanation: У слові рука́ наголос падає на останній склад.
  - prompt: апте́ка
    options:
    - text: середній склад
      correct: true
    - text: перший склад
      correct: false
    - text: останній склад
      correct: false
    explanation: У слові апте́ка наголос падає на середній склад.
- id: act-303
  type: quiz
  title: Розділові знаки та інтонація
  instruction: Обери правильний розділовий знак за змістом і мелодикою речення.
  items:
  - prompt: Це апте́ка_
    options:
    - text: '? (знак питання)'
      correct: true
    - text: . (крапка)
      correct: false
    - text: '! (знак оклику)'
      correct: false
    explanation: Загальне так/ні питання потребує знака питання та висхідної інтонації.
  - prompt: Так, це апте́ка_
    options:
    - text: . (крапка)
      correct: true
    - text: '? (знак питання)'
      correct: false
    - text: '! (знак оклику)'
      correct: false
    explanation: Твердження закінчується крапкою та має спадну інтонацію.
  - prompt: Як га́рно_
    options:
    - text: '! (знак оклику)'
      correct: true
    - text: . (крапка)
      correct: false
    - text: '? (знак питання)'
      correct: false
    explanation: Окличне речення закінчується знаком оклику.
  - prompt: Де метро́_
    options:
    - text: '? (знак питання)'
      correct: true
    - text: . (крапка)
      correct: false
    - text: '! (знак оклику)'
      correct: false
    explanation: Питання з де має знак питання, але спадну інтонацію.
  - prompt: Ось стари́й за́мок_
    options:
    - text: . (крапка)
      correct: true
    - text: '? (знак питання)'
      correct: false
    - text: '! (знак оклику)'
      correct: false
    explanation: Розповідне речення закінчується крапкою.
  - prompt: Це ка́ва_ (питання)
    options:
    - text: '? (знак питання)'
      correct: true
    - text: . (крапка)
      correct: false
    - text: '! (знак оклику)'
      correct: false
    explanation: Питальне речення закінчується знаком питання.
- id: act-304
  type: quiz
  title: Інтонаційний контур речення
  instruction: Обери напрямок мелодики для кожного типу речення.
  items:
  - prompt: Це за́мок?
    options:
    - text: висхідна ↗
      correct: true
    - text: спадна ↘
      correct: false
    explanation: Загальне так/ні питання вимовляється з висхідною інтонацією ↗.
  - prompt: Це за́мок.
    options:
    - text: спадна ↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Твердження вимовляється зі спадною інтонацією ↘.
  - prompt: Де апте́ка?
    options:
    - text: спадна ↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Питання з де має спадну інтонацію ↘.
  - prompt: Як га́рно!
    options:
    - text: сильніша спадна ↘↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Окличне речення має сильну спадну мелодику ↘↘.
  - prompt: Що це?
    options:
    - text: спадна ↘
      correct: true
    - text: висхідна ↗
      correct: false
    explanation: Питання зі словом що має спадну інтонацію ↘.
  - prompt: А у тебе́?
    options:
    - text: висхідна ↗
      correct: true
    - text: спадна ↘
      correct: false
    explanation: Зворотне питання має висхідну інтонацію ↗.
- id: act-305
  type: odd-one-out
  title: Зайве слово за наголосом
  instruction: Знайди слово, у якому наголос падає на інший склад.
  items:
  - options:
    - text: ма́ма
      correct: false
    - text: та́то
      correct: false
    - text: кни́га
      correct: false
    - text: зима́
      correct: true
    explanation: У слові зима́ наголос на останньому складі, а в інших — на першому.
  - options:
    - text: вода́
      correct: false
    - text: рука́
      correct: false
    - text: кафе́
      correct: false
    - text: ра́нок
      correct: true
    explanation: У слові ра́нок наголос на першому складі, а в інших — на останньому.
  - options:
    - text: люди́на
      correct: false
    - text: столи́ця
      correct: false
    - text: апте́ка
      correct: false
    - text: ка́ва
      correct: true
    explanation: У слові ка́ва наголос на першому складі, а в інших — на середньому.
  - options:
    - text: за́мок
      correct: false
    - text: ка́ва
      correct: false
    - text: та́то
      correct: false
    - text: метро́
      correct: true
    explanation: У слові метро́ наголос на останньому складі, а в інших — на першому.
  - options:
    - text: молоко́
      correct: false
    - text: зима́
      correct: false
    - text: рука́
      correct: false
    - text: ма́ма
      correct: true
    explanation: У слові ма́ма наголос на першому складі, а в інших — на останньому.
  - options:
    - text: столи́ця
      correct: false
    - text: люди́на
      correct: false
    - text: апте́ка
      correct: false
    - text: вода́
      correct: true
    explanation: У слові вода́ наголос на останньому складі, а в інших — на середньому.
workbook:
- id: act-w5
  type: true-false
  title: Факти про наголос і мелодику
  instruction: Обери правда чи неправда.
  items:
  - statement: Український на́голос може бути на різних складах.
    correct: true
    explanation: На́голос вільний, тому вчи його разом із кожним словом.
  - statement: Звичайні українські тексти завжди мають позначки наголосу.
    correct: false
    explanation: Позначки наголосу є в навчальних матеріалах і словниках, а не в більшості
      звичайних текстів.
  - statement: Так/ні питання Це вода́? має висхідну мелодику на A1.
    correct: true
    explanation: Так/ні питання має висхідну мелодику.
  - statement: Питання з де завжди потребує висхідної мелодики на A1.
    correct: false
    explanation: Питання з питальним словом як де має спадну мелодику.
- id: act-w6
  type: translate
  title: Слова з наголосом
  instruction: Спочатку прочитай українське слово, потім обери англійську підказку.
  items:
  - source: на́голос
    options:
    - text: stress / accent
      correct: true
    - text: lock
      correct: false
    - text: water
      correct: false
    explanation: На́голос — stress / accent.
  - source: ка́ва
    options:
    - text: coffee
      correct: true
    - text: capital
      correct: false
    - text: morning
      correct: false
    explanation: Ка́ва — coffee.
  - source: вода́
    options:
    - text: water
      correct: true
    - text: photograph
      correct: false
    - text: atlas
      correct: false
    explanation: Вода́ — water.
  - source: столи́ця
    options:
    - text: capital
      correct: true
    - text: metro
      correct: false
    - text: family
      correct: false
    explanation: Столи́ця — capital.
- id: act-w301
  type: fill-in
  title: Встав правильне слово
  instruction: Обери слово, яке підходить за змістом речення.
  items:
  - sentence: Де моя́ ___?
    answer: кни́га
    options:
    - кни́га
    - рука́
    - ка́ва
    explanation: У цьому реченні за змістом підходить слово кни́га.
  - sentence: На дворі́ холодна ___ .
    answer: зима́
    options:
    - зима́
    - ка́ва
    - вода́
    explanation: У реченні про холодну пору року вживаємо слово зима́.
  - sentence: У мене́ болить лі́ва ___ .
    answer: рука́
    options:
    - рука́
    - голова́
    - вода́
    explanation: Слово рука́ позначає частину тіла.
  - sentence: Ми йдемо́ пи́ти ка́ву в ___ .
    answer: кафе́
    options:
    - кафе́
    - метро́
    - апте́ка
    explanation: Каву п'ють у кафе́.
  - sentence: Кожна ___ має пра́во на пова́гу.
    answer: люди́на
    options:
    - люди́на
    - столи́ця
    - кни́га
    explanation: Слово люди́на називає особу.
  - sentence: Тут працю́є нова́ ___ .
    answer: апте́ка
    options:
    - апте́ка
    - столи́ця
    - ка́ва
    explanation: Ліки купують в апте́ці.
- id: act-w302
  type: match-up
  title: Словникові відповідності
  instruction: З'єднай українське слово з англійським перекладом.
  pairs:
  - left: ма́ма
    right: mother
  - left: та́то
    right: father
  - left: кни́га
    right: book
  - left: зима́
    right: winter
  - left: рука́
    right: hand / arm
  - left: апте́ка
    right: pharmacy
- id: act-w303
  type: group-sort
  title: Розподіл слів за наголосом
  instruction: Розподіли слова за наголошеним складом.
  groups:
  - label: Перший склад
    items:
    - ма́ма
    - та́то
    - кни́га
    - ка́ва
    - ра́нок
  - label: Середній склад
    items:
    - люди́на
    - столи́ця
    - апте́ка
    - одина́дцять
  - label: Останній склад
    items:
    - зима́
    - рука́
    - кафе́
    - вода́
    - метро́
- id: act-w304
  type: error-correction
  title: Виправ помилки в інтонації
  instruction: Знайди та виправ неправильну інтонаційну позначку.
  items:
  - sentence: Це апте́ка ↘
    error: ↘
    answer: ↗
    options:
    - ↗
    - ↘
    - ↘↘
    explanation: Загальне питання (так/ні) має висхідну інтонацію ↗.
  - sentence: Де метро́ ↗
    error: ↗
    answer: ↘
    options:
    - ↘
    - ↗
    - ↘↘
    explanation: Питання зі словом де має спадну інтонацію ↘.
  - sentence: Як га́рно ↗
    error: ↗
    answer: ↘↘
    options:
    - ↘↘
    - ↗
    - ↘
    explanation: Окличне речення має сильну спадну інтонацію ↘↘.
  - sentence: Це ка́ва ↗
    error: ↗
    answer: ↘
    options:
    - ↘
    - ↗
    - ↘↘
    explanation: Твердження має спадну інтонацію ↘.
  - sentence: Що це ↗
    error: ↗
    answer: ↘
    options:
    - ↘
    - ↗
    - ↘↘
    explanation: Питання зі словом що має спадну інтонацію ↘.
  - sentence: А у тебе́ ↘
    error: ↘
    answer: ↗
    options:
    - ↗
    - ↘
    - ↘↘
    explanation: Зворотне так/ні питання має висхідну інтонацію ↗.
- id: act-w305
  type: unjumble
  title: Порядок слів у реченнях
  instruction: Розстав слова у правильному порядку, щоб утворити речення.
  items:
  - words:
    - Це
    - апте́ка?
    - ↗
    sentence: Це апте́ка? ↗
    explanation: Це апте́ка? ↗
  - words:
    - Так,
    - це
    - апте́ка.
    - ↘
    sentence: Так, це апте́ка. ↘
    explanation: Так, це апте́ка. ↘
  - words:
    - Як
    - га́рно!
    - ↘↘
    sentence: Як га́рно! ↘↘
    explanation: Як га́рно! ↘↘
  - words:
    - Де
    - метро́?
    - ↘
    sentence: Де метро́? ↘
    explanation: Де метро́? ↘
  - words:
    - Ось
    - нова́
    - кни́га.
    - ↘
    sentence: Ось нова́ кни́га. ↘
    explanation: Ось нова́ кни́га. ↘
  - words:
    - Це
    - стари́й
    - за́мок.
    - ↘
    sentence: Це стари́й за́мок. ↘
    explanation: Це стари́й за́мок. ↘


## vocabulary.yaml

- lemma: замок
  translation: castle / lock
  pos: noun
  usage: За́мок і замо́к.
- lemma: атлас
  translation: atlas / satin
  pos: noun
  usage: А́тлас і атла́с.
- lemma: орган
  translation: organ
  pos: noun
  usage: О́рган і орга́н.
- lemma: сім'я
  translation: seed / family by stress
  pos: noun
  usage: Сі́м'я і сім'я́.
- lemma: мама
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: тато
  translation: father
  pos: noun
  usage: Та́то.
- lemma: книга
  translation: book
  pos: noun
  usage: Кни́га.
- lemma: зима
  translation: winter
  pos: noun
  usage: Зима́.
- lemma: рука
  translation: hand / arm
  pos: noun
  usage: Рука́.
- lemma: кафе
  translation: cafe
  pos: noun
  usage: Кафе́.
- lemma: людина
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: аптека
  translation: pharmacy
  pos: noun
  usage: Апте́ка.


## resources.yaml

- title: Заболотний Grade 5, p.73
  source: Заболотний О. В., Заболотний В. В. Українська мова. 5 клас, с. 73
  notes: 'Plan reference: 38 sounds and stress as the louder/longer syllable; stress
    is free and mobile.'
- title: Авраменко Grade 5, p.19
  source: Авраменко О. М. Українська мова. 5 клас, с. 19
  notes: 'Plan reference: sentence intonation categories and punctuation patterns.'
- title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: 'Plan reference: beginner stress practice with numerals and sentence rhythm.'


## Task

Review the assigned dimension `engagement` and return the required JSON object now.
No preamble, no markdown, no questions.
