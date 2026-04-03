## Linguistic Scan
Found 2 issues:
1. Incorrect stress mark on `А́ліна` (should be `Алі́на`).
2. Unnatural calque / awkward phrasing: `У тебе є стадіон?` translated as "Do you have a stadium nearby?". "У тебе є..." expresses possession, not location in a neighborhood. 

## Exercise Check
Found 5 markers:
1. `<!-- INJECT_ACTIVITY: quiz-prepositions -->`
2. `<!-- INJECT_ACTIVITY: match-places-activities -->`
3. `<!-- INJECT_ACTIVITY: quiz-where-would-you-go -->`
4. `<!-- INJECT_ACTIVITY: fill-in-your-city -->`
5. `<!-- INJECT_ACTIVITY: quiz-mixed-review -->`

Issues:
- The marker `<!-- INJECT_ACTIVITY: quiz-mixed-review -->` is extraneous and was not in the plan's `activity_hints` (which only listed 4 activities).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | Missed the explicit setting "Drawing a map of your Kyiv neighborhood for a pen pal", turning it into a generic chat. Completely omitted the required vocabulary words "озеро" and "поруч з". |
| 2. Linguistic accuracy | 6/10 | "А́ліна" has incorrect stress (should be "Алі́на"). "У тебе́ є стадіо́н?" literally means "Do you possess a stadium?" which is an unnatural calque for asking about neighborhood locations. |
| 3. Pedagogical quality | 6/10 | The plan stated Dialogue 2 should "Review: в/на + locative for all places", but the dialogue only contains `біля дому`, `далеко від центру` (genitive), and `на вулиці` (locative for street), failing to demonstrate `в/на` with city places. |
| 4. Vocabulary coverage | 8/10 | Covered most required/recommended words, but completely missed "озеро" and "поруч з" from the dialogue setup hints. |
| 5. Exercise quality | 7/10 | Added an extraneous 5th activity marker (`quiz-mixed-review`) that was not requested in the plan. |
| 6. Engagement & tone | 8/10 | Dialogues are okay, but the stranger exchange is highly transactional. |
| 7. Structural integrity | 6/10 | The word count (1567) is nearly 30% over the target (1200). The "Підсумок — Summary" section exacerbates this by copying 150 words verbatim from earlier sections. |
| 8. Cultural accuracy | 10/10 | Good integration of culturally relevant landmarks like Khreshchatyk, Maidan Nezalezhnosti, and Ploshcha Rynok. |
| 9. Dialogue & conversation quality | 7/10 | "У тебе є стадіон?" is stilted and robotic in the context of neighborhoods. |

## Findings
[1. Plan adherence] [major]
Location: "Now Аліна is chatting with her friend **І́гор** about their neighborhoods."
Issue: Completely missed the plan's required setting ("Drawing a map of your Kyiv neighborhood for a pen pal") and missed the required vocabulary "озеро" and "поруч з".
Fix: Rewrite the dialogue setup and add the missing words to the dialogue.

[2. Linguistic accuracy] [critical]
Location: "**А́ліна** has just moved to a new part of Kyiv."
Issue: Incorrect stress on the name Аліна. The stress falls on the 'і', not the 'А'.
Fix: Change `**А́ліна**` to `**Алі́на**`.

[3. Linguistic accuracy] [critical]
Location: "> — **Ігор:** У тебе́ є стадіо́н? *(Do you have a stadium nearby?)*"
Issue: "У тебе є..." literally translates to "Do you possess...". Using it to mean "Is there a stadium in your neighborhood?" is an English calque and sounds unnatural. Natural Ukrainian would use "Біля тебе" or "У твоєму районі".
Fix: Change to `Біля тебе́ є стадіо́н?`.

[4. Pedagogical quality] [major]
Location: "Now Аліна is chatting with her friend **І́гор**..." (Dialogue 2)
Issue: The plan specified "Review: в/на + locative for all places" for Dialogue 2. However, the dialogue only uses `біля дому` (genitive), `далеко від центру` (genitive), and `на вулиці` (locative for street). It fails to demonstrate `в/на` prepositions with city places.
Fix: Add locative examples to the dialogue (e.g., `у це́нтрі`, `на пло́щі`, `на вокза́лі`).

[5. Structural integrity] [major]
Location: "## Підсумок — Summary"
Issue: The module word count (1567) is significantly over the 1200 target (+30%). The Summary section contributes to this bloat by verbatim repeating ~150 words from previous sections.
Fix: Delete the redundant lists from the Summary section and keep only a short reminder.

