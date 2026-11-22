# Practice

Learners open `/practice/`, pick a mode (flashcards, matching, cloze, …), and get a real round or a clear empty/prepared state — never an ambiguous "all done" dead-end for a fresh session.

## Sub-features

- `practice-home` loads `/practice/` and shows the mode grid.
- `practice-cloze` shows a cloze card or `[data-testid="practice-cloze-empty"]`, never a false completion.
- `practice-matching` renders at least three pairs (`[data-activity="match-left-tile"]`).
- `practice-mode-switch` starts a new mode without inheriting an unfinished session's UI.
- `practice-secondary-tools` keeps deck filters behind `[data-testid="practice-secondary-tools"]` disclosure.

## How to get to it (user POV)

- Choose Practice in site chrome (`/practice/`, nav key `nav.practice`).
- Deep-link with `?lemmaId=` (URL-encoded lemma).
- Enter from a word-card practice CTA when present.
- Open the secondary tools `<details>` to manage decks.

## Driving it with Playwright

Preconditions:

- Preview is healthy (`doctor.sh` OK).
- Practice shards/public lexicon JSON committed or hydrated (shell build uses committed public assets).

- **Cloze non-dead-end.** Run `bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh practice`. Spec clicks `button[data-mode="cloze"]` and expects `[data-testid="practice-cloze"]` or `[data-testid="practice-cloze-empty"]`.
- **Matching round.** Same drive: `button[data-mode="matching"]` → `[data-testid="practice-matching"]` with ≥3 left tiles.
- **Mode switch.** Matching → Home → flashcards shows `[data-activity="flashcard"]` and hides matching; progress contains `0/`.
- **Secondary tools.** Before deck chips, open `[data-testid="practice-secondary-tools"]` summary (helper `openSecondaryTools` in the spec).
- **Proof.** `$LU_VERIFY_EVIDENCE_DIR/playwright-practice.log` exit `0`.

## Gotchas

- Cloze may be empty until reviewed sentences exist — empty-with-message is green; silent "all done" is red.
- Mode snapshots can linger in the K3 dashboard; switching modes must not show the previous mode's widget.
- Deck UI is folded behind secondary tools — clicking deck controls without opening the disclosure flakes.
- Some practice tests route mock JSON; when grepping, prefer the unmocked learner-path tests for proof of the real build.
