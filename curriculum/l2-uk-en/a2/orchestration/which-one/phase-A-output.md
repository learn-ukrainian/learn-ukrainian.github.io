✅ Message sent to Gemini (ID: 14726) [auto-acked: self-addressed]
✓ Message 14726 acknowledged
   Pre-acknowledged (orchestration mode — won't appear in Gemini inbox)

🚀 Invoking Gemini to process message #14726...
📨 Message #14726
   From: gemini → To: gemini
   Type: query
   Task: v3-which-one-pA
   Time: 2026-02-23T02:55:09.292972+00:00

============================================================

Activate skill full-rebuild-core-a. Read and execute the instructions at /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/orchestration/which-one/phase-A-prompt.md

============================================================
📎 Attached Data:
{"to_model": "gemini-3-pro-preview"}

🤖 Processing with Gemini (gemini-3-pro-preview) [sync, 15 min timeout]...
===RESEARCH_START===

# Дослідження: Which One?

## State Standard Reference
§4.4.3 (B1 syntax bridge): "складнопідрядне речення з підрядною означальною частиною (сполучні слова який (яка, яке, які) у називному та непрямих відмінках)"
Alignment: While A2 §4.4.2 covers basic complex sentences, this module acts as a critical bridge to B1 syntax requirements (§4.4.3) by introducing relative clauses with «який» as a descriptive tool.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| який (masc) | Top 20 | який це?, той, який... |
| яка (fem) | Top 50 | яка різниця?, дівчина, яка... |
| яке (neut) | Top 100 | яке сьогодні число? |
| які (pl) | Top 100 | люди, які..., які плани? |
| той | Top 200 | той самий, той, хто... |

## Cultural Hooks
1. Folk wisdom: «Який пан, такий жупан» (Like master, like coat) — perfectly illustrates how adjectives/relative pronouns must match their noun.
2. Naming logic: «Як ви човен назвете, так він і попливе» (As you name the boat, so it shall float).
3. The Selection Culture: Navigating a Ukrainian «ринок» (market) where precision and the question «Який?» («Який вам зважити?») are constant.

## Common Learner Errors
1. Using «хто» for people instead of «який» → «Чоловік, який живе тут» (Correct) vs. «Чоловік, хто живе тут» (Incorrect). In Ukrainian, «який» must be used as the relative pronoun to modify a noun, even if it's a person.
2. Case Mismatch → Assuming «який» takes the case of the main sentence noun. It actually takes the case of its function *inside* the relative clause (The "Chameleon" rule).
3. Missing Commas → Failing to use a comma before «який». Ukrainian relative clauses almost always require a preceding comma, unlike English restrictive clauses.

## Cross-References
- Builds on: Basic adjectives, A2 basic complex sentences (що, тому що).
- Prepares for: B1 full relative clauses, participles, and advanced syntactic structures.

## Notes for Content Writing
- **Decolonized Framing**: Present the "mirror" (gender/number agreement) and "chameleon" (case selection) rules as inherent logic of Ukrainian grammar. Do not compare it negatively or positively to Russian. 
- **Immersion Band 2**: This is A2 M32. Apply Band 2 immersion (60-75%). Use English *only* for the abstract grammatical rules (explaining how case works inside a clause). Use Ukrainian for section intros, examples, and market scenarios.
- **Word Target**: Expand practice and presentation significantly to reach the 3000-word target.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ: Опис за межами прикметників"
    words: 450
    points:
      - "Note Band 2 Immersion: Use English briefly to introduce the abstract concept of relative clauses, but write the rest of the intro in Ukrainian."
      - "Introduce the power of complex sentences to describe people and things, framing it as a transition from simple adjectives."
      - "Introduce the idiom «Який пан, такий жупан» to illustrate agreement in gender and number."
      - "Present the 'Mirror' analogy: «який» reflects the gender and number of its antecedent noun."
  - section: "Презентація: Відмінювання та узгодження"
    words: 900
    points:
      - "Create a comprehensive table of Nominative forms (який, яка, яке, які) with multiple Ukrainian examples."
      - "Explain 'The Case Detective' rule using English scaffolding: the case of «який» is determined by its role inside the relative clause, not the main sentence."
      - "Detail the Accusative forms, focusing on «якого» (masc/anim) and «яку» (fem) for object clauses."
      - "Provide scaffolded examples moving from Nominative subjects (e.g., «чоловік, який стоїть») to Accusative objects (e.g., «чоловік, якого я знаю»)."
  - section: "Культурний контекст та вибір"
    words: 600
    points:
      - "Describe the 'Selection' culture at a Ukrainian market (ринок) primarily in Ukrainian."
      - "Include market interaction phrases like «Який вам зважити?» and «Які помідори найсолодші?» with rich descriptive context."
      - "Discuss the logic of naming with the idiom «Як ви човен назвете, так він і попливе»."
  - section: "Практика та типові помилки"
    words: 700
    points:
      - "Explicitly correct the common learner error of using «хто» instead of «який» for people."
      - "Explain the mandatory comma rule for Ukrainian relative clauses."
      - "Provide sentence transformation drills (e.g., combining two simple sentences into one complex sentence)."
      - "Include 'Chameleon' drills to practice case selection for the relative pronoun based on its internal clause function."
  - section: "Діалоги та підсумок"
    words: 500
    points:
      - "Write a detailed 'Witness Interview' dialogue in Ukrainian using varied forms of «який» to describe people or lost items."
      - "Write a 'Shopping' scenario focusing on specifying preferences («Мені подобається той, який...»)."
      - "Provide a final synthesis summarizing the 'mirror' (gender/number) and 'chameleon' (case) rules."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Full Phase A
**Friction Type**: TOOL_REDUNDANCY / STATE_STANDARD_NOT_FOUND
**Raw Error**: The built-in `grep_search` failed with an internal `--threads` error. Also, the A2 State Standard mapping for `який` points to line 1403-1416, but the actual relative pronoun `який` is formalized in the B1 section (§4.4.3).
**Self-Correction**: Used `run_shell_command` with `rg` to bypass the tool error. Referenced the B1 syntax standard as this module acts as a bridge from A2 to B1.
**Proposed Tooling Fix**: Fix the internal `grep_search` `--threads` bug, and consider updating the A2 mapping to explicitly note that relative clauses bridge into the B1 standard.
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (5869 chars)
✅ Message sent to Claude (ID: 14727)
✓ Message 14727 acknowledged
   Auto-acknowledged reply #14727 (stdout delivery — no inbox accumulation)
✓ Message 14726 acknowledged
