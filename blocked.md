# Blocked: Live slovnyk.me Re-Enrichment

## Status
- **HTTP Status Code**: `403 Forbidden`
- **Security Provider**: Cloudflare (`Cf-Mitigated: challenge`, `Server: cloudflare`, `Title: Just a moment...`)
- **Impact**: Live lookup requests to `slovnyk.me` (`newsum` / СУМ-20 and `vts` / ВТС) cannot proceed from this host because all incoming HTTP requests trigger a Cloudflare challenge.
- **Pointer Status**: Pointer is NOT updated; reverted to canonical GitHub release `9e4acef7890d` (#7349).

## Sample URLs Tested
- `https://slovnyk.me/dict/newsum/%D0%B0%D0%B1%D0%BE%D0%BD%D0%B5%D0%BD%D1%82` (`абонент` - newsum) -> HTTP 403
- `https://slovnyk.me/dict/vts/%D0%B0%D0%B1%D0%BE%D0%BD%D0%B5%D0%BD%D1%82` (`абонент` - vts) -> HTTP 403
- `https://slovnyk.me/dict/newsum/%D0%B2%D0%BE%D0%B4%D0%B0` (`вода` - newsum) -> HTTP 403
- `https://slovnyk.me/dict/vts/%D0%B2%D0%BE%D0%B4%D0%B0` (`вода` - vts) -> HTTP 403
- `https://slovnyk.me/` -> HTTP 403

## Response Headers & Signature
- `Server`: `cloudflare`
- `Cf-Mitigated`: `challenge`
- `Content-Type`: `text/html; charset=UTF-8`
- `Body Title`: `<title>Just a moment...</title>`

## Census on Easy Slugs (1,696 lemmas)
- `sum20` cards: 0 (or 2 pre-cached)
- `vts` cards: 0 (or 2 pre-cached)
- `poc_thin_pages`: 5,740
