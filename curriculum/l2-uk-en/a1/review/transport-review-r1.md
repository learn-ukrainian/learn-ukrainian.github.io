## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four markers are present: `quiz-which-transport`, `quiz-instrumental-or-locative`, `fill-in-buy-ticket`, `fill-in-ask-directions`. They match the four `activity_hints`, appear after the relevant teaching sections, and are spread well across the module. No inline DSL exercise logic issues are visible because the exercises themselves are still external YAML to be injected later.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present and the four activity markers match the plan, but the planned 300-word pacing is badly overshot in the first three sections: `Діалоги` 387 words, `Транспорт` 395, `Корисні фрази` 394. |
| 2. Linguistic accuracy | 9/10 | No confirmed Ukrainian-form errors found in the learner-facing Ukrainian. Verified forms in use include `їхати автобусом`, `на метро`, `на таксі`, `Потяг рушає`; no Russian letters (`ы`, `э`, `ё`, `ъ`) appear. |
| 3. Pedagogical quality | 7/10 | The core A1 chunks are useful, but long English exposition delays practice, e.g. “Moving around efficiently requires much more than simply memorizing the names of vehicles...” The advanced `:::tip` on `рушати / відбувати / виїжджати` is also outside the plan’s core A1 scope. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary appears in prose: `автобус`, `метро`, `таксі`, `потяг`, `квиток`, `зупинка`. Recommended items also appear: `трамвай`, `маршрутка`, `літак`, `направо`, `наліво`, `прямо`, `дістатися`. |
| 5. Exercise quality | 10/10 | Marker count matches the plan exactly, and each marker follows the relevant teaching block: transport types, pattern choice, buying a ticket, asking directions. |
| 6. Engagement & tone | 7/10 | The teacher voice is mostly neutral, but some phrasing is inflated rather than instructive, e.g. “completely essential survival skill” and “absolute backbone of urban life in Ukraine.” |
| 7. Structural integrity | 7/10 | Headings are complete and ordered correctly, and the module is above the 1200-word target, but a learner-facing placeholder remains: `the direct translation \`<!-- VERIFY -->\``. |
| 8. Cultural accuracy | 9/10 | No Russian-centered framing; examples stay in Ukrainian settings and transport reality (Kyiv/Boryspil, Lviv, metro, маршрутка). |
| 9. Dialogue & conversation quality | 9/10 | Two named-speaker dialogues cover realistic situations: asking how to get somewhere and buying a ticket. They are useful and not robotic. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Діалоги` opening: “In any modern city, knowing how to navigate the public transport network is a completely essential survival skill...”; `Транспорт` opening: “City transport, known as **громадський транспорт**...”; `Корисні фрази` opening: “Navigating complex transport networks requires mastering a few core phrases.”  
Issue: The first three sections are padded with long English exposition, pushing them to 387/395/394 words instead of the planned 300-word pacing and delaying the actual A1 language chunks.  
Fix: Shorten the expository paragraphs so each section gets to the Ukrainian patterns and examples immediately.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: `Корисні фрази` tip block: “It is best to use these authentic verbs instead of the direct translation `<!-- VERIFY -->`...”  
Issue: A raw placeholder is still visible in learner-facing prose, and the whole tip is an advanced off-plan aside after the core A1 material.  
Fix: Remove the `:::tip` block.

## Verdict: REVISE
REVISE because there are major fixable issues: section pacing is materially off-plan, and a raw placeholder remains in learner-facing content. This is not a full rebuild; the module structure, vocabulary coverage, exercise placement, and core Ukrainian forms are otherwise solid.

<fixes>
- find: |
    In any modern city, knowing how to navigate the public transport network is a completely essential survival skill. Moving around efficiently requires much more than simply memorizing the names of vehicles; you need to know how to ask for directions, find the correct stop, and purchase the right ticket. This module covers the vocabulary and grammar patterns you need to confidently ride a bus, take the metro, or catch a train anywhere in Ukraine.
  replace: |
    To use transport in Ukrainian, you need a few core skills: ask for directions, find the stop, and buy a ticket.

- find: |
    Consider a practical scenario. A visitor has arrived in a new city and needs to find the main railway station.
  replace: |
    Consider this practical scenario: a visitor needs to get to the main railway station.

- find: |
    City transport, known as **громадський транспорт** (public transport), forms the absolute backbone of urban life in Ukraine. The single most common vehicle you will see is the **автобус** (bus, masculine). Many large cities also operate a **тролейбус** (trolleybus, masculine), which runs quietly on electricity from overhead wires, and a **трамвай** (tram, masculine), which runs on metal tracks through the streets. Another ubiquitous option is the **маршрутка** (minibus, feminine), a smaller private bus that follows a specific, fixed route. You will also frequently encounter two highly useful indeclinable nouns of foreign origin: **метро** (metro / subway, neuter) and **таксі** (taxi, neuter). Because they are indeclinable, their endings never change, regardless of their grammatical role in the sentence.

    When you need to travel between different cities or countries, you will switch to using **міжміський транспорт** (intercity transport). For comfortable, long-distance journeys across the vast territory of Ukraine, the most popular and reliable option is the **потяг** (train, masculine). You can also take an intercity **автобус** (bus) for shorter regional trips between neighboring towns. For international flights or rapid cross-country travel, you would instead use a **літак** (plane, masculine).
  replace: |
    Common city transport includes **автобус** (bus, masculine), **тролейбус** (trolleybus, masculine), **трамвай** (tram, masculine), **маршрутка** (minibus, feminine), **метро** (metro, neuter), and **таксі** (taxi, neuter). The nouns **метро** and **таксі** are indeclinable, so their forms do not change. For longer trips, common options are **потяг** (train, masculine), intercity **автобус** (bus), and **літак** (plane, masculine).

- find: |
    Navigating complex transport networks requires mastering a few core phrases. Before you can even ride, you must locate the correct **зупинка** (stop or station). If you are specifically looking for a bus, you would ask a passerby:
  replace: |
    Start with a few core questions: where the **зупинка** is, how much a **квиток** costs, and how to get to a place.

- find: |
    Locals will often reply by combining transport modes with the basic directional words you have already learned in previous modules. For example, they might say: **Йдіть прямо, потім наліво** (Go straight, then left) or **Поверніть направо** (Turn right). They might also tell you: **Їдьте прямо автобусом** (Ride straight by bus).
  replace: |
    Locals may reply with the direction words you learned in earlier modules, for example: **Йдіть прямо, потім наліво** (Go straight, then left) or **Поверніть направо** (Turn right).

- find: |
    :::tip
    When talking about a train or a bus leaving its station, native Ukrainian speakers use the verb **рушати** (to depart / to start moving) for trains, and **відбувати** or **виїжджати** for buses. It is best to use these authentic verbs instead of the direct translation `<!-- VERIFY -->`, which is a very common error among language learners. For instance, you should say **Потяг рушає** (The train is departing).
    :::
  replace: ""
</fixes>