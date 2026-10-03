# «Український правопис» (2019): which text is official (#9610)

Step E3b of `docs/projects/open-model-data/PLAN.md`. This records which publication of the
2019 orthography we hold, why it is the official one, and how the stored copy is identified.
Register entry: `pravopys_2019` in [`permissions-register.yaml`](permissions-register.yaml).

## Choice

**The authorized edition: Український правопис. Київ: Наукова думка, 2019. 392 с.
ISBN 978-966-00-1728-3**, as distributed byte for byte by the Ministry of Education and
Science and by the Ukrainian Language-Information Fund of the National Academy of Sciences.

| Copy | URL | SHA-256 | Pages | Role |
| --- | --- | --- | --- | --- |
| ULIF (УМІФ НАН України, a co-holder of the copyright) | <https://www.ulif.org.ua/system/files/pravopus-new.pdf> | `0d2fd75a2e9b2a412d4c8e072f6a8cac06d075a297a770fd037312054b0e501a` | 392 | Ingested |
| Ministry of Education and Science | <https://mon.gov.ua/static-objects/mon/sites/1/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf> | `ff7548cacc63e96420d652e068ea6e6fb5d35f983117668f2e8c94571cc1beae` | 393 | Accepted alternative |

Both hashes are pinned in `scripts/wiki/pravopys_official.py` (`OFFICIAL_FILES`); the
ingest refuses any other file.

## Evidence that it is official

