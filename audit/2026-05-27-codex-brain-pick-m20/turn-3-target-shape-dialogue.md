# Codex brain-pick on m20 — turn 3 (clean §Діалоги target shape)

**Session:** `019e6944-d4c8-7da0-853f-8676ddf526b0` (continued from turn 2)
**Bridge ID:** `bridge-9c48f477`
**Duration:** 85.0s
**When:** 2026-05-27 ~14:00 UTC

## The target shape — clean §Діалоги under the hardened pipeline

This is what `curriculum/l2-uk-en/a1/my-morning/module.md` §Діалоги SHOULD look like, written by codex under the constraints of the 6 in-flight `#R-` rules + rendered-lesson-pass + textbook_grounding split. Compare against the shipped version (current `module.md` lines 1-37) to see the salad → clean transformation.

```markdown
## Діалоги

<DialogueBox uk="Ліна: Доброго ранку, Настю!" en="Lina: Good morning, Nastia!" />
<DialogueBox uk="Настя: Доброго ранку, Ліно!" en="Nastia: Good morning, Lina!" />
<DialogueBox uk="Ліна: Коли ти прокидаєшся?" en="Lina: When do you wake up?" />
<DialogueBox uk="Настя: Я прокидаюся о сьомій." en="Nastia: I wake up at seven." />
<DialogueBox uk="Ліна: Що ти робиш потім?" en="Lina: What do you do next?" />
<DialogueBox uk="Настя: Вмиваюся, одягаюся і снідаю." en="Nastia: I wash, get dressed, and eat breakfast." />
<DialogueBox uk="Ліна: А коли ти йдеш на роботу?" en="Lina: And when do you go to work?" />
<DialogueBox uk="Настя: О восьмій." en="Nastia: At eight." />
<DialogueBox uk="Ліна: У суботу я не поспішаю." en="Lina: On Saturday I do not hurry." />
<DialogueBox uk="Настя: Я теж не поспішаю." en="Nastia: I do not hurry either." />
<DialogueBox uk="Ліна: Прокидаюся пізно." en="Lina: I wake up late." />
<DialogueBox uk="Ліна: Потім дивлюся телефон." en="Lina: Then I look at my phone." />
<DialogueBox uk="Настя: А я навчаюся вранці." en="Nastia: And I study in the morning." />
<DialogueBox uk="Настя: Потім гуляю." en="Nastia: Then I go for a walk." />
<DialogueBox uk="Ліна: Ти збираєшся швидко?" en="Lina: Do you get ready quickly?" />
<DialogueBox uk="Настя: Так, я збираюся швидко." en="Nastia: Yes, I get ready quickly." />

Your first morning pattern is simple: wake up, wash, get dressed, eat breakfast, go. In Ukrainian, many routine verbs use the reflexive ending **-ся**. Keep the ordinary present-tense ending, then add **-ся**: **Я прокидаюся о сьомій** means "I wake up at seven." The subject is **я**, the verb ending is **-ю**, and the reflexive ending is **-ся**.

| Pattern | Ukrainian form | English |
| --- | --- | --- |
| question | **Коли ти прокидаєшся?** | When do you wake up? |
| answer with time | **Я прокидаюся о сьомій.** | I wake up at seven. |
| short routine chain | **Вмиваюся, одягаюся і снідаю.** | I wash, get dressed, and eat breakfast. |
| leaving home | **Я йду на роботу.** | I go to work. |

Use the dialogue as a template for your own morning. Start with one time phrase, then add two or three short actions. You do not need long sentences yet: **Я прокидаюся о сьомій. Потім я вмиваюся. Після цього я снідаю. Нарешті я йду на роботу.** That is already a clear A1 morning story.

Use **сніданок** (breakfast) for the noun, not the Russian-influenced <!-- bad -->завтрак<!-- /bad -->. Use **снідати** (to eat breakfast) for the verb: **Я снідаю о восьмій.**

:::tip
**Noun vs verb:** **сніданок** names the meal. **снідати** names the action. Use the noun in a phrase like **мій сніданок** (my breakfast). Use the verb when a person does it: **Я снідаю.**
:::

<!-- INJECT_ACTIVITY: act-1 -->
```

