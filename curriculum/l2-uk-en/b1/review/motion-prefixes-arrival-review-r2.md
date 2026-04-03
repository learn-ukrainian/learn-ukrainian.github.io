vspace:120000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010<EPHEMERAL_MESSAGE>

CRITICAL INSTRUCTION 1: You may have access to a variety of tools at your disposal. Some tools may be for a specific task such as 'view_file' (for viewing contents of a file). Others may be very broadly applicable such as the ability to run a command on a terminal. Always prioritize using the most specific tool you can for the task at hand. Here are some rules:
(a) NEVER run cat inside a bash command to create a new file or append to an existing file if custom tools exist.
(b) ALWAYS use custom grep tools if available instead of running grep inside a bash command unless absolutely needed.
(c) DO NOT use ls for listing, cat for viewing, grep for finding, sed for replacing if custom tools that perform these functionalities are available.
CRITICAL INSTRUCTION 2: Before making tool calls T, think and explicitly list out any related tools for the task at hand. You can only execute a set of tools T if all other tools in the list are either more generic or cannot be used for the task at hand.
ALWAYS START your thought with recalling critical instructions 1 and 2. In particular, the format for the start of your thought block must be '...94>thought
CRITICAL INSTRUCTION 1: ...
CRITICAL INSTRUCTION 2: ...'.
</EPHEMERAL_MESSAGE>
</response>
</mcp_rag_verify_words>
<thought>
CRITICAL INSTRUCTION 1: Use specific tools like `mcp_rag_verify_lemma` over more generic ones.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_query_r2u`, `mcp_rag_search_style_guide`.

The word 'доставка' is a known Russicism/calque in some contexts or at least not in VESUM under that spelling? Wait, VESUM might have "доставляння". Let's check `mcp_rag_search_style_guide` for 'доставка' or 'доставляти'.
Wait, 'доставка' - usually 'доставлення', 'довіз', or it's a known Russianism. In the text: "доставлення", "доставляння". What does the text say?
Text: "швидке доставляння людей або комерційних вантажів", wait, text says:
"швидке доставляння людей або комерційних вантажів" - oh, I searched for "доставку". Let me check where "доставку" is in the text.
Ah, text says: "обережну доставку різних об'єктів".
"доставку" -> 'доставка' is NOT FOUND. Let's check r2u for 'доставка'.
Also 'парковка': text says: "машина вже приїхала на парковку."
Let's check 'парковка' and 'доставка' on r2u.
## Linguistic Scan
- `доставку` - Russianism/calque in this context (or not registered in VESUM in this spelling), standard Ukrainian uses `доставлення` or `доставання` or `доправлення`.
- `парковку` - Colloquial/Russianism (not in VESUM), standard Ukrainian uses `автостоянку` or `паркінг`.
- `довів свій транспортний засіб` - Calque/semantic error. The verb `довести` means leading someone/something by hand (e.g., a group of people, a horse). You cannot `довести` a vehicle to drive it; you must use `довіз` (if transporting passengers) or `доїхав`.

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-up -->` is present (8 items) after Section 2.
- `<!-- INJECT_ACTIVITY: group-sort -->` is present (10 items) after Section 2.
- `<!-- INJECT_ACTIVITY: fill-in -->` is present (8 items) after Section 3.
- `<!-- INJECT_ACTIVITY: quiz -->` is present (8 items) after Section 4.
- `<!-- INJECT_ACTIVITY: error-correction -->` is present (6 items) after Section 4.
- `<!-- INJECT_ACTIVITY: free-write -->` is present (6 items) after Section 5.
All activity markers match the plan in count, focus, and type, and they are placed appropriately after their teaching sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Deducted for missing the explicit grammatical rules for prepositions with `при-` (в/у + Зн.в., на + Зн.в., до + Р.в.) which the plan mandated in the section "Префікс при-: прибуття". |
| 2. Linguistic accuracy | 7/10 | Deducted for Russianisms/calques (`доставку`, `парковку`) and the incorrect semantic use of `довести` for a vehicle ("довів свій транспортний засіб"). |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of the difference between "arrival" vs "reaching", with good scaffolding from base verbs to prefixes. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are seamlessly integrated into the prose and dialogue. |
| 5. Exercise quality | 10/10 | The injected markers correspond perfectly to the plan's requirements. |
| 6. Engagement & tone | 9/10 | Engaging travel narratives and a relatable focus on the emotional nuance of travel (e.g., the relief of reaching a destination). |
| 7. Structural integrity | 8/10 | Word count is quite high (4796 words) compared to the 4000-word target, resulting in a minor deduction. All headings match the plan exactly. |
| 8. Cultural accuracy | 10/10 | Natural geographical references (Carpathians, Dovbush rocks, Odesa, Kyiv) with appropriate context. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is a realistic exchange about coordinating arrivals at a train station. |