1. **Approval.** Cabinet of Ministers Resolution No. 437 of 22 May 2019 «Питання
   українського правопису» approves the new edition developed by the Ukrainian National
   Commission on Orthography: <https://zakon.rada.gov.ua/laws/show/437-2019-%D0%BF>. The
   resolution is printed on p. 3 of the book. It remains in force: the Sixth Administrative
   Court of Appeal overturned, on 11 May 2021, the January 2021 first-instance ruling that had
   annulled it ([Радіо Свобода, 11 May 2021](https://www.radiosvoboda.org/a/news-minjust-oask-pravopys/31249527.html);
   [Укрінформ](https://www.ukrinform.ua/rubric-society/3243221-novij-pravopis-zalisaetsa-sud-skasuvav-risenna-oask.html)).
2. **Authorized edition.** The imprint page (p. 2) of the PDF reads: «Українська національна
   комісія з питань правопису своїм рішенням від 12 липня 2019 р. визначила Видавництво
   «Наукова думка» НАН України установою, яка уповноважена випустити у світ авторизоване
   видання Українського правопису в редакції 2019 р.» It lists the approvals (Cabinet
   Resolution No. 437; joint resolution of the Presidium of the NAS of Ukraine and the Board
   of the Ministry, 24 October 2018; the Commission, protocol No. 5 of 22 October 2018) and
   the copyright of the Інститут мовознавства ім. О. О. Потебні, the Інститут української
   мови and the Український мовно-інформаційний фонд НАН України.
3. **The Ministry distributes this same edition.** mon.gov.ua answers scripted clients with
   a Cloudflare challenge (HTTP 403 on 2026-10-03), so the Ministry's file was taken from the
   Internet Archive: the CDX index lists HTTP 200 captures with SHA-1 digest
   `4F5ZQVQK7VKHORWJCFTK52VIHA4TIKSH` of the URL above (2024-09-04 to 2026-08-02) and of its
   earlier address `…/storage/app/media/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf`
   (from 2022-06-24), and the raw
   capture <https://web.archive.org/web/20260802101536id_/https://mon.gov.ua/static-objects/mon/sites/1/zagalna%20serednya/Pravopys.2019/ukr.pravopys-2019.pdf>
   has exactly that SHA-1. Its PDF metadata (created 2019-11-19 14:51:29 +03:00) matches the
   ULIF file, and after one extra blank first page its page texts equal the ULIF file's, page
   for page.
4. **The ULIF copy** was retrieved directly (HTTP 200) on 2026-10-03; its exact retrieval
   time and hash are stored in `pravopys_sources.retrieved_at` / `file_sha256`.

## Not chosen

- **The 3 June 2019 text** (Word-generated PDF, 282 pages; mirrored e.g. at
  <https://testportal.gov.ua/wp-content/uploads/2019/09/05062019-onovl-pravo.pdf>,
  SHA-256 `9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c`): the version
  first posted after approval, superseded by the authorized edition, whose wording differs.
  Example, § 1: «тому їх передаємо тими самими буквами» (June) against «тому їх передаємо
  відповідними буквами» (authorized edition).
- **2019.pravopys.net**: an unofficial copy with advertising that stops before § 168
  (HTTP 404 for `/sections/168/` on 2026-10-03). It stays only as the live fallback of
  `query_pravopys` when the offline tables are missing.

## What is stored

`scripts/ingest/pravopys_2019_ingest.py` writes three tables of `data/sources.db`:

- `pravopys_sources`: one row of provenance (edition, approvals, file URL and SHA-256,
  official URLs, retrieval time, parser version, counts).
- `pravopys_paragraphs`: one row per § (1–168): title from the printed contents, the
  contents page, start and end page, heading path, margin labels, `text` (the printed text
  line by line, stress marks included), `text_normalized` (lines joined, line-end hyphens
  resolved), `hyphen_alternatives` (for each hyphen the lexicon did not decide, the reading
  not chosen, indexed by search), `text_sha256` of `text`, and a locator such as «Український правопис. Київ:
  Наукова думка, 2019, § 7, с. 13–14».
- `pravopys_sections`: the printed headings (parts I–V, group headings, subheadings) with
  their introductory text, and the foreword (ПЕРЕДМОВА).

The ingest aborts unless the body yields exactly the 168 §§ of the printed contents
(pp. 383–391), each starting on the page the contents give, and every printed page number
matches. Not stored: the title and imprint pages, the resolution page and the word index
(ПОКАЖЧИК, pp. 257–382).

### Reading the PDF

The text layer uses three encodings, decoded in `scripts/wiki/pravopys_official.py` and
checked against rendered page images: `1251…` fonts carry Windows-1251 bytes; `1251TimesNew…`
fonts hold the stressed vowels (и́, у́, я́, ю́, є́, ї́, І́, Я́…) at the position of the plain
letter; the Unicode fonts write stressed а, е, і, о, у, и as Latin á, é, í, ó, ý, ú inside
Cyrillic words, including endings set off by a hyphen («душ-á») or on the next line
(«пліч-/ó-пліч»). A few words also encode a letter with its lookalike from the other script
(«Cкладені» with a Latin C, «Мicrosóft» with a Cyrillic М, «ХVІ»). Each part of a hyphenated
word, read across line breaks, is written in the script its distinct letters decide; a part
of stressed vowels only takes the script of its word, and a lone ending «(-о́ві, -í)» that of
the preceding word. Left as encoded: printed Latin inside Ukrainian compounds («PIN-код»),
and the Polish letter «ó» cited in § 150. `tests/fixtures/pravopys_2019_script_allowlist.json`
lists these, and the PDF regression test fails on any other word that mixes scripts. Tokens
spelled only with letters both scripts share keep the script they are encoded in, except
where the text of their § decides it (`CONTEXT_READINGS`): the foreign ending «-ia» of
§ 129 is stored in Latin, the § 34 margin label «-ІР-» (beside «-ИР-») in Cyrillic, and the
Roman numerals I, II, III, IV of the declensions in § 66 in Latin capitals. Roman numerals
elsewhere stay as encoded (mostly Cyrillic «І»). `section_path` follows the printed heading sizes, so a 10.5 pt heading such as
«ЧЕРГУВАННЯ ГОЛОСНИХ» nests under the preceding 12.5 pt heading even where the contents treat
both as one level.

`text_normalized` is a derived reading aid: VESUM decides a line-end hyphen when it knows the
joined or the hyphenated form; the others (proper names, rare compounds) are decided by rule
and counted in `unresolved_hyphenations`. Quotes and examples should be taken from `text`.
