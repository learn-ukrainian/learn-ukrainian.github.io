  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=15574 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
===RESEARCH_START===

# Дослідження: Спонукальні конструкції: Прагматика та стилістика

## State Standard Reference
§: Not explicitly mapped. 
Alignment: Due to execution constraints preventing live file reading, an exact section number from `UKRAINIAN-STATE-STANDARD-2024.txt` cannot be cited. However, the module perfectly aligns with the CEFR C1 requirement for Pragmatic Competence and Sociolinguistic Appropriateness: the ability to recognize and produce a wide range of illocutionary acts (requests, commands, suggestions) using varied linguistic means tailored to specific professional, academic, and social registers.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| спонукання | Середня (академ. тексти) | засоби спонукання, пряме/непряме спонукання |
| гортатив | Низька (спеціальна) | гортативна форма, гортативне значення |
| перформатив | Низька (спеціальна) | перформативне дієслово, перформативний акт |
| дозвольте | Висока (публічний дискурс) | дозвольте зауважити, дозвольте не погодитися |
| нехай | Дуже висока (загальна) | нехай щастить, нехай знають |

## Cultural Hooks
1. **Зростання ролі гортативу під час війни**: In contemporary Ukrainian public and military discourse, synthetic hortative forms ending in *-ймо/-імо* (e.g., "Боронімо!", "Єднаймося!", "Перемагаймо!") have become powerful tools of national mobilization. They emphasize collective action and agency, distinctively contrasting with the analytical *давайте + дієслово* construction, which is often criticized as a Russian calque.
2. **Ритуальні побажання**: The particle *хай/нехай* is deeply embedded in traditional Ukrainian performative speech acts, ranging from blessings ("Хай Бог береже!") to culturally specific curses ("Хай йому грець!"), demonstrating the language's rich emotive spectrum.

## Common Learner Errors
1. **Калькування «давайте + дієслово»** → *Давайте напишемо* замість *Напишімо*. — This is a direct structural calque from Russian ("давайте напишем"). While colloquially understood, it is considered a stylistic error in literary Ukrainian, where the synthetic hortative is the standard.
2. **Прямий переклад англійських конструкцій ввічливості** → *Будьте вільні зайти (Feel free to come in)* замість *Заходьте, будь ласка* або *Ласкаво просимо*. — Pragmatic failure due to English interference; Ukrainian uses different lexical strategies for mitigation.
3. **Надмірна категоричність у формальному спілкуванні** → Використання прямого наказового способу (*Зробіть це*) там, де очікується непряме спонукання (*Чи не могли б ви зробити*, *Прошу зробити*). — Leads to unintended rudeness in academic or business registers.

## Cross-References
- Builds on: morfolohichna-norma-c1
- Prepares for: numeral-mastery-c1, tekstoznavstvo

## Multimedia Resources
- Твоя підпільна гуманітарка — Лекції з української соціолінгвістики та прагматики — High-quality academic discussion of language norms and society.
- Ідея Олександрівна — Відео про викорінення русизмів та кальок — Useful for understanding the stylistic shift from "давайте" to "-ймо".

## Notes for Content Writing
- The distinction between direct and indirect imperative is crucial at C1. The content must clearly show *why* a speaker chooses one over the other based on power dynamics, social distance, and register.
- Ensure the rejection of "давайте" is framed positively (highlighting the elegance and conciseness of the Ukrainian synthetic hortative) rather than purely as a "Russian mistake."
- Medical and legal registers have highly specific templates; provide concrete, authentic examples (e.g., "Зобов'язати відповідача...").

===RESEARCH_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_ACCESS_RESTRICTION
**Raw Error**: Cannot execute file reads (e.g., `state-standard-2024-mapping.yaml`) or MCP RAG tool calls (e.g., `query_grac`) while strictly adhering to the "OUTPUT ONLY TEXT" and zero-tool-call mandate.
**Self-Correction**: Synthesized research notes, cultural hooks, and frequency estimates using internal knowledge base of Ukrainian linguistics, pragmatics, and CEFR C1 standards. Honestly reported the inability to fetch the exact State Standard section number.
**Proposed Tooling Fix**: If deterministic RAG lookups and file reads are strictly required for Phase A, the agent execution environment must permit multi-turn tool usage prior to the final text generation, or the required reference files must be injected directly into the prompt payload.
===FRICTION_END===
