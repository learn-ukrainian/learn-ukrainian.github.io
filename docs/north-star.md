# North Star — Curriculum Reboot (#1577 Phase 0 draft)

> **Status:** DRAFT v3 — signed off by Codex + Gemini in `architecture`
> channel thread `6de2be4789394536abdb6356cd5bb006` (round 2, both
> `[AGREE]`). Open questions §OPEN QUESTIONS resolved per panel
> consensus and folded into policy. Ready for Phase 3 prompt-template
> injection.
>
> v3 corrects v2 on the immersion model: there is **no B1 entry sub-band**.
> The transition out of English finishes inside A2; B1 onwards is 100 %
> Ukrainian. The only sanctioned English at B1+ is the **Словник (vocab
> tab) translation column** — used for L1 anchoring of new lemmas and
> idiom/expression explanation. `scripts/config.py` IMMERSION_POLICIES
> still encodes the old "rescue English" model at B1; that file is stale
> and gets corrected in Phase 2 config audit. The docs are the source of
> truth; config follows.
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
   target. Immersion ramps from 5–25 % Ukrainian (A1 m01–03) up to
   65–90 % Ukrainian (A2 final ramp, `a2-m51-70`). The end of A2 is
   structurally where the learner finishes the transition out of
   English; A2's final band absorbed the work that used to live in a
   "B1 entry" sub-band.

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

**Immersion is band-strict and tab-aware.** A1+A2 immersion follows
the per-band ramps in `scripts/config.py` IMMERSION_POLICIES.
**B1 onwards is uniformly 100 % Ukrainian** in every tab except
Tab 2 (Словник), where English translations and idiom/expression
explanations are sanctioned as the only L1 scaffolding. Writer hits
the band; reviewer scores against the band; nobody freelances. The
A2→B1 boundary is the single biggest discontinuity in the whole
curriculum.

> **Known pipeline drift to clean up in Phase 2:** `scripts/config.py`
> still defines a `b1-m01-05` sub-band at 75–100 % Ukrainian and a
> `b1-core` band at 85–100 % with a "rescue English" allowance. This
> doc supersedes both. The Phase 2 config audit deletes the
> `b1-m01-05` band entirely, collapses `b1-core` to 100 %, and
> rewrites the rule string to match the B2+ language ("Full Ukrainian
> immersion. No English in module body. Tab 2 (Словник) keeps L1
> translations and idiom explanations as the only English."). Any
> pipeline code that branches on `b1-m01-05` as a key gets removed.

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
5. **Immersion band respected.** A1+A2 modules respect the per-band
   ramp in IMMERSION_POLICIES. **B1 and every higher level are 100 %
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

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` (lesson contract P1).
2. File the Phase 2 `scripts/config.py` IMMERSION_POLICIES B1
   cleanup issue per P7.
3. Wire `{NORTH_STAR}` and `{LESSON_CONTRACT}` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.
