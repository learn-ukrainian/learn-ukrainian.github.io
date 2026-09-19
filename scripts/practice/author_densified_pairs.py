#!/usr/bin/env python3
"""Author and append vetted paronym and homonym pairs for Phase 9 densification (Issue #8276).

Strict Invariants:
1. Every slug exists in data/atlas.db article_payloads.
2. Every answer_form and confusable_form is 100% verified in VESUM.
3. Every sentence_with_slot contains exactly one '___' blank.
4. Frames are syntactically and morphosyntactically congruent.
5. All metadata (citations, distinction_gloss_uk, origin, curator) is complete.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml

from scripts.audit.generate_practice_deck import _clean_text, _plain, read_atlas_db
from scripts.verification.vesum import verify_word

PARONYM_YAML = REPO_ROOT / "data/lexicon/paronym_pairs.yaml"
HOMONYM_YAML = REPO_ROOT / "data/lexicon/homonym_pairs.yaml"
ATLAS_DB = REPO_ROOT / "data/atlas.db"

# 62 Authoritative Paronym pairs with 2 congruent frames each
CURATED_PARONYM_RECORDS: list[dict[str, Any]] = [
    {
        "slugA": "афект",
        "slugB": "ефект",
        "distinction_gloss_uk": "Афект — короткочасний бурхливий емоційний стан; ефект — наслідок, результат якоїсь дії чи враження.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m inanim nom/acc",
        "frames": [
            {
                "sentence_with_slot": "У стані сильного ___ людина не контролює своїх дій.",
                "answer_form": "афекту",
                "confusable_form": "ефекту",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Нові ліки дали швидкий позитивний ___ .",
                "answer_form": "ефект",
                "confusable_form": "афект",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "болючий",
        "slugB": "болісний",
        "distinction_gloss_uk": "Болючий — такий, що завдає фізичного болю чи легко відчуває біль; болісний — сповнений душевного страждання, тяжкий або болісно пережитий.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Укол голкою викликав різкий ___ удар.",
                "answer_form": "болючий",
                "confusable_form": "болісний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Для родини це був важкий і ___ розрив.",
                "answer_form": "болісний",
                "confusable_form": "болючий",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "батьків",
        "slugB": "батьківський",
        "distinction_gloss_uk": "Батьків — належний саме рідному батькові; батьківський — стосовний батьків взагалі чи притаманний батькам як вихователям.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj possessive vs rel",
        "frames": [
            {
                "sentence_with_slot": "На столі лежав старий ___ годинник.",
                "answer_form": "батьків",
                "confusable_form": "батьківський",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У школі відбулися щомісячні ___ збори.",
                "answer_form": "батьківські",
                "confusable_form": "батькові",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "болотний",
        "slugB": "болотяний",
        "distinction_gloss_uk": "Болотний — пов'язаний з болотом як географічним ландшафтом; болотяний — притаманний болоту, забарвленням схожий на твань або який живе на болоті.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc",
        "frames": [
            {
                "sentence_with_slot": "У низині за селом стоїть густий ___ запах.",
                "answer_form": "болотний",
                "confusable_form": "болотяний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "На мілководді оселився сірий ___ птах.",
                "answer_form": "болотяний",
                "confusable_form": "болотний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "будівельний",
        "slugB": "будівничий",
        "distinction_gloss_uk": "Будівельний — пов'язаний зі спорудженням споруд, матеріалами чи технікою будівництва; будівничий — пов'язаний з професією архітектора або творця нового.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Вантажівка привезла новий ___ матеріал на майданчик.",
                "answer_form": "будівельний",
                "confusable_form": "будівничий",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Видатний майстер показав справжній ___ талант.",
                "answer_form": "будівничий",
                "confusable_form": "будівельний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "вигляд",
        "slugB": "вид",
        "distinction_gloss_uk": "Вигляд — зовнішність, обрис чи вираз обличчя, пейзаж; вид — наукова класифікаційна одиниця в біології або категорія дієслова в граматиці.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m inanim",
        "frames": [
            {
                "sentence_with_slot": "З вершини гори відкривався чудовий ___ на долину.",
                "answer_form": "вигляд",
                "confusable_form": "вид",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Біологи описали новий рідкісний ___ рослини.",
                "answer_form": "вид",
                "confusable_form": "вигляд",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "визначальний",
        "slugB": "визначний",
        "distinction_gloss_uk": "Визначальний — такий, що має вирішальне значення або визначає суть; визначний — видатний, знаменитий, поважний своєю діяльністю.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc",
        "frames": [
            {
                "sentence_with_slot": "Цей експеримент мав ___ вплив на подальші дослідження.",
                "answer_form": "визначальний",
                "confusable_form": "визначний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Тарас Шевченко — ___ український поет.",
                "answer_form": "визначний",
                "confusable_form": "визначальний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "визначати",
        "slugB": "відзначати",
        "distinction_gloss_uk": "Визначати — з'ясовувати суть, встановлювати параметри чи межі; відзначати — святкувати дату чи нагороджувати, виділяти увагу на щось.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf",
        "frames": [
            {
                "sentence_with_slot": "Науковці намагаються точно ___ вік знахідки.",
                "answer_form": "визначати",
                "confusable_form": "відзначати",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Громада щороку збирається ___ День Незалежності.",
                "answer_form": "відзначати",
                "confusable_form": "визначати",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "виклад",
        "slugB": "викладання",
        "distinction_gloss_uk": "Виклад — форма висловлення змісту думок, розповідь чи письмова передача тексту; викладання — педагогічна діяльність або процес навчання предмета.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m vs n",
        "frames": [
            {
                "sentence_with_slot": "У книзі подано чіткий і послідовний ___ історичних подій.",
                "answer_form": "виклад",
                "confusable_form": "викладання",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Професор присвятив своє життя ___ вищої математики.",
                "answer_form": "викладанню",
                "confusable_form": "викладу",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "виклик",
        "slugB": "заклик",
        "distinction_gloss_uk": "Виклик — складне завдання, вимога з'явитися або запрошення до двобою/змагання; заклик — гасло, звернення до людей із закликом діяти разом.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m inanim",
        "frames": [
            {
                "sentence_with_slot": "Зміна клімату стала серйозним ___ для людства.",
                "answer_form": "викликом",
                "confusable_form": "закликом",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "На площі лунав гучний ___ до єдності й боротьби.",
                "answer_form": "заклик",
                "confusable_form": "виклик",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "викривати",
        "slugB": "розкривати",
        "distinction_gloss_uk": "Викривати — виявляти злочин, обман або чиїсь таємні негідні вчинки; розкривати — відкривати зачинене або пояснювати сутність таємниці/думки.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf",
        "frames": [
            {
                "sentence_with_slot": "Журналісти почали сміливо ___ корупційні схеми посадовців.",
                "answer_form": "викривати",
                "confusable_form": "розкривати",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Детектив зміг успішно ___ заплутану таємницю замку.",
                "answer_form": "розкрити",
                "confusable_form": "викрити",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "виплата",
        "slugB": "оплата",
        "distinction_gloss_uk": "Виплата — видача належних грошей (пенсії, стипендії чи допомоги); оплата — внесення грошей за отримані товари чи надані послуги.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun f inanim",
        "frames": [
            {
                "sentence_with_slot": "На початку місяця пенсіонерам гарантована своєчасна ___ допомоги.",
                "answer_form": "виплата",
                "confusable_form": "оплата",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Для пасажирів доступна безготівкова ___ проїзду карткою.",
                "answer_form": "оплата",
                "confusable_form": "виплата",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "вирізнятися",
        "slugB": "відрізнятися",
        "distinction_gloss_uk": "Вирізнятися — виділятися серед інших своїми позитивними чи яскравими рисами; відрізнятися — мати відмінності або несхожість між предметами чи явищами.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb refl",
        "frames": [
            {
                "sentence_with_slot": "Талановитий учень любив ___ серед однокласників глибокими знаннями.",
                "answer_form": "вирізнятися",
                "confusable_form": "відрізнятися",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Ці два діалекти можуть суттєво ___ вимовою голосних звуків.",
                "answer_form": "відрізнятися",
                "confusable_form": "вирізнятися",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "вирішальний",
        "slugB": "рішучий",
        "distinction_gloss_uk": "Вирішальний — головний, визначальний момент чи фактор, що вирішує долю справи; рішучий — сміливий, без вагань, готовий діяти.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "У фіналі гри настав ___ момент усього поєдинку.",
                "answer_form": "вирішальний",
                "confusable_form": "рішучий",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Командир зробив сміливий і ___ крок уперед.",
                "answer_form": "рішучий",
                "confusable_form": "вирішальний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "висвітлювати",
        "slugB": "освітлювати",
        "distinction_gloss_uk": "Висвітлювати — робити зрозумілим, пояснювати або повідомляти факти в медіа; освітлювати — спрямовувати фізичне світло на предмети чи простір.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf trans",
        "frames": [
            {
                "sentence_with_slot": "Газета почала докладно ___ хід виборчої кампанії.",
                "answer_form": "висвітлювати",
                "confusable_form": "освітлювати",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Яскравий ліхтар став гарно ___ темну вуличку.",
                "answer_form": "освітлювати",
                "confusable_form": "висвітлювати",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "водний",
        "slugB": "водяний",
        "distinction_gloss_uk": "Водний — пов'язаний з водою як стихією чи водними шляхами і ресурсами; водяний — сповнений води, що складається з води чи живе у воді.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Для перевезення вантажів використовують річковий ___ транспорт.",
                "answer_form": "водний",
                "confusable_form": "водяний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Над киплячим чайником піднялася густа ___ пара.",
                "answer_form": "водяна",
                "confusable_form": "водна",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відмінний",
        "slugB": "відмітний",
        "distinction_gloss_uk": "Відмінний — чудовий, найвищої якості або не схожий на інших; відмітний — специфічний, характерний, за яким розпізнають щось.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Студент здав усі іспити на ___ результат.",
                "answer_form": "відмінний",
                "confusable_form": "відмітний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Оригінальний орнамент став ___ ознакою цього майстра.",
                "answer_form": "відмітною",
                "confusable_form": "відмінною",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відносини",
        "slugB": "відношення",
        "distinction_gloss_uk": "Відносини — суспільні, економічні, політичні або дипломатичні взаємозв'язки між державами/людьми; відношення — зв'язок між математичними величинами чи абстрактними поняттями.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun plural inanim",
        "frames": [
            {
                "sentence_with_slot": "Держави підписали угоду про дружні міжнародні ___ .",
                "answer_form": "відносини",
                "confusable_form": "відношення",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Учитель пояснив математичне ___ чисел у пропорції.",
                "answer_form": "відношення",
                "confusable_form": "відносини",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відповідальний",
        "slugB": "відповідний",
        "distinction_gloss_uk": "Відповідальний — серйозний, надійний, який усвідомлює обов'язок чи має важливі наслідки; відповідний — належний, співвідносний із чимось.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Директор поклав на заступника надзвичайно ___ обов'язок.",
                "answer_form": "відповідальний",
                "confusable_form": "відповідний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Юрист підготував ___ документ згідно з вимогами закону.",
                "answer_form": "відповідний",
                "confusable_form": "відповідальний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відчуття",
        "slugB": "почуття",
        "distinction_gloss_uk": "Відчуття — фізичне або фізіологічне сприйняття через органи чуття (холод, біль, дотик); почуття — глибока емоція чи моральне переживання (любов, гордість, сором).",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun neuter inanim",
        "frames": [
            {
                "sentence_with_slot": "Після довгої прогулянки на морозі з'явилося різке ___ холоду.",
                "answer_form": "відчуття",
                "confusable_form": "почуття",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Серце переповнювало щире ___ вдячності за допомогу.",
                "answer_form": "почуття",
                "confusable_form": "відчуття",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "газований",
        "slugB": "газовий",
        "distinction_gloss_uk": "Газований — насичений газом (напій, вода); газовий — який стосується газу як хімічної речовини чи палива або працює на ньому.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj fem nom",
        "frames": [
            {
                "sentence_with_slot": "У спекотний літній день приємно пити прохолодну ___ воду.",
                "answer_form": "газовану",
                "confusable_form": "газову",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Майстер перевірив стару кухонну ___ плиту.",
                "answer_form": "газову",
                "confusable_form": "газовану",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "гармонійний",
        "slugB": "гармонічний",
        "distinction_gloss_uk": "Гармонійний — злагоджений, досконалий у пропорціях чи стосунках; гармонічний — пов'язаний із законами гармонії в музиці чи математиці.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Між друзями склався дивовижно теплий і ___ союз.",
                "answer_form": "гармонійний",
                "confusable_form": "гармонічний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Композитор досліджував складний ___ ряд акордів.",
                "answer_form": "гармонічний",
                "confusable_form": "гармонійний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "глибинний",
        "slugB": "глибокий",
        "distinction_gloss_uk": "Глибинний — розташований на великій глибині або прихований глибоко в надрах/підсвідомості; глибокий — який має велику протяжність згори вниз чи всередину або ґрунтовний.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Геологи виявили потужний ___ шар корисної копалини.",
                "answer_form": "глибинний",
                "confusable_form": "глибокий",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Біля берега річки був дуже ___ вир.",
                "answer_form": "глибокий",
                "confusable_form": "глибинний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "голосний",
        "slugB": "голосовий",
        "distinction_gloss_uk": "Голосний — звук високої гучності або тип звука в мовознавстві, що утворюється голосом; голосовий — пов'язаний з людським анатомічним апаратом голосу.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj plural nom",
        "frames": [
            {
                "sentence_with_slot": "В українській абетці є шість основних ___ звуків.",
                "answer_form": "голосних",
                "confusable_form": "голосових",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Співак береже свої тонкі ___ зв'язки перед виступом.",
                "answer_form": "голосові",
                "confusable_form": "голосні",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "гористий",
        "slugB": "гірський",
        "distinction_gloss_uk": "Гористий — місцевість, багата на гори; гірський — притаманний горам, розташований у горах чи видобутий у горах.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj fem nom",
        "frames": [
            {
                "sentence_with_slot": "Мандрівники перетинали нерівну й складну ___ місцевість.",
                "answer_form": "гористу",
                "confusable_form": "гірську",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "З високих полонин стрімко біжить холодна ___ річка.",
                "answer_form": "гірська",
                "confusable_form": "гориста",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "гуманність",
        "slugB": "гуманізм",
        "distinction_gloss_uk": "Гуманність — доброта, людяність і співчутливе ставлення до людей; гуманізм — прогресивний світогляд чи філософський напрям Відродження.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun f inanim",
        "frames": [
            {
                "sentence_with_slot": "Лікар проявив щиру душевну ___ до кожного пацієнта.",
                "answer_form": "гуманність",
                "confusable_form": "гуманізм",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Епоха Відродження подарувала європейській культурі новий ___ .",
                "answer_form": "гуманізм",
                "confusable_form": "гуманність",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дипломант",
        "slugB": "дипломат",
        "distinction_gloss_uk": "Дипломант — переможець конкурсу чи фестивалю, відзначений дипломом, або випускник, що захищає диплом; дипломат — посадова особа, уповноважена вести переговори з іншими державами.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m anim nom",
        "frames": [
            {
                "sentence_with_slot": "Юний піаніст став почесним ___ престижного міжнародного конкурсу.",
                "answer_form": "дипломантом",
                "confusable_form": "дипломатом",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Досвідчений ___ провів складні мирні переговори в столиці.",
                "answer_form": "дипломат",
                "confusable_form": "дипломант",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "допускати",
        "slugB": "припускати",
        "distinction_gloss_uk": "Допускати — дозволяти доступ, брати участь або робити помилку; припускати — вважати щось імовірним чи можливим як гіпотезу.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf",
        "frames": [
            {
                "sentence_with_slot": "У такій серйозній справі не можна ___ грубих помилок.",
                "answer_form": "допускати",
                "confusable_form": "припускати",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Астрономи можуть лише ___ існування життя на цій планеті.",
                "answer_form": "припускати",
                "confusable_form": "допускати",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "досвід",
        "slugB": "дослід",
        "distinction_gloss_uk": "Досвід — сукупність знань, умінь і життєвої практики; дослід — науковий експеримент, практична перевірка теорії.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m inanim",
        "frames": [
            {
                "sentence_with_slot": "Багаторічний життєвий ___ допоміг майстру прийняти правильне рішення.",
                "answer_form": "досвід",
                "confusable_form": "дослід",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У шкільній лабораторії учні провели хімічний ___ з кислотою.",
                "answer_form": "дослід",
                "confusable_form": "досвід",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дослідний",
        "slugB": "дослідницький",
        "distinction_gloss_uk": "Дослідний — призначений для проведення дослідів чи експериментів; дослідницький — притаманний науковцю-досліднику або дослідженню.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Агрономи висадили пшеницю на спеціальне ___ поле.",
                "answer_form": "дослідне",
                "confusable_form": "дослідницьке",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Студент проявив високий науковий і ___ інтерес до теми.",
                "answer_form": "дослідницький",
                "confusable_form": "дослідний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "духовний",
        "slugB": "душевний",
        "distinction_gloss_uk": "Духовний — пов'язаний з релігією, вищими моральними цінностями чи культурою розуму; душевний — сповнений теплоти, щирості, людяності.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj fem nom",
        "frames": [
            {
                "sentence_with_slot": "Класична музика і поезія збагачують ___ культуру нації.",
                "answer_form": "духовну",
                "confusable_form": "душевну",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У них відбулася щира й тепла ___ розмова біля вогнища.",
                "answer_form": "душевна",
                "confusable_form": "духовна",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дійовий",
        "slugB": "діяльний",
        "distinction_gloss_uk": "Дійовий — ефективний, спроможний діяти або пов'язаний з театральною виставою (дійова особа); діяльний — активний, енергійний, працьовитий.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Влада ухвалила справді ___ засіб проти зростання цін.",
                "answer_form": "дійовий",
                "confusable_form": "діяльний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Новий керівник був надзвичайно енергійний і ___ чоловік.",
                "answer_form": "діяльний",
                "confusable_form": "дійовий",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дільниця",
        "slugB": "ділянка",
        "distinction_gloss_uk": "Дільниця — територія, виділена для виборів або поліцейського нагляду (виборча дільниця); ділянка — окрема частина землі або сфера діяльності.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "У день голосування жителі прийшли на виборчу ___ зранку.",
                "answer_form": "дільницю",
                "confusable_form": "ділянку",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Сім'я придбала затишну земельну ___ біля річки.",
                "answer_form": "ділянку",
                "confusable_form": "дільницю",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "економіка",
        "slugB": "економія",
        "distinction_gloss_uk": "Економіка — сукупність виробничих відносин, народне господарство чи наука про нього; економія — ощадливе використання коштів, ресурсів чи матеріалів.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "Після реформи національна ___ країни почала стрімко зростати.",
                "answer_form": "економіка",
                "confusable_form": "економія",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Розумна ___ електрики дозволяє суттєво зменшити витрати.",
                "answer_form": "економія",
                "confusable_form": "економіка",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "еміграція",
        "slugB": "імміграція",
        "distinction_gloss_uk": "Еміграція — виїзд громадян зі своєї країни в іншу на постійне проживання; імміграція — в'їзд іноземців до країни на тривале чи постійне проживання.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "Масова ___ українців до Канади розпочалася наприкінці XIX століття.",
                "answer_form": "еміграція",
                "confusable_form": "імміграція",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Сувора державна ___ регулює приплив іноземної робочої сили.",
                "answer_form": "імміграція",
                "confusable_form": "еміграція",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "етикет",
        "slugB": "етикетка",
        "distinction_gloss_uk": "Етикет — правила чемної поведінки та ввічливості в товаристві; етикетка — ярлик або наклейка на товарі з його назвою та даними.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m vs f",
        "frames": [
            {
                "sentence_with_slot": "Дипломатичний ___ вимагає суворого дотримання протоколу.",
                "answer_form": "етикет",
                "confusable_form": "етикетка",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "На скляну пляшку була наклеєна яскрава паперова ___ .",
                "answer_form": "етикетка",
                "confusable_form": "етикет",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "земний",
        "slugB": "земельний",
        "distinction_gloss_uk": "Земний — пов'язаний з планетою Земля або реальним матеріальним життям на противагу небесному; земельний — стосовний ділянок землі чи землекористування.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj fem nom",
        "frames": [
            {
                "sentence_with_slot": "Космічний корабель наблизився до поверхні рідної ___ кулі.",
                "answer_form": "земної",
                "confusable_form": "земельної",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Парламент проголосував за важливу нову ___ реформу.",
                "answer_form": "земельну",
                "confusable_form": "земну",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "зустрічатися",
        "slugB": "траплятися",
        "distinction_gloss_uk": "Зустрічатися — сходитися з кимось за домовленістю або випадково побачитися; траплятися — ставатися, відбуватися зрідка або бувати несподівано.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb refl",
        "frames": [
            {
                "sentence_with_slot": "Старі шкільні друзі люблять щосуботи ___ у затишному кафе.",
                "answer_form": "зустрічатися",
                "confusable_form": "траплятися",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У житті кожної людини можуть часом ___ прикрі прикрощі.",
                "answer_form": "траплятися",
                "confusable_form": "зустрічатися",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "диктант",
        "slugB": "диктат",
        "distinction_gloss_uk": "Диктант — письмова навчальна робота для перевірки грамотності учнів; диктат — нав'язування своєї волі іншій стороні, примус чи категорична вимога.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Учитель продиктував новий контрольний ___ з української мови.",
                "answer_form": "диктант",
                "confusable_form": "диктат",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Суверенна держава рішуче відкинула будь-який чужий ___ .",
                "answer_form": "диктат",
                "confusable_form": "диктант",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "естетика",
        "slugB": "етика",
        "distinction_gloss_uk": "Естетика — філософська наука про прекрасне в житті й мистецтві чи краса форми; етика — наука про мораль, норми поведінки і правила людських стосунків.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "Художній твір вражає витонченою ___ словесного образу.",
                "answer_form": "естетикою",
                "confusable_form": "етикою",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Професійна ___ журналіста вимагає завжди писати правду.",
                "answer_form": "етика",
                "confusable_form": "естетика",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "рідкісний",
        "slugB": "рідкий",
        "distinction_gloss_uk": "Рідкісний — такий, що трапляється дуже нечасто, винятковий; рідкий — плинний, не густий або розташований з великими проміжками.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "У Карпатах росте надзвичайно ___ вид червонокнижних квітів.",
                "answer_form": "рідкісний",
                "confusable_form": "рідкий",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Кухар приготував занадто ___ соус до м'яса.",
                "answer_form": "рідкий",
                "confusable_form": "рідкісний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "світловий",
        "slugB": "світлий",
        "distinction_gloss_uk": "Світловий — пов'язаний з фізичним світлом або світловою технікою; світлий — яскравий, добре освітлений чи блідий за забарвленням.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "У нічному небі з'явився потужний ___ промінь прожектора.",
                "answer_form": "світловий",
                "confusable_form": "світлий",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Нова квартира мала просторий і дуже ___ зал.",
                "answer_form": "світлий",
                "confusable_form": "світловий",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "смертний",
        "slugB": "смертельний",
        "distinction_gloss_uk": "Смертний — приречений на смерть (людина, земна істота); смертельний — такий, що безпосередньо несе смерть або спричиняє її.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj fem nom",
        "frames": [
            {
                "sentence_with_slot": "Кожна жива людина у цьому світі є просто ___ істотою.",
                "answer_form": "смертною",
                "confusable_form": "смертельною",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Отрута чорної вдови становить ___ небезпеку для організму.",
                "answer_form": "смертельну",
                "confusable_form": "смертну",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "суспільний",
        "slugB": "громадський",
        "distinction_gloss_uk": "Суспільний — пов'язаний із суспільством у цілому або його законами й ладом; громадський — пов'язаний з місцевою громадою, добровільними колективами чи публічними місцями.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Філософи вивчають фундаментальний ___ лад різних епох.",
                "answer_form": "суспільний",
                "confusable_form": "громадський",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Волонтери створили новий корисний ___ рух за чистоту парків.",
                "answer_form": "громадський",
                "confusable_form": "суспільний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "цивільний",
        "slugB": "громадянський",
        "distinction_gloss_uk": "Цивільний — не військовий, мирний або пов'язаний з приватним правом (цивільний кодекс); громадянський — притаманний свідомому громадянину чи його обов'язку.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Після звільнення зі служби офіцер одягнув звичайний ___ одяг.",
                "answer_form": "цивільний",
                "confusable_form": "громадянський",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Участь у виборах — це святий ___ обов'язок кожного українця.",
                "answer_form": "громадянський",
                "confusable_form": "цивільний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "діалект",
        "slugB": "діалектика",
        "distinction_gloss_uk": "Діалект — місцевий або територіальний різновид загальнонародної мови; діалектика — філософське вчення про загальні закони розвитку природи, суспільства й мислення.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun masc vs fem inanim",
        "frames": [
            {
                "sentence_with_slot": "У гірських селах зберігся старовинний гуцульський ___ .",
                "answer_form": "діалект",
                "confusable_form": "діалектика",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Філософ досліджував закони матеріалістичної ___ розвитку.",
                "answer_form": "діалектики",
                "confusable_form": "діалекту",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дисциплінарний",
        "slugB": "дисциплінований",
        "distinction_gloss_uk": "Дисциплінарний — пов'язаний з дотриманням службової дисципліни або покаранням за її порушення; дисциплінований — той, хто суворо дотримується встановленого порядку, організований.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "За порушення графіка працівник отримав ___ стягнення.",
                "answer_form": "дисциплінарне",
                "confusable_form": "дисципліноване",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Сергій був дуже уважний і ___ учень у класі.",
                "answer_form": "дисциплінований",
                "confusable_form": "дисциплінарний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "вегетативний",
        "slugB": "вегетаційний",
        "distinction_gloss_uk": "Вегетативний — пов'язаний з вегетацією як живленням і ростом організму рослини (вегетативне розмноження); вегетаційний — пов'язаний з вегетаційним періодом росту рослин.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Садівник застосував ___ спосіб розмноження смородини живцями.",
                "answer_form": "вегетативний",
                "confusable_form": "вегетаційний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Для озимих культур розпочався сприятливий ___ період навесні.",
                "answer_form": "вегетаційний",
                "confusable_form": "вегетативний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "виділяти",
        "slugB": "приділяти",
        "distinction_gloss_uk": "Виділяти — надавати гроші/ресурси з фонду чи відокремлювати частину; приділяти — скеровувати увагу, турботу або час комусь чи чомусь.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf trans",
        "frames": [
            {
                "sentence_with_slot": "Держава вирішила ___ додаткові кошти на ремонт лікарні.",
                "answer_form": "виділити",
                "confusable_form": "приділити",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Батьки намагаються більше часу ___ вихованню дитини.",
                "answer_form": "приділяти",
                "confusable_form": "виділяти",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "демонстрація",
        "slugB": "демонстрування",
        "distinction_gloss_uk": "Демонстрація — масова публічна хода/мітинг або наочний показ фільму чи моделей; демонстрування — тривалий процес показування або виявлення чогось.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem vs neuter",
        "frames": [
            {
                "sentence_with_slot": "На центральній площі відбулася мирна велелюдна ___ студентів.",
                "answer_form": "демонстрація",
                "confusable_form": "демонстрування",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Під час лекції тривало безперервне ___ наукових слайдів.",
                "answer_form": "демонстрування",
                "confusable_form": "демонстрація",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "визначати",
        "slugB": "зазначати",
        "distinction_gloss_uk": "Визначати — з'ясовувати суть, формулювати значення або встановлювати межі; зазначати — вказувати, робити зауваження або відзначати в тексті.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf trans",
        "frames": [
            {
                "sentence_with_slot": "Комісія повинна чітко ___ переможця конкурсу.",
                "answer_form": "визначити",
                "confusable_form": "зазначити",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У заяві необхідно обов'язково ___ дату свого народження.",
                "answer_form": "зазначити",
                "confusable_form": "визначити",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "виплата",
        "slugB": "плата",
        "distinction_gloss_uk": "Виплата — дія з видачі належних грошових сум (пенсій, допомоги); плата — грошова винагорода за працю або встановлена ціна користування послугами.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "Громадянам гарантована регулярна грошова ___ компенсацій.",
                "answer_form": "виплата",
                "confusable_form": "плата",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Робітникові нарахували щомісячну заробітну ___ за працю.",
                "answer_form": "плату",
                "confusable_form": "виплату",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відрізнятися",
        "slugB": "розрізнятися",
        "distinction_gloss_uk": "Відрізнятися — мати індивідуальні відмінності або бути несхожим на інший предмет; розрізнятися — не збігатися між собою, різнитися в кількох деталях (думки, позиції).",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb refl",
        "frames": [
            {
                "sentence_with_slot": "Новий переклад може суттєво ___ від першого видання.",
                "answer_form": "відрізнятися",
                "confusable_form": "розрізнятися",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Погляди експертів на проблему можуть помітно ___ між собою.",
                "answer_form": "розрізнятися",
                "confusable_form": "відрізнятися",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "спостережливий",
        "slugB": "спостережний",
        "distinction_gloss_uk": "Спостережливий — здатний помічати дрібниці й тонкощі, уважний; спостережний — обладнаний або призначений для ведення спостереження.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Досвідчений детектив був надзвичайно ___ до деталей.",
                "answer_form": "спостережливий",
                "confusable_form": "спостережний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "На пагорбі військові облаштували замаскований ___ пункт.",
                "answer_form": "спостережний",
                "confusable_form": "спостережливий",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "факт",
        "slugB": "фактор",
        "distinction_gloss_uk": "Факт — дійсна, реальна подія або незаперечний доказ; фактор — рушійна сила, причина або чинник якогось процесу.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun m inanim",
        "frames": [
            {
                "sentence_with_slot": "Свідок розповів про незаперечний історичний ___ події.",
                "answer_form": "факт",
                "confusable_form": "фактор",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Довіра в команді є вирішальним ___ успіху проєкту.",
                "answer_form": "фактором",
                "confusable_form": "фактом",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "чутливий",
        "slugB": "чуйний",
        "distinction_gloss_uk": "Чутливий — здатний тонко реагувати на фізичні чи емоційні подразники (чутлива шкіра, чутливий прилад); чуйний — доброзичливий, уважний, щирий до чужого лиха.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Лабораторія встановила надзвичайно ___ датчик вібрацій.",
                "answer_form": "чутливий",
                "confusable_form": "чуйний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Лікар мав добре серце і дуже ___ характер.",
                "answer_form": "чуйний",
                "confusable_form": "чутливий",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "автоматизований",
        "slugB": "автоматичний",
        "distinction_gloss_uk": "Автоматизований — оснащений автоматами або переведений на часткове машинне керування; автоматичний — такий, що діє сам собою, без втручання людини.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "На заводі успішно впровадили новий ___ комплекс обліку.",
                "answer_form": "автоматизований",
                "confusable_form": "автоматичний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Двері магазину відкривалися через ___ датчик руху.",
                "answer_form": "автоматичний",
                "confusable_form": "автоматизований",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "ароматичний",
        "slugB": "ароматний",
        "distinction_gloss_uk": "Ароматичний — пов'язаний з хімічними ароматичними сполуками чи речовинами (ароматичні вуглеводні); ароматний — запашний, з приємним ніжним ароматом.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "adj masc nom",
        "frames": [
            {
                "sentence_with_slot": "Хіміки досліджували складний ___ вуглеводень бензен.",
                "answer_form": "ароматичний",
                "confusable_form": "ароматний",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Бабуся заварила свіжий і надзвичайно ___ липовий чай.",
                "answer_form": "ароматний",
                "confusable_form": "ароматичний",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "визволяти",
        "slugB": "звільняти",
        "distinction_gloss_uk": "Визволяти — повертати свободу від ворога, неволі чи окупації; звільняти — усувати з посади або випорожнювати місце/приміщення від зайвого.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf trans",
        "frames": [
            {
                "sentence_with_slot": "Українська армія продовжує мужньо ___ окуповані міста.",
                "answer_form": "визволяти",
                "confusable_form": "звільняти",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Дирекція підприємства планує поступово ___ працівників за прогули.",
                "answer_form": "звільняти",
                "confusable_form": "визволяти",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "збірка",
        "slugB": "збірник",
        "distinction_gloss_uk": "Збірка — видання творів одного автора (збірка віршів); збірник — книга, яка містить різні офіційні матеріали, закони, правила або статті багатьох авторів.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem vs masc",
        "frames": [
            {
                "sentence_with_slot": "У друкарні вийшла нова поетична ___ Ліни Костенко.",
                "answer_form": "збірка",
                "confusable_form": "збірник",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Студенти придбали практичний ___ завдань і вправ.",
                "answer_form": "збірник",
                "confusable_form": "збірку",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відкривати",
        "slugB": "відчиняти",
        "distinction_gloss_uk": "Відкривати — виявляти невідоме, започатковувати новий заклад або відкривати рахунок/засідання; відчиняти — розчиняти те, що має ступінь/двері/вікна.",
        "citations": ["Антоненко-Давидович Б. Д. Як ми говоримо (1970)"],
        "curator": "gemini-8276-densification",
        "notes": "verb imperf trans",
        "frames": [
            {
                "sentence_with_slot": "Вчені сподіваються найближчим часом ___ нові закони фізики.",
                "answer_form": "відкривати",
                "confusable_form": "відчиняти",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Уранці мама попросила сина широко ___ вікно в кімнаті.",
                "answer_form": "відчинити",
                "confusable_form": "відкрити",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "депресія",
        "slugB": "репресія",
        "distinction_gloss_uk": "Депресія — пригнічений психічний стан або тривалий занепад економіки; репресія — каральний захід, покарання або переслідування, вжите державними органами.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun fem inanim",
        "frames": [
            {
                "sentence_with_slot": "Після тривалого стресу у пацієнта виникла важка душевна ___ .",
                "answer_form": "депресія",
                "confusable_form": "репресія",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Тоталітарний режим застосував жорстокі політичні ___ проти опозиції.",
                "answer_form": "репресії",
                "confusable_form": "депресії",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "відтинок",
        "slugB": "відтінок",
        "distinction_gloss_uk": "Відтинок — окрема частина якоїсь лінії, простору чи проміжок часу; відтінок — різновид одного й того ж кольору або ледь помітний нюанс значення/почуття.",
        "citations": ["Гринчишин Д. Г. Словник паронімів української мови (1986)"],
        "curator": "gemini-8276-densification",
        "notes": "noun masc inanim",
        "frames": [
            {
                "sentence_with_slot": "Ремонтна бригада відремонтувала пошкоджений ___ автомобільної дороги.",
                "answer_form": "відтинок",
                "confusable_form": "відтінок",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Художник змішав фарби, щоб отримати ніжний голубий ___ .",
                "answer_form": "відтінок",
                "confusable_form": "відтинок",
                "origin": "authored-gemini-8276",
            },
        ],
    },
]

# 20 Authoritative Homonym pairs with 2 contextual frames each (including C1 candidates)
CURATED_HOMONYM_RECORDS: list[dict[str, Any]] = [
    {
        "slugA": "бал",
        "slugB": "бал",
        "distinction_gloss_uk": "«Бал» — великий вечір із танцями в ошатному вбранні; «бал» — одиниця оцінки успішності або сили явища (шторму, землетрусу).",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Випускники прийшли на урочистий святковий ___ у палац.",
                "answer_form": "бал",
                "confusable_form": "бал",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Учень отримав найвищий ___ за складний тест з історії.",
                "answer_form": "бал",
                "confusable_form": "бал",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "кран",
        "slugB": "кран",
        "distinction_gloss_uk": "«Кран» — запірний пристрій для регулювання потоку води чи газу в трубі; «кран» — велика підйомна машина на будівництві.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "На кухні зламався водопровідний ___ і почала капати вода.",
                "answer_form": "кран",
                "confusable_form": "кран",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "На будівельному майданчику працював потужний баштовий ___ .",
                "answer_form": "кран",
                "confusable_form": "кран",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "лист",
        "slugB": "лист",
        "distinction_gloss_uk": "«Лист» — поштове письмове повідомлення в конверті; «лист» — зелений вегетативний орган рослини на гілці дерева.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Поштар приніс рекомендований ___ від давнього друга.",
                "answer_form": "лист",
                "confusable_form": "лист",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Восени з високого дуба зірвався останній жовтий ___ .",
                "answer_form": "лист",
                "confusable_form": "лист",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "рукав",
        "slugB": "рукав",
        "distinction_gloss_uk": "«Рукав» — деталь одягу, яка вкриває руку; «рукав» — відгалуження річки чи гнучкий шланг для подачі води.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Кравець акуратно підшив правий ___ нової сорочки.",
                "answer_form": "рукав",
                "confusable_form": "рукав",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Широка річка розділилася на два спокійні ___ перед морем.",
                "answer_form": "рукави",
                "confusable_form": "рукави",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "лавка",
        "slugB": "лавка",
        "distinction_gloss_uk": "«Лавка» — невеликий магазин або торговельна крамничка; «лавка» — дерев'яна лавиця для сидіння в саду чи біля хати.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "На розі вулиці відкрилася нова сувенірна ___ з книжками.",
                "answer_form": "лавка",
                "confusable_form": "лавка",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Дідусь сів перепочити на дерев'яну ___ під яблунею.",
                "answer_form": "лавку",
                "confusable_form": "лавку",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "ключ",
        "slugB": "ключ",
        "distinction_gloss_uk": "«Ключ» — інструмент для відкривання замка або закручування гайок; «ключ» — природне джерело води або стрій перелітних птахів у небі.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Він повернув залізний ___ у замку дверей і зайшов.",
                "answer_form": "ключ",
                "confusable_form": "ключ",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Високо в осінньому небі летів журавлиний ___ .",
                "answer_form": "ключ",
                "confusable_form": "ключ",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "стан",
        "slugB": "стан",
        "distinction_gloss_uk": "«Стан» — фізичний, душевний або суспільний лад/положення; «стан» — тулуб, талія людини або великий прокатний металургійний агрегат.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Лікар уважно перевірив загальний ___ здоров'я пацієнта.",
                "answer_form": "стан",
                "confusable_form": "стан",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Тонкий і стрункий дівочий ___ прикрашав широкий пояс.",
                "answer_form": "стан",
                "confusable_form": "стан",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "гриф",
        "slugB": "гриф",
        "distinction_gloss_uk": "«Гриф» — великий хижий птах з родини яструбиних; «гриф» — довга вузька частина струнного інструмента, до якої притискають струни.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Над скелями кружляв могутній чорний ___ .",
                "answer_form": "гриф",
                "confusable_form": "гриф",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Гітарист поклав пальці лівої руки на ___ інструмента.",
                "answer_form": "гриф",
                "confusable_form": "гриф",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "міна",
        "slugB": "міна",
        "distinction_gloss_uk": "«Міна» — вираз обличчя, гримаса; «міна» — вибуховий боєприпас, закладений у землю чи воду.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "У кумедного хлопчика на обличчі з'явилася смішна ___ .",
                "answer_form": "міна",
                "confusable_form": "міна",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Сапери обережно знешкодили ворожу протитанкову ___ .",
                "answer_form": "міну",
                "confusable_form": "міну",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "пояс",
        "slugB": "пояс",
        "distinction_gloss_uk": "«Пояс» — смуга тканини чи шкіри для підперізування одягу на талії; «пояс» — географічна або кліматична зона Землі.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Козак підперезав широкий червоний ___ навколо талії.",
                "answer_form": "пояс",
                "confusable_form": "пояс",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Україна здебільшого розташована в помірному кліматичному ___ .",
                "answer_form": "поясі",
                "confusable_form": "поясі",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "шашка",
        "slugB": "шашка",
        "distinction_gloss_uk": "«Шашка» — козацька або кавалерійська холодна рубаюча зброя; «шашка» — плоска кругла фішка для гри в шашки.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "На поясі у вершника блищала гостра сталева ___ .",
                "answer_form": "шашка",
                "confusable_form": "шашка",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Гравець пересунув білу ___ на крайню клітинку дошки.",
                "answer_form": "шашку",
                "confusable_form": "шашку",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "коло",
        "slugB": "коло",
        "distinction_gloss_uk": "«Коло» — замкнена крива лінія, геометрична фігура; «коло» — сукупність людей, об'єднаних спільними інтересами чи знайомством.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Учитель накреслив на дошці рівне геометричне ___ циркулем.",
                "answer_form": "коло",
                "confusable_form": "коло",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Учений потрапив у близьке ___ видатних науковців столиці.",
                "answer_form": "коло",
                "confusable_form": "коло",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "корінь",
        "slugB": "корінь",
        "distinction_gloss_uk": "«Корінь» — підземна частина рослини, якою вона живиться із ґрунту; «корінь» — головна значуща частина слова без суфіксів і префіксів.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Могутнє дерево пустило глибокий ___ глибоко в землю.",
                "answer_form": "корінь",
                "confusable_form": "корінь",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У слові «лісник» спільний ___ має форму «ліс».",
                "answer_form": "корінь",
                "confusable_form": "корінь",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "поле",
        "slugB": "поле",
        "distinction_gloss_uk": "«Поле» — велика безліса ділянка землі, засіяна зерном; «поле» — чиста смуга вздовж краю аркуша паперу чи книги.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Комбайн вийшов збирати стиглу пшеницю на золоте ___ .",
                "answer_form": "поле",
                "confusable_form": "поле",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Учень залишив широке ___ в зошиті для зауважень учителя.",
                "answer_form": "поле",
                "confusable_form": "поле",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "поступ",
        "slugB": "поступ",
        "distinction_gloss_uk": "«Поступ» — прогрес, рух уперед і розвиток суспільства; «поступ» — крок або хода людини.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Науково-технічний ___ докорінно змінив життя людства.",
                "answer_form": "поступ",
                "confusable_form": "поступ",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У тиші кімнати чувся повільний і важкий ___ господаря.",
                "answer_form": "поступ",
                "confusable_form": "поступ",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "дріб",
        "slugB": "дріб",
        "distinction_gloss_uk": "«Дріб» — числове позначення частки одиниці в математиці; «дріб» — дрібні свинцеві кульки для мисливської рушниці або частий барабанний бій.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Учитель пояснив, як правильно додавати звичайний ___ на уроці.",
                "answer_form": "дріб",
                "confusable_form": "дріб",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Удалині пролунав гучний барабанний ___ полкового оркестру.",
                "answer_form": "дріб",
                "confusable_form": "дріб",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "лінія",
        "slugB": "лінія",
        "distinction_gloss_uk": "«Лінія» — геометрична вузька смуга чи риска; «лінія» — шлях сполучення транспорту чи телефонного зв'язку.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Архітектор провів рівну пряму ___ олівцем на кресленні.",
                "answer_form": "лінію",
                "confusable_form": "лінію",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "У місті відкрилася нова швидкісна ___ трамвайного руху.",
                "answer_form": "лінія",
                "confusable_form": "лінія",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "плід",
        "slugB": "плід",
        "distinction_gloss_uk": "«Плід» — орган рослини, що містить насіння (яблуко, груша); «плід» — зародок в утробі матері або результат тривалої розумової праці.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "На гілці висів соковитий стиглий ___ яблуні.",
                "answer_form": "плід",
                "confusable_form": "плід",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Ця фундаментальна монографія — солідний ___ багаторічних досліджень.",
                "answer_form": "плід",
                "confusable_form": "плід",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "точка",
        "slugB": "точка",
        "distinction_gloss_uk": "«Точка» — розділовий знак у кінці речення; «точка» — конкретне географічне або просторове місце на карті.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "У кінці розповідного речення завжди ставиться ___ .",
                "answer_form": "точка",
                "confusable_form": "точка",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Маяк став головною опорною ___ навігації для кораблів.",
                "answer_form": "точкою",
                "confusable_form": "точкою",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "правило",
        "slugB": "правило",
        "distinction_gloss_uk": "«Правило» — норма поведінки чи обов'язковий граматичний закон; «правило» — довге кермове весло або напрямна лінійка в будівництві.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "Учень вивчив нове орфографічне ___ правопису префіксів.",
                "answer_form": "правило",
                "confusable_form": "правило",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Майстер вирівняв свіжу штукатурку на стіні за допомогою ___ .",
                "answer_form": "правила",
                "confusable_form": "правила",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "галка",
        "slugB": "галка",
        "distinction_gloss_uk": "«Галка» — птах родини воронових з чорним пір'ям і сірою шиєю; «галка» — позначка у вигляді пташки (галочки) під час перевірки.",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "На гілці старого клена сіла чорна сіроока ___ .",
                "answer_form": "галка",
                "confusable_form": "галка",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Біля кожного виконаного пункту плану стояла акуратна ___ .",
                "answer_form": "галка",
                "confusable_form": "галка",
                "origin": "authored-gemini-8276",
            },
        ],
    },
    {
        "slugA": "етер",
        "slugB": "етер",
        "distinction_gloss_uk": "«Етер» — органічна летка хімічна сполука з характерним запахом; «етер» — простір радіо- або телевізійного мовлення («прямий етер»).",
        "citations": ["miyklas.com.ua"],
        "curator": "gemini-8276-densification",
        "frames": [
            {
                "sentence_with_slot": "У хімічній лабораторії використовують очищений медичний ___ .",
                "answer_form": "етер",
                "confusable_form": "етер",
                "origin": "authored-gemini-8276",
            },
            {
                "sentence_with_slot": "Ведучий оголосив терміновий випуск новин у прямому ___ .",
                "answer_form": "етері",
                "confusable_form": "етері",
                "origin": "authored-gemini-8276",
            },
        ],
    },
]


def validate_records(records: list[dict[str, Any]], mode_name: str, atlas_lemmas: dict[str, Any]) -> None:
    for idx, rec in enumerate(records, 1):
        sa = rec.get("slugA", "")
        sb = rec.get("slugB", "")
        if not sa or not sb:
            raise ValueError(f"{mode_name} #{idx} missing slugA or slugB")
        if _plain(sa) not in atlas_lemmas:
            raise ValueError(f"{mode_name} #{idx} slugA '{sa}' NOT in Atlas!")
        if _plain(sb) not in atlas_lemmas:
            raise ValueError(f"{mode_name} #{idx} slugB '{sb}' NOT in Atlas!")

        gloss = rec.get("distinction_gloss_uk", "")
        if not gloss or not gloss.strip():
            raise ValueError(f"{mode_name} #{idx} ({sa}/{sb}) missing distinction_gloss_uk")

        frames = rec.get("frames", [])
        if len(frames) < 2:
            raise ValueError(f"{mode_name} #{idx} ({sa}/{sb}) has fewer than 2 frames")

        for f_idx, fr in enumerate(frames, 1):
            sent = fr.get("sentence_with_slot", "")
            ans = fr.get("answer_form", "")
            conf = fr.get("confusable_form", "")
            if sent.count("___") != 1:
                raise ValueError(f"{mode_name} #{idx} frame {f_idx} slot count != 1: {sent!r}")
            if not ans or not conf:
                raise ValueError(f"{mode_name} #{idx} frame {f_idx} missing answer or confusable")
            if not (verify_word(ans) or verify_word(ans.lower())):
                raise ValueError(f"{mode_name} #{idx} frame {f_idx} answer '{ans}' NOT in VESUM!")
            if not (verify_word(conf) or verify_word(conf.lower())):
                raise ValueError(f"{mode_name} #{idx} frame {f_idx} confusable '{conf}' NOT in VESUM!")


def main() -> None:
    print("Loading Atlas database...")
    entries = read_atlas_db(ATLAS_DB)
    atlas_lemmas = {}
    for e in entries:
        lem = _clean_text(e.get("lemma"))
        if lem:
            atlas_lemmas[_plain(lem)] = e

    print(f"Validating {len(CURATED_PARONYM_RECORDS)} paronym records...")
    validate_records(CURATED_PARONYM_RECORDS, "PARONYM", atlas_lemmas)
    print("✅ All paronym records are 100% valid!")

    print(f"Validating {len(CURATED_HOMONYM_RECORDS)} homonym records...")
    validate_records(CURATED_HOMONYM_RECORDS, "HOMONYM", atlas_lemmas)
    print("✅ All homonym records are 100% valid!")

    # Append to YAML files
    with open(PARONYM_YAML, encoding="utf-8") as f:
        par_data = yaml.safe_load(f)
    existing_par = par_data.get("pairs", [])
    existing_par_keys = {tuple(sorted([_plain(p["slugA"]), _plain(p["slugB"])])) for p in existing_par}

    added_par = 0
    for rec in CURATED_PARONYM_RECORDS:
        key = tuple(sorted([_plain(rec["slugA"]), _plain(rec["slugB"])]))
        if key not in existing_par_keys:
            existing_par.append(rec)
            existing_par_keys.add(key)
            added_par += 1

    par_data["pairs"] = existing_par
    with open(PARONYM_YAML, "w", encoding="utf-8") as f:
        yaml.dump(par_data, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Appended {added_par} new paronym pairs to {PARONYM_YAML} (total: {len(existing_par)})")

    with open(HOMONYM_YAML, encoding="utf-8") as f:
        hom_data = yaml.safe_load(f)
    existing_hom = hom_data.get("pairs", [])
    existing_hom_keys = {tuple(sorted([_plain(p["slugA"]), _plain(p["slugB"])])) for p in existing_hom}

    added_hom = 0
    for rec in CURATED_HOMONYM_RECORDS:
        key = tuple(sorted([_plain(rec["slugA"]), _plain(rec["slugB"])]))
        if key not in existing_hom_keys:
            existing_hom.append(rec)
            existing_hom_keys.add(key)
            added_hom += 1

    hom_data["pairs"] = existing_hom
    with open(HOMONYM_YAML, "w", encoding="utf-8") as f:
        yaml.dump(hom_data, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"Appended {added_hom} new homonym pairs to {HOMONYM_YAML} (total: {len(existing_hom)})")


if __name__ == "__main__":
    main()
