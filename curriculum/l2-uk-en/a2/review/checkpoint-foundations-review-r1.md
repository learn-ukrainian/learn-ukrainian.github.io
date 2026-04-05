## Linguistic Scan
Errors found:
1. **Russianism/Calque**: "давай повторимо" (давай + future tense verb instead of the imperative "повторімо").
2. **Russianism/Calque**: "давай робити" (давай + infinitive verb instead of the imperative "робімо").

## Exercise Check
- **Marker placements**: `exercise-3` is incorrectly placed under Part 2, and the writer hallucinated an `exercise-8` under Part 3 (the plan only outlines 7 exercises total).
- **Alignment with plan**: The plan asks for 4 `activity_hints` items, but the writer instantiated 8 separate markers mapped strictly to the outline bullet points. This breaks the expected one-to-one mapping, but fixing the extraneous/misplaced markers will restore structural order. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missing reference to Заболотний. Marker mapping deviates from the plan outline (`exercise-3` misplaced, `exercise-8` added). |
| 2. Linguistic accuracy | 8/10 | Two Russianisms found ("давай повторимо", "давай робити") using calqued imperatives. |
| 3. Pedagogical quality | 9/10 | Excellent pedagogical flow, effectively using character mistakes to demonstrate the rule of 5-20 ("У мене є п’ять брати... Ні, почекай."). |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is present naturally, but the recommended word "обрати" was substituted with "вибрати". |
| 5. Exercise quality | 7/10 | Markers are misaligned: `exercise-3` is misplaced in Part 2, and `exercise-8` is hallucinated. |
| 6. Engagement & tone | 7/10 | Overuse of meta-commentary ("Let us start by...", "Let us continue...") which tells the learner what to do instead of transitioning smoothly. |
| 7. Structural integrity | 9/10 | Clean markdown, though pacing is extremely heavy for the intended level. |
| 8. Cultural accuracy | 10/10 | Culturally appropriate context and naming. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues serve the grammar well, though slightly transactional. |

## Findings

1. [Linguistic accuracy] [Critical]
Location: Частина 1: Вправи на розпізнавання: "> **Олена:** Марку, давай повторимо граматику перед уроком. *(повторимо — let's review)*"
Issue: Russianism/Calque. "Давай" + future tense is a direct calque of Russian "давай повторим". The correct Ukrainian imperative is "повторімо".
Fix: Replace "давай повторимо" with "повторімо".

2. [Linguistic accuracy] [Critical]
Location: Частина 1: Вправи на розпізнавання: "> **Марко:** Зрозумів. Добре, давай робити вправи!"
Issue: Russianism/Calque. "Давай" + infinitive is a direct calque of Russian "давай делать". The correct Ukrainian imperative is "робімо".
Fix: Replace "давай робити" with "робімо".

3. [Exercise quality] [Major]
Location: Частина 2 and Частина 3
Issue: The marker `exercise-3` is incorrectly placed in Part 2 instead of Part 1 (as dictated by the `content_outline`). Additionally, the writer hallucinated an `exercise-8` marker at the end of Part 3, although the outline only specifies 7 exercises.
Fix: Move `exercise-3` marker to the end of Part 1 and delete the `exercise-8` marker entirely.

4. [Vocabulary coverage] [Minor]
Location: Частина 2: Вправи на вибір: "When you take a test, you need to **вибрати** (to choose) the **правильний варіант**"
Issue: The recommended vocabulary word "обрати" from the plan was missed, with "вибрати" used instead.
Fix: Replace "вибрати" with "обрати".

5. [Engagement & tone] [Major]
Location: Multiple locations (e.g., "Let us start by listening to two friends...", "Let us continue with another conversation.")
Issue: The text frequently uses "Let us..." meta-commentary, which tells the learner what is happening instead of showing it naturally. This violates the Engagement & tone dimension.
Fix: Replace the meta-commentary phrases with direct, active transitions.

6. [Plan adherence] [Major]
Location: Entire text
Issue: The mandatory textbook reference "Заболотний Grade 5-6" with the note "Повторення вивченого" was omitted from the content.
Fix: Add a sentence acknowledging the pedagogical approach of Заболотний to the Summary section.

## Verdict: REVISE
The module contains two critical linguistic errors (Russianisms regarding the imperative form), misses a mandatory textbook reference, includes misplaced exercise markers, and suffers from repetitive meta-commentary. These issues must be repaired before publishing.

<fixes>
- find: "Олена:** Марку, давай повторимо граматику перед уроком. *(повторимо — let's review)*"
  replace: "Олена:** Марку, повторімо граматику перед уроком. *(повторімо — let's review)*"
- find: "**Марко:** Зрозумів. Добре, давай робити вправи!"
  replace: "**Марко:** Зрозумів. Добре, робімо вправи!"
- find: "<!-- INJECT_ACTIVITY: exercise-2 -->"
  replace: "<!-- INJECT_ACTIVITY: exercise-2 -->\n<!-- INJECT_ACTIVITY: exercise-3 -->"
- find: "<!-- INJECT_ACTIVITY: exercise-5 -->\n<!-- INJECT_ACTIVITY: exercise-3 -->"
  replace: "<!-- INJECT_ACTIVITY: exercise-5 -->"
- find: "<!-- INJECT_ACTIVITY: exercise-7 -->\n<!-- INJECT_ACTIVITY: exercise-8 -->"
  replace: "<!-- INJECT_ACTIVITY: exercise-7 -->"
- find: "When you take a test, you need to **вибрати** (to choose) the **правильний варіант**"
  replace: "When you take a test, you need to **обрати** (to choose) the **правильний варіант**"
- find: "Let us start by listening to two friends who are preparing for a Ukrainian language class. Read the dialogue aloud to practice your pronunciation."
  replace: "Listen to two friends who are preparing for a Ukrainian language class. Read the dialogue aloud to practice your pronunciation."
- find: "Let us continue with another conversation. Two university students are discussing their homework."
  replace: "Read another conversation. Two university students are discussing their homework."
- find: "Now, let us bring these grammar rules together to tell your own story."
  replace: "Now, bring these grammar rules together to tell your own story."
- find: "Let us look at how you can use these rules to organize and talk about your future plans. Here is a short conversation about the upcoming weekend."
  replace: "Here is how you can use these rules to organize and talk about your future plans in a short conversation about the upcoming weekend."
- find: "You can always go back and review the previous modules to strengthen your foundation. Keep practicing these patterns, read the Ukrainian examples aloud every day, and the grammatical rules for cases and verbal aspects will soon become natural to you!"
  replace: "You can always go back and review the previous modules to strengthen your foundation. Keep practicing these patterns, read the Ukrainian examples aloud every day, and the grammatical rules for cases and verbal aspects will soon become natural to you!\n\nThis checkpoint review incorporates the pedagogical approach of **Заболотний Grade 5-6** (Повторення вивченого), ensuring that your foundations are solid before progressing."
</fixes>
