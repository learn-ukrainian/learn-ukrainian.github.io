# Wiki: Academic Brief Compilation (C1–C2)

You are compiling an **academic brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building advanced modules for learners at near-native proficiency.

**Historical context:** The previous version of this prompt produced articles that scored 5–6/10 in adversarial review. The root cause was that it **passively endorsed Russian-influenced "scientific-style" patterns** (passive `було + доконане дієслово`, excessive nominalization, calques like `являти собою`, `в якості`, `відноситися до`) as if they were authentic Ukrainian scholarly register. They are not. The rules below exist to prevent that class of failure.

## Your Task

Compile an academic brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks, scholarly works, and linguistic resources. Source format:

```
### Source N: {work/author/grade metadata}
Chunk ID: `{chunk_id}`

{text}
```

**Every claim in your article MUST cite a specific source** using short inline citations like `[S1]`, `[S2]`. The sibling `{slug}.sources.yaml` file will map those ids back to the exact chunk ids for review.

If no source supports a claim, mark it `<!-- VERIFY -->`. Do NOT invent support.

{sources}

### Source quality weighting — read before you write

Not all sources are equal. When endorsing a linguistic claim as "standard academic Ukrainian," weigh your sources:

| Source type | Reliability for written academic register |
|---|---|
| Textbook chunks (Заболотний, Авраменко, Вашуленко, Карман, Літвінова, Глазова, etc.) | **Primary** — use freely |
| МійКлас, school curriculum resources | **Primary** — use freely |
| Антоненко-Давидович "Як ми говоримо" | **Authoritative** for calque/Russianism calls — overrides textbook when they conflict |
| Правопис 2019 | **Authoritative** for orthography and morphology |
| Wikipedia (Ukrainian or English) chunks (`ext-wikipedia-*`) | **Background context only** — do not cite as authority for register |
| YouTube transcripts (`ext-*_youtube-*`) | **SPOKEN language** — often contains speech errors, fillers, ungrammatical pivots. NEVER cite as an example of standard WRITTEN academic style. |
| Blog posts (`ext-*_blogs-*`, `ext-realna_istoria-*`) | **Contemporary usage** — cite for attested usage, but not as normative |

If your ONLY support for a claim is a Wikipedia or YouTube chunk, mark the claim `<!-- VERIFY -->`.

## What an Academic Brief IS

A reference guide for the writer covering:
- Academic Ukrainian conventions for this topic — with SPECIFIC examples from textbook sources
- Stylistic nuances and register requirements — demonstrated through contrasting pairs
- Advanced grammar, syntax, or vocabulary systems — with complete paradigm tables
- How this topic is taught at Ukrainian university level (as reported in sources)
- Scholarly debates — presented with attribution, not collapsed to one position

## What an Academic Brief Is NOT

- NOT a dense theoretical essay. Break up prose with tables, example blocks, and bullet lists.
- NOT an opportunity to invent claims. If the sources don't cover something, say "джерела не охоплюють цей аспект" — never fabricate.
- NOT a place for Russianisms or calques. See the **Forbidden patterns** section below — those constructions are never "acceptable alternatives," not even in academic style.
- NOT a place to promote passive/nominalized prose as "the scientific style." Ukrainian academic Ukrainian is more active and more concrete than Russian scientific prose. Do not import Russian conventions.

## Forbidden patterns (hard rule — never endorse these)

These constructions are calques from Russian that Антоненко-Давидович explicitly warns against. Even if a source uses them in passing, do NOT endorse them as the academic norm:

| ❌ Calque | ✅ Authentic Ukrainian | Антоненко's rationale |
|---|---|---|
| `було встановлено / проведено / зроблено` | `встановлено / проведено / зроблено` (no `було`) OR active voice | Ukrainian impersonal passives take -но/-то directly; the `було` auxiliary is a calque of Russian `было сделано` |
| `являти собою` | `бути`, `становити`, `являти + instr.` (without `собою`) | `являть собой` is Russian; Ukrainian `являти` takes the instrumental directly |
| `в якості (кого/чого)` | `як (хто/що)`, `у ролі (кого)` | `в качестве` is Russian; `в якості` only exists in Ukrainian to mean "in the quality/grade of" |
| `відноситися до` (meaning "pertain to") | `стосуватися`, `належати до` | `относиться к` is Russian; Ukrainian `відноситися` means "have an attitude toward" |
| `на протязі (часу)` | `протягом`, `упродовж` | `на протяжении` is Russian; `протяг` in Ukrainian is "draft (air current)" |
| `слідуючий` | `наступний`, `такий` | `следующий` is Russian; `слідуючий` is not a standard Ukrainian participle form |
| `приймати участь` | `брати участь` | `принимать участие` is Russian |
| `діючий (закон, президент)` | `чинний`, `нинішній` | `действующий` is Russian; `діючий` is used for things that physically act |

If the topic is `academic-style-markers` or similar register-focused content, your job is to **teach the writer to AVOID these**, not to list them as stylistic options.

## Article Structure

