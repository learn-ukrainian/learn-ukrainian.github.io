# [WITHDRAWN] uldr_v06_general_assistant

> **DO NOT USE FOR TRAINING**
>
> **Governing Issue:** [#8341](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8341) (replaces [#8139](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8139))
> **Parent Epic:** [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321)
> **Status:** **PERMANENTLY WITHDRAWN / SUPERSEDED**

## Reason for Withdrawal (Audited 2026-09-20)

1. **High Duplication**: The 75,000 generated lines contained only 4,220 distinct question–answer pairs; individual questions were duplicated up to 398 times under different ID numbers due to unconstrained cyclic sampling.
2. **Generic Boilerplate Answers**: Responses frequently provided generic advice ("use correct quotation marks", "avoid copied constructions") rather than genuine pedagogical explanations of the underlying school subjects (physics, biology, chemistry, history, etc.).
3. **Rights Record Missing**: Verbatim textbook passages were embedded without per-book rights determination.

## Successor

All active development and authentic school-subject data mining are relocated to the canonical component path:
- **Registry:** `registry/projects/open_model_data/components/textbooks/`
- **Data:** `data/projects/open_model_data/components/textbooks/`
- **Governing Engine:** `scripts/projects/open_model_data/v6_mine_general_assistant_textbooks.py` under Issue #8341.
