# Дослідження: Корпусна лінгвістика та цифрові інструменти

## State Standard Reference

No single § is dedicated to corpus linguistics as a discipline — this is a C2.5 meta-skill module, not a grammar or stylistics topic. The most relevant alignments are:

**§3.19 (Наука і техніка)**: "наукові дисципліни; наукові дослідження; розвиток науки і техніки (комп'ютеризація, телекомунікація)"
*Alignment*: Corpus linguistics is presented as a scientific discipline; NLP tools (pymorphy2-uk, Stanza, LanguageTool-UA) are language-technology research.

**§4.3.1.1 (Стилі мови)**: Lists all 7 functional styles — розмовний, офіційний, науковий, публіцистичний, художній, релігійний, епістолярний.
*Alignment*: The module explicitly uses corpus frequency profiles to study register variation across these styles — corpus data is the empirical foundation for C2 stylistic mastery.

**§4.3.8 (Вторинні тексти)**: "Уміння утворювати вторинні тексти, зокрема реферати, повідомлення, довідково-інформаційні тексти."
*Alignment*: The workshop section (Практикум) and practical applications section require learners to write analytical corpus-based reports — directly exercising §4.3.8 production skills.

**Honest note**: The State Standard 2024 predates widespread Ukrainian NLP tools and does not reference corpus linguistics explicitly. This module extends beyond the Standard into professional meta-skills territory appropriate for C2.5 capstone work.

---

## Vocabulary Frequency

| Word | GRAC Freq / IPM | VESUM Status | Notes for Content |
|------|-----------------|--------------|-------------------|
| корпус | 26,831 / 13.26 | ✅ FOUND (noun) | Very high — but polysemous: military corps, building, legislature. Must qualify as **мовний корпус** |
| розмітка | 1,080 / 0.53 | ✅ FOUND (noun) | Medium; use корпусна розмітка, морфологічна розмітка |
| частотність | 643 / 0.32 | ✅ FOUND (noun) | Low; preferred over "частота" for linguistic frequency |
| частотний | attested | ✅ FOUND (adj) | In GRAC collocates with "діапазон" (physics context) — reinforce **частотний словник**, **частотний профіль** |
| лінгвістика | attested | ✅ FOUND (noun) | Standard term; корпусна лінгвістика works as compound |
| анотований | attested | ✅ FOUND (adj) | анотований корпус — well-formed |
| паралельний | attested | ✅ FOUND (adj) | паралельний корпус — well-formed |
| діахронний | 84 / 0.04 | ✅ FOUND (adj) | Rare, academic; reinforce meaning carefully |
| конкорданс | 26 / 0.01 | ✅ FOUND (noun) | Very rare in general corpus — specialist term |
| конкордансний | attested | ✅ FOUND (adj) | конкордансні рядки — verified |
| колокація | 8 / 0.00 | ✅ FOUND (noun) | Essentially absent from general corpus — must be explicitly taught |
| семантична просодія | 0 / 0.00 | ✅ (compound: семантичний + просодія) | Compound has zero GRAC attestation — not established in standard Ukrainian discourse; teach as specialist borrowing from English corpus linguistics |
| корпусний | attested | ✅ FOUND (adj) | корпусний запит, корпусний метод — well-formed |
| парсер | attested | ✅ FOUND (noun) | синтаксичний парсер — well-formed |
| лема | attested | ✅ FOUND (noun) | лематизація — FOUND |
| токен | attested | ✅ FOUND (noun) | standard NLP term |

**VESUM ALERT — конкорданцер**: NOT FOUND in VESUM (neither "конкорданцер" nor "конкордансер"). The plan lists this as a recommended vocabulary item. Use "конкорданс" as the primary term and introduce "конкорданцер" explicitly as a technical English borrowing without a fixed Ukrainian VESUM form yet. Do not use it in vocabulary YAML as a standalone lemma.

---

## Cultural Hooks

1. **ГРАК — 1.7 мільярда токенів**: Confirmed via Ukrainian Wikipedia: "Генеральний регіонально анотований корпус української мови — корпус обсягом понад 1,7 млрд токенів, призначений для лінгвістичних досліджень із граматики, лексики, історії української літературної мови, а також для укладання словників і граматик." This is a powerful pedagogical anchor — ГРАК is larger than many national corpora and was built entirely through Ukrainian scholarly initiative, making it a landmark of language technology development. Source: uk.wikipedia.org/wiki/ГРАК.

2. **Інститут мовознавства ім. О. О. Потебні НАН України (ІНМО)**: "Центр мовознавчих досліджень в Україні" — the principal institutional driver of Ukrainian corpus development and the НАН corpus at lcorp.ulif.org.ua (ULIF = Українська лінгво-інформаційна фундація). The link between digital tools and institutionalized Ukrainian language scholarship frames corpus linguistics not as borrowed methodology but as an expression of Ukrainian scholarly sovereignty. Source: uk.wikipedia.org/wiki/Інститут_мовознавства_НАН_України.

---

## Common Learner Errors

1. **Partial term "корпус" without disambiguator** → Correct: **мовний корпус** — The word "корпус" in Ukrainian most frequently refers to legislative bodies (депутатський корпус) or buildings. GRAC shows 26,831 occurrences, the majority non-linguistic. Learners (and Gemini) may write "корпус" where context requires "мовний корпус." Every first occurrence must be fully qualified.