## Rule-by-rule audit of the rewrite

| Rule | Verdict | Evidence |
|---|---|---|
| `#R-SINGLE-VOICE-A1` | ✅ | Consistent direct address: "Your first morning pattern", "you do not need", "Use the dialogue as a template for your own morning". No third-person "the student". No mid-section register shift. |
| `#R-AUDIENCE-LANGUAGE-A1` | ✅ | All explanation in English. Ukrainian appears only as target — DialogueBox content, inline target words (`сніданок`, `снідати`), table rows, model-sentence chains. No "Контролюй чистоту словника" style. |
| `#R-NO-CHILDREN-PRIMARY-QUOTES` | ✅ (vacuous in §Діалоги) | This section didn't have Grade 1 blockquotes in the shipped version either; the Grade 1 quotes were in §Дієслова на -ся and §Мій ранок. Real test of this rule comes when codex rewrites those sections. |
| `#R-NO-SCAFFOLDING-LEAKS` | ✅ | No `Крок N:`, no panel IDs, no obligation names, no gate-language. |
| `#R-GRAMMAR-TERMS-A1` | ✅ | "noun", "verb", "subject", "verb ending", "reflexive ending". Tip header: "**Noun vs verb:**". No "thing/action". |
| `#R-CLEAN-TABLES` | ✅ | Bold only on Ukrainian target forms. Pattern column + English column in regular weight. |

## Diff observations vs shipped m20

| Shipped m20 (salad) | Codex's clean rewrite (turn 3) |
|---|---|
| Line 20: "Two roommates give you a natural morning chain" (gimmicky intro) | "Your first morning pattern is simple: wake up, wash, get dressed, eat breakfast, go." (direct, learner-anchored) |
| Lines 30-31: Ukrainian metalanguage + preachy 3rd-person "занурює студента" | Replaced with the contrast pair + grammar tip |
| Line 35 tip: "сніданок is a thing; снідати is an action" | Tip: "**Noun vs verb:** сніданок names the meal. снідати names the action." (real grammar terms) |
| Line 18 dialogue: "Так, я готова швидко" (adjective predicate, weak chain with `збираєшся` two lines up) | "Так, я збираюся швидко" (cleaner reflexive parallel with the question) |
| 4-row table headed "Ukrainian chunk / English" (no organizing rationale) | 4-row table headed "Pattern / Ukrainian form / English" (the **rationale** is the new column) |

The shipped section was ~230 words of prose + 15 dialogue lines. The rewrite is ~190 words of prose + 16 dialogue lines (added `Так, я збираюся` parallel). Tighter without losing content.

## What this proves

1. **The 6 rules are sufficient for §Діалоги.** Codex (the same model class as the writer who produced the salad) can produce a clean section just from the rule set + the rendered-lesson-pass concept. No 7th rule needed for this section.
2. **The target shape exists and is checkable.** Phase 2a refire's §Діалоги should land within ±20% of this. Materially worse → hardening isn't strong enough.
3. **The harder test is §Дієслова на -ся and §Мій ранок** — those sections had the Grade 1 blockquotes and the `Крок 5:` leak. The textbook_grounding gate split (queued as task #11.1) is load-bearing for those sections to come out clean.

## Notes for orchestrator

- Save this section's hash so the Phase 2a refire output can be diffed against it: `sha256sum < <(rewrite-above) → <fill on save>`. Or just visual review — same shape, single voice, no Grade 1 quotes, clean tables.
- The rewrite preserved the existing bad-form contrast (`сніданок` not `завтрак`) and the wake-up-time pattern, so the wiki_coverage obligations still resolve. Codex didn't drop required content.
- The dialogue tweak (`Так, я збираюся швидко`) is a pedagogical improvement codex made on its own — reflexive parallel with the question two lines above. Phase 2a refire may or may not surface this; not a blocker.
