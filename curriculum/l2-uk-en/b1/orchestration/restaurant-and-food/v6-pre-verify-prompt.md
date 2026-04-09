<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 18: Ресторан і їжа (B1, B1.1 [Morphophonemics])

## Plan vocabulary to verify

- страва (dish/course — a prepared food item)
- борщ (borscht — quintessential Ukrainian beet soup)
- вареники (varenyky — filled dumplings, pl of вареник)
- деруни (potato pancakes — pl of дерун)
- пампушки (garlic bread rolls — served with борщ, pl of пампушка)
- сало (cured pork fat — iconic Ukrainian product)
- узвар (dried fruit compote — traditional Ukrainian drink)
- меню (menu — невідмінюване noun)
- замовлення (order — the act of ordering food)
- офіціант (waiter — masc; fem: офіціантка)
- рахунок (bill/check — restaurant bill)
- гарнір (side dish — served with a main course)
- закуска (appetizer/starter — first course before soup)
- кухня (cuisine/kitchen — both meanings in Ukrainian)
- порція (portion — a serving of food)
- чайові (tip — plural noun, від чай)
- смачний (tasty/delicious)
- гострий (spicy/sharp — taste)
- смажений (fried — cooking method)
- запечений (baked — cooking method)
- тушкований (stewed — cooking method)
- сметана (sour cream — essential Ukrainian condiment)

## Sections to research

- **Українська кухня: страви і продукти**: Traditional Ukrainian dishes — systematic vocabulary: Перші страви (soups): борщ (the quintessential Ukrainian soup, varieties: червоний, зелений, холодний), юшка (fish soup or light broth), капусняк (cabbage soup), розсольник (pickle soup). Другі страви (main courses): вареники (filled dumplings — з картоплею, з сиром, з вишнями), деруни (potato pancakes), голубці (stuffed cabbage rolls), галушки (dumplings served in broth or with sauce).; More dishes and sides: пампушки (garlic bread rolls, served with борщ), млинці (thin crepes — з м'ясом, з сиром, з варенням), каша (porridge — гречана, пшенична, вівсяна), сало (cured pork fat — iconic Ukrainian product). Напої: узвар (dried fruit compote — traditional Christmas drink), компот (fruit drink), кисіль (starchy fruit drink).; Food categories and ingredients: м'ясо (meat), риба (fish), овочі (vegetables), фрукти (fruit), крупи (grains), молочне (dairy), спеції (spices). Key ingredients: картопля (potatoes), цибуля (onion), часник (garlic), буряк (beetroot), капуста (cabbage), сметана (sour cream — essential condiment).
- **У ресторані: замовлення і спілкування**: Restaurant vocabulary: ресторан (restaurant), кафе (café, невідм.), їдальня (cafeteria/canteen), меню (menu, невідм.), офіціант/офіціантка (waiter/waitress), замовлення (order), рахунок (bill/check), чайові (tip — plural noun), порція (portion), гарнір (side dish), закуска (appetizer/starter).; Ordering patterns — natural Ukrainian (grounded in situational speech, Литвінова Grade 7 p.205 register model): Polite request: Принесіть, будь ласка, борщ із пампушками. Conditional: Я б хотів/хотіла замовити... Question: Що ви порадите? Що є сьогодні на перше/друге/десерт? Specification: Мені, будь ласка, вареники з картоплею та сметаною.; Genitive partitive in food context (Заболотний Grade 8 p.22 — genitive functions): After quantity words: тарілка борщу (gen), склянка узвару (gen), шматок хліба (gen), ложка меду (gen), порція вареників (gen pl). Partitive genitive: Дайте хліба (gen). Покладіть сметани (gen). Налийте узвару (gen). This is natural Ukrainian — the genitive expresses 'some of.'
- **Відмінки в контексті їжі**: Noun subclass forms in food vocabulary — morphophonemic review: Masculine nouns in genitive: борщу (not *борща — partitive -у for uncountable/mass nouns), узвару, хліба, меду (partitive -у), сиру. But: вареника (gen sg, countable), деруна (gen sg, countable). Rule review: -у/-ю for abstract, mass, uncountable; -а/-я for countable, concrete (Заболотний Grade 6 p.47).; Instrumental case with food: з + instrumental for accompaniments and ingredients: борщ із пампушками (f pl, instr), вареники з картоплею (f, instr), млинці з м'ясом (n, instr), кава з молоком (n, instr), чай із цукром (m, instr). Note alternation із/з depending on following consonant.; Accusative for ordering (direct object): Замовлю борщ (m, acc=nom), візьму каву (f, acc), принесіть салат (m, acc=nom). For feminine nouns: замовити каву (acc -у), порцію (acc -ю), закуску (acc -у). Practice distinguishing accusative from genitive partitive: Дайте каву (acc, specific) vs Дайте кави (gen, partitive — some coffee).
- **Підсумок: їжа і мова**: Vocabulary summary organized by category: страви (борщ, вареники, деруни, галушки, голубці, пампушки, млинці), продукти (м'ясо, риба, овочі, крупи, молочне), смак (смачний, гострий, солоний, кислий, солодкий), приготування (варений, смажений, запечений, тушкований), ресторан (меню, офіціант, замовлення, рахунок, чайові).; Cultural note: Ukrainian food culture — their їжа is deeply tied to identity. Борщ is UNESCO Intangible Cultural Heritage of Ukraine (inscribed 2022 during the full-scale invasion as an emergency safeguarding measure). Вареники, пампушки, and деруни are regional markers. Food is communal — 'Просимо до столу!' is an invitation to belonging.; Case summary table for food nouns: борщ — борщу (gen part), борщ (acc), борщем (instr). вареники — вареників (gen pl), вареники (acc pl), з варениками (instr pl). кава — кави (gen part), каву (acc), з кавою (instr). сметана — сметани (gen part), сметану (acc), зі сметаною (instr).

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
