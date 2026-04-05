Now I have enough data to compile the full review.

---

## Linguistic Scan

**Russianisms:** None found. All key vocabulary verified against VESUM (737/737 content words confirmed).

**Surzhyk:** None found.

**Calques:**
1. **"старі друзі" / "старі університетські друзі"** — Антоненко-Давидович (ad-114, "Старий і давній") explicitly states: when referring to long-standing friendship (not the physical age of people), the correct word is **давні**, not **старі**. "Ми з вами — старі приятелі" is a calque from Russian "старые друзья". The module uses this twice: "мої вірні старі **друзі** чекають на вулиці" and "старі університетські **друзі**". Both should use **давні**.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case errors:** None found. All plural forms verified correct: сестра→сестри, земля→землі, стіл→столи, місто→міста, ніч→ночі, сіль→солі (confirmed VESUM), мати→матері, курча→курчата, людина→люди, дитина→діти, око→очі, вухо→вуха, плече→плечі (confirmed VESUM).

**Factual claims about grammar:** All checked rules are correct. The animate/inanimate Accusative plural rule is stated accurately. Consonant alternation друг→друзі (г→з) is correct.

## Exercise Check

**Marker inventory (4 markers):**
1. `<!-- INJECT_ACTIVITY: nominative-plural-fill -->` — after Section 1 (Nominative Plural) ✓ placement correct, matches plan hint #1 (fill-in)
2. `<!-- INJECT_ACTIVITY: accusative-animate-sort -->` — after Section 2 (Accusative Plural) ✓ placement correct, matches plan hint #2 (group-sort)
3. `<!-- INJECT_ACTIVITY: accusative-plural-quiz -->` — after Section 2 ✓ placement correct, matches plan hint #3 (quiz)
4. `<!-- INJECT_ACTIVITY: nominative-accusative-context -->` — after Section 3 ✓ placement correct, but **name suggests context-identification, not error-correction** as plan hint #4 specifies

**Issues:**
- **Marker #4 mismatch:** Plan specifies `error-correction` type ("Find and fix wrong plural noun endings, e.g., *дітей грають → діти грають, *бачу студенти → студентів"). The marker `nominative-accusative-context` suggests a context/comprehension exercise instead. The activity YAML generator will produce the wrong exercise type unless the marker name signals error-correction.
- Marker distribution: 1 after §1, 2 after §2, 1 after §3. Slightly front-loaded toward §2, but acceptable since that section covers both animate and inanimate.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Covers all 3 content_outline sections with correct structure. **Missing:** (a) рік→роки explicitly listed in plan §1 "Consonant alternations: друг → друзі, рік → роки" — module covers друг→друзі but omits рік→роки; (b) preposition "через" listed in plan §3 "через, на (direction), у/в (direction), про" — module covers на, у/в, про but omits через; (c) activity hint #4 is error-correction but marker name suggests context exercise. Vocabulary hints all present (множина, називний/знахідний відмінок, живий/неживий, закінчення, люди, діти, речі, очі ✓). Section word budgets reasonable (~650/650/700 plan vs actual distribution). |
| 2. Linguistic accuracy | 9/10 | All grammar rules stated correctly. All plural forms verified via VESUM. One calque: "старі друзі"/"старі університетські друзі" should be "давні" per Антоненко-Давидович (ad-114). No Russianisms, no Surzhyk, no Russian characters. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: intro dialogue situates the grammar → systematic presentation by відміна with 3+ examples each → practice in context paragraphs. Each declension class gets multiple contextualized examples (сестра→сестри, мама→мами, газети; стіл→столи, телефон→телефони, леви etc.). One minor weakness: "знання" used to illustrate -е/-я → -я pattern but знання is already -я in singular, showing no visible change — pedagogically confusing for learners. |
| 4. Vocabulary coverage | 9/10 | All 10 required vocab items present: множина, називний відмінок, знахідний відмінок, живий, неживий, закінчення, люди, діти, речі, очі — all used naturally in prose context. Recommended vocab: відміна ✓, чергування ✓, предмет ✓, група ✓. New words introduced in context sentences, never as bare lists. |
| 5. Exercise quality | 8/10 | 4 markers present for 4 plan hints. Placement is logical (after teaching, not before). However, marker #4 (`nominative-accusative-context`) doesn't match plan's error-correction type — this will generate the wrong activity type. Markers 1-3 match well. |
| 6. Engagement & tone | 9/10 | No motivational filler, no "magic of" language, no gamification. Prose is direct and instructional. Good cultural grounding (козак example, zoo setting, dinner party dialogue). One minor meta-phrase: "In Ukrainian, forming the plural is about understanding the declension class of the noun" in the intro — generic but brief. |
| 7. Structural integrity | 10/10 | All H2 headings from plan present and correctly ordered. Clean markdown. Word count 2105 vs target 2000 ✓. No stray tags, no duplicate summaries, no meta-commentary sections. Підсумок is concise and useful. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms. No "like Russian but..." framing. козак example is culturally appropriate. No decolonization issues. |
| 9. Dialogue & conversation quality | 9/10 | Zoo dialogue (intro): natural, named speakers (Батько/Дитина), demonstrates both Nom.Pl and Acc.Pl naturally, matches plan's dialogue situation exactly. Dinner party dialogue (§3, Олена/Андрій): natural multi-turn, named speakers, real situation (preparing for guests), mixes animate/inanimate Acc naturally. Q&A in Підсумок is functional. Minor: Олена/Андрій not in VESUM (proper nouns, expected — not an error). |

