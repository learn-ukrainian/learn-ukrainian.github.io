# Readings

Learners open the reading reference (`/readings/`), browse public-domain primary texts grouped by genre, and open one full text such as `/readings/shchedrivka-shchedryk-lastivochka/`.

## Sub-features

- `readings-landing` loads `/readings/` with search field `#readings-q` and at least one `[data-reading]` card.
- `readings-genre` groups those cards under `[data-genre-block]` headings.
- `readings-text` opens a published text and shows `.primary-reading-box` with that work's title.
- `readings-search` filters cards from `#readings-q` in the browser. A miss shows `[data-readings-empty]`.

## How to get to it (user POV)

- Choose Reading reference in site chrome (`/readings/`, nav key `nav.readings`).
- Choose the home card that links to `/readings/`.
- Open a genre card (`a.reading-card`) into `/readings/<id>/`.
- Follow a lesson link to a full text (for example the folk koliadky lesson link to `/readings/shchedrivka-shchedryk-lastivochka/`).

## Driving it with route smoke

Preconditions:

- Preview is healthy (`doctor.sh` OK). `source` the `env.sh` path launch printed, so `$LU_VERIFY_BASE_URL` and `$LU_VERIFY_EVIDENCE_DIR` are set.
- Site built with shell mode. Readings are committed under `site/src/content/readings/` and do not need a private database or an Atlas hydrate.

- **Open the library.** Run `code="$(curl -sS -o "$LU_VERIFY_EVIDENCE_DIR/route-_readings_.txt" -w '%{http_code}' --max-time 20 "$LU_VERIFY_BASE_URL/readings/")"; test "$code" = 200; grep -F -q 'id="readings-q"' "$LU_VERIFY_EVIDENCE_DIR/route-_readings_.txt"; grep -F -q 'data-reading' "$LU_VERIFY_EVIDENCE_DIR/route-_readings_.txt"; grep -F -q 'shchedrivka-shchedryk-lastivochka' "$LU_VERIFY_EVIDENCE_DIR/route-_readings_.txt"`. Observable: exit `0`.
- **Open one text.** Run `code="$(curl -sS -o "$LU_VERIFY_EVIDENCE_DIR/route-_readings_shchedrivka-shchedryk-lastivochka_.txt" -w '%{http_code}' --max-time 20 "$LU_VERIFY_BASE_URL/readings/shchedrivka-shchedryk-lastivochka/")"; test "$code" = 200; grep -F -q 'Щедрик, щедрик, щедрівочка' "$LU_VERIFY_EVIDENCE_DIR/route-_readings_shchedrivka-shchedryk-lastivochka_.txt"; grep -F -q 'primary-reading-box' "$LU_VERIFY_EVIDENCE_DIR/route-_readings_shchedrivka-shchedryk-lastivochka_.txt"`. Observable: exit `0`.
- **Filter the library.** Unmet precondition: no readings Playwright spec is mapped (`drive-playwright.sh` accepts only `lessons`, `atlas`, `practice`, and `all`). Record `SKIP` with that precondition. Landing HTML is not proof of typeahead.
- **Preview unavailable.** Unmet precondition: `$LU_VERIFY_BASE_URL` is unset, or `doctor.sh` is not OK. Record `SKIP` with that precondition. Do not start another server and do not report the route as driven.

## Gotchas

- `bin/drive-routes.sh` does not request `/readings/`. A green `drive-routes OK` is not readings proof.
- `drive-playwright.sh readings` is not a drive. Do not add a Playwright spec in the change that only extends this map.
- Entries with `published: false` or `canonical: false` are omitted. A 404 for such an id is expected; pick a published id from the landing HTML.
- Search does not change the URL. A static grep cannot prove a filtered count.
- Shell build is enough. Do not treat a missing Atlas release download as a readings failure.
