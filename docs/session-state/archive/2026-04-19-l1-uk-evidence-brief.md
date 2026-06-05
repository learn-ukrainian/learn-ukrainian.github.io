# L1-UK Pivot — Evidence Brief for Re-Discussion

**Purpose**: the 2026-04-19 tri-agent discussion reached the wrong conclusion because Codex and Gemini both mis-read what the current wiki compile layer actually produces. This brief exists to make the evidence unmisreadable for the next round.

**Date**: 2026-04-19 evening (written after dispatching #1338, before re-opening the L1-UK discussion)

**Supersedes the tri-agent consensus at** `orchestration/discussions/2026-04-19-l1-uk-wiki-pivot.md` **on the specific claim** "the wiki compile layer already emits Ukrainian articles, not English briefs."

## 1. The claim under dispute

Discussion consensus (Codex lead, Gemini [AGREE]):

> **"The wiki compile layer already emits Ukrainian articles, not English briefs."**

Implication the discussion drew: therefore, "build canonical wiki in Ukrainian" is not a pivot, it's already the status quo. The real variable is the writer-layer prompt framing.

**This is false for A1 pedagogy wiki.** It is also false for the other three active compile prompts on inspection, though the failure mode differs by track.

## 2. Evidence — direct file excerpts

### 2.1 The output file Codex and Gemini claimed was Ukrainian

`wiki/pedagogy/a1/sounds-letters-and-hello.md`, lines 10–16 (section headings bilingual, body prose in English):

```markdown
## Методичний підхід (Methodological Approach)

The foundational approach for teaching Ukrainian sounds to beginners,
as derived from Grade 1-2 textbooks, is "звук перед буквою" (sound
before letter). The learner must first learn to hear, identify, and
produce the core sounds of Ukrainian before associating them with
written symbols [S17, S31]. This method builds a strong phonetic base
and minimizes negative transfer from the learner's native language.
```

Further down, the error table (lines 57–64) — left column (the "wrong" pronunciation) is English, middle column (the correction) mixes Ukrainian letters with IPA-ish phonetic brackets, right column (the explanation) is English:

```
| ❌ Помилково                                      | ✅ Правильно   | Чому                                  |
| Pronouncing и like English "i" in bit or "ee"...  | [и] - a retracted, unrounded... | English lacks this specific vowel... |
| Devoicing final consonants, e.g., saying зуб ...  | зуб is [зуб]                    | In English, word-final voiced ...     |
| Pronouncing г as a hard [g] (like in "go").       | [г] is a voiced glottal...      | The English [g] sound is represented...|
```

The decolonization section (lines 66–77) — heading is Ukrainian-parenthesized, body prose is entirely English:

```markdown
## Деколонізаційні застереження (Decolonization Notes)

**This is a mandatory section.** The teaching of Ukrainian, especially at
the phonetic level, must be actively decolonized from Russian influence,
which has historically sought to erase Ukrainian's distinctiveness.

1.  **Build from a Ukrainian Base, Not Russian Comparisons:** Under no
    circumstances should Ukrainian phonetics be taught "through" Russian...
```

### 2.2 The compile prompt that produced it

`scripts/wiki/prompts/compile_pedagogy_brief.md`:

- Line 3: `You are compiling a **pedagogical brief**... for the content writer (a separate AI) when building A1 modules for **English-speaking teens and adults** learning Ukrainian from zero.`
- Line 37: `WHAT mistakes English-speaking learners make (and how to prevent them)`
- Line 103: `**English-speaker focused.** Frame advice through what an English speaker expects vs what Ukrainian actually does`
- Line 110: `English phonetic approximations ("И sounds like the i in bit") → ✅ Ukrainian phonetic description with audio guidance` — explicitly framed as guidance *to an English reader* about what *not* to do
- No instruction anywhere in this prompt requires the body prose to be Ukrainian

### 2.3 Why the misread happened

The page has four Ukrainian-heavy surface features that, at a glance, look like Ukrainian-language output:

1. Bilingual section headings (`## Методичний підхід (Methodological Approach)`)
2. Inline Ukrainian example words and phrases (`мама`, `тато`, `Привіт!`)
3. IPA-style phonetic notation bracketed in Cyrillic (`[ў]`, `[шч]`, `[йі]`)
4. Ukrainian metalanguage sprinkled into English sentences (`звук перед буквою`, `голосні`, `приголосні`, `милозвучність`)

If you don't read the paragraph-level prose, you see a Ukrainian-looking page. The paragraph-level prose is English. **This is the misread.**

The compile-prompt text `compile_article.md:45`, `compile_grammar_brief.md:41`, `compile_academic.md:79` that Codex cited as "requires Ukrainian output today" — those lines ask for Ukrainian *citations* / *terminology* / *examples*, not Ukrainian explanatory prose. The body medium is English. The Ukrainian content is lexical surface, not narrative substance.

## 3. What the wiki actually is today

**Medium**: English explanatory prose aimed at an L1-English pedagogy reader (the A1/A2 writer persona).

**Ukrainian content**: lexical surface — section titles, quoted examples, named concepts, error-pair targets, IPA-ish brackets.

**Decolonization framing**: explicit in the prompt, meta-level — the text explains *to an English reader* how to avoid Russian-through-English teaching. The decolonization section is itself in English.

**Retrieval output**: textbook chunks with bilingual source labels, surfaced in English-language citation syntax (`[S17, S31]`).

**Consumer**: the v6 writer (`scripts/build/phases/v6-write.md`) reads this brief as English guidance, cross-references it against plans, generates the final module MDX in mixed Ukrainian-in-Ukrainian + English-scaffolding per the level contract in `scripts/config.py:215, 231, 311, 391`.

## 4. What the pivot would actually change

The real pivot question is whether the wiki's explanatory prose should be **Ukrainian** (monolingual, for a Ukrainian-pedagogy reader or native-teacher reader), while keeping decolonization and citation rigor intact.

That is a substantial change, not a prompt-framing tweak. It touches:

| Layer | Today (English-scaffolded Ukrainian-about-Ukrainian) | After pivot (Ukrainian-only) |
|---|---|---|
| Compile prompts (4 files) | "English-speaker focused" framing | Ukrainian-native-teacher framing, Ukrainian output requirement, Ukrainian decolonization register |
| Error tables | Left column: English wrong-form-in-English | Left column: Ukrainian description of the L1-interference error |
| Decolonization sections | English prose arguing against Russian-through-English | Ukrainian prose in native decolonization register (Антоненко-Давидович style) |
| Writer layer | Consumes English brief, produces mixed output per A1/A2 English-scaffolding contract | Consumes Ukrainian brief — at risk of over-shifting into pure Ukrainian A1 output (violating `scripts/config.py:215`-style contracts) unless the writer prompt is hardened against that leak |
| Review layer | 4-dim wiki review (English-scaffolded reviewer) | 4-dim wiki review rebuilt against Ukrainian-prose rubric |
| Retrieval | Unchanged (sources are textbook-native, already Ukrainian) | Unchanged |
| #1338 pipeline | Unchanged | Unchanged |

**The retrieval pipeline (#1338 T1-T2, #1341 T3-T4) is orthogonal to this pivot.** That's the one correct framing from the original discussion — ship #1338 regardless of how the pivot resolves.

**Everything above `search_sources` and below the module MDX is coupled to the pivot.**

## 5. The writer-layer risk Codex flagged — it's real, and it's the main failure mode

The writer-layer concern from the discussion:

> A1/A2 writer could "over-shift into Ukrainian technical prose" when primed with Ukrainian briefs, violating the English-scaffolding contracts in `scripts/config.py:215, 231, 311, 391`.

This is the actual thing the A/B test must surface. If the writer reads a fully Ukrainian brief and produces an A1 module whose metalanguage (grammatical terms, task instructions, section headings) stays in English per the A1 contract — pivot is viable. If the writer leaks Ukrainian metalanguage into A1 task instructions because the brief primed it, the brief has broken the writer's L2-appropriate scaffolding.

A naive writer prompt re-read against a Ukrainian brief will leak. Hardening the writer prompt is the actual engineering cost of the pivot, and it will need its own adversarial audit before any A/B results are trustworthy.

## 6. Experiment design for the next discussion

Two clean arms, one variable under test:

| Arm | Wiki brief language | Writer prompt | Level |
|---|---|---|---|
| **Control (A)** | Current English-scaffolded brief (`wiki/pedagogy/a1/sounds-letters-and-hello.md` as-is, validated) | Current `v6-write.md` unchanged | A1/M01 |
| **Treatment (B)** | Ukrainian-only rebuild of the same brief, same retrieval output, same decolonization requirements | Current `v6-write.md` unchanged | A1/M01 |

Then a third arm only if (B) materially differs from (A):

| Arm | Wiki brief language | Writer prompt | Level |
|---|---|---|---|
| **Treatment + hardened writer (C)** | Ukrainian-only rebuild | `v6-write.md` with explicit "metalanguage stays English for A1/A2" guard | A1/M01 |

Measurement:
- **Module quality**: 9-dim content reviewer (the real production reviewer, not the 4-dim wiki reviewer — measurement gap from the prior discussion resolved in favor of the downstream reviewer, because what we care about is module quality, not brief aesthetics)
- **Metalanguage leak**: mechanical check — count Ukrainian-only metalanguage tokens in A1 module task instructions (target: zero for A1)
- **Immersion calculator**: run `calculate_immersion()` — A1 target stays 30–50% per the A1 contract

Blinded review required (reviewer doesn't know which arm). Identical retrieval required. Two-batch confirmation rule: if (B) or (C) wins once, run again on a different module; only commit architecture if both runs agree.

## 7. What to NOT do in the next discussion

- Don't re-litigate whether the current wiki is Ukrainian. **It isn't.** Section 2 closes this.
- Don't create `l1-uk/` as a new publish root. If the immersion track ever ships, its home is `l2-uk-direct` — separate project.
- Don't couple the A/B to any routing, publishing, or landing-page changes. Writer-layer only.
- Don't reuse the 4-dim wiki reviewer as the measurement instrument. The downstream 9-dim module reviewer is the correct scoreboard.
- Don't ask Gemini or Codex "is the wiki Ukrainian today?" The answer is in Section 2. Give them this brief; don't ask them to re-derive it.

## 8. Open decisions for the human

Three calls I need from the user before dispatching the A/B:

1. **Is the pivot worth the engineering cost?** ~4 compile prompts + decolonization register rewrite + writer-prompt hardening + 4-dim review rubric rebuild. If the answer is "not yet, finish #1338 → #1340 → #1344 first," then this brief parks until those ship.
2. **Canary module**: A1/M01 per Section 6, or a different one? M01 is maximally concrete (sounds/letters) and has the one existing wiki article, which makes the control arm free — no rebuild required.
3. **Reviewer**: 9-dim downstream reviewer OK, or prefer a new purpose-built immersion reviewer?

No menu — I'll default to pivot-after-#1338, A1/M01 canary, 9-dim downstream reviewer unless the user overrides any of the three.

## 9. Bridge bug noted during the prior discussion

Claude's responses in the tri-agent thread failed because `ab discuss` passes pinned context as CLI flags, which Claude CLI rejects. Gemini + Codex work fine because their adapters tolerate long context via stdin. This is why the prior discussion ended with "Gemini [AGREE] + Codex [AGREE] + Claude silent" — not because Claude agreed. File as a separate issue if not already tracked.