## Findings

**[PLAN ADHERENCE] [MAJOR]**
Location: Section 1, paragraph on II відміна consonant alternations: "Найвідоміший приклад — це слово друг… Слово козак має звичайне закінчення «-и»"
Issue: Plan explicitly lists "Consonant alternations: друг → друзі, рік → роки" but the module only covers друг→друзі. рік→роки is missing. This is a notable example because рік has stem vowel alternation (рік/рок-) that learners need to know.
Fix: Add a sentence about рік→роки after the друг→друзі paragraph.

**[PLAN ADHERENCE] [MAJOR]**
Location: Section 3, preposition paragraph: "We frequently use the short prepositions на… і у/в… Another important preposition is про."
Issue: Plan specifies "через, на (direction), у/в (direction), про" but "через" is completely absent from the module. Learners miss this common Accusative-governing preposition.
Fix: Add a sentence with "через" before the "про" paragraph.

**[LINGUISTIC ACCURACY] [MAJOR]**
Location: Section 1: "мої вірні старі **друзі** чекають на вулиці" and Section 3 dialogue: "старі університетські **друзі**"
Issue: Антоненко-Давидович (ad-114, "Старий і давній") explicitly corrects this: when referring to long-standing friendship, the correct word is "давні", not "старі". "Старі друзі" is a calque from Russian "старые друзья". In a module teaching Ukrainian plurals, this calque is particularly inappropriate.
Fix: Replace "старі" with "давні" in both instances.

**[EXERCISE QUALITY] [MAJOR]**
Location: `<!-- INJECT_ACTIVITY: nominative-accusative-context -->`
Issue: Plan's 4th activity hint specifies `error-correction` type ("Find and fix wrong plural noun endings, e.g., *дітей грають → діти грають, *бачу студенти → студентів"), but the marker name `nominative-accusative-context` signals a context/comprehension exercise. The YAML generator will produce the wrong activity type.
Fix: Rename the marker to `error-correction-plural-endings` to match the plan.

**[PEDAGOGICAL QUALITY] [MINOR]**
Location: Section 1, II відміна neuter soft stems: "Важливе знання допомагає жити. Наші глибокі знання зростають щодня."
Issue: "знання" is used to illustrate the -е/-я → -я plural pattern, but знання ends in -я in BOTH singular and plural (confirmed via VESUM: singular v_naz = знання, plural v_naz = знання). There is no visible ending change, making this a confusing example for the pattern being taught. поле→поля and море→моря already demonstrate the pattern well.
Fix: Replace знання example with a more visible alternation like завдання (which at least illustrates that -ння words keep their form, a useful observation) — or better, use питання/питання with a note that -ння/-ття neuter nouns keep the same nominative form in plural. Actually, the simplest fix is to replace with a word that shows the change, like серце→серця.

## Verdict: REVISE

The module is well-structured with accurate grammar rules, natural Ukrainian prose, and good pedagogical flow. However, it has 3 major plan adherence gaps (missing рік→роки, missing через, wrong activity type for marker #4) and 1 major linguistic issue (calque "старі друзі" caught by Антоненко-Давидович). These are fixable with targeted patches.

<fixes>
- find: "мої вірні старі **друзі** *(friends)* чекають на вулиці"
  replace: "мої вірні давні **друзі** *(friends)* чекають на вулиці"
- find: "старі університетські **друзі** *(friends)*"
  replace: "давні університетські **друзі** *(friends)*"
- find: "Слово **козак** *(Cossack)* має звичайне закінчення «-и», але ми кажемо **козаки** *(Cossacks)* без зміни приголосного."
  replace: "Цілий **рік** *(year)* ми працюємо, а потім згадуємо минулі **роки** *(years)*. Тут голосний у корені змінюється: рік → роки. Слово **козак** *(Cossack)* має звичайне закінчення «-и», але ми кажемо **козаки** *(Cossacks)* без зміни приголосного."
- find: "Another important preposition is **про** *(about)*."
  replace: "An important preposition is **через** *(through, because of)*. It always requires the Accusative case. Ми йдемо **через** широкі зелені **поля** *(fields)*. Він не прийшов **через** важливі робочі **справи** *(matters)*. Another important preposition is **про** *(about)*."
- find: "Важливе **знання** *(knowledge)* допомагає жити. Наші глибокі **знання** *(knowledge)* зростають щодня."
  replace: "Маленьке червоне **серце** *(heart)* б'ється швидко. Наші вдячні **серця** *(hearts)* завжди пам'ятають рідних."
- find: "<!-- INJECT_ACTIVITY: nominative-accusative-context -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction-plural-endings -->"
</fixes>
