# A1 lessons

Learners open the A1 arc landing (`/a1/`), see modules grouped by phase with status badges, and open a module landing such as `/a1/sounds-letters-and-hello/`. An older “upgrade edition” sidebar contract still lives in `site/e2e/a1-lesson-nav.spec.ts` and no longer matches the arc landing DOM.

## Sub-features

- `a1-arc-landing` lists modules in arc order with links into `/a1/<slug>/`.
- `a1-module-landing` opens a module page with title and course chrome.
- `a1-nav-chrome` exposes A1 in the primary nav (`nav.a1`).
- `a1-upgrade-sidebar-contract` (legacy Playwright) expects `.lu-sidebar-nav` on `/a1/` — currently a product/spec drift against the arc landing.

## How to get to it (user POV)

- Choose A1 in site chrome (`/a1/`).
- Choose a module card (e.g. sounds-letters-and-hello, things-have-gender).
- Use “A1 previous” (`/a1-v1/`) only when checking the prior edition.

## Driving it with route smoke + Playwright

Preconditions:

- Preview is healthy (`doctor.sh` OK) at `$LU_VERIFY_BASE_URL`.
- Site built (`build:shell` is enough).

- **Arc landing modules.** Run `bash .cursor/skills/verify-learn-ukrainian/bin/drive-routes.sh`. Asserts HTTP 200 for `/a1/` containing `sounds-letters-and-hello` and `things-have-gender`, and `/a1/sounds-letters-and-hello/` title content.
- **Legacy sidebar contract (optional / expect red until rewritten).** Run `bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh lessons`. Spec `e2e/a1-lesson-nav.spec.ts` looks for `.lu-sidebar-nav` on `/a1/` — against the current arc landing this fails. Treat as contract debt, not as the primary green proof for lessons.
- **Proof (green path).** `$LU_VERIFY_EVIDENCE_DIR/route-__a1__.txt` and sibling route excerpts from `drive-routes.sh`; exit `0`.

## Gotchas

- `/a1/` is the arc landing (dozens of modules), not the bilingual upgrade sidebar the 2026 e2e file describes.
- Numbered lesson URLs like `/a1/things-have-gender/1/` may 404 when the module is still `planned` — prefer module landings that exist in `dist/`.
- Do not “fix” a red `a1-lesson-nav` by rewriting product code in a verification-skill PR; update the feature map / file a product issue, or wait for `/maintain-verification-skill`.
