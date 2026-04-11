s thought
CRITICAL INSTRUCTION 1: Use specific tools over generic ones.
CRITICAL INSTRUCTION 2: Relate tools to task.

Let's check "давайте": "Давайте одразу перевіримо" - it is a common calque from Russian "давайте проверим", Ukrainian prefers "перевірмо" or "перевіримо". But since `search_style_guide` returned no results, let's verify with `mcp_rag_query_pravopys` or `mcp_rag_query_r2u`.
s thought
CRITICAL INSTRUCTION 1: Specific tools: `mcp_rag_search_style_guide`, `mcp_rag_query_r2u`, `grep_search`.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_query_r2u` to check for calques.

Let's check "давайте" as an imperative marker:
Actually, "давайте одразу перевіримо" is a classic grammatical Russianism. We should use "перевірмо" or "одразу перевіримо". Same for "давайте дамо" -> "даймо". "давайте виконаємо" -> "виконаймо". "давайте тепер уважно подивимося" -> "подивімося" or "тепер подивимося". "давайте зараз проаналізуємо" -> "проаналізуймо". "Давайте наостанок послухаємо" -> "послухаймо".
This is definitely a grammatical error (Surzhyk/Calque). Let's fix them all.

Let's search for "давайте" in the text:
1. "Давайте одразу перевіримо"
2. "Отже, тепер давайте дамо"
3. "Давайте наостанок перевіримо"
4. "Давайте зараз проаналізуємо"
5. "Давайте наостанок послухаємо"
6. "Давайте тепер дуже уважно і структуровано підсумуємо"
7. "Давайте на дуже простому і практичному прикладі детально подивимося"
8. "давайте виконаємо одне велике"

I will replace them with regular imperative plural.
- "Давайте одразу перевіримо" -> "Одразу перевірмо"
- "Отже, тепер давайте дамо" -> "Отже, тепер даймо"
- "Давайте наостанок перевіримо" -> "Наостанок перевірмо"
- "Давайте зараз проаналізуємо" -> "Зараз проаналізуймо"
- "Давайте наостанок послухаємо" -> "Наостанок послухаймо"
- "Давайте тепер дуже уважно і структуровано підсумуємо" -> "Тепер дуже уважно і структуровано підсумуймо"
- "Давайте на дуже простому і практичному прикладі детально подивимося" -> "На дуже простому і практичному прикладі детально подивімося"
- "давайте виконаємо одне велике" -> "виконаймо одне велике"

Are there any other errors?
"приймати рішення" - wait, text says "ухвалила (made - pf) складне рішення" - that's correct.
"брати участь" - didn't see.

Let's check "поки що зовсім не думаючи про граматичні правила". (Thinking about grammar rules - "не думаючи" is an active participle).
"Зверніть особливу увагу" - correct.
"сильно здригнувся" - "сильно" is okay.
"впустив свою склянку" - "впустити" meaning to drop? "впустив з рук" vs "випустив". In Ukrainian, "впустити" means let someone in. "Впустити" is also "to drop" (впустити склянку). Let's check SUM-11 for "впустити".
s thought
CRITICAL INSTRUCTION 1: Specific tools prioritized.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_search_definitions` for `упустити`.

Let's check `упустити`. "упустити" in Ukrainian means to drop something out of one's hands. "Я сильно здригнувся від несподіванки і впустив свою склянку прямо на підлогу" -> This is correct (впустив/упустив). However, "впустив" has a main meaning "let in". Better to say "випустив з рук" or "упустив". But it is grammatically correct. Let's leave it.

What about "значно краще зрозуміти"?
"велике місто дуже міцно спало" - The city slept tightly.
"я швидко прокинувся" - woke up quickly.
"ухвалила (made - pf) складне рішення назавжди залишитися тут" - good.

Let's look at "відіграє роль" - it's "бере на себе важливу роль активного двигуна". This is correct.

What about "на цьому перехідному етапі навчання іноземні студенти часто роблять кілька дуже типових і дуже помітних для носіїв помилок."
"Натомість передній план"

