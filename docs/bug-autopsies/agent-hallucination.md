# Agent Hallucination Autopsies

Reproducible cases where an agent fabricated a verbatim citation,
attributed a claim to a non-existent source, or invented a
linguistic/historical "fact" that contradicts the project's
authoritative corpus. Distinct from `code-review` reviewer hallucinations
(those live in `docs/playbooks/anti-hallucination-review-protocol.md`)
— this file is for content-side / citation-side fabrications that
threaten curriculum quality.

## Why this file exists

LLMs hallucinate citations stably. When a model has a strong prior
that "Author X likely commented on Topic Y," it can produce a fake
verbatim quote attributing the prior to Author X — repeatedly, with
the same fake quote, hours apart. These are not noise; they are
reproducible failure modes that need explicit knowledge-base entries
so future agents (and future sessions) can recognize them.

Each entry below documents:

1. **The fabrication** — what was claimed
2. **The verification** — proof it's false (MCP tool output, primary
   source check)
3. **The thread(s)** where it occurred
4. **The mitigation** — what stopped it from shipping, what should
   stop it next time

---

## Gemini × Антоненко-Давидович × «собака feminine = Russianism»

**Date discovered:** 2026-05-05

**The fabrication.** Gemini, in `ab discuss` deliberation rounds on
the gender of the noun «собака», cited Антоненко-Давидович «Як ми
говоримо» as flagging feminine adjectival agreement on «собака» as a
Russianism. The fabricated direct Ukrainian quote:

> "В українській мові іменник собака — чоловічого роду... Треба
> казати: великий собака, кудлатий собака, злий собака."

**Reproduced twice in one day,** with the **same fake quote**, in two
separate deliberation threads (`482884ca054e` morning, `7c6e401053bb`
afternoon). This is a stable hallucination, not a one-off slip.

**Verification (MCP tools).**

- `mcp__sources__search_style_guide("собака")` → `No results in
  Антоненко-Давидович for: "собака"`. There is no entry on this
  lemma in the indexed Antonenko-Davydovych corpus (279 of ~600+
  entries indexed; #1663 tracks completion, but Claude's independent
  read of additional АД indices also confirmed absence).

- The actual Ukrainian lexicographic position is the **opposite** of
  what Gemini fabricated:
  - **VESUM** (`mcp__sources__verify_lemma собака`) returns 22
    forms, with both `noun:anim:m` and `noun:anim:f` paradigms
    codified in parallel.
  - **СУМ-11** lemma header: `СОБА́КА, и, ч. і рідше ж.` — explicitly
    "masculine, and less commonly, feminine."
  - **СУМ-11's own example sentences** include feminine agreement
    attributed to canonical authors: «Велика, чорна, кудлата собака
    кинулась на його з-під загороди» (Панас Мирний, 1949). Mirny is
    19th-century literary Ukrainian canon, not dialect or Russified
    speech.

- **Орфографічний словник** lists собака as `іменник чоловічого
  або жіночого роду`.

- **Грінченко 1907–09** (`Словник української мови Грінченка`)
  lists `собака — м. и ж.` (masculine and feminine). This is the
  load-bearing piece of evidence: Грінченко was published in the
  Russian Empire as an explicit documentation of pre-Soviet,
  native, indigenous Ukrainian — deliberately anti-Russification
  by design. He already codifies both genders **decades before
  any Soviet Russification effort**. Therefore feminine собака
  cannot be a Russification; it predates the colonial language
  policies that would later shape Russian's lexicographic norms.
  This single attestation falsifies the "feminine = Russianism"
  theory completely.

- **Six dictionaries on slovnyk.me corroborate:** Орфографічний
  («чоловічого або жіночого роду»), Орфоепічний («ч. і рідко
  ж.»), Великий тлумачний словник («ч. і рідше ж.»), СУМ-11
  («ч. і рідше ж.»), Грінченко («м. и ж.»), and the jargon
  dictionary («(-и) ж.», feminine in narrow jargon usage). The
  Український-English dictionary glosses the English: *"dog;
  hound; bloodhound, sleuth-hound; cur, mongrel"*.

