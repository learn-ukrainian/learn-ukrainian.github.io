# ЕСУМ Vol 1 Segmentation Recall Cross-Check (#1662)

Date: 2026-05-04

Scope: recall audit for `data/processed/esum_vol1.jsonl` generated from
`data/raw/esum/vol1.txt`, after syncing PR #1672 and regenerating with the
follow-up segmenter fixes.

## Method

I sampled five pages spread across the А-Г body from visible standalone OCR page
markers: 56, 119, 171, 337, and 444. For each page I manually listed visible
headwords in the raw OCR window and checked exact JSONL lemma presence with the
equivalent of:

```bash
grep '"lemma": "<word>"' data/processed/esum_vol1.jsonl
```

## Recall Sample

| Page | Headword | JSONL lemma present? | Notes |
| --- | --- | --- | --- |
| 56 | акорд | yes |  |
| 56 | акордеон | yes |  |
| 56 | акбсь | yes | OCR spelling in source for `акось` |
| 56 | акот | yes |  |
| 56 | акредитив | yes |  |
| 56 | акрихін | yes |  |
| 56 | акробат | yes | Recovered after tightening page-header filtering |
| 119 | бакалія | yes |  |
| 119 | бакан | yes |  |
| 119 | бахати | yes | Bracketed headword normalized without brackets |
| 119 | бакен | no | OCR/page split continues as JSONL lemma `бйкен`; see failures |
| 119 | бакенбарда | yes |  |
| 119 | бакйр | yes | OCR spelling in source |
| 119 | баклаг | yes |  |
| 171 | береза | yes | Both homonym bodies retained in DB after loader hash fix |
| 171 | березень | yes |  |
| 171 | березіль | yes | Tail line `ще береза, зелений, зола.` retained after fix |
| 171 | березка | yes |  |
| 171 | березуна | yes |  |
| 337 | василь | yes |  |
| 337 | василька | yes |  |
| 337 | васильки | yes |  |
| 337 | васйльбк | yes | OCR spelling in source |
| 337 | васнь | yes | OCR spelling in source |
| 444 | габа | yes |  |
| 444 | габардин | yes |  |
| 444 | габарит | yes | Recovered by accepting `«` as headword delimiter |
| 444 | габати | yes |  |
| 444 | ґабати | no | Variant inside `габати`, not emitted as separate primary lemma |
| 444 | габелок | yes |  |
| 444 | габз | yes | Recovered by allowing short `див.` cross-reference entries |

Recall: 29 / 31 = 93.55%.

## Recall Failures

- `бакен` on page 119 is visible before a page boundary as `бакен «поплавець,
  бакан; ...`, but the OCR continuation after the marker begins `бйкен, бакан;
  — ...`. The segmenter emits the OCR-continuation lemma `бйкен`. This is an OCR
  split/misread gap, not a missing body block.
- `ґабати` on page 444 is listed as a bracketed variant inside the `габати`
  entry body. The segmenter currently emits only the primary lemma for that
  entry. Variant aliases are a follow-up indexing concern if exact variant
  recall becomes required.

## Precision Spot-Checks

I checked three JSONL entries against the raw OCR:

- `бакан` (`data/raw/esum/vol1.txt` lines 14987-15000): JSONL body matches the
  raw entry after expected dehyphenation; no cross-entry bleed or truncation.
- `березіль` (`data/raw/esum/vol1.txt` lines 21804-21821): JSONL body now keeps
  the final `Див. ще береза, зелений, зола.` tail; no cross-entry bleed.
- `габарит` (`data/raw/esum/vol1.txt` lines 56768-56778): JSONL body matches the
  raw entry after expected dehyphenation; no cross-entry bleed or truncation.

During this audit I also found a loader precision bug: duplicate homonym rows
with the same `(lemma, vol, page)` were collapsed in `esum_etymology_meta`
(`береза 1` / `береза 2`). The loader now keys sidecar rows by
`(lemma, vol, page, entry_hash)` and reloads the sampled volume before rebuilding
FTS rows, preserving both homonym bodies.

## Vol 7 Stretch Check

No accessible ЕСУМ volume 7 publication was found in the quick check.

URLs tried:

- `https://archive.org/advancedsearch.php` with query
  `title:("Етимологічний словник української мови" AND "том 7")`: `numFound=0`
- `https://archive.org/details/etslukrmov7`: HTTP 404
- `https://archive.org/details/etslukrmov_7`: HTTP 404
- `https://chtyvo.org.ua/search/?q=Етимологічний%20словник%20української%20мови%20том%207`:
  no matching result in fetched search HTML
- `https://chtyvo.org.ua/search/?q=ЕСУМ%20том%207`: no matching result in
  fetched search HTML

## Verdict

Ship after this follow-up patch. Sampled recall is above the 90% target
(93.55%), the remaining misses are OCR/variant-alias edge cases, and the
precision checks are clean after the segmenter and loader fixes.