Let's check the dialogue:
> — Юлія: Був такий приємний теплий вечір... Ми довго сиділи в улюбленій кав'ярні, дуже спокійно пили каву. *(It was such a pleasant warm evening... We sat in our favorite cafe for a long time, calmly drinking coffee.)*
> — Катерина: І раптом туди швидко зайшов наш Максим! *(And suddenly our Maksym walked in there quickly!)*
> — Юлія: Так, там грала дуже тиха музика, ніхто нікуди не поспішав... *(Yes, very quiet music was playing there, nobody was rushing anywhere...)*
> — Катерина: А він кинув свою важку сумку на стіл і голосно сказав: «Я нарешті знайшов нову роботу!» *(And he threw his heavy bag on the table and said loudly: "I finally found a new job!")*
This matches the plan.

Wait, is "завдавати тон" a calque? The text has "задає правильний тон".
Let's check `search_style_guide` for "задавати тон".
s thought
CRITICAL INSTRUCTION 1: Use specific MCP tools (e.g. `mcp_rag_search_definitions`, `mcp_rag_search_style_guide`). No generic bash commands unless needed.
CRITICAL INSTRUCTION 2: Related tools for fact-checking include `mcp_rag_query_r2u` and `mcp_rag_search_definitions`. `search_style_guide` was executed and gave no results.

Let's check `mcp_rag_query_r2u` for "задавать тон" and "задать тон".
s thought
CRITICAL INSTRUCTION 1: Use specific MCP tools (e.g. `mcp_rag_search_definitions`, `mcp_rag_search_style_guide`). No generic bash commands unless needed.
CRITICAL INSTRUCTION 2: Related tools for fact-checking include `mcp_rag_query_r2u` and `mcp_rag_search_definitions`. `search_style_guide` was executed and gave no results.

Let's look at "задавати тон" in the translation output:
`ЗАДАВА́ТЬ, задава́ть тон, ще гра́ти пе́ршу скри́пку; задаю́щий, що завдає́ тощо`
It says `задавати тон` is also translated as `грати першу скрипку`, but "задавати тон" exists. It's OK to keep "задає правильний тон".

What about "доконане дієслово"? Is it better to say "дієслово доконаного виду"? Yes, but "доконане дієслово" is acceptable and widely used in linguistic contexts.
What about "багаторазово повторюваний"? This is okay.
What about "приймати душ", "брати душ"? Not in text.

Let's check the dialogue.
Dialogue says:
> — Юлія: Був такий приємний теплий вечір... Ми довго сиділи в улюбленій кав'ярні, дуже спокійно пили каву.
> — Катерина: І раптом туди швидко зайшов наш Максим!
> — Юлія: Так, там грала дуже тиха музика, ніхто нікуди не поспішав...
> — Катерина: А він кинув свою важку сумку на стіл і голосно сказав: «Я нарешті знайшов нову роботу!»

Wait, the plan says:
`dialogue_situations:`
`  - setting: "Two friends recounting a dramatic evening — one describes the atmosphere (impf background), the other jumps in with the key events (pf foreground): Було тихо. Ми сиділи в кав'ярні, пили каву... — І раптом зайшов Максим! Він кинув сумку на стіл і сказав: 'Я знайшов роботу!'"`
`    speakers:`
`      - Юлія`
`      - Катерина`
The dialogue matches perfectly. It has good natural interplay.

Let's check the exercise markers:
- `<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->` - matches `quiz` from `activity_hints`. Wait, the plan has `type: quiz` with focus "Identify each verb in a narrative as тло (background/impf) or подія (foreground/pf) and explain why". Text has `<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->` right after explaining the two types. This is great.
- `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` - The plan has `type: match-up` (focus: "Match narrative functions..."). Text has it after the imperfective section. But wait, plan match-up focus is "setting, turning point, simultaneous action, sequential chain". These are for BOTH aspects, so placing it after the imperfective section is premature. Wait, the imperfective section talks about imperfective functions (setting, simultaneous, mental state). The perfective section talks about perfective functions. The matching covers both. Let's see if there is another matching activity.
The activity markers in the generated text:
1. `<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->` (Plan: quiz)
2. `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` (Is it match-up or fill-in?)
3. `<!-- INJECT_ACTIVITY: group-sort-connectors -->` (Plan: group-sort)
4. `<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->` (Plan: fill-in)
5. `<!-- INJECT_ACTIVITY: error-correction-narrative -->` (Plan: error-correction)
6. `<!-- INJECT_ACTIVITY: open-writing-narrative -->` (Plan: open-writing)

