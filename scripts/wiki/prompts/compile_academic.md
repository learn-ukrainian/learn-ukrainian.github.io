# Wiki: Academic Brief Compilation (C1–C2)

You are compiling an **academic brief** for the Ukrainian language curriculum wiki. This brief will guide the content writer (a separate AI) when building advanced modules for learners at near-native proficiency.

## Your Task

Compile an academic brief on: **{topic}**
Domain: **{domain}**
Tracks served: **{tracks}**

## Source Material

The following source chunks come from Ukrainian textbooks, scholarly works, and linguistic resources. **Every claim in your article MUST cite a specific source** using the format `(Source N)` or `(Джерело: chunk_id)`. If no source supports a claim, mark it `<!-- VERIFY -->`.

{sources}

## What an Academic Brief IS

A reference guide for the writer covering:
- Academic Ukrainian conventions for this topic — with SPECIFIC examples from the sources
- Stylistic nuances and register requirements — demonstrated through contrasting pairs
- Advanced grammar, syntax, or vocabulary systems — with complete paradigm tables
- How this topic is taught at Ukrainian university level
- Scholarly debates and authoritative references

## What an Academic Brief Is NOT

- NOT a dense theoretical essay. Break up prose with tables, example blocks, and bullet lists.
- NOT an opportunity to invent claims. If the sources don't cover something, say "джерела не охоплюють цей аспект" — never fabricate.
- NOT a place for Russianisms or calques. If you're unsure about a form, mark it `<!-- VERIFY -->`.

## Article Structure

```markdown
# {topic}

<!-- wiki-meta
slug: {slug}
domain: {domain}
tracks: [{tracks}]
sources: [{source_ids}]
compiled: {date}
-->

## Академічний контекст (Academic Context)
Where this topic fits in Ukrainian higher education. What courses cover it, what level of sophistication is expected. **Cite sources:** "Згідно з (Source N), цю тему розглядають у курсі..."

## Основний зміст (Main Content)
The core reference material, organized into 3-5 subsections. For EACH subsection:
- State the principle or rule
- Show 3-5 Ukrainian examples demonstrating it (from the sources or natural speech)
- Show 1-2 contrasting pairs: ❌ помилково → ✅ правильно
- Cite the source for each claim

### Structure rules:
- Use TABLES for systematic data (paradigms, register contrasts, terminology lists)
- Use BULLET LISTS for rules and features
- Use EXAMPLE BLOCKS for Ukrainian sentences (with source attribution)
- Break sections every 200-300 words with a subheading

## Типові помилки L2 (Common L2 Errors)
What makes this topic HARD at C1-C2, with specific error-correction pairs:
| ❌ Помилково | ✅ Правильно | Пояснення |
For each error: explain WHY English speakers make this mistake (structural transfer, false analogy, etc.)
**Minimum: 5 error pairs.**

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY section — never omit.** Where Ukrainian differs from Russian on this topic:
- Specific forms/constructions that are Ukrainian (not shared with Russian)
- Common teaching errors that assume Russian = Ukrainian
- Russianisms to actively avoid (with correct Ukrainian alternatives)
- Frame: Ukrainian is the DEFAULT. Russian is the deviation, not the other way around.
**If the topic has no Russian connection, explain why Ukrainian's approach is independently developed.**

## Наукові дискусії (Scholarly Debates)
Where experts disagree. Present 2-3 positions with source citations. The writer should present these fairly. If no genuine debate exists, state: "Серед науковців немає суттєвих розбіжностей щодо цього питання."

## Приклади високого рівня (Advanced Examples)
**Minimum 10 examples.** Each demonstrates mastery-level usage:
- From Ukrainian academic writing, journalism, or literature
- Source-attributed: "«цитата» (Source N)" or "(Авраменко, Grade 11)"
- Cover different facets of the topic (don't repeat the same pattern 10 times)
- Group into 2-3 thematic clusters with brief commentary

## Рекомендації для письменника (Writer Guidance)
Actionable instructions for the module writer:
- What exercises to create for this topic (specific types, not vague)
- What vocabulary to introduce (list 10-15 key terms with definitions)
- What common pitfalls the module must address
- Suggested teaching sequence (Phase 1 → Phase 2 → Phase 3)

## Пов'язані статті (Related Articles)
Cross-links to other wiki articles.
```

## Quality Standards

### ABSOLUTE REQUIREMENTS (article fails without these):
1. **Source citations in EVERY paragraph.** Not just listed in metadata — woven into claims. "Згідно з (Source 5), науковий стиль характеризується..."
2. **Minimum 2,000 words.** C1-C2 topics require depth. If you can't reach 2,000 with the given sources, note the gap explicitly.
3. **Minimum 10 advanced examples.** With source attribution. From real Ukrainian texts.
4. **Minimum 5 error pairs.** ❌ → ✅ format with explanations.
5. **Decolonization section present and substantive.** Not a token paragraph.
6. **No Russianisms.** Not even as "acceptable alternatives." If a form is Russian (e.g., `Протокол складається` instead of `Протокол складено`), mark it as ❌.
7. **No self-contradiction.** If you warn against a construction, don't use it in your own prose.

### STRONG PREFERENCES:
- Write the article **predominantly in Ukrainian** (this is C1-C2 content — full immersion). English glosses only for metalinguistic commentary.
- Use paradigm tables, not prose, for systematic data.
- Match the sophistication expected at university level.
- Cite Ukrainian scholarship. Not Western textbooks about Ukrainian.

## Anti-patterns (what NOT to do)

These patterns have caused articles to score 5-6/10 in the past. Avoid them:

1. ❌ Dense walls of prose without examples → ✅ Break every 200 words, add examples
2. ❌ "This is an important topic in Ukrainian linguistics" → ✅ Skip filler, give specifics
3. ❌ Endorsing calques as "acceptable" (e.g., passive -ся where -но/-то is correct) → ✅ Only endorse forms confirmed by Правопис 2019
4. ❌ "Деякі вчені вважають..." without citing WHO → ✅ Always name the scholar and source
5. ❌ Framing Russification as a "neutral descriptive position" → ✅ Call it what it is: linguocide (мовоцид)
6. ❌ Generic advice ("teach this well") → ✅ Specific sequences, exercise types, vocabulary lists
7. ❌ Presenting ongoing debates as settled (feminitives, -ся passives) → ✅ Present positions with evidence

## Output

Return ONLY the markdown article. No preamble. Start with `# Title`.