## Findings

[1. Plan adherence] [major]
Location: "Отже, префікс при- завжди вказує на успішне прибуття до фінальної точки маршруту." (End of first paragraph in "Префікс при-: прибуття")
Issue: The plan explicitly required teaching the specific prepositions and cases used with `при-` (до + Р.в., в/у + Зн.в., на + Зн.в.), but this grammatical instruction was omitted entirely in this section, unlike the `до-` section which got a dedicated paragraph.
Fix: Add the missing grammar instruction before concluding the paragraph.

[2. Linguistic accuracy] [critical]
Location: "Ці слова означають обережну доставку різних об'єктів"
Issue: `доставку` is a Russianism or colloquialism not registered in VESUM. The standard Ukrainian term is `доставлення`.
Fix: Replace with "обережне доставлення".

[2. Linguistic accuracy] [critical]
Location: "Він щойно написав, що його машина вже приїхала на парковку."
Issue: `парковку` is a colloquialism/Russianism not found in VESUM. The correct standard term is `автостоянку` or `паркінг`.
Fix: Replace with "автостоянку".

[2. Linguistic accuracy] [critical]
Location: "проте досвідчений водій обережно та впевнено довів (led/drove all the way) свій транспортний засіб до кінцевої зупинки."
Issue: Semantic error/calque. The verb `довести` implies leading on foot. A driver driving a bus full of passengers should be described as `довіз` (transported), not `довів`.
Fix: Change `довів` to `довіз`, and adjust the translation to match.

## Verdict: REVISE
The module contains multiple linguistic inaccuracies (unregistered/colloquial words and a semantic calque) and misses a key grammatical requirement from the plan. It requires targeted revisions via the find/replace block before it can pass.

<fixes>
- find: "Це означає, що вона тепер фізично знаходиться у поштовому відділенні, і я можу її забрати. Отже, префікс при- завжди вказує на успішне прибуття до фінальної точки маршруту."
  replace: "Це означає, що вона тепер фізично знаходиться у поштовому відділенні, і я можу її забрати. На відміну від префікса до-, який завжди вимагає одного прийменника, дієслова з префіксом при- використовуються з різними прийменниками простору: прийти до + Р.в. (прийти до лікаря), прийти в/у + Зн.в. (прийти в магазин), прийти на + Зн.в. (прийти на роботу). Отже, префікс при- завжди вказує на успішне прибуття до фінальної точки маршруту."
- find: "Ці слова означають обережну доставку різних об'єктів"
  replace: "Ці слова означають обережне доставлення різних об'єктів"
- find: "Він щойно написав, що його машина вже приїхала на парковку."
  replace: "Він щойно написав, що його машина вже приїхала на автостоянку."
- find: "проте досвідчений водій обережно та впевнено довів (led/drove all the way) свій транспортний засіб до кінцевої зупинки."
  replace: "проте досвідчений водій обережно та впевнено довіз (transported all the way) нас до кінцевої зупинки."
</fixes>