[6. Exercise quality] [major]
Location: "<!-- INJECT_ACTIVITY: quiz-mixed-review -->"
Issue: The writer inserted a 5th activity marker that was not in the plan's `activity_hints`.
Fix: Remove the extraneous marker.

## Verdict: REVISE
The module has several critical linguistic errors (wrong stress on a name, unnatural phrasing/calque), ignores a specific structural requirement from the plan (pen pal map setting, specific vocabulary), and fails to follow the pedagogical instructions for the second dialogue (missing locative review). Word count bloat and extraneous markers require fixing.

<fixes>
- find: "**А́ліна** has just moved to a new part of Kyiv."
  replace: "**Алі́на** has just moved to a new part of Kyiv."
- find: "Now Аліна is chatting with her friend **І́гор** about their neighborhoods.\n\n> — **Ігор:** Що є біля твого́ до́му? *(What's near your house?)*\n> — **Аліна:** Біля дому є магази́н і кафе́. *(Near the house there's a shop and a café.)*\n> — **Ігор:** А ліка́рня? *(And a hospital?)*\n> — **Аліна:** Лікарня там, далеко від це́нтру. *(The hospital is over there, far from the center.)*\n> — **Ігор:** У тебе́ є стадіо́н? *(Do you have a stadium nearby?)*\n> — **Аліна:** Так, стадіон на вулиці Ле́сі Украї́нки. *(Yes, the stadium is on Lesya Ukrainka Street.)*"
  replace: "Now Аліна is drawing a map of her Kyiv neighborhood for her pen pal, and chatting with her friend **І́гор** about what to mark.\n\n> — **Ігор:** Що є біля твого́ до́му? *(What's near your house?)*\n> — **Аліна:** Біля дому є магази́н і кафе́. А по́руч з кафе — о́зеро. *(Near the house there's a shop and a café. And next to the café is a lake.)*\n> — **Ігор:** А ліка́рня у це́нтрі? *(And is the hospital in the center?)*\n> — **Аліна:** Ні, лікарня там, далеко від це́нтру. *(No, the hospital is over there, far from the center.)*\n> — **Ігор:** Біля тебе́ є стадіо́н? *(Is there a stadium near you?)*\n> — **Аліна:** Так, стадіон на пло́щі, а по́шта на вокза́лі. *(Yes, the stadium is on the square, and the post office is at the train station.)*"
- find: "The phrase **далеко від центру** (far from the center) pairs the adverb **далеко** with a genitive chunk."
  replace: "The phrase **далеко від центру** (far from the center) pairs the adverb **далеко** with a genitive chunk. We also introduced **по́руч з** (next to), which takes the instrumental case, though **кафе** doesn't change."
- find: "**Neuter (n):**\n- **кафе** (café)"
  replace: "**Neuter (n):**\n- **кафе** (café) · **о́зеро** (lake)"
- find: "**В/у + locative:**\n- аптека → **в аптеці** · бібліотека → **у бібліотеці** · лікарня → **у лікарні** · магазин → **в магазині** · банк → **у банку** · готель → **у готелі** · ресторан → **у ресторані** · музей → **в музеї** · університет → **в університеті** · кінотеатр → **у кінотеатрі** · театр → **у театрі** · церква → **у церкві**\n\n**На + locative:**\n- пошта → **на пошті** · вокзал → **на вокзалі** · стадіон → **на стадіоні** · зупинка → **на зупинці** · площа → **на площі**\n\nPattern for these places: **на** = **пошта**, **вокзал**, **стадіон**, **зупинка**, **площа**. The rest take **в/у**.\n\nLocation words at a glance:\n- **тут** — here: **Магазин тут.**\n- **там** — there: **Вокзал там.**\n- **далеко** — far: **Університет далеко.**\n- **близько** / **недалеко** — near: **Парк близько.**\n- **біля** + gen — next to: **Аптека біля дому.**\n- **у центрі** — in the center: **Театр у центрі.**\n- **на розі** — on the corner: **Банк на розі.**\n- **у районі** — in the neighborhood: **Шко́ла у районі.**"
  replace: "Remember the core pattern: **на** is used with **пошта**, **вокзал**, **стадіон**, **зупинка**, and **площа**. Most other places take **в/у**."
- find: "<!-- INJECT_ACTIVITY: quiz-mixed-review -->\n\n**Deterministic word count:"
  replace: "**Deterministic word count:"
</fixes>