```markdown
# {topic}

<!-- wiki-meta
slug: {slug}
domain: {domain}
tracks: [{tracks}]
compiled: {date}
-->

## Академічний контекст (Academic Context)
Where this topic fits in Ukrainian higher education. What courses cover it, what level of sophistication is expected. Cite sources like: `Згідно з даними [S5], цю тему розглядають...`

## Основний зміст (Main Content)
The core reference material, organized into 3–5 subsections. For EACH subsection:
- State the principle or rule
- Show 3–5 Ukrainian examples from textbook sources (source-attributed with `[S1]`-style citations)
- Show 1–2 contrasting pairs: ❌ помилково → ✅ правильно
- Cite the source for each claim

### Structure rules:
- Use TABLES for systematic data (paradigms, register contrasts, terminology lists)
- Use BULLET LISTS for rules and features
- Use EXAMPLE BLOCKS for Ukrainian sentences (with source attribution)
- Break sections every 200–300 words with a subheading

## Типові помилки L2 (Common L2 Errors)
What makes this topic HARD at C1–C2. **Minimum: 5 error pairs.** For each:

| ❌ Помилково | ✅ Правильно | Пояснення |

Explain WHY English speakers make each mistake (structural transfer, false analogy, etc.)

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY section — never omit.** Where Ukrainian differs from Russian on this topic:
- Specific forms/constructions that are Ukrainian, not shared with Russian
- Common teaching errors that assume Russian = Ukrainian
- Russianisms to actively avoid (use the **Forbidden patterns** table above as a starting point, and add any topic-specific ones)
- Frame: Ukrainian is the DEFAULT. Russian is the deviation, not the other way around.

**If the topic has no Russian connection, explain why Ukrainian's approach is independently developed** — don't try to contrast with Russian just to fill the section.

## Наукові дискусії (Scholarly Debates)
Where experts disagree. Present 2–3 positions with source citations and **name the scholar** if the source attributes one. If no genuine debate exists in the provided sources, write exactly: `Серед надійних джерел немає суттєвих розбіжностей щодо цього питання.` Do not fabricate a debate.

## Приклади високого рівня (Advanced Examples)
**Minimum 10 examples.** Each demonstrates mastery-level usage:
- From Ukrainian academic writing, journalism, or literature (cite source + chunk_id)
- Do NOT use YouTube transcripts as examples of standard written style
- Cover different facets of the topic (don't repeat the same pattern 10 times)
- Group into 2–3 thematic clusters with brief commentary

## Рекомендації для письменника (Writer Guidance)
Actionable instructions for the module writer:
- What exercises to create for this topic (specific types, not vague)
- What vocabulary to introduce (list 10–15 key terms with definitions)
- What common pitfalls the module must address
- Suggested teaching sequence (Phase 1 → Phase 2 → Phase 3)

## Пов'язані статті (Related Articles)
Cross-links to other wiki articles.
```

## Quality Standards — ABSOLUTE REQUIREMENTS

The article FAILS review if any of these is missing:

1. **Short source citation in EVERY paragraph.** Format: `[S1]`, `[S2]`.
2. **Minimum 2,000 words.** C1–C2 topics require depth. If you can't reach 2,000 with the given sources, note the gap explicitly and stop — do not pad.
3. **Minimum 10 advanced examples.** With full source attribution. From textbook/scholarly sources, not YouTube transcripts.
4. **Minimum 5 L2 error pairs.** ❌ → ✅ format with explanations.
5. **Decolonization section present and substantive** — at least 200 words, specific examples, not a token paragraph.
6. **No Russianisms endorsed.** Check every sentence of your own prose against the **Forbidden patterns** table above.
7. **No self-contradiction.** If you mark `було встановлено` as a Russianism in one section, do not use it in your own prose in another section. Search your own output for each forbidden pattern before concluding.
8. **Predominantly Ukrainian** (95%+ of prose). English only for metalinguistic commentary in parentheses.

## Anti-patterns (what NOT to do)

Past failures this prompt is built to prevent:

1. ❌ Dense walls of prose without examples → ✅ Break every 200 words, add example blocks
2. ❌ Filename-heavy inline citations → ✅ short citations like `[S1]`
3. ❌ Quoting a YouTube transcript as "academic style" → ✅ Cite textbook chunks for academic register; transcripts only for "attested colloquial usage"
4. ❌ Endorsing `було встановлено` / `являти собою` / `в якості` as academic style → ✅ Teach the writer to AVOID these
5. ❌ `"Деякі вчені вважають..."` without naming anyone → ✅ Name the scholar and cite the source, or omit the sentence
6. ❌ Framing Russification as a "neutral descriptive position" → ✅ Call it by name: `мовоцид`, `русифікація`
7. ❌ Generic advice (`teach this well`, `use good examples`) → ✅ Specific sequences, exercise types, vocabulary lists
8. ❌ Presenting ongoing debates as settled (feminitives, -ся passives) → ✅ Present positions with evidence
9. ❌ Contradiction (endorsing a passive construction in the prose while marking it as an error below) → ✅ Grep your own output before finalizing

## Self-audit (run through this checklist before outputting)

Before you emit the final article, mentally verify:

- [ ] Every paragraph has at least one `[S1]`-style citation
- [ ] Total word count ≥ 2000
- [ ] ≥ 10 advanced examples with attribution
- [ ] ≥ 5 L2 error pairs
- [ ] Decolonization section present, ≥ 200 words, substantive
- [ ] Not a single `було встановлено / являти собою / в якості / відноситися до / на протязі / слідуючий / приймати участь / діючий` (in the endorsement/teaching context)
- [ ] No claim endorsed solely by a Wikipedia or YouTube chunk (all such claims marked `<!-- VERIFY -->`)
- [ ] No scholarly debate fabricated — if no debate in sources, the section says so
- [ ] Ukrainian-first: 95%+ Ukrainian prose
- [ ] No contradiction between "correct form" in one section and usage in another

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
