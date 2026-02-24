===RESEARCH_START===
# Дослідження: Scheduling Appointments

## State Standard Reference
§1.1.2.1.1: "особисті повідомлення та повідомлення на автовідповідачі, зокрема про запрошення, про місце зустрічі, зміну часу зустрічі чи її скасування"
Alignment: This module directly fulfills the requirement to comprehend and produce messages regarding invitations, meeting locations, and changing or canceling appointment times.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| записатися | High (Services) | записатися на прийом, записатися до лікаря |
| домовитися | High (Social/Biz) | домовитися про зустріч, домовитися про час |
| скасувати | Medium (Formal) | скасувати запис, скасувати зустріч |
| перенести | High (Admin) | перенести на завтра, перенести на іншу годину |
| вільний | High (General) | вільне місце, вільний час, ви вільні? |

## Cultural Hooks
1. **The "Academic Quarter" (академічна чверть):** A 15-minute grace period socially accepted for casual meetups, inherited from university culture, but strictly avoided for doctor's appointments or business meetings.
2. **Messenger Dominance:** Ukrainians heavily favor Viber and Telegram over voice calls or SMS for booking services. Confirming an appointment usually involves the business saying "Напишіть нам у Вайбер" or sending automated messenger confirmations.

## Common Learner Errors
1. **Time Prepositions:** Confusing «на котру?» (for what time/deadline - Accusative) with «о котрій?» (at what time - Locative). Learners often incorrectly say "Я прийду на п'яту" when they mean "at 5:00" (о п'ятій).
2. **Verb Contrast:** Using «зустріти» (to physically meet/greet someone arriving, e.g., at a station) instead of «зустрітися з» (to meet up with someone for an appointment or hangout).
3. **The "Half Past" Logic:** Misinterpreting «пів на четверту» as 4:30 instead of 3:30. Learners must understand it structurally means "halfway to the fourth hour".

## Cross-References
- Builds on: a2-62 (Rental Accommodation)
- Prepares for: a2-64 (Scheduling Interviews), a2-59 (Medical Care)

## Notes for Content Writing
- **Immersion Band 3 (75-90%):** English is restricted to brief clarifications and vocabulary translation columns. All prose, dialogues, and practice instructions must be in Ukrainian. Explicitly state English scaffolding limits in the intro.
- **Decolonized Framing:** Do not explain the 24-hour clock or "half past" logic by comparing it to Russian. Present the Ukrainian system independently as the standard European model or contrast it with the 12-hour AM/PM system.
- **IPA Annotations:** Only provide IPA for the *first* occurrence of new words. Do not annotate full sentences. Follow the strict vowel mapping (о = [ɔ], е = [ɛ]).
===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - section: "Вступ"
    words: 450
    points:
      - "Explicitly note the high-immersion environment for this module: explanations will primarily be in Ukrainian."
      - "Introduce the 'Academic Quarter' (академічна чверть) cultural hook: contrast social lateness with strict business/medical punctuality."
      - "Explain the dominance of Viber/Telegram for booking appointments ('Check your Viber' as a standard confirmation)."
      - "Clarify the use of the 24-hour clock for official schedules vs. the 12-hour clock for casual conversation."
  - section: "Презентація"
    words: 800
    points:
      - "Define and clearly contrast «записатися на...» (booking a service) with «домовитися про зустріч» (arranging a social meeting)."
      - "Provide a formatted table of key collocations: записатися на прийом, на стрижку, до лікаря."
      - "Explain the 'Half Past' logic (e.g., «пів на четверту» = 3:30) with clear visual breakdowns to prevent chronological errors."
      - "Present standard polite phrases and etiquette for opening and closing a scheduling message or call."
  - section: "Практика"
    words: 650
    points:
      - "Provide targeted drills distinguishing «о котрій?» (Locative) and «на котру?» (Accusative) with contrastive examples."
      - "Create an immersion exercise mimicking a Ukrainian booking app interface (using terms like календар, вільне місце, підтвердити)."
      - "Include a specific practice section contrasting the usage of «зустріти» and «зустрітися з»."
  - section: "Діалоги"
    words: 600
    points:
      - "Model a formal scenario: scheduling a doctor's appointment using the 24-hour clock and asking for 'вільні місця'."
      - "Model an informal scenario: rescheduling a coffee meetup via messenger, using 'перенести' and referencing the 'academic quarter'."
      - "Ensure both dialogues naturally demonstrate State Standard §1.1.2.1.1 competencies (inviting, changing, canceling)."
  - section: "Розповідь"
    words: 350
    points:
      - "Write a cohesive narrative about a character juggling multiple appointments (e.g., a haircut and a business meeting)."
      - "Integrate the 'half past' logic naturally into the story's timeline to test comprehension."
      - "Include realistic vocabulary for confirming via messenger and having to reschedule ('перенести на іншу годину')."
  - section: "Підсумок"
    words: 150
    points:
      - "Recap the essential collocations for scheduling, rescheduling, and canceling."
      - "Summarize the critical grammatical rule regarding Locative vs. Accusative for time."
      - "Provide a brief self-assessment checklist based on §1.1.2.1.1 (Can I make, change, and cancel an appointment?)."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: Searching for State Standard mapping reference
**Friction Type**: TOOL_BUG / TOOL_REDUNDANCY
**Raw Error**: Error during grep search operation: Process exited with code 2: error: The argument '--threads <NUM>' requires 1 values, but 2 were provided
**Self-Correction**: Bypassed the broken `grep_search` system tool and used `run_shell_command` with `rg` (ripgrep) and `sed` to successfully extract and search the specific lines within the A2 range of the State Standard document, as recommended by the project's GEMINI.md guidelines.
**Proposed Tooling Fix**: The MCP or Python bridge injecting the duplicate `--threads` flag into the `grep_search` tool needs to be fixed.
===FRICTION_END===
