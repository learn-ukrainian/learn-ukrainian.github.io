===RESEARCH_START===

# Дослідження: At the Market

## State Standard Reference
§3.8: "Купівля (закупи): магазини і ринки; споживчі товари (овочі, фрукти, м’ясо і молочні продукти, хліб, яйця)... одиниці ваги й об’єму; гроші."
§4.2.3.2.1: "Знахідний відмінок... Без прийменника (об’єкт дії)"
Alignment: The module perfectly aligns with the A1 thematic requirement to cover "Purchasing", specifically markets, consumer goods (fruits, vegetables), units of weight, and money. It practically applies the Accusative case for direct objects when making polite requests ("Дайте...").

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ринок | High (Daily life) | на ринку, піти на ринок, базар (colloquial) |
| кілограм | High (Commerce) | один кілограм, два кілограми, пів кілограма |
| свіжий | High (Food) | свіжі овочі, свіжі фрукти, тільки з грядки |
| штука | Medium (Commerce) | одна штука, поштучно |
| скільки | Core interrogative| скільки коштує?, скільки з мене? |
| здача | Medium (Commerce) | без здачі, візьміть здачу |

## Cultural Hooks
1. **Odesa's Pryvoz (Привоз)**: Established in 1827, it is legendary for its vibrant atmosphere, unique humor, and the cultural expectation of tasting food and bargaining. It epitomizes the authentic Ukrainian "bazar" experience.
2. **Kyiv's Bessarabskyi Market (Бессарабський ринок)**: Built in 1912 in early modern style, it was the first indoor market in Kyiv to feature modern refrigeration. It remains an iconic, premium marketplace in the capital.
3. **The tradition of "Спробуйте!" (Try it!)**: In Ukrainian markets, vendors actively encourage buyers to taste their products (cheese, fruit, honey) to prove quality and establish trust.

## Common Learner Errors
1. **Case after quantity** → *Кілограм картопля* (wrong) vs *Кілограм картоплі* (correct) — Learners default to Nominative instead of Genitive after units of measurement.
2. **Number agreement** → *Два кілограм* (wrong) vs *Два кілограми* (correct) — Learners forget to decline the unit of measurement after numbers 2-4.
3. **False friends/Synonyms** → Confusing *здача* (change in money) with *решта* (the rest of something).

## Cross-References
- Builds on: a1-18 (Food and Shopping), a1-53 (At the Restaurant)
- Prepares for: a1-61 (At the Store)

## Notes for Content Writing
- **Decolonized framing**: Emphasize the distinct nature of the Ukrainian *bazar* as a social hub. Highlight local markets (Pryvoz, Bessarabka) on their own terms without comparative references to Russian equivalents. Avoid any Russianisms in vocabulary.
- **Scaffolding**: As an A1 module, English scaffolding is mandatory for grammatical concepts (like the "кілограм + noun" chunk) and explaining the cultural nuances of the market.
- **Tone**: Adopt a Patient & Supportive Ukrainian Tutor persona. Build a "Safe Harbor" by presenting "кілограм + noun" as a simple vocabulary chunk rather than an intimidating grammar table.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ та культура"
    words: 500
    points:
      - "Introduce the vibrant culture of the Ukrainian market (базар). Contrast it with supermarkets, focusing on fresh (свіжий), homemade (домашній) products, and social interaction. Use English scaffolding for cultural concepts."
      - "Cultural Spotlight: Odesa's legendary Pryvoz (Привоз, 1827) and its humor, and Kyiv's historic Bessarabskyi Market (Бессарабський ринок, 1912)."
      - "Explain the tradition of «Спробуйте!» (Try it!): the importance of tasting goods before buying to build trust with the vendor."
  - section: "Презентація лексики та граматики"
    words: 600
    points:
      - "Introduce essential vocabulary: кілограм, грам, штука, пучок, овочі, фрукти. Use tables with English translations and IPA for first occurrences."
      - "Grammar Lite: Teach the «кілограм + родовий відмінок» pattern as a lexical chunk (e.g., «кілограм картоплі», «кілограм яблук»). Do not dive into deep Genitive theory."
      - "Essential phrases: Polite requests («Дайте, будь ласка», «Можна...») and asking about price («Скільки коштує?», «Скільки з мене?»)."
  - section: "Мовні помилки та практика"
    words: 400
    points:
      - "Address quantity errors: Explicitly contrast «Кілограм картопля» (wrong) with «Кілограм картоплі» (correct)."
      - "Address number agreement errors: Explain the difference between «Два кілограми» (Nom.Pl for 2-4) and «П'ять кілограмів» (Gen.Pl for 5+)."
      - "Clarify vocabulary nuance: Teach the difference between «здача» (change) and «решта» (the rest), focusing on «без здачі» and «візьміть здачу»."
  - section: "Діалоги та рольові ігри"
    words: 500
    points:
      - "Mini-dialogue 1: Buying vegetables by weight. Demonstrate polite requests, asking for «кілограм помідорів», and finding out the total price."
      - "Mini-dialogue 2: A lively scenario at Pryvoz. Buying fruit, tasting it («Можна спробувати?»), and practicing light bargaining («А дешевше можна?»)."
      - "Interactive Roleplay: Provide a guided scenario for learners to practice being the buyer, using all learned units of measurement and polite phrases."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Search file content for State Standard references
**Friction Type**: TOOL_ERROR
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Shifted from `grep_search` tool to `run_shell_command` utilizing `rg` as directed by project context workarounds.
**Proposed Tooling Fix**: Fix the `grep_search` tool to correctly handle the `--threads` argument or remove duplicate thread flags being injected.
===FRICTION_END===