Total markers: 6.
Plan activity_hints:
- quiz (10 items)
- fill-in (8 items)
- group-sort (8 items)
- error-correction (6 items)
- match-up (8 items)
- open-writing (6 items)
Total 6 types. So all 6 types have a marker.
The marker `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` is placed at the end of the imperfective section.
Wait, if it's about "setting, turning point, simultaneous action, sequential chain", then it tests both aspects. But at this point in the text, perfective (turning point, sequential chain) hasn't been taught yet!
Let's look at the text just before `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->`:
The text talks about:
- atmosphere (стояти, світити, шуміти)
- simultaneous actions (читав, готувала)
- mental background (хвилювався, не розуміла)
- habitual background (вставав, пив, йшов)
So it teaches 4 functions of the imperfective aspect.
The `match-up` activity focus in the plan is: "Match narrative functions (setting, turning point, simultaneous action, sequential chain) to the correct aspect".
If the learner hasn't learned the perfective functions yet, they can't match "turning point" to perfective. They might be able to guess by elimination, but it's poor placement. It should be placed after both aspects have been taught, or at the end of the perfective section.
Let's check the marker placement for perfective:
`<!-- INJECT_ACTIVITY: group-sort-connectors -->` is placed after discussing perfective connectors. Connectors for both were taught (imperfective: тим часом, поки, у цей час. perfective: раптом, спочатку, потім, нарешті). This placement is fine.
`<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->` is placed after perfective section summary. This requires both. It's fine here.
Wait, `<!-- INJECT_ACTIVITY: error-correction-narrative -->` and `<!-- INJECT_ACTIVITY: open-writing-narrative -->` are both placed right after the paragraph about "моноаспектна стагнація" and right before the summary. That's fine.

So `match-narrative-function-impf` is prematurely placed. It should be moved after the perfective section, or renamed. Wait, I shouldn't just rename it, because the pipeline maps it to the YAML. But I can move it.
Let's see where to move `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->`. I will move it to the perfective section, maybe right before `<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->`, and rename the marker to just `<!-- INJECT_ACTIVITY: match-narrative-function -->`. Wait, does the name of the marker matter? Yes, the downstream step generates YAML based on these markers. Actually, the generation script matches hints to markers based on order or semantic similarity. Just moving it is fine.
Wait, the `match-up` hint: `Match narrative functions (setting, turning point, simultaneous action, sequential chain) to the correct aspect`.
Let's just move it down, after the perfective functions are explained.
Where is the perfective section explaining functions?
"Перша і найголовніша функція ... ланцюжок сюжету."
"Друга важлива функція ... поворотних моментів."
"Третя важлива функція ... вирішальних результатів."
Then it talks about connectors. Then the dialogue.
So we can move `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` down to just before `<!-- INJECT_ACTIVITY: group-sort-connectors -->`.
Actually, it's better to just leave it and accept a small deduction for pedagogical flow, or fix it by moving it. I will fix it by moving it down.

Let's review the `давайте` occurrences and create find/replace pairs.

1.
```yaml
- find: "Давайте одразу перевіримо вашу мовну інтуїцію."
  replace: "Одразу перевірмо вашу мовну інтуїцію."
```

2.
```yaml
- find: "Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення"
  replace: "Отже, тепер даймо максимально чіткі та зрозумілі визначення"
```

3.
```yaml
- find: "Давайте наостанок перевіримо цю граматичну логіку"
  replace: "Наостанок перевірмо цю граматичну логіку"
```

4.
```yaml
- find: "давайте виконаємо одне велике письмове завдання."
  replace: "виконаймо одне велике письмове завдання."
```

5.
```yaml
- find: "Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює"
  replace: "Тепер уважно подивімося, як саме цей складний механізм ефективно працює"
```

6.
```yaml
- find: "Давайте зараз проаналізуємо один дуже класичний абзац тексту."
  replace: "Зараз проаналізуймо один дуже класичний абзац тексту."
```

7.
```yaml
- find: "Давайте наостанок послухаємо ще одну дуже типову розмову."
  replace: "Наостанок послухаймо ще одну дуже типову розмову."
```

8.
```yaml
- find: "Давайте тепер дуже уважно і структуровано підсумуємо все те важливе,"
  replace: "Тепер дуже уважно і структуровано підсумуймо все те важливе,"
```

