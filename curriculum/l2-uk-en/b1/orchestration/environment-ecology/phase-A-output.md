===RESEARCH_START===

# Дослідження: Довкілля та екологія

## State Standard Reference
§4.4.3: "складнопідрядні речення з підрядною частиною причини (сполучники тому що, бо, через те що): Віктор не був на лекції, тому що він захворів"
§3.14: "Природне середовище: погода, пори року, клімат; рослини; деякі види свійських тварин, дикі тварини; природні об’єкти (ліс, озеро, річка, гори, море)."
Alignment: The module introduces essential thematic vocabulary from §3.14 (nature, geographic objects, flora, fauna) and integrates it with §4.4.3 causal clauses to explain environmental issues and their consequences.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| довкілля | High, modern usage | захист довкілля, збереження довкілля |
| забруднення | High | забруднення повітря, забруднення води (Genitive mandatory) |
| відходи | Medium/High | побутові відходи, сортування відходів |
| переробка | Standard term | вторинна переробка (prefer over ресайклінг) |
| сміття | High | сортування сміття, викидати сміття |
| викиди | Specific/High in media | викиди газів, промислові викиди |

## Cultural Hooks
1. **Rekava Startup**: A Lviv-based company producing 100% biodegradable and compostable cups made from spent coffee grounds, showcasing modern Ukrainian «еко-свідомість» (eco-consciousness) and circular economy.
2. **The 7% Problem**: Landfills and waste dumps occupy approximately 7% of Ukraine's territory (roughly the size of Denmark), emphasizing the urgent need for recycling infrastructure, which currently handles a critically low percentage of waste.

## Common Learner Errors
1. **Anglicisms**: Defaulting to «ресайклінг» instead of the native Ukrainian «переробка» or «вторинна переробка».
2. **Case Errors**: Failing to use the Genitive case after verbal nouns like «забруднення» (saying *забруднення вода* instead of *забруднення води*).
3. **Semantic Confusion**: Using «природа» (the natural world) interchangeably with «довкілля» (the surrounding environment, which includes urban spaces). Using the formal «навколишнє середовище» in everyday speech.

## Cross-References
- Builds on: b1-61 (Professional Communication)
- Prepares for: b1-63 (Health Wellness)

## Notes for Content Writing
- Ensure 100% Ukrainian immersion for all prose, explanations, and instructions (B1.6 requirement).
- Frame Ukraine actively — Ukrainians solving problems (e.g., Rekava), not just victims of ecological disasters.
- Treat the Carpathians as a recurring setting to organically integrate §3.14 vocabulary (ліс, озеро, гори).
- Emphasize the semantic distinction between довкілля and природа clearly before moving to grammar.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ"
    words: 600
    points:
      - "Introduce the modern Ukrainian concept of «еко-свідомість» (eco-consciousness) using the cultural hook of 'Rekava', the Lviv startup producing biodegradable coffee cups."
      - "Detail the critical '7% Problem', explaining that landfills cover an area of Ukraine the size of Denmark, creating a massive ecological threat."
      - "Establish the thematic setting of the Carpathians, framing them as the «легені Європи» (lungs of Europe) to highlight the importance of conservation."
  - section: "Словник та поняття"
    words: 1000
    points:
      - "Clarify the semantic differences between the natural «довкілля» (environment), the formal «навколишнє середовище», and «природа» (the natural world)."
      - "Integrate State Standard §3.14 vocabulary: list and provide examples for natural geographic objects (ліс, озеро, річка, гори) within the Carpathian context."
      - "Teach the grammatical requirement of the Genitive case with verbal nouns. Drill collocations: «забруднення повітря», «забруднення води», «забруднення ґрунту»."
      - "Introduce waste management terms: «відходи», «сміття», and strongly recommend the native «вторинна переробка» over the borrowed «ресайклінг»."
  - section: "Природа України: Карпати"
    words: 1000
    points:
      - "Provide a descriptive reading focus on the Carpathian ecosystem, featuring Lake Synevyr (the largest) and Lake Brebeneskul (the highest)."
      - "Discuss the severe ecological threat of «вирубка лісів» (deforestation) in the mountains and its direct impact on regional climate and flooding."
      - "Detail the local biodiversity within the Carpathian Biosphere Reserve, incorporating State Standard §3.14 terms for flora and wild animals (дикі тварини)."
  - section: "Причина і наслідок"
    words: 800
    points:
      - "Introduce State Standard §4.4.3 grammar: complex sentences using causal conjunctions «тому що», «через те що», and «бо»."
      - "Provide syntactic models explaining ecological issues: e.g., 'Ліси зникають через те, що...' or 'Ми сортуємо сміття, бо це важливо'."
      - "Map problem-to-solution vocabulary chains: link «викиди газів» to «глобальне потепління», and propose «відновлювана енергія» as the remedy."
  - section: "Практика та підсумок"
    words: 600
    points:
      - "Write a dialogue between a Carpathian ecologist and a tourist discussing actionable steps to preserve the «крихка екосистема» (fragile ecosystem)."
      - "Simulate an 'eco-tips' poster (Еко-поради) that uses imperative or infinitive forms to encourage saving water and reducing plastic use."
      - "Summarize the core vocabulary distinctions and reiterate the importance of individual contribution to the «захист довкілля»."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Searching for State Standard 3.14 requirements.
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Manually read the `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` file via `read_file` with targeted offsets instead of relying on the broken `grep_search` tool wrapper.
**Proposed Tooling Fix**: Fix the `grep_search` internal tool definition that injects a duplicate or malformed `--threads` argument into the `rg` underlying command.
===FRICTION_END===
