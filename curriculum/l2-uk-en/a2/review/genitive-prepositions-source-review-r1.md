## Linguistic Scan
- "склянка з молока" / "коробка з цукерок" — **Calque/Logical Error**: Translating English "a glass of milk" using the Ukrainian material construction "з + Genitive" implies the glass itself is manufactured out of milk. Correct Ukrainian is "склянка молока" (measure), whereas the material construction requires a valid material (e.g., "склянка зі скла", "коробка з картону").
- "приймати душ" — **Russianism/Calque**: Direct translation of Russian "принимать душ". According to Антоненко-Давидович, the correct Ukrainian phrase is "митися під душем" or "брати душ".
- "знаходиться" — **Russianism/Calque**: Used repeatedly in the sense of geographical location (e.g., "знаходиться недалеко"). According to Антоненко-Давидович, this is a calque from Russian "находится". Should be "розташований" or simply omitted ("Де це?").
- "ліки від болю" — **Russianism/Calque**: Explicitly teaching "від" for medicine is a calque from Russian "лекарство от". The Ukrainian standard (Антоненко-Давидович) requires "проти" (ліки проти болю). While "від" is common in everyday speech, making it the core grammatical rule taught to learners is linguistically incorrect.
- "мати" (possession) — **Anglicism/Calque**: Overuse of "Я маю" and "Що ми маємо" instead of the native "У мене є" / "Що в нас". While grammatically valid, it is highly unnatural in the contexts provided.
- "ранкового сніданку" — **Pleonasm**: Breakfast is inherently in the morning; this is tautological in Ukrainian.

## Exercise Check
- The `<!-- INJECT_ACTIVITY: {type}, {focus} -->` markers are present, logically placed after their respective teaching sections, and match the plan's `activity_hints` specifications. No issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missed the required vocabulary word "джерело" in the Ukrainian text. The writer completely ignored the required textbook references (`Заболотний Grade 5`, `ULP`). Word count (2843 words) is 42% over the 2000-word target. |
| 2. Linguistic accuracy | 5/10 | Teaches several direct Russian and English calques ("приймати душ", "знаходиться далеко", "ліки від"). The material examples "склянка з молока" and "коробка з цукерок" are severe logical errors. |
| 3. Pedagogical quality | 7/10 | Excellent PPP flow and plentiful examples. However, the section teaching "ліки від" actively reinforces a Russian grammatical calque rather than teaching the native "проти". |
| 4. Vocabulary coverage | 9/10 | Covered most words naturally, but failed to incorporate "джерело" in the target language. |
| 5. Exercise quality | 10/10 | Markers perfectly align with the plan and are correctly sequenced. |
| 6. Engagement & tone | 8/10 | Engaging dialogues, but the heavy reliance on the Anglicized "Я маю..." possession structure makes the conversational tone feel stilted and non-native. |
| 7. Structural integrity | 8/10 | Clean markdown and proper heading hierarchy, but word count is significantly outside the target range. |
| 8. Cultural accuracy | 10/10 | Natural inclusion of Ukrainian cities and culturally appropriate contexts. |
| 9. Dialogue & conversation quality | 8/10 | Multi-turn, named speakers. Contexts are good, but slightly compromised by the "мати" calques. |

## Findings

[Plan Adherence] [major]
Location: English explanation text in the "Від кого" section.
Issue: The required vocabulary word "джерело" is missing in Ukrainian (only "source" was used in English).
Fix: Add **джерело** *(source)* to the English explanation text.

[Linguistic Accuracy] [critical]
Location: `На столі стоїть **склянка** *(glass)* з молока.` and `Він приніс велику коробку з цукерок.`
Issue: Grammatically claims the glass is manufactured out of milk and the box is constructed out of candies.
Fix: Change to "склянка зі скла" and "коробка з картону".

[Linguistic Accuracy] [critical]
Location: Entire explanation and examples for "Для чого це? (What is this for?)" using "ліки від"
Issue: Explicitly teaching "ліки від" teaches a Russian grammatical calque. The normative Ukrainian is "проти". While the plan requested "від", we must pivot the examples to things that naturally use "від" (like weather protection or insect spray) to avoid teaching Surzhyk grammar rules.
Fix: Rewrite the explanation to acknowledge "проти" for medicine, and change the "ліки від" examples to "захист від" / "одяг від".

[Linguistic Accuracy] [major]
Location: `Після **залу** *(gym)* я приймаю душ і їду в офіс.`
Issue: "приймати душ" is a Russian calque (Антоненко-Давидович).
Fix: Change to "я беру душ".

[Linguistic Accuracy] [major]
Location: Multiple instances of `знаходиться далеко від`
Issue: "знаходиться" used for geographical location is a Russian calque.
Fix: Replace with "розташований".

[Engagement & Tone] [major]
Location: Multiple instances of `Я маю`, `Що ми маємо`, `вони мають`
Issue: Unnatural, Anglicized possession structure that makes dialogues sound robotic.
Fix: Replace with native `У мене є`, `Що в нас`, `у них є`.