2. **"Частота" calque instead of "частотність"** → Correct: **частотність** — Under Russian-influenced academic writing habits, learners may write "частота слова" (physics/Russian pattern) instead of standard Ukrainian "частотність слова" or "частота вживання." The noun "частотність" (0.32 IPM) is specifically attested for linguistic use; reinforce it at first introduction.

3. **Conflating concordance output with the tool** → Correct distinction: **конкорданс** (the output — concordance lines) vs. **конкорданцер/конкордансер** (the software tool — no VESUM form). English-background learners will try to map "concordancer" to a single Ukrainian word; the module should explicitly distinguish the two concepts and acknowledge the tool term's unsettled status in Ukrainian terminological practice.

---

## Cross-References

- **Builds on**: `language-policy-decolonization` (c2-083) — empirical corpus evidence for language policy arguments; `complete-grammar-review` (c2-079) — all grammar mastery now verifiable via corpus; `sociolinguistic-mastery` — register variation, now quantifiable through corpus frequency profiles
- **Prepares for**: `c2-85` (Error Analysis — corpus methods applied to identifying systematic learner errors); capstone modules where authentic Ukrainian production is assessed against corpus norms

---

## Notes for Content Writing

- **Decolonized framing critical**: The development of ГРАК and Ukrainian NLP tools (LanguageTool-UA, Stanza Ukrainian model) represents Ukrainian linguistic sovereignty in digital space. Frame this explicitly — corpus linguistics was historically dominated by Russian-language tools that treated Ukrainian as a variant. ГРАК's regional annotation design deliberately captures Ukrainian dialectal diversity, not a Moscow-centric standard.
- **"Семантична просодія" — use with care**: Zero GRAC attestation. Introduce it as an English-origin analytical concept (Bill Louw, 1993, "semantic prosody"), acknowledge it is not yet standardized in Ukrainian metalinguistic discourse, and provide a working Ukrainian explanation: "прихована оцінна конотація, яку слово набуває через типові контексти вживання."
- **Statistics section**: MI-показник (mutual information), t-score, log-likelihood — all require brief but clear Ukrainian-language explanations. Don't assume learners know statistics. One worked example per measure is ideal.
- **Word target discipline**: 5000 minimum. Seven sections total. Sections 2 and 3 (900 words each) are the core — allocate generously. Section 7 workshop (300 words) is a floor, not a ceiling — can expand to 400-500 if needed.
- **ULIF corpus URL**: lcorp.ulif.org.ua — the НАН corpus; ГРАК at grak.org.ua. Both are real, accessible, and should be referenced concretely in the practical sections to ground the hands-on exercises.

## Multimedia Resources

- (none encountered during research — discover phase handles this)

## Resource Discovery


### Textbook References (RAG)

**Grade 10, Сторінка 5** ():
5
 
 лінгвістичні, призначення яких  — пояснення слова з  погляду властивого 
йому лексичного значення, походження, правопису, наголошення; такі слов-
ники подають граматичну характеристику слова тощо. Лінгвістичні словники можуть бути одномовними, двомовними, багатомовними. Двомовні чи багатомовні — це перекладні словники. У них подано переклад 
слів з  однієї мови на іншу. Одномовні словники розкривають особливості слів у  певному аспекті. Вони 
поділяються на окремі різновиди: тлумачні, словн


**Grade 10, Сторінка 4** ():
4
Вступ
 § 1 
Лексикографія. Сучасні лексикографічні 
 джерела: словники, довідкова література 
(у тому числі на електронних носіях)
1. Прочитайте. Визначте тему висловлення.
Поняття лексикографічні джерела об’єднує 
енциклопедичні видання довідкового характеру 
(енциклопедії, енциклопедичні словники й до-
відники) та лінгвістичні словники. Ті й інші 
розширюють світогляд людей, сприяють інтелек-
туальному розвитку й формуванню ненастанної 
потреби в самоосвіті.
Лінгвістичні словники є скарбниця


**Grade 11, Сторінка 271** ():
271
Синтаксис і стилістика тексту
§ 43. Зміст і будова тексту. Складне синтаксичне ціле  
як семантико-синтаксична одиниця тексту......................................... 234
§ 44. Дискурс як комунікативний процес і як текст. Професійний дискурс......................................................................... 238
 
Аудіодиктант (QR-код)..................................................................... 240
Узагальнення і систематизація найважливіших відомостей 
з української мови
§ 4


**Grade 6, Сторінка 104** ():
Розділ 4
Морфологія. Орфографія
Що на нас чекає в цьому розділі?
• Ми розберемося, для чого потрібні частини мови. 
• Пригадаємо, які частини мови є  в українській мові.
• Поміркуємо, чому вони так називаються.
• З’ясуємо, від чого незалежні самостійні частини 
мови та  чому служать службові.
А також поспілкуємося про винаходи й  наукові досяг-
нення.


**Grade 9, Сторінка 67** ():
«Поняття про культуру мовлення» (перша група);
2. «Функції мови, спілкування» (друга група);
3. «Поняття про українську літературну мову» (третя група). II. Прослухайте представників кожної групи із підготовленим матеріалом. Дайте оцінку виступам однокласників. III. Поміркуйте, який вид тематичних виписок є доречним при опрацюванні 
наукової літератури, а який краще застосовувати під час роботи з публі­
цистичними статтями. 67