9.
```yaml
- find: "Давайте на дуже простому і практичному прикладі детально подивимося,"
  replace: "На дуже простому і практичному прикладі детально подивімося,"
```

Let's double-check the text for exact `find` string:
"Давайте одразу перевіримо вашу мовну інтуїцію." - Yes.
"Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення цим двом різним наративним шарам." - Yes.
"Давайте наостанок перевіримо цю граматичну логіку на одному досить цікавому і неочевидному прикладі." - Yes.
"Щоб надійно закріпити цю нову навичку, давайте виконаємо одне велике письмове завдання." - Yes.
"Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює у звичайній живій розмові." - Yes.
"Давайте зараз проаналізуємо один дуже класичний абзац тексту." - Yes.
"Давайте наостанок послухаємо ще одну дуже типову розмову." - Yes.
"Давайте тепер дуже уважно і структуровано підсумуємо все те важливе, що ми сьогодні вивчили про правильне конструювання захопливої історії." - Yes.
"Давайте на дуже простому і практичному прикладі детально подивимося, як свідома зміна граматичного аспекту повністю трансформує вашу звичайну історію." - Yes.

Wait, are there any other Russianisms?
Let's check "вирішальний результат" -> it's okay.
"вкрай рідко" -> very rarely, correct.
"без упину" -> correct.
"з великим полегшенням" -> correct.
"маркують" -> correct.
"магічним чином" -> correct.
"сухий і нудний поліцейський звіт" -> "сухий і нудний поліцейський звіт" is perfectly valid. The VESUM error for "Поліцейський" (capitalized) and "поліцейський" is because it might be listed as an adjective or noun without those specific caps in the limited 409K list, but it's a completely standard Ukrainian word (noun/adj). Wait, VESUM has "поліцейський" usually. But anyway, it's not a Russianism.

Wait, the plan says: "Using imperfective for clearly sequential events (*Він вставав, одягався, виходив з дому — sounds habitual, not narrative). Over-using one aspect — either all-pf (reads like a police report) or all-impf (reads like a description with no events)."
The text includes this example correctly:
"Учора я дуже швидко **вставав** *(was getting up)*, нервово **одягався** *(was dressing)* і поспіхом **виходив** *(was leaving)* зі свого темного будинку на роботу"
And:
"«Він встав, швидко одягнувся, вийшов, сів у свою машину, поїхав, приїхав, зайшов у будівлю». Це звучить дуже нервово і відверто штучно."

Let's check the placement of `match-narrative-function-impf`. I will move it.
```yaml
- find: |
    рутина формує базовий рівень нормальності, який трохи згодом буде різко і назавжди порушений дієсловами доконаного виду.
    
    <!-- INJECT_ACTIVITY: match-narrative-function-impf -->
    
    Тут дуже важливо бути обережним
  replace: |
    рутина формує базовий рівень нормальності, який трохи згодом буде різко і назавжди порушений дієсловами доконаного виду.
    
    Тут дуже важливо бути обережним
```
Wait, the regex or exact replace in the python pipeline might struggle with multi-line replacements if the line endings are different. Let's just replace the exact text if possible. The python script usually just does `text.replace(find, replace)`. But since I don't know the exact newlines, I can just replace the marker with empty string and re-insert it later.

Wait! A simpler way to move the marker without multi-line issues:
Find:
```yaml
- find: "порушений дієсловами доконаного виду.\n\n<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\nТут дуже важливо"
  replace: "порушений дієсловами доконаного виду.\n\nТут дуже важливо"
```
Wait, what if there's no double newline? It's better to just do:
```yaml
- find: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->"
  replace: ""
```
And then insert it where it belongs. Let's insert it before `group-sort-connectors`.
Wait, if I just replace `<!-- INJECT_ACTIVITY: group-sort-connectors -->` with BOTH markers:
```yaml
- find: "<!-- INJECT_ACTIVITY: group-sort-connectors -->"
  replace: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\n<!-- INJECT_ACTIVITY: group-sort-connectors -->"
```
Wait, `match-narrative-function-impf` is still in the text. I need to remove it from the original location.
Since I don't want to mess up the whitespace too much, I can do:
```yaml
- find: "дієсловами доконаного виду.\n\n<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\nТут дуже важливо"
```
But I can't be sure of the exact whitespace. Let's just deduct points for exercise placement in dimension 5 (Exercise quality) and provide the exact find/replace. Or I can just replace `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` with empty string.
```yaml
- find: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->"
  replace: ""
```
Wait, this will leave double blank lines. That's not a big deal for markdown.
Then I will add it back where it belongs:
```yaml
- find: "<!-- INJECT_ACTIVITY: group-sort-connectors -->"
  replace: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\n<!-- INJECT_ACTIVITY: group-sort-connectors -->"
```
This moves the exercise marker logically to after the perfective section and before the connectors exercise. But wait! The `match-up` focus is: "Match narrative functions (setting, turning point, simultaneous action, sequential chain) to the correct aspect". It should be placed after both aspects and their functions have been explained. The perfective functions (sequential chain, turning point, decisive results) are explained in the first half of the perfective section, before the connectors. The `group-sort-connectors` marker is placed right after the dialogue and connector explanation. So placing it there is perfect.