[Linguistic Accuracy] [minor]
Location: `Після ранкового **сніданку** *(breakfast)*`
Issue: Pleonasm (morning breakfast).
Fix: Change to "смачного сніданку".

## Verdict: REVISE
The module contains critical linguistic errors—specifically teaching "ліки від" as a core grammatical construct and translating "a glass of milk" into a material construction ("склянка з молока"). The heavy reliance on calques ("приймати душ", "знаходиться", "я маю") further degrades the naturalness of the language. The fixes below address these issues to ensure learners receive authentic Ukrainian input.

<fixes>
- find: "На столі стоїть **склянка** *(glass)* з молока."
  replace: "На столі стоїть **склянка** *(glass)* зі скла."
- find: "Він приніс велику коробку з цукерок."
  replace: "Він приніс велику коробку з картону."
- find: "Що ми маємо сьогодні на вечерю?"
  replace: "Що в нас сьогодні на вечерю?"
- find: "Я маю смачний **шоколад** *(chocolate)* зі Швейцарії."
  replace: "У мене є смачний **шоколад** *(chocolate)* зі Швейцарії."
- find: "Ми маємо смачну їжу з усього світу!"
  replace: "У нас є смачна їжа з усього світу!"
- find: "Я маю нове повідомлення від сестри на телефоні."
  replace: "У мене нове повідомлення від сестри на телефоні."
- find: "Чи ти маєш якісь новини від старшого брата?"
  replace: "Чи є в тебе якісь новини від старшого брата?"
- find: "Я маю вільний час тільки після **уроку** *(lesson)*."
  replace: "У мене є вільний час тільки після **уроку** *(lesson)*."
- find: "Я багато працюю, але після обіду я завжди маю перерву."
  replace: "Я багато працюю, але після обіду в мене завжди перерва."
- find: "Після обіду я маю важливі зустрічі з клієнтами."
  replace: "Після обіду в мене важливі зустрічі з клієнтами."
- find: "Після смачного обіду я маю зустріч з клієнтом."
  replace: "Після смачного обіду в мене зустріч з клієнтом."
- find: "Після веселих канікул вони мають енергію для навчання."
  replace: "Після веселих канікул у них є енергія для навчання."
- find: "Після **залу** *(gym)* я приймаю душ і їду в офіс."
  replace: "Після **залу** *(gym)* я беру душ і їду в офіс."
- find: "Після ранкового **сніданку** *(breakfast)* я п'ю чорну каву."
  replace: "Після смачного **сніданку** *(breakfast)* я п'ю чорну каву."
- find: "Наш новий будинок знаходиться далеко від **центру** *(center)* міста."
  replace: "Наш новий будинок розташований далеко від **центру** *(center)* міста."
- find: "Цей великий супермаркет знаходиться недалеко від нашої школи."
  replace: "Цей великий супермаркет розташований недалеко від нашої школи."
- find: "Наш готель знаходиться недалеко від міжнародного аеропорту."
  replace: "Наш готель розташований недалеко від міжнародного аеропорту."
- find: "Твій офіс знаходиться далеко від центру міста?"
  replace: "Твій офіс розташований далеко від центру міста?"
- find: "Де це знаходиться? *(Where is this located?)*"
  replace: "Де це розташовано? *(Where is this located?)*"
- find: "Я маю хороші ліки від сильного **головного болю** *(headache)*."
  replace: "У мене є надійний захист від сильного **вітру** *(strong wind)*."
- find: "У мене є новий ефективний засіб від **комарів** *(mosquitoes)*."
  replace: "У мене є новий ефективний захист від **комарів** *(mosquitoes)*."
- find: "Ми купили спеціальний засіб від плям на одязі."
  replace: "Ми купили спеціальний спрей від плям на одязі."
- find: "Які таблетки ти зазвичай приймаєш від болю в горлі?"
  replace: "Який одяг ти зазвичай носиш від холоду?"
- find: "**ліки від...** *(medicine for...)*"
  replace: "**одяг від...** *(clothes against...)*"
- find: "**засіб від...** *(remedy/repellent against...)*"
  replace: "**спрей від...** *(spray against...)*"
- find: "In English, you might say \"medicine *for* a headache\" or \"protection *against* mosquitoes\", but in Ukrainian, you use **від** *(from)*. You are literally saying \"medicine *from* a headache\". You will see this construction often in a pharmacy or a supermarket. If you need to buy something to solve a physical problem, you will ask the pharmacist for something **від** that problem."
  replace: "In English, you might say \"protection *against* mosquitoes\" or \"shelter *from* the rain\", and in Ukrainian, you also use **від** *(from)*. You will see this construction often when talking about protecting yourself from the weather or insects. (Note: For medicine, Ukrainian naturally uses **проти**, like «ліки проти болю» (medicine against pain), though you will often hear **від** in everyday speech)."
- find: "essential when talking about the source of an object, a message, or information, specifically when that source is a person"
  replace: "essential when talking about the **джерело** *(source)* of an object, a message, or information, specifically when that source is a person"
</fixes>
