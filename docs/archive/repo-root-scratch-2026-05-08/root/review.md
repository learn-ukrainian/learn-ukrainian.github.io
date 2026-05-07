Here is the adversarial review of the 4 wiki-compile prompts, evaluating them for Ukrainian-canonical output and potential escape hatches.

### 1. `scripts/wiki/prompts/compile_pedagogy_brief.md`
**Verdict: MAJOR**
- **Language-contract clarity**: The contract is explicit ("Нарис пишеться українською мовою"), but is undermined by a contradictory structural exception.
- **Escape hatches**:
  1. **Quote:** `Заголовки стовпців у таблицях, коли жодного українського відповідника немає (тоді український варіант у дужках)`
     **Why:** This is logically contradictory ("if no Ukrainian equivalent exists, provide the Ukrainian variant in parentheses"). More dangerously, it gives the LLM explicit permission to use English column headers if it feels a concept is "too English".
     **Proposed rewrite:** Remove this bullet point entirely. All column headers must be Ukrainian.
  2. **Quote:** `Фонетична інтерференція, хибні когнати, структурне перенесення з англійської. Як запобігти кожній помилці.`
     **Why:** When explaining L2 structural transfer, the LLM will naturally want to switch to English to explain the "English side" of the rule or the mechanism of the error.
     **Proposed rewrite:** Add explicitly: `Пояснення механізму помилки має бути написано ВИКЛЮЧНО українською мовою.`
- **Structural completeness**: All 8 template placeholders (`{topic}`, `{domain}`, `{tracks}`, `{slug}`, `{date}`, `{sources}`, `{text}`, `{chunk_id}`) are preserved verbatim.
- **Register target**: Explicitly required ("науково-методичний, деколонізований (за нормами Антоненка-Давидовича)").
- **Self-audit checklist**: The item `- [ ] Текст прози — українською, не англійською` is present but weak. It should be tightened to `- [ ] 100% прози написано українською мовою`.

### 2. `scripts/wiki/prompts/compile_grammar_brief.md`
**Verdict: MAJOR**
- **Language-contract clarity**: Clear overall, but contains the same contradictory bullet point for tables.
- **Escape hatches**:
  1. **Quote:** `Заголовки стовпців у таблицях, коли жодного українського відповідника немає (тоді український варіант у дужках)`
     **Why:** Grants permission to use English column headers.
     **Proposed rewrite:** Remove entirely.
  2. **Quote:** `| ❌ Помилково | ✅ Правильно | Чому |`
     **Why:** The "Чому" column explaining English L2 errors is highly susceptible to slipping into English prose for the explanation.
     **Proposed rewrite:** Add a clarifying note: `Пояснення "Чому" в таблиці повинно бути ВИКЛЮЧНО українською мовою.`
- **Structural completeness**: All 8 template placeholders are preserved verbatim.
- **Register target**: Explicitly required ("науково-навчальний, деколонізований (за нормами Антоненка-Давидовича)").
- **Self-audit checklist**: Present (`- [ ] Текст прози — українською, не англійською`), but similarly weak.

### 3. `scripts/wiki/prompts/compile_academic.md`
**Verdict: MINOR**
- **Language-contract clarity**: Good, but features the same column header escape hatch.
- **Escape hatches**:
  1. **Quote:** `Заголовки стовпців у таблицях, коли жодного українського відповідника немає (тоді український варіант у дужках)`
     **Why:** Same logical contradiction and permission to use English headers.
     **Proposed rewrite:** Remove entirely.
- **Structural completeness**: All 8 template placeholders are preserved verbatim.
- **Register target**: Explicitly required ("академічний, деколонізований (за нормами Антоненка-Давидовича)").
- **Self-audit checklist**: `- [ ] Україномовність: 100% прози українською`. Excellent. This is the strongest checklist item among the 4 prompts.

### 4. `scripts/wiki/prompts/compile_article.md`
**Verdict: MAJOR**
- **Language-contract clarity**: The contract mentions "Прагни до 100% української прози", but is immediately undermined by specific permissions that allow English leakage.
- **Escape hatches**:
  1. **Quote:** `Заголовки стовпців у таблицях, коли жодного українського відповідника немає (тоді український варіант у дужках)`
     **Why:** Same as above.
     **Proposed rewrite:** Remove entirely.
  2. **Quote:** `Короткі англомовні глоси — лише для вузькоспеціалізованих термінів`
     **Why:** This is a massive escape hatch. A confused LLM will classify any term it struggles to translate as "highly specialized" and output English glosses or even whole sentences.
     **Proposed rewrite:** Change to: `Англомовні відповідники допускаються ЛИШЕ в дужках після українського терміна при його першому згадуванні.`
  3. **Quote:** `- [ ] ≥ 95% прози — українською`
     **Why:** This explicitly tells the LLM that 5% English prose is acceptable! This is a fatal flaw for a "no English surface" constraint.
     **Proposed rewrite:** Change to: `- [ ] 100% прози — українською (без винятків)`.
- **Structural completeness**: All 8 template placeholders are preserved verbatim.
- **Register target**: Explicitly required ("науково-популярний / науковий, деколонізований (за нормами Антоненка-Давидовича)").
- **Source-weighting hierarchy**: Excellent. The primary-source-over-Wikipedia weighting is clearly laid out in a table and explicitly calls out "Семінарські треки ... МАЮТЬ спиратися на первинні джерела".
- **Self-audit checklist**: Present, but fundamentally broken by the `≥ 95%` allowance mentioned above.