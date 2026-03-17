===REVIEW_START===

```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 5 Guidelines > Immersion Target vs Audit Gates > Immersion"
      problem: >
        The Immersion Target section says "PARADIGM TABLES: Conjugation/declension tables
        with all cells Ukrainian. This is the highest-density immersion tool. Do not explain
        usage nuances in English prose — instead, create dual-column tables." But the same
        section later says "Tables contribute zero to immersion" and the Audit Gates confirm
        "Tables count ZERO for immersion." For a pronoun declension module, this is especially
        dangerous — Gemini will naturally build paradigm tables for all 4 cases and believe
        they are hitting immersion targets, when the audit strips them entirely. The instruction
        to "Move the teaching logic inside the tables" actively pushes Ukrainian content into
        a container that scores zero.
      suggested_fix: >
        Remove "This is the highest-density immersion tool" from the PARADIGM TABLES line.
        Add a warning: "NOTE: Tables count ZERO toward immersion score. For every paradigm
        table, include a matching dialogue or bulleted example list with the same forms so
        immersion is covered." Change "Move the teaching logic inside the tables" to
        "Use tables for reference, but duplicate key forms in dialogues and example lists
        that DO count toward immersion."
      severity: HIGH
```

The table/immersion contradiction is the only gate-failing issue. A pronoun declension module will naturally be table-heavy (4 case paradigms), so Gemini following the "highest-density immersion tool" instruction will almost certainly fail the immersion gate unless warned that tables score zero and compensating dialogues/examples are needed.

Everything else checks out — word targets are achievable, activity counts/types are feasible, vocab target (20) is reachable with 11 required + 4 recommended + 5 from content, and structure requirements are clear.

===REVIEW_END===