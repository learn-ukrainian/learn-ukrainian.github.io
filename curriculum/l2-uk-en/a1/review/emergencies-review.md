## Linguistic Scan
No linguistic errors found.

## Exercise Check
All 4 activity markers are present and mapped sensibly to the plan: `order-112-call` after Dialogues, `quiz-emergency-phrases` and `fill-in-emergency-call` after Emergencies, and `fill-in-reporting-issue` after Getting Help. The marker count matches the 4 `activity_hints`, placement is after the relevant teaching, and the markers are spread through the module rather than dumped at the end. No inline exercise-logic errors are visible in this prose excerpt.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | One objective is underdelivered: the plan says “Ask for help at a pharmacy, hospital, or police station,” but `аптека` appears only once as `Аптека навпроти.` and not as a help scenario. The plan reference `State Standard 2024, §3` is absent (`State Standard 2024`: 0; `§3`: 0). Section pacing is also off: Dialogues 376 words, Emergencies 420, Getting Help 374, Summary 378 vs planned 300 each. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian letters found. VESUM confirms the core forms used here, including `допоможіть`, `викличте`, `загубив`, `відділку`, `адреса`, `алергія`, and `пожежа`. |
| 3. Pedagogical quality | 7/10 | The overall PPP skeleton is serviceable, but too much English meta-commentary crowds out teachable Ukrainian: `Every emergency conversation follows a strict logical structure.`, `When disaster strikes...`, `Your survival kit relies...`. `антибіотики` is also harder than needed for A1 when the plan only requires `алергія на...`. |
| 4. Vocabulary coverage | 8/10 | Required emergency vocabulary is broadly present, but the pharmacy-help objective is not actually taught; `аптека` is only a location example, not a usable request pattern. |
| 5. Exercise quality | 9/10 | Marker inventory is correct, marker IDs match the plan, and placement is pedagogically sensible. No inline exercise block here shows faulty logic. |
| 6. Engagement & tone | 7/10 | Several lines drift into generic dramatic filler instead of teaching: `Memorize them completely.`, `your first line of defense`, `Your survival kit relies on knowing exactly what to say`. This inflates the prose without adding much usable language. |
| 7. Structural integrity | 8/10 | All H2 sections are present and ordered correctly, and the total pipeline word count is above target (1615). The problem is section-level bloat: all four H2 sections overshoot the 300-word plan budget by well over 10%. |
| 8. Cultural accuracy | 7/10 | `This number works everywhere in the country from any mobile phone, even without a SIM card.` is too strong for safety guidance. Official MVS materials confirm nationwide handling and describe the app/Wi‑Fi fallback when mobile service is absent, but not that blanket no-SIM claim ([MVS, 2026-03-25](https://mvs.gov.ua/news/strategicni-iniciativi-ta-projekti-mvs-1), [MVS, 2026-02-09](https://mvs.gov.ua/news/operatori-sluzbi-112-opraciuvali-ponad-105-mln-viklikiv-gromadian-za-25-roki)). |
| 9. Dialogue & conversation quality | 7/10 | The scenarios are relevant and named, but `Вибачте, де тут поліція?` / `Поліція? Прямо і наліво.` is stilted and teaches the wrong destination noun; a learner needs a station/building phrase, not the institution name. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `*   **Аптека навпроти.** — The pharmacy is opposite.`  
Issue: The objective says “Ask for help at a pharmacy, hospital, or police station,” but the module never teaches an actual pharmacy help request. I checked the content: `аптека` appears once, `фармацевт` appears 0 times.  
Fix: Add one usable pharmacy request pattern in Getting Help, e.g. `Мені потрібні ліки від болю.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Ukraine has a centralized system for emergencies. The universal emergency number is **один один два** (112).`  
Issue: The plan’s reference `State Standard 2024, §3` is not cited anywhere in the module. I checked the content: `State Standard 2024` appears 0 times and `§3` appears 0 times.  
Fix: Add a brief citation sentence in the emergency-number explanation.

[CULTURAL ACCURACY] [SEVERITY: critical]  
Location: `This number works everywhere in the country from any mobile phone, even without a SIM card.`  
Issue: This is an unsafe overclaim. The MVS source I checked says 112 operators take calls from all regions, and a separate MVS note says the `112 Ukraine` app works when mobile service is absent if Wi‑Fi is available; that does not justify teaching a blanket “even without a SIM card” rule ([MVS, 2026-03-25](https://mvs.gov.ua/news/strategicni-iniciativi-ta-projekti-mvs-1), [MVS, 2026-02-09](https://mvs.gov.ua/news/operatori-sluzbi-112-opraciuvali-ponad-105-mln-viklikiv-gromadian-za-25-roki)).  
Fix: Remove the no-SIM clause and keep the nationwide 112 explanation.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `*   **У мене алергія на антибіотики.** — I am allergic to antibiotics.`  
Issue: `антибіотики` is unnecessary vocabulary inflation for A1 here; the plan only needs the pattern `У мене алергія на...`, and `ліки` is A1-level.  
Fix: Replace `антибіотики` with `ліки`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Адам:** Вибачте, де тут поліція?` / `> **Перехожий:** Поліція? Прямо і наліво.`  
Issue: This is stilted and teaches an odd target phrase. Learners need a place noun like `відділення поліції`, plus a more natural direction pattern.  
Fix: Replace it with `Вибачте, де тут відділення поліції?` / `Прямо, потім ліворуч.`

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `Every emergency conversation follows a strict logical structure.`, `When disaster strikes, call for help immediately.`, `Your survival kit relies on knowing exactly what to say...`  
Issue: These generic English filler lines are what push all four sections well past the plan budget (376/420/374/378 vs 300 each). They add urgency rhetoric more than teachable language.  
Fix: Compress or delete the quoted filler paragraphs and keep the concrete Ukrainian patterns.

## Verdict: REVISE
This cannot pass because it has fixable but real issues: one critical safety overclaim, one missed plan objective, one omitted plan reference, one awkward dialogue model, unnecessary A1 vocabulary inflation, and substantial section-budget bloat.

<fixes>
- find: |
    Ukraine has a centralized system for emergencies. The universal emergency number is **один один два** (112). This number works everywhere in the country from any mobile phone, even without a SIM card. You can also dial specific services directly if you know exactly what you need. The direct number for the fire service is **один нуль один** (101). The direct number for the police is **один нуль два** (102). The direct number for an ambulance is **один нуль три** (103). These three numbers are standard across Ukraine. Memorize them completely.
  replace: |
    Ukraine has a centralized system for emergencies. The universal emergency number is **один один два** (112). You can call this number across Ukraine from a mobile phone. You can also dial specific services directly if you know exactly what you need. The direct number for the fire service is **один нуль один** (101). The direct number for the police is **один нуль два** (102). The direct number for an ambulance is **один нуль три** (103). This health-and-safety topic matches **State Standard 2024, §3**.

- find: |
    > **Адам:** Вибачте, де тут поліція? *(Excuse me, where is the police here?)*
    > **Перехожий:** Поліція? Прямо і наліво. *(Police? Straight and to the left.)*
  replace: |
    > **Адам:** Вибачте, де тут відділення поліції? *(Excuse me, where is the police station?)*
    > **Перехожий:** Відділення поліції? Прямо, потім ліворуч. *(The police station? Straight ahead, then left.)*

- find: |
    This dialogue shows a critical situation on the road. The driver uses short, urgent sentences. **Аварія** (accident) immediately tells the operator the nature of the event. The driver then gives the exact location and answers simple questions. The operator confirms that a **швидка** (ambulance) is coming.
  replace: |
    This call models the core order: problem, location, contact details.

- find: |
    Losing documents is stressful but common. Adam first asks a passerby where the **поліція** (police) is located. Inside the station, he uses the past tense verb **загубив** (lost) to report the missing item. The officer asks standard identification questions. Adam provides his details and receives a **форма** (form) to complete.
  replace: |
    At the station, Adam reports the loss and gives his details.

- find: |
    Every emergency conversation follows a strict logical structure. You must first state the specific problem so they know who to send. Next, you must give your exact location. Finally, you provide your personal information for their official records.
  replace: |
    In an emergency call, say the problem, then the location, then your name and number.

- find: |
    When disaster strikes, call for help immediately. Learn these phrases as ready-made chunks and use them exactly as you hear them.
  replace: |
    Learn these phrases as ready-made chunks.

- find: |
    Shouting **Допоможіть** (help) is your first line of defense. **Викликати** (to call/summon) is used specifically for ordering emergency services or a taxi. You command others to summon the ambulance or police.
  replace: |
    Use **Допоможіть!** to attract attention. **Викликати** means to summon a service.

- find: |
    If someone is experiencing a medical crisis, use the fixed expression **людині погано**. This literally means "to a person it is bad". If you are the one in danger, ask for **допомога** (help) directly.
  replace: |
    Use **Людині погано!** for a medical crisis. If you need help yourself, say **Мені потрібна допомога!**.

- find: |
    > Марк на вулиці. Він бачить густий дим. Це велика пожежа. Марк телефонує один один два. Він просить про допомогу.
    > *Mark is on the street. He sees thick smoke. It is a big fire. Mark calls one one two. He asks for help.*
  replace: ""

- find: |
    The operator will always ask **Де ви?** (Where are you?). You must provide your location accurately. Review the location phrases you already know. Use **я на вулиці** (I am on the street), **я біля** (I am near), **навпроти** (opposite), or **поруч** (nearby).
  replace: |
    The operator will ask **Де ви?** (Where are you?). Give your location with phrases you already know.

- find: |
    Medical emergencies require specific vocabulary. If you arrive at a **лікарня** (hospital) or a clinic, state your primary need immediately. Use the fixed chunk **мені потрібен** (I need) for a masculine noun, or **мені потрібна** for a feminine noun.
  replace: |
    Medical emergencies require specific vocabulary. If you arrive at a **лікарня** (hospital), a pharmacy, or a clinic, state your primary need immediately. Use the fixed chunk **мені потрібен** (I need) for a masculine noun, or **мені потрібна** for a feminine noun.

- find: |
    **Лікарня** refers to the physical hospital building, while a **лікар** is the doctor who treats you. Keep your statements brief and direct.
  replace: |
    **Лікарня** refers to the hospital building, while a **лікар** is the doctor. At a pharmacy, you can ask **Мені потрібні ліки від болю.** Keep your statements brief and direct.

- find: |
    *   **У мене алергія на антибіотики.** — I am allergic to antibiotics.
  replace: |
    *   **У мене алергія на ліки.** — I am allergic to medicine.

- find: |
    Stressful situations make understanding a foreign language much harder. If you do not comprehend the doctor or the police officer, do not pretend that you do. Ask them to clarify.
    
    *   **Я не розумію.** — I do not understand.
    *   **Повторіть, будь ласка.** — Repeat, please.
    *   **Ви говорите англійською?** — Do you speak English?
    
    Using the formal imperative **повторіть** ensures they know you need to hear the information again.
  replace: |
    If you do not understand, ask for clarification.
    
    *   **Я не розумію.** — I do not understand.
    *   **Повторіть, будь ласка.** — Repeat, please.
    *   **Ви говорите англійською?** — Do you speak English?

- find: |
    Whether you are at a hospital or a police station, authorities require your personal data. They will ask for your name, phone number, and country of origin.
  replace: |
    Authorities may ask for your name, phone number, and country.

- find: |
    If you are at the police station because you lost a document, use the past tense. Remember that the verb **загубити** (to lose) changes its ending based on your grammatical gender.
  replace: |
    At the police station, use the past tense for lost documents.

- find: |
    The officer will likely give you a piece of paper and say **заповніть форму** (fill out the form).
  replace: |
    You may also hear **заповніть форму** (fill out the form).

- find: |
    > Анна в поліції. Вона дуже сумна. Анна загубила сумку. Там був паспорт. Анна бере форму.
    > *Anna is at the police station. She is very sad. Anna lost her bag. The passport was there. Anna takes a form.*
  replace: ""

- find: |
    Navigating an emergency abroad is a daunting experience. Your survival kit relies on knowing exactly what to say without thinking about complex grammar. Remember that **один один два** (112) is your universal lifeline in Ukraine. When you face immediate danger, shout your first commands clearly: **Допоможіть!** (Help!), **Викличте швидку!** (Call an ambulance!), or **Викличте поліцію!** (Call the police!).
  replace: |
    In an emergency, use short phrases. Remember that **один один два** (112) is the universal emergency number in Ukraine. Say **Допоможіть!**, **Викличте швидку!**, or **Викличте поліцію!** clearly.

- find: |
    When the operator answers, state the problem using the word "тут". Tell them **Тут пожежа!** (There is a fire here!) or **Тут аварія!** (There is an accident here!). Immediately follow this with your location: **Я на вулиці...** (I am on ... street), **Я біля...** (I am near...), or provide your full **адреса** (address).
  replace: |
    When the operator answers, state the problem with **Тут пожежа!** or **Тут аварія!**. Then give your location: **Я на вулиці...**, **Я біля...**, or your full **адреса**.

- find: |
    At a medical facility, be direct about your needs. Say **Мені потрібен лікар** (I need a doctor) and describe your symptoms with **У мене болить...** (My ... hurts). Always have your personal information ready. You must be able to state your name, surname, phone number, address, and country. Finally, if you lose something important, report it clearly: **Я загубив паспорт** or **Я загубила паспорт** (I lost my passport). As a final self-check, practice a simulated 112 call aloud: state the specific problem, give your exact location, and give your name.
  replace: |
    At a medical facility, say **Мені потрібен лікар** and **У мене болить...**. Keep your name, phone number, and address ready. For lost documents, say **Я загубив паспорт** or **Я загубила паспорт**. Practice one short 112 call aloud: problem, location, name.

- find: |
    > Це екстрена ситуація. Антон телефонує один нуль два. Він швидко дає свою адресу. Офіцер слухає уважно. Поліція вже їде.
    > *This is an emergency situation. Anton calls one zero two. He quickly gives his address. The officer listens carefully. The police are already on their way.*
  replace: ""
</fixes>