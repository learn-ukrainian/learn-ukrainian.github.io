#!/usr/bin/env python3
"""Batch-fix English titles in LIT track meta YAMLs.

Applies a hardcoded mapping of slug → correct Ukrainian title.
Uses double-quote YAML values to safely handle Ukrainian apostrophes (').

Usage:
    .venv/bin/python scripts/fix_lit_titles.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Mapping: track/slug → correct Ukrainian title
# Uses double-quote YAML values so Ukrainian apostrophes (') don't break parsing.
TITLE_MAP: dict[str, str] = {
    # ---------------------------------------------------------------------------
    # lit-fantastika
    # ---------------------------------------------------------------------------
    "lit-fantastika/arenev-powder": (
        "«Порошок»: Темне Фентезі Владислава Арєнєва"
    ),
    "lit-fantastika/arenev-soul-traps": (
        "«Пастки для душ»: Фентезі-цикл Владислава Арєнєва"
    ),
    "lit-fantastika/babenko-witch": (
        "Відьма у сучасній прозі: Фентезі Валентини Бабенко"
    ),
    "lit-fantastika/berdnyk-prometheus": (
        "«Дорога богів»: Прометеївський міф у прозі Олеся Бердника"
    ),
    "lit-fantastika/berdnyk-star-corsair-1": (
        "«Зоряний Корсар»: I — Пригода і Ноосфера в Олеся Бердника"
    ),
    "lit-fantastika/berdnyk-star-corsair-2": (
        "«Зоряний Корсар»: II — Філософія Творення і Космічна Свідомість"
    ),
    "lit-fantastika/deresh-arche": (
        "«Архе»: Постмодерна Готика Любка Дереша"
    ),
    "lit-fantastika/deresh-cult-psychotropic": (
        "«Культ»: Психоделічна Проза і Межа Реального у Любка Дереша"
    ),
    "lit-fantastika/fantastika-anthology": (
        "Антологія Фантастики: Еволюція Жанру від Романтизму до Сьогодні"
    ),
    "lit-fantastika/kidruk-bot-thriller": (
        "Технотрилер Макса Кідрука: Людина, Бот і Межа Свідомості"
    ),
    "lit-fantastika/kidruk-bots": (
        "«Боти»: Штучний Інтелект і Людяність у Прозі Макса Кідрука"
    ),
    "lit-fantastika/kidruk-colony": (
        "«Де немає Бога»: Марсіанська Колонія Макса Кідрука"
    ),
    "lit-fantastika/kidruk-colony-hard-scifi": (
        "Твердий Sci-Fi Кідрука: Наука, Катастрофа і Виживання"
    ),
    "lit-fantastika/korniy-chimaeras": (
        "«Химери»: Слов'янська Фентезі Дари Корній"
    ),
    "lit-fantastika/korniy-forest": (
        "Лісова Магія Дари Корній: Фольклорне Фентезі"
    ),
    "lit-fantastika/kotsiubynsky-shadows-revisit": (
        "«Тіні забутих предків»: Містичний і Галюцинаторний Вимір"
    ),
    "lit-fantastika/kvitka-dead-mans-easter": (
        "«Мертвецький Великдень»: Готика Квітки-Основ'яненка"
    ),
    "lit-fantastika/pavliuk-flesh": (
        "Тіло і Тінь: Темна Проза Сергія Павлюка"
    ),
    "lit-fantastika/rosokhovatsky-cyborgs": (
        "«Кіборги»: Наукова Фантастика Ігоря Росохватського"
    ),
    "lit-fantastika/smolych-beautiful-catastrophes": (
        "«Прекрасні катастрофи»: Утопія та Антиутопія Юрія Смолича"
    ),
    "lit-fantastika/storozhenko-devil": (
        "«Закоханий чорт» і Романтична Готика: Темна проза Олександра Стороженка"
    ),
    "lit-fantastika/vynnychenko-solar-machine-revisit": (
        "«Сонячна машина»: Утопія, Dystopia і SF-візія Винниченка"
    ),
    "lit-fantastika/vynnychuk-night-maiden": (
        "«Нічна дівчина»: Готика і Нічний Львів у Прозі Винничука"
    ),
    "lit-fantastika/vynnychuk-tango-death": (
        "«Танго смерті»: Міжвоєнна Галичина у Містичній Прозі Винничука"
    ),
    # ---------------------------------------------------------------------------
    # lit-drama
    # ---------------------------------------------------------------------------
    "lit-drama/karpenko-karyi-theatre": (
        "Іван Карпенко-Карий: Від Бурлаки до Хазяїна — Мистецтво Корифея"
    ),
    "lit-drama/kulish-dramaturgy": (
        "Микола Куліш: Драматургія Розстріляного Відродження"
    ),
    "lit-drama/kulish-myna-mazailo": (
        "«Мина Мазайло»: Мовна Комедія як Трагічний Документ Доби"
    ),
    "lit-drama/kulish-narodnyi-malahii": (
        "«Народний Малахій»: Утопія і Безумство у Драмі Куліша"
    ),
    "lit-drama/kulish-pathetique": (
        "«Патетична Соната»: Революція, Інтелектуал і Трагедія Нації"
    ),
    "lit-drama/kurbas-berezil-theater": (
        "«Березіль»: Театр Леся Курбаса як Лабораторія Авангарду"
    ),
    "lit-drama/kurbas-legacy": (
        "Спадщина Леся Курбаса: Від Розстрілу до Реабілітації"
    ),
    "lit-drama/kurbas-philosophy": (
        "Філософія Сцени: Курбас про Природу Театру і Актора"
    ),
    # ---------------------------------------------------------------------------
    # lit-doc
    # ---------------------------------------------------------------------------
    "lit-doc/amelina-women-looking-at-war": (
        "Вікторія Амеліна: Жінки, Що Дивляться на Війну"
    ),
    "lit-doc/aseyev-camp-paradise": (
        "Станіслав Асєєв: «Світлий шлях» — Концтабір як Документ"
    ),
    "lit-doc/aseyev-isolation-donetsk": (
        "Станіслав Асєєв: Репортажі з Окупованого Донецька"
    ),
    "lit-doc/aseyev-the-torture-camp": (
        "Станіслав Асєєв: «Таборовий майданчик» — Свідчення Катування"
    ),
    "lit-doc/kipiani-case-of-stus": (
        "Вахтанг Кіпіані: «Справа Василя Стуса» — Архів і Присуд"
    ),
    "lit-doc/matviichuk-human-rights": (
        "Олександра Матвійчук: Документ як Правозахисна Зброя"
    ),
    "lit-doc/vakulenko-occupation-diary": (
        "Щоденник Окупації: Останні Записи Вол. Вакуленка-Кришталя"
    ),
    "lit-doc/yermolenko-philosophical-narrative": (
        "Володимир Єрмоленко: Філософський Нарис як Свідчення Доби"
    ),
    # ---------------------------------------------------------------------------
    # lit-humor
    # ---------------------------------------------------------------------------
    "lit-humor/andrukhovych-postmodern-irony": (
        "Юрій Андрухович: Постмодерна Іронія як Художній Метод"
    ),
    "lit-humor/hlazovyi-satire": (
        "Анатолій Глазовий: Майстер Байки і Сатиричного Слова"
    ),
    "lit-humor/ilchenko-cossack-mamai": (
        "«Козацькому роду нема переводу»: Олесь Ільченко і Козацький Гумор"
    ),
    "lit-humor/kotliarevsky-laughter": (
        "«Енеїда»: Бурлеск і Сміх як Зброя у Котляревського"
    ),
    "lit-humor/lyubka-carbide-satire": (
        "«Карбід»: Закарпатська Гумореска Андрія Любки"
    ),
    "lit-humor/modern-memes-as-folklore": (
        "Мем як Фольклор: Цифровий Гумор у Сучасній Україні"
    ),
    "lit-humor/nechuy-levytsky-kaidash-humor": (
        "Комічне в «Кайдашевій сім'ї»: Нечуй-Левицький і Народний Гумор"
    ),
    "lit-humor/ostap-vyshnia-prison": (
        "Остап Вишня в Засланні: Сміх як Зброя Виживання"
    ),
    "lit-humor/ostap-vyshnia-smiles-1": (
        "«Усмішки»: I — Мистецтво Народного Гумору Остапа Вишні"
    ),
    "lit-humor/ostap-vyshnia-smiles-2": (
        "«Усмішки»: II — Пейзаж, Побут і Народна Душа в Гуморесках"
    ),
    "lit-humor/poderviansky-hamlet-critique": (
        "«Гамлет, або Феномен данського інтелігентизму»: Театральний Абсурд Подерв'янського"
    ),
    "lit-humor/rudansky-spivomovky": (
        "«Співомовки»: Народний Сміх Степана Руданського"
    ),
    "lit-humor/vynnychuk-hoaxes": (
        "Містифікація як Жанр: Юрій Винничук і Гра з Читачем"
    ),
    # ---------------------------------------------------------------------------
    # lit-war
    # ---------------------------------------------------------------------------
    "lit-war/amelina-new-renaissance": (
        "«Нове Розстріляне відродження»: Амеліна про Письменників на Війні"
    ),
    "lit-war/babich-poetry": (
        "Глеб Бабіч «Лєнтяй»: Поезія з Передової"
    ),
    "lit-war/bilozerska-diary": (
        "Олена Білозерська: Щоденник Снайперки — Жіночий Голос Фронту"
    ),
    "lit-war/chekh-absolute-zero": (
        "«Абсолютний нуль»: Артем Чех і Проза АТО"
    ),
    "lit-war/chekh-point-zero": (
        "«Точка нуль»: Артем Чех про Повернення з Фронту"
    ),
    "lit-war/kalytko-borders-lit": (
        "Катерина Калитко: Поезія на Межі — Голос Покоління Війни"
    ),
    "lit-war/kotsyubailo-legacy-lit": (
        "Дмитро «Да Вінчі» Коцюбайло: Від Бійця до Культурного Символу"
    ),
    "lit-war/lozko-poetry-of-maidan": (
        "Поезія Майдану: Слово як Зброя Революції Гідності"
    ),
    "lit-war/maksym-kryvtsov-poetry": (
        "Максим Кривцов «Лось»: Поет, Що Загинув і Став Легендою"
    ),
    "lit-war/markus-infantry": (
        "«Піхота»: Валерій Маркус і Проза Окопів"
    ),
    "lit-war/markus-traces-on-road": (
        "«Сліди на дорозі»: Валерій Маркус — Щоденник Ротного"
    ),
    "lit-war/polozhiy-ilovaisk": (
        "«Іловайськ»: Сергій Положій і Хроніка Катастрофи"
    ),
    "lit-war/yakimchuk-apricots-war": (
        "«Абрикоси Донбасу»: Поезія Любові Якимчук між Домом і Втратою"
    ),
    "lit-war/yaryna-chornohuz-war": (
        "Ярина Чорногуз: Поезія Опору і Жіночий Голос на Фронті"
    ),
    "lit-war/yashchenko-donbas-stories": (
        "Оповідання з Донбасу: Іван Ященко і Голоси Окупованого Краю"
    ),
    "lit-war/zernya-daughter-donetsk": (
        "«Доця»: Тамара Горіха Зерня і Жінка з Окупованого Міста"
    ),
    "lit-war/zhadan-internat-war": (
        "«Інтернат»: Сергій Жадан — Людина між Двох Вогнів"
    ),
    "lit-war/zhadan-life-maria": (
        "«Життя Марії»: Сергій Жадан — Фронтова Поема"
    ),
    # ---------------------------------------------------------------------------
    # lit-hist-fic
    # ---------------------------------------------------------------------------
    "lit-hist-fic/bilyk-sword-ares": (
        "«Меч Арея»: Іван Білик і Таємниця Праісторичного Минулого України"
    ),
    "lit-hist-fic/ivanychuk-malvy": (
        "«Мальви»: Роман Іваничук — Козацька Драма на Чорноморських Берегах"
    ),
    "lit-hist-fic/ivanychuk-scar": (
        "«Шрами на скалі»: Роман Іваничук і Трагедія Карпатської Гуцульщини"
    ),
    "lit-hist-fic/ivanychuk-water": (
        "«Вода з каменю»: Роман Іваничук і Антигабсбурзький Опір"
    ),
    "lit-hist-fic/kokotyukha-chervonyi": (
        "«Червоний»: Андрій Кокотюха і Детектив з Революційного Києва"
    ),
    "lit-hist-fic/kokotyukha-red": (
        "Андрій Кокотюха: Жанр Українського Історичного Бойовика"
    ),
    "lit-hist-fic/kulish-black-council-revisit": (
        "«Чорна рада»: Куліш як Засновник Українського Історичного Роману"
    ),
    "lit-hist-fic/lepkyi-mazepa": (
        "«Мазепа»: Богдан Лепкий і Трагедія Гетьмана в Трилогії"
    ),
    "lit-hist-fic/lys-century-jacob": (
        "«Століття Якова»: Іван Лис і Волинська Пам'ять XX Ст."
    ),
    "lit-hist-fic/rafeyenko-long-times": (
        "«Довгий час»: Рафєєнко — Внутрішній Емігрант і Зміна Мов"
    ),
    "lit-hist-fic/shevchuk-three-leaves": (
        "«Три листочки за вікном»: Валерій Шевчук і Метафізична Проза"
    ),
    "lit-hist-fic/shklyar-black-raven-1": (
        "«Чорний ворон»: I — Холодноярська Республіка в Романі Шкляра"
    ),
    "lit-hist-fic/shklyar-black-raven-2": (
        "«Чорний ворон»: II — Партизанський Рух і Криваве Завершення"
    ),
    "lit-hist-fic/shklyar-marusia": (
        "«Маруся»: Шкляр і Легенда про Жінку-Отамана"
    ),
    "lit-hist-fic/starytsky-bohdan": (
        "«Богдан Хмельницький»: Михайло Старицький і Міф про Гетьмана"
    ),
    "lit-hist-fic/zahrebelny-death-in-kyiv": (
        "«Смерть у Києві»: Загребельний і Парсуна Давньоруського Правителя"
    ),
    "lit-hist-fic/zahrebelny-dyvo": (
        "«Диво»: Загребельний і Пам'ять про Будівничих Святої Софії"
    ),
    "lit-hist-fic/zahrebelny-roksolana-1": (
        "«Роксолана»: I — Настя Лисовська і Доля Полонянки на Порті"
    ),
    "lit-hist-fic/zahrebelny-roksolana-2": (
        "«Роксолана»: II — Хасекі Хуррем і Геополітика Гарему"
    ),
    # ---------------------------------------------------------------------------
    # lit-crimea
    # ---------------------------------------------------------------------------
    "lit-crimea/sentsov-numbers": (
        "«Числа»: Олег Сенцов — Від Кінорежисера до Символу Спротиву"
    ),
    "lit-crimea/sentsov-stories": (
        "«Оповідання»: Олег Сенцов — Проза з Полону"
    ),
    # ---------------------------------------------------------------------------
    # lit-youth
    # ---------------------------------------------------------------------------
    "lit-youth/andrusyak-adventures": (
        "Іван Андрусяк: Пригодницька Поезія для Дітей"
    ),
    "lit-youth/andrusyak-rabbits": (
        "«Мій кролик Ромчик»: Іван Андрусяк і Нова Хвиля Дитячої Прози"
    ),
    "lit-youth/bachynsky-140-decibels": (
        "«140 Децибелів»: Любко Баченський і Голос Нового Покоління"
    ),
    "lit-youth/blyznets-zemlyanyk": (
        "«Земляники»: Іван Близнець і Лірична Повість про Дитинство"
    ),
    "lit-youth/dermansky-chu-drove": (
        "Чу та Дровосік: Сашко Дерманський і Переосмислення Казки"
    ),
    "lit-youth/dermansky-monsters": (
        "«Корпорація монстрів»: Сашко Дерманський і Дитяча Абсурдистська Проза"
    ),
    "lit-youth/franko-fox-mykyta": (
        "«Лис Микита»: Іван Франко і Традиція Звіриного Епосу"
    ),
    "lit-youth/kids-folklore": (
        "Дитячий фольклор: Лічилки, Скоромовки і Традиція Народного Слова"
    ),
    "lit-youth/kids-poetry-anthology": (
        "Антологія Дитячої Поезії: від Олени Пчілки до Сучасних Авторів"
    ),
    "lit-youth/lutsyshyna-whale": (
        "Кит Оксани Луцишиної: Поетична Метафора Дитячого Світосприйняття"
    ),
    "lit-youth/malkovych-poems": (
        "Іван Малкович: Дитяча Поезія між Природою і Магією"
    ),
    "lit-youth/malyk-alice": (
        "«Аліса»: Наталія Малик і Жіноча Фентезі-Пригода для Підлітків"
    ),
    "lit-youth/nestayko-fantasy": (
        "Фантастична Проза Всеволода Нестайка: Дитяча Уява і Наукова Пригода"
    ),
    "lit-youth/nestayko-forest-school": (
        "«Школа над хмарами»: Нестайко і Мрія про Особливе Навчання"
    ),
    "lit-youth/nestayko-toreadors-1": (
        "«Тореадори з Васюківки»: I — Пригодницька Дитяча Класика Нестайка"
    ),
    "lit-youth/nestayko-toreadors-2": (
        "«Тореадори з Васюківки»: II — Павлуша і Яват на Шляху до Мрії"
    ),
    "lit-youth/nestayko-toreadors-3": (
        "«Тореадори з Васюківки»: III — Підсумок Трилогії і Постать Нестайка"
    ),
    "lit-youth/oksenyk-forest-valley": (
        "Лісова Долина: Природа і Дитинство в Поезії Василя Оксенюка"
    ),
    "lit-youth/pavliuk-rytm": (
        "«Ритм»: Сергій Павлюк і Верлібр у Сучасній Дитячій Поезії"
    ),
    "lit-youth/pchilka-fables": (
        "Олена Пчілка: Байки і Дитяча Поезія на Захисті Мови"
    ),
    "lit-youth/rutkivsky-dzhury": (
        "«Джури козацького роду»: Рутківський і Козацький Пригодницький Роман"
    ),
    "lit-youth/rutkivsky-dzhury-1": (
        "«Джури козацького роду»: I — Час Козацтва і Юнацький Дух"
    ),
    "lit-youth/rutkivsky-dzhury-2": (
        "«Джури козацького роду»: II — Тернистий Шлях до Запорізької Вольниці"
    ),
    "lit-youth/rutkivsky-dzhury-3": (
        "«Джури козацького роду»: III — Фінал Трилогії і Формування Героя"
    ),
    "lit-youth/starovyt-my-kyiv": (
        "«Мій Київ»: Мирослава Старовит і Місто-Казка для Дітей"
    ),
    "lit-youth/voronyna-agent-000": (
        "«Агент 000»: Марія Вороніна і Шпигунський Детектив для Підлітків"
    ),
    "lit-youth/vynnychuk-lviv-tales": (
        "Казки Старого Львова: Юрій Винничук і Міська Магія для Дітей"
    ),
    "lit-youth/zabila-poems": (
        "Наталя Забіла: Класична Дитяча Поезія Радянської Доби"
    ),
    "lit-youth/zavadovych-adventures": (
        "Роман Завадович: Пригодницька Проза для Юнацтва Діаспори"
    ),
    # ---------------------------------------------------------------------------
    # lit-essay
    # ---------------------------------------------------------------------------
    "lit-essay/chmut-institutions": (
        "Людмила Чмут: Культурні Інституції як Підвалини Нації"
    ),
    "lit-essay/chyzhevsky-baroque-history": (
        "Дмитро Чижевський: «Історія Літератури України» і Бароко як Вісь"
    ),
    "lit-essay/dontsov-chaos": (
        "Дмитро Донцов: «Дух нашої давнини» — Між Порядком і Хаосом"
    ),
    "lit-essay/dontsov-nationalism": (
        "«Націоналізм»: Дмитро Донцов і Чинний Ідеалізм"
    ),
    "lit-essay/drahomanov-chudatski-dumky": (
        "«Чудацькі думки»: Михайло Драгоманов і Ліберальна Традиція"
    ),
    "lit-essay/drahomanov-shevchenko": (
        "Драгоманов про Шевченка: Народництво і Літературна Критика"
    ),
    "lit-essay/dziuba-internationalism": (
        "«Інтернаціоналізм чи русифікація?»: Іван Дзюба і Голос Шістдесятництва"
    ),
    "lit-essay/essay-origins-polemics": (
        "Витоки Українського Есею: Полеміка XVI–XVII Ст. як Народження Жанру"
    ),
    "lit-essay/franko-some-words": (
        "«Декілька слів...»: Іван Франко і Маніфест Нового Реалізму"
    ),
    "lit-essay/franko-what-is-progress": (
        "«Що таке прогрес?»: Франко і Соціальна Думка Кінця XIX Ст."
    ),
    "lit-essay/grabowicz-myth-shevchenko": (
        "Григорій Грабович: «Поет як Міфотворець» — Шевченкознавство зі Сторони"
    ),
    "lit-essay/grabowicz-poet-prophet": (
        "Григорій Грабович: Шевченко і Образ Поета-Пророка"
    ),
    "lit-essay/hrytsak-history-ukraine": (
        "Ярослав Грицак: «Нарис Історії України» — Нова Критична Школа"
    ),
    "lit-essay/hrytsak-overcoming-past": (
        "Ярослав Грицак: «Подолання Минулого» — Пам'ять та Ідентичність"
    ),
    "lit-essay/khvylovy-thoughts-current": (
        "Хвильовий: «Думки проти течії» — Памфлети Культурної Революції"
    ),
    "lit-essay/khvylovy-ukraine-or-little-russia": (
        "Хвильовий: «Україна чи Малоросія?» — Орієнтація на Захід"
    ),
    "lit-essay/kipiani-case-of-stus": (
        "«Справа Василя Стуса»: Кіпіані і Жанр Документального Розслідування"
    ),
    "lit-essay/kostomarov-two-rus-nationalities": (
        "Костомаров: «Дві Руські Народності» — Витоки Відмінності"
    ),
    "lit-essay/kotsyubailo-legacy": (
        "Дмитро «Да Вінчі» Коцюбайло: Від Бійця до Культурного Символу"
    ),
    "lit-essay/lesia-ukrainka-voice": (
        "Леся Українка: Есеїстика і Голос Нового Жінка-Поета"
    ),
    "lit-essay/lutsky-diaspora-bridge": (
        "Юрій Луцький: Діаспора як Міст Між Двома Культурами"
    ),
    "lit-essay/lypynsky-ham-japheth": (
        "В'ячеслав Липинський: «Хам і Яфет» — Союз Аристократії і Народу"
    ),
    "lit-essay/lypynsky-letters-brothers": (
        "В'ячеслав Липинський: «Листи до братів-хліборобів» — Консервативна Традиція"
    ),
    "lit-essay/lysiah-rudnytsky-history": (
        "Іван Лисяк-Рудницький: «Між Історією та Політикою» і Діаспорна Думка"
    ),
    "lit-essay/malaniuk-little-russianism": (
        "Євген Маланюк: «Малоросіянство» — Синдром Колоніальної Свідомості"
    ),
    "lit-essay/mariia-berlinska-dignity": (
        "Марія Берлінська: «Людська гідність» і Документальна Есеїстика про Фронт"
    ),
    "lit-essay/marynovych-universe-barbed-wire": (
        "Мирослав Маринович: «Всесвіт за колючим дротом» — Свідчення Дисидента"
    ),
    "lit-essay/mikhnovsky-independent-ukraine": (
        "Микола Міхновський: «Самостійна Україна» — Перший Маніфест Незалежності"
    ),
    "lit-essay/oxana-hundorova-postcolonialism": (
        "Оксана Гундорова: «Транзитна Культура» і Постколоніальна Критика"
    ),
    "lit-essay/plokhy-frontline": (
        "Сергій Плохій: «Фронтова Лінія» і Нова Парадигма Українського Простору"
    ),
    "lit-essay/plokhy-gates-of-europe": (
        "Сергій Плохій: «Брама Європи» — Переосмислення Місця України в Цивілізації"
    ),
    "lit-essay/portnikov-bells": (
        "Віталій Портніков: «Дзвони» і Публіцистика про Духовну Незалежність"
    ),
    "lit-essay/portnikov-conclusion": (
        "Віталій Портніков: «Підсумок» — Журналістика як Суспільне Свідчення"
    ),
    "lit-essay/prokhasko-fm-halychyna": (
        "Тарас Прохасько: «FM Галичина» — Ліричний Есей про Рідний Простір"
    ),
    "lit-essay/riabchuk-two-ukraines": (
        "Микола Рябчук: «Дві України» — Образ Розколотого Суспільства"
    ),
    "lit-essay/sherekh-fifth-kharkiv": (
        "Юрій Шерех: «П'ята Харків'янка» і Есеїстика Еміграції"
    ),
    "lit-essay/shevelov-history-language": (
        "Юрій Шевельов: Есеїстика про Мову і Культурний Геноцид"
    ),
    "lit-essay/shevelov-moscow-maros": (
        "Юрій Шевельов: Москва, Маросейка і Культурний Колоніалізм"
    ),
    "lit-essay/snyder-dialogues": (
        "Тімоті Снайдер: «Дорога до несвободи» — Діалог із Заходом про Україну"
    ),
    "lit-essay/solomea-pavlychko-modernism": (
        "Соломія Павличко: «Дискурс модернізму» і Нове Жіноче Літературознавство"
    ),
    "lit-essay/stus-phenomenon": (
        "Феномен Василя Стуса: Поет-Мученик як Дзеркало Нації"
    ),
    "lit-essay/sverstiuk-cathedral": (
        "Євген Сверстюк: «Собор у риштованні» і Дисидентська Есеїстика"
    ),
    "lit-essay/vira-ageyeva-canon": (
        "Віра Агеєва: Жіночий Канон і Феміністична Критика в Українській Літературі"
    ),
    "lit-essay/yermolenko-fluid-ideologies": (
        "Володимир Єрмоленко: «Плинні ідеології» — Філософія Трансформацій"
    ),
    "lit-essay/zabuzhko-fortinbras": (
        "«Хроніки від Фортінбраса»: Забужко і Українська Інтелектуальна Есеїстика 1990-х"
    ),
    "lit-essay/zabuzhko-longest-journey": (
        "«Найдовша подорож»: Забужко — Особистий Маніфест у Час Вторгнення"
    ),
    "lit-essay/zabuzhko-notre-dame": (
        "«Notre Dame d'Ukraine»: Забужко і Образ Лесі Українки як Духовного Першообразу"
    ),
    "lit-essay/zerov-ad-fontes": (
        "«Ad fontes»: Микола Зеров і Неокласицизм як Повернення до Першоджерел"
    ),
}


def fix_title(file_path: Path, new_title: str, dry_run: bool) -> bool:
    """Replace the title line in a meta YAML using double quotes.
    Double quotes safely handle Ukrainian apostrophes (').
    Returns True if changed."""
    content = file_path.read_text(encoding="utf-8")
    # Match: title: 'old' or title: "old" or title: old (unquoted)
    pattern = re.compile(r'^(title:\s*).*$', re.MULTILINE)
    # Always use double quotes to avoid apostrophe issues in Ukrainian text
    new_line = f'title: "{new_title}"'
    new_content, n = pattern.subn(new_line, content, count=1)
    if n == 0:
        print(f"  WARN: no title line found in {file_path.name}")
        return False
    if new_content == content:
        return False  # already correct
    if dry_run:
        print(f"  [DRY-RUN] {file_path.parent.parent.name}/{file_path.name}")
        print(f"    → {new_title}")
    else:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  FIXED: {file_path.parent.parent.name}/{file_path.name}")
        print(f"    → {new_title}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-fix English titles in LIT track meta YAMLs")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    lit_root = PROJECT_ROOT / "curriculum" / "l2-uk-en"
    changed = 0
    skipped = 0

    for key, new_title in sorted(TITLE_MAP.items()):
        track, slug = key.split("/", 1)
        file_path = lit_root / track / "meta" / f"{slug}.yaml"
        if not file_path.exists():
            print(f"  MISSING: {file_path}")
            skipped += 1
            continue
        if fix_title(file_path, new_title, args.dry_run):
            changed += 1
        else:
            skipped += 1

    print(f"\nDone. Changed: {changed}, Skipped/unchanged: {skipped}")
    if args.dry_run:
        print("(dry-run — no files written)")


if __name__ == "__main__":
    main()