- **The grammatical category is `двородовий іменник`**
  (dual-gender noun) — the property is `двородовість`, used by
  Вихованець & Городенська (*Теоретична морфологія української
  мови*, 2004). Distinct from `спільний рід` (common gender),
  which is reserved for nouns like *сирота*, *нероба* where
  gender tracks biological sex of the referent. Собака is the
  cleaner `двородовість` case — both genders are lexically
  available regardless of the referent's biological sex.

So the academic Ukrainian lexicographic norm is "masculine primary,
feminine attested and codified, both standard." Gemini's claim that
АД flags feminine agreement as a Russianism is **the opposite** of
the truth.

**Why it's reproducible.** Hypothesis: the Russian cognate «собака»
is feminine; many Ukrainian style guides (correctly) flag various
gender-copy Russianisms (степ/степь, біль/боль, Сибір/Сибирь). Gemini's
training-data prior conflates "Ukrainian gender ≠ Russian gender → AD
will have flagged it" into "AD flags feminine собака," and confidently
generates a fake direct quote consistent with that prior. The base
rate of this hallucination class is high enough that the same fake
quote was produced by Gemini twice in one day.

**Threads.**

- `482884ca054e` (2026-05-05 morning, 3-agent first-take). All three
  signed `[AGREE]` in round 1, deliberation protocol short-circuited
  at round 1 (parallel fan-out — agents had not seen each other's
  replies yet, but `[AGREE]` was treated as cross-agent assent). The
  hallucinated citation went unchallenged in the transcript.

- `7c6e401053bb` (2026-05-05 afternoon, same 3-agent question, after
  round-1-no-short-circuit fix `872d8376b0`). Round 1: same
  hallucination from Gemini. Round 2: Claude and Codex both
  independently named the fabrication, cited MCP verification + the
  codebase comment from `872d8376b0`, refused to `[AGREE]` until the
  retraction was on record. Gemini conceded explicitly: *"Codex is
  correct. I hallucinated the reference to Антоненко-Давидович in my
  round 1 reply... My initial position was a hallucinated rule that
  contradicted actual dictionary evidence."*

**What stopped it from shipping.**

1. **Round-1 short-circuit fix** (`872d8376b0`) — without this, the
   morning thread would have committed `[AGREE]` consensus and the
   fabrication would have entered the channel record as
   "three-agent-consensus-validated."
2. **Cross-agent verification** — Codex and Claude both independently
   ran MCP queries and read the project codebase; their convergent
   counter-evidence forced Gemini's concession.
3. **Refusal to `[AGREE]` after concession** — Claude and Codex held
   `[DISAGREE]` in round 2 specifically to keep the fabrication
   visible in the transcript rather than letting a polite `[AGREE]`
   paper over the lesson. This is correct behavior.

**What should stop it next time.**

- **Citation-provenance check before commit** (issue #1683): bridge
  detects verbatim citations in agent replies, runs them against the
  corresponding MCP tool, blocks or annotates if the quote is not in
  the source corpus. The empirical case for this is now strong.
- **Pre-pinned known-fabrications list** in the linguistic channel
  context, so any future agent (Claude / Gemini / Codex / a new
  agent we add) sees this entry on every post and won't re-cite the
  fake quote even from training-data prior.
- **Curriculum-side rule**: feminine собака is **NOT** a Russianism.
  Add to the reviewer's "false-positive Russianism list" so adversarial
  reviewers don't flag canonical Ukrainian prose as Russified.

**Pedagogically correct treatment of собака gender (for the eventual
B1 grammar module on `двородовість`):**

- Masculine is the unmarked default. Teach `мій собака`, `великий
  собака`, `цей вірний собака` at A1–A2.
- Feminine agreement is lexicographically admitted and attested in
  literary Ukrainian (СУМ-11 «ч. і рідше ж.», Мирний 1949). Mention
  at B2+ as a stylistic register variant.
- For natural-sex specificity, use distinct lexemes: `пес` (m) /
  `сука` (f) / `цуценя` (n, dim.) — not gender-switching of «собака».
- Do NOT teach "feminine because -а ending." The first-declension
  hard-group paradigm (Микола, староста, собака) is morphologically
  uniform; agreement gender is a separate axis.