Let's check the score dimensions:
1. **Plan adherence**: 9/10. The plan points are covered comprehensively with rich examples. It mentions all sections and uses the examples from the plan (e.g. "Надворі було холодно. Подув сильний вітер"). However, the plan specifically asks for a short story about an unexpected event (open-writing), which is included in the activity hints, and is covered. Word target is 4000, actual is 5215. All good.
2. **Linguistic accuracy**: 8/10. The text contains several instances of the Russianism/calque "давайте + [дієслово]" to express the imperative (e.g., "Давайте одразу перевіримо"). Ukrainian strictly prefers the 1st person plural imperative form ("перевірмо", "даймо"). Otherwise, grammar and vocabulary are highly accurate and rich.
3. **Pedagogical quality**: 9/10. The module effectively contrasts the imperfective (background) and perfective (foreground) using the theater metaphor, giving very clear examples. PPP flow is observed. The only minor issue is the premature placement of a match-up exercise that tests both aspects before the second aspect is introduced.
4. **Vocabulary coverage**: 10/10. All required vocabulary from the plan is used naturally in the prose, many with inline translation hints as requested.
5. **Exercise quality**: 8/10. The marker `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` is placed prematurely (at the end of the imperfective section) even though its plan hint tests narrative functions of BOTH aspects (including turning point and sequential chain, which are perfective). It should be moved after the perfective section.
6. **Engagement & tone**: 10/10. The tone is encouraging, uses a great theater metaphor ("масштабні декорації на сцені театру"), and the narrative examples (the sudden explosion on a quiet terrace) are engaging and effectively illustrate the grammatical points.
7. **Structural integrity**: 10/10. All H2 headings from the plan are present and perfectly ordered. The word count is well above the 4000-word target. No meta-commentary.
8. **Cultural accuracy**: 10/10. Explanations are authentic to the Ukrainian language system without defaulting to "it's like Russian". Uses appropriate Ukrainian contexts (e.g., Berezhany).
9. **Dialogue & conversation quality**: 10/10. The dialogues are natural and effectively demonstrate the interplay of aspects in a spoken conversational context (e.g., the conversation between Yulia and Kateryna).

Total score will be solid.

Let's compile the findings and fixes:

Finding 1:
[Linguistic accuracy] [Critical]
Location: Multiple places, e.g., "Давайте одразу перевіримо вашу мовну інтуїцію."
Issue: The phrase "давайте + [дієслово]" is a common Russianism/calque for the imperative in Ukrainian. Ukrainian requires the morphological 1st person plural imperative (e.g., "перевірмо", "подивімося").
Fix: Replace all instances of "давайте + [дієслово]" with the correct imperative form.

Finding 2:
[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->`
Issue: The exercise marker for matching narrative functions (which tests BOTH aspects, including "turning point" and "sequential chain" from the perfective aspect) is placed at the end of the imperfective section, before the learner has been taught the perfective functions.
Fix: Move the marker down to the perfective section, placing it before the connectors exercise.

Let's list the fixes:
```yaml
<fixes>
- find: "Давайте одразу перевіримо вашу мовну інтуїцію."
  replace: "Одразу перевірмо вашу мовну інтуїцію."
- find: "Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення"
  replace: "Отже, тепер даймо максимально чіткі та зрозумілі визначення"
- find: "Давайте наостанок перевіримо цю граматичну логіку"
  replace: "Наостанок перевірмо цю граматичну логіку"
- find: "давайте виконаємо одне велике письмове завдання."
  replace: "виконаймо одне велике письмове завдання."
- find: "Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює"
  replace: "Тепер уважно подивімося, як саме цей складний механізм ефективно працює"
- find: "Давайте зараз проаналізуємо один дуже класичний абзац тексту."
  replace: "Зараз проаналізуймо один дуже класичний абзац тексту."
- find: "Давайте наостанок послухаємо ще одну дуже типову розмову."
  replace: "Наостанок послухаймо ще одну дуже типову розмову."
- find: "Давайте тепер дуже уважно і структуровано підсумуємо все те важливе,"
  replace: "Тепер дуже уважно і структуровано підсумуймо все те важливе,"
- find: "Давайте на дуже простому і практичному прикладі детально подивимося,"
  replace: "На дуже простому і практичному прикладі детально подивімося,"
- find: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: group-sort-connectors -->"
  replace: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\n<!-- INJECT_ACTIVITY: group-sort-connectors -->"
</fixes>
```

Wait, if I use `replace: ""` for the first find of the marker, it will completely erase it. But there might be whitespace around it. If I just erase it, there will be two blank lines. That's fine.

Let me double check if there are any other uses of "давайте" in the text.
- "Давайте одразу перевіримо"
- "Отже, тепер давайте дамо"
- "Давайте наостанок перевіримо"
- "давайте виконаємо"
- "Давайте тепер уважно подивимося"
- "Давайте зараз проаналізуємо"
- "Давайте наостанок послухаємо"
- "Давайте тепер дуже уважно і структуровано підсумуємо"
- "Давайте на дуже простому і практичному прикладі детально подивимося"

Are there any other Russianisms?
- "навколишня природа" -> ok.
- "об'єктивної реальності" -> ok.
- "прийшов у центральний банк" -> ok.
- "викликає" / "вимагає" -> "вимагають дієслів доконаного виду" -> ok.
- "відбуваються суворо послідовно" -> ok.
- "кардинально змінює" -> ok.
- "зупиняйтеся на одну коротку хвилину" -> ok.
- "щоденних справ" -> ok.
- "улюблена кав'ярня" -> ok.
- "показові приклади" -> ok.
- "стабільного статусу-кво" -> ok.

I think the review is solid.
Let's assemble the final output.

Wait, check the word count note in the prompt: "Word count: 5215 words".
Structural integrity should be 10/10 (exceeds 4000).

Let's quickly check the dialogue format:
> — Юлія: Був такий приємний теплий вечір... Ми довго сиділи в улюбленій кав'ярні, дуже спокійно пили каву. *(It was such a pleasant warm evening... We sat in our favorite cafe for a long time, calmly drinking coffee.)*
> — Катерина: І раптом туди швидко зайшов наш Максим! *(And suddenly our Maksym walked in there quickly!)*

Yes, dialogue uses correct names and english translations in parens.

Let's check the first exercise marker again:
"<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->"
Plan: "Identify each verb in a narrative as тло (background/impf) or подія (foreground/pf) and explain why". This comes right after the diagnostic text. This is correct.

Check the `error-correction` marker.
"<!-- INJECT_ACTIVITY: error-correction-narrative -->"
"<!-- INJECT_ACTIVITY: open-writing-narrative -->"
Both are grouped together at the end of the text, before the conclusion section.
Wait, they are placed right after the "mono-aspect stagnation" paragraph. This is appropriate as it allows the learner to correct errors and write their own text.

One final check on the exact find/replace strings:
I need to make sure the find string matches the text *exactly*.
Text:
"Давайте одразу перевіримо вашу мовну інтуїцію."
"Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення цим двом різним наративним шарам."
"Давайте наостанок перевіримо цю граматичну логіку на одному досить цікавому і неочевидному прикладі."
"Щоб надійно закріпити цю нову навичку, давайте виконаємо одне велике письмове завдання."
"Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює у звичайній живій розмові."
"Давайте зараз проаналізуємо один дуже класичний абзац тексту."
"Давайте наостанок послухаємо ще одну дуже типову розмову."
"Давайте тепер дуже уважно і структуровано підсумуємо все те важливе, що ми сьогодні вивчили про правильне конструювання захопливої історії."
"Давайте на дуже простому і практичному прикладі детально подивимося, як свідома зміна граматичного аспекту повністю трансформує вашу звичайну історію."

Everything matches perfectly.

```yaml
<fixes>
- find: "Давайте одразу перевіримо вашу мовну інтуїцію."
  replace: "Одразу перевірмо вашу мовну інтуїцію."
- find: "Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення"
  replace: "Отже, тепер даймо максимально чіткі та зрозумілі визначення"
- find: "Давайте наостанок перевіримо цю граматичну логіку"
  replace: "Наостанок перевірмо цю граматичну логіку"
- find: "давайте виконаємо одне велике"
  replace: "виконаймо одне велике"
- find: "Давайте тепер уважно подивимося, як саме цей складний механізм"
  replace: "Тепер уважно подивімося, як саме цей складний механізм"
- find: "Давайте зараз проаналізуємо один дуже класичний"
  replace: "Зараз проаналізуймо один дуже класичний"
- find: "Давайте наостанок послухаємо ще одну дуже типову розмову."
  replace: "Наостанок послухаймо ще одну дуже типову розмову."
- find: "Давайте тепер дуже уважно і структуровано підсумуємо все те"
  replace: "Тепер дуже уважно і структуровано підсумуймо все те"
- find: "Давайте на дуже простому і практичному прикладі детально подивимося,"
  replace: "На дуже простому і практичному прикладі детально подивімося,"
- find: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: group-sort-connectors -->"
  replace: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\n<!-- INJECT_ACTIVITY: group-sort-connectors -->"
</fixes>
```
To be absolutely safe with "давайте виконаємо", I will use `давайте виконаємо одне велике письмове завдання.`, since "давайте виконаємо одне велике" might be too short or maybe it continues on the next line.
Actually, the text says: `Щоб надійно закріпити цю нову навичку, давайте виконаємо одне велике письмове завдання.`
So:
```yaml
- find: "давайте виконаємо одне велике письмове завдання."
  replace: "виконаймо одне велике письмове завдання."
```
Text says: `Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює`
```yaml
- find: "Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює"
  replace: "Тепер уважно подивімося, як саме цей складний механізм ефективно працює"
```
Text says: `Давайте зараз проаналізуємо один дуже класичний абзац тексту.`
```yaml
- find: "Давайте зараз проаналізуємо один дуже класичний абзац тексту."
  replace: "Зараз проаналізуймо один дуже класичний абзац тексту."
```
Text says: `Давайте тепер дуже уважно і структуровано підсумуємо все те важливе,`
```yaml
- find: "Давайте тепер дуже уважно і структуровано підсумуємо все те важливе,"
  replace: "Тепер дуже уважно і структуровано підсумуймо все те важливе,"
```

This looks solid. The review is ready to be written.
## Linguistic Scan
Errors found:
1. **Russianisms / Calques:** The module repeatedly uses the structure «Давайте + [дієслово в майбутньому часі]» (e.g., "Давайте одразу перевіримо", "Давайте зараз проаналізуємо"). Це типовий росіянізм (калька з "давайте проверим"). В українській мові для спонукання до спільної дії використовується форма першої особи множини наказового способу (перевірмо, проаналізуймо, подивімося, підсумуймо).

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-aspect-analysis -->` - Placed correctly after the diagnostic text to test identification.
- `<!-- INJECT_ACTIVITY: match-narrative-function-impf -->` - **ISSUE:** Placed prematurely. The focus for this match-up exercise includes both imperfective and perfective narrative functions (setting, turning point, simultaneous action, sequential chain), but it is injected right after the imperfective section, before the student has learned about perfective functions ("turning points", "sequence").
- `<!-- INJECT_ACTIVITY: group-sort-connectors -->` - Placed correctly after perfective connectors are explained.
- `<!-- INJECT_ACTIVITY: fill-in-aspect-narrative -->` - Placed logically.
- `<!-- INJECT_ACTIVITY: error-correction-narrative -->` - Placed logically.
- `<!-- INJECT_ACTIVITY: open-writing-narrative -->` - Placed logically at the end.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The module covers all content outline points brilliantly, follows the TTT pedagogy precisely, and embeds the required English-Ukrainian vocabulary explicitly in the prose. |
| 2. Linguistic accuracy | 8/10 | The persistent use of "давайте + дієслово" (9 occurrences) instead of the proper Ukrainian imperative plural is a significant stylistic and grammatical flaw (калька). Otherwise, the text is extremely well-written and precise. |
| 3. Pedagogical quality | 9/10 | The use of the theater metaphor to contrast background (тло) and foreground (передній план) is exceptional. The only deduction is for the premature placement of the matching exercise before both sides of the concept were taught. |
| 4. Vocabulary coverage | 10/10 | Target vocabulary is fully integrated into the prose naturally, with inline translations exactly as expected. |
| 5. Exercise quality | 8/10 | The `match-narrative-function-impf` exercise marker is placed too early, requiring learners to match perfective functions before they have been taught. It should be moved after the perfective section. |
| 6. Engagement & tone | 10/10 | The tone is deeply engaging, maintaining the persona of an encouraging and knowledgeable instructor. The examples feel visceral and cinematic. |
| 7. Structural integrity | 10/10 | The formatting is impeccable, markdown is clean, and the word count (5215) comfortably exceeds the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Flawless handling of Ukrainian aspect without drawing false parallels to Russian or English. Strong cultural anchoring with authentic examples (e.g., "затишних Бережанах"). |
| 9. Dialogue & conversation quality | 10/10 | The dialogue between Yulia and Kateryna perfectly captures the natural, unconscious distribution of aspect roles among native speakers. |

## Findings
[Linguistic accuracy] [Critical]
Location: Multiple occurrences across sections (e.g., "Давайте одразу перевіримо вашу мовну інтуїцію.", "Давайте тепер уважно подивимося").
Issue: The phrase "давайте + [дієслово]" is a persistent Russianism/calque for the imperative mood. Standard Ukrainian requires the 1st person plural imperative form ("перевірмо", "подивімося", "проаналізуймо").
Fix: Replace all instances of "давайте + [дієслово]" with the morphological imperative form.

[Exercise quality] [Major]
Location: The end of section "Тло: недоконаний вид у наративі" (`<!-- INJECT_ACTIVITY: match-narrative-function-impf -->`)
Issue: The matching exercise tests narrative functions of BOTH aspects (including perfective "turning points" and "sequential chains"), but it is placed before perfective functions have been introduced.
Fix: Remove the marker from the imperfective section and move it down to the perfective section, placing it just before the `group-sort-connectors` exercise.

## Verdict: REVISE
The module is beautifully written, cinematic, and pedagogically strong, but it contains a systemic grammar/style error (давайте + дієслово) and one prematurely placed exercise marker. These issues must be fixed before publishing.

<fixes>
- find: "Давайте одразу перевіримо вашу мовну інтуїцію."
  replace: "Одразу перевірмо вашу мовну інтуїцію."
- find: "Отже, тепер давайте дамо максимально чіткі та зрозумілі визначення"
  replace: "Отже, тепер даймо максимально чіткі та зрозумілі визначення"
- find: "Давайте наостанок перевіримо цю граматичну логіку"
  replace: "Наостанок перевірмо цю граматичну логіку"
- find: "давайте виконаємо одне велике письмове завдання."
  replace: "виконаймо одне велике письмове завдання."
- find: "Давайте тепер уважно подивимося, як саме цей складний механізм ефективно працює"
  replace: "Тепер уважно подивімося, як саме цей складний механізм ефективно працює"
- find: "Давайте зараз проаналізуємо один дуже класичний абзац тексту."
  replace: "Зараз проаналізуймо один дуже класичний абзац тексту."
- find: "Давайте наостанок послухаємо ще одну дуже типову розмову."
  replace: "Наостанок послухаймо ще одну дуже типову розмову."
- find: "Давайте тепер дуже уважно і структуровано підсумуємо все те важливе,"
  replace: "Тепер дуже уважно і структуровано підсумуймо все те важливе,"
- find: "Давайте на дуже простому і практичному прикладі детально подивимося,"
  replace: "На дуже простому і практичному прикладі детально подивімося,"
- find: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: group-sort-connectors -->"
  replace: "<!-- INJECT_ACTIVITY: match-narrative-function-impf -->\n\n<!-- INJECT_ACTIVITY: group-sort-connectors -->"
</fixes>