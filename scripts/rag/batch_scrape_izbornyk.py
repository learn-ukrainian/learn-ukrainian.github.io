"""Batch scrape all remaining texts from izbornyk.org.ua link pages.

Usage:
    .venv/bin/python scripts/rag/batch_scrape_izbornyk.py [--wave N] [--dry-run] [--start-from SLUG]

Scrapes texts organized into waves 5-10 by source page category.
"""

import subprocess
import sys
import time
from pathlib import Path

BASE = "http://izbornyk.org.ua"

# ══════════════════════════════════════════════════════════════════════
# Wave 5: Old Ukrainian Literature (inoldlit.htm)
# ══════════════════════════════════════════════════════════════════════
WAVE_5_OLDLIT = [
    # Anthologies & collections
    {"slug": "oldukr-xi-xiii", "url": f"{BASE}/oldukr2/oldukr2.htm", "work": "Українська література XI-XIII ст.", "author": "Антологія", "year": 1200, "genre": "anthology", "period": "old_east_slavic", "follow": True, "max_pages": 100},
    {"slug": "oldukr-xiv-xvi", "url": f"{BASE}/old14_16/old14.htm", "work": "Українська література XIV-XVI ст.", "author": "Антологія", "year": 1500, "genre": "anthology", "period": "middle_ukrainian", "follow": True, "max_pages": 100},
    {"slug": "oldukr-xvii", "url": f"{BASE}/old17/old17.htm", "work": "Українська література XVII ст.", "author": "Антологія", "year": 1650, "genre": "anthology", "period": "middle_ukrainian", "follow": True, "max_pages": 100},
    {"slug": "oldukr-xviii", "url": f"{BASE}/old18/old18.htm", "work": "Українська література XVIII ст.", "author": "Антологія", "year": 1750, "genre": "anthology", "period": "middle_ukrainian", "follow": True, "max_pages": 100},
    # Individual works
    {"slug": "velychkovsky", "url": f"{BASE}/velych/vel.htm", "work": "Іван Величковський. Твори", "author": "Величковський І.", "year": 1972, "genre": "poetry", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "suspilna-dumka-xvi-xvii", "url": f"{BASE}/suspil/sus.htm", "work": "Суспільно-політична думка XVI-XVII ст.", "author": "Антологія", "year": 1600, "genre": "polemic", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "humanisty-vidrodzennia", "url": f"{BASE}/human/hum.htm", "work": "Українські гуманісти епохи Відродження", "author": "Антологія", "year": 1550, "genre": "scholarly", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "klementiy-zinoviiv", "url": f"{BASE}/klyment/kly.htm", "work": "Климентій Зіновіїв. Вірші. Приповісті.", "author": "Зіновіїв К.", "year": 1971, "genre": "poetry", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "biletsky-khrestomatiia", "url": f"{BASE}/biletso/bilo.htm", "work": "Хрестоматія давньої української літератури (Білецький)", "author": "Білецький О.", "year": 1952, "genre": "anthology", "period": "modern", "follow": True, "max_pages": 100},
    {"slug": "yushkov-ruska-pravda", "url": f"{BASE}/yushkov/yu.htm", "work": "Руська Правда (Юшков)", "author": "Юшков С.", "year": 1935, "genre": "legal", "period": "old_east_slavic", "follow": True, "max_pages": 30},
    {"slug": "buhoslavsky-borys-hlib", "url": f"{BASE}/buhos/bu.htm", "work": "Україно-руські памʼятки про князів Бориса та Гліба", "author": "Бугославський С.", "year": 1928, "genre": "hagiography", "period": "old_east_slavic", "follow": True, "max_pages": 30},
    {"slug": "prokopovych-filosofski", "url": f"{BASE}/procop/proc.htm", "work": "Феофан Прокопович. Філософські твори", "author": "Прокопович Ф.", "year": 1981, "genre": "philosophy", "period": "middle_ukrainian", "follow": True, "max_pages": 60},
    {"slug": "dovhalevsky-poetyka", "url": f"{BASE}/dovg/dovg.htm", "work": "Митрофан Довгалевський. Поетика.", "author": "Довгалевський М.", "year": 1973, "genre": "rhetoric", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "skovoroda-tvory", "url": f"{BASE}/skovoroda/skov.htm", "work": "Григорій Сковорода. Повне зібрання творів", "author": "Сковорода Г.", "year": 1973, "genre": "philosophy", "period": "middle_ukrainian", "follow": True, "max_pages": 100},
    {"slug": "dramaturhiia-xix", "url": f"{BASE}/dramukr/dram.htm", "work": "Українська драматургія першої половини XIX ст.", "author": "Антологія", "year": 1958, "genre": "drama", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "hramoty-xv-rozov", "url": f"{BASE}/djvu/rozov_gramoty_xiv_xv.htm", "work": "Розов — Українські грамоти XIV-XV ст.", "author": "Розов В.", "year": 1928, "genre": "legal", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "hramoty-xv", "url": f"{BASE}/djvu/gramoty_xv.htm", "work": "Українські грамоти XV ст.", "author": "Колектив", "year": 1965, "genre": "legal", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "hramoty-volyn-xvi", "url": f"{BASE}/djvu/gramoty_volyn_xvi.htm", "work": "Волинські грамоти XVI ст.", "author": "Колектив", "year": 1995, "genre": "legal", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
]

# ══════════════════════════════════════════════════════════════════════
# Wave 6: Chronicles & Diaries (inlitop.htm) — not already scraped
# ══════════════════════════════════════════════════════════════════════
WAVE_6_CHRONICLES = [
    {"slug": "galvol-kostruba", "url": f"{BASE}/kostruba/gvl.htm", "work": "ГВЛ (переклад Коструби)", "author": "Коструба Т.", "year": 1936, "genre": "chronicle", "period": "old_east_slavic", "follow": True, "max_pages": 30},
    {"slug": "litovsko-biloruski", "url": f"{BASE}/psrl3235/lytov.htm", "work": "Литовсько-білоруські літописи та хроніки", "author": "ПСРЛ", "year": 1980, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 80},
    {"slug": "sofonovych-khronika", "url": f"{BASE}/sofon/sof.htm", "work": "Феодосій Софонович. Хроніка з літописців стародавніх", "author": "Софонович Ф.", "year": 1673, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "synopsis-1674", "url": f"{BASE}/synopsis/syn.htm", "work": "Синопсис. Київ, 1674", "author": "Невідомий", "year": 1674, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "khanenko-shchodennyk", "url": f"{BASE}/khanenko/khan.htm", "work": "Щоденник Миколи Ханенка (1719-1754)", "author": "Ханенко М.", "year": 1754, "genre": "diary", "period": "middle_ukrainian", "follow": True, "max_pages": 60},
    {"slug": "ostrozky-litopys", "url": f"{BASE}/ostrog/ostr.htm", "work": "Львівський та Острозький літописці (1498-1649)", "author": "Невідомий", "year": 1649, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 20},
    {"slug": "bilozersky-pivdennoruski", "url": f"{BASE}/bilozer/bilz.htm", "work": "Південноруські літописи (Білозерський)", "author": "Білозерський М.", "year": 1856, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "sborlet-zbirnyk", "url": f"{BASE}/sborlet/sborlet.htm", "work": "Добірка літописів (Київська археографічна комісія)", "author": "Колектив", "year": 1888, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "kyivskyi-litopys-xvii", "url": f"{BASE}/kyl/kyl.htm", "work": "Київський літопис першої чверті XVII ст.", "author": "Невідомий", "year": 1625, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 10},
    {"slug": "istrus-drach", "url": f"{BASE}/istrus/rusiv.htm", "work": "Історія Русів (переклад Драча)", "author": "Драч І.", "year": 2003, "genre": "chronicle", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "boplan-opys-ukrainy", "url": f"{BASE}/boplan/index.html", "work": "Боплан — Опис України (1660)", "author": "Боплан Г.", "year": 1660, "genre": "travelogue", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "chevalier-istoriia-viiny", "url": f"{BASE}/chevalier/shevl.htm", "work": "Шевальє — Історія війни козаків проти Польщі (1663)", "author": "Шевальє П.", "year": 1663, "genre": "travelogue", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "krman-shchodennyk", "url": f"{BASE}/krman/krm.htm", "work": "Даніел Крман — Подорожній щоденник (1708-1709)", "author": "Крман Д.", "year": 1709, "genre": "diary", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "scherer-litopys-malorosiyi", "url": f"{BASE}/scherer/sher.htm", "work": "Шерер — Літопис Малоросії (1788)", "author": "Шерер Ж.", "year": 1788, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "symonovskyi-korotky-opys", "url": f"{BASE}/symon/sym.htm", "work": "Симоновський — Короткий опис про козацький малоросійський народ", "author": "Симоновський П.", "year": 1765, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 50},
    {"slug": "rihelman-litopysna-opovid", "url": f"{BASE}/rigel/rig.htm", "work": "Рігельман — Літописна оповідь про Малу Росію", "author": "Рігельман О.", "year": 1785, "genre": "chronicle", "period": "middle_ukrainian", "follow": True, "max_pages": 80},
    {"slug": "deflise-etnohrafichnyi", "url": f"{BASE}/deflise/flise.htm", "work": "Де ля Фліз — Етнографічний опис (1854)", "author": "Де ля Фліз Д.", "year": 1854, "genre": "ethnography", "period": "modern", "follow": True, "max_pages": 30},
]

# ══════════════════════════════════════════════════════════════════════
# Wave 7: History & Political Thought (inistor.htm + inpolit.htm)
# ══════════════════════════════════════════════════════════════════════
WAVE_7_HISTORY = [
    {"slug": "hrushevsky-vybrani-statti", "url": f"{BASE}/hrs/hrs.htm", "work": "Грушевський — Вибрані статті", "author": "Грушевський М.", "year": 1920, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "dvornik-sloviany", "url": f"{BASE}/dvornik/dv.htm", "work": "Дворнік — Слов'яни в Європейській історії та цивілізації", "author": "Дворнік Ф.", "year": 2000, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "krypyakevych-gvk", "url": f"{BASE}/krypgvol/krypgv.htm", "work": "Крип'якевич — Галицько-Волинське князівство", "author": "Крип'якевич І.", "year": 1984, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "ivakin-kyiv-xiii-xvi", "url": f"{BASE}/ivakin/ivak.htm", "work": "Івакін — Історичний розвиток Києва XIII-XVI ст.", "author": "Івакін Г.", "year": 1996, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "shcherbak-kozatstvo", "url": f"{BASE}/coss1/shch.htm", "work": "Щербак — Українське козацтво: формування соціального стану", "author": "Щербак В.", "year": 1999, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "holobutsky-zaporizhzhia", "url": f"{BASE}/holob/hol.htm", "work": "Голобуцький — Запорозьке козацтво", "author": "Голобуцький В.", "year": 1994, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "lytvynov-renesans-humanizm", "url": f"{BASE}/lytv/lyt.htm", "work": "Литвинов — Ренесансний гуманізм в Україні", "author": "Литвинов В.", "year": 2000, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "gvozdyk-pritsak-khmelnytsky", "url": f"{BASE}/coss2/gvpr.htm", "work": "Гвоздик-Пріцак — Економічна і політична візія Хмельницького", "author": "Гвоздик-Пріцак Л.", "year": 1999, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 40},
    {"slug": "matskiv-mazepa-dzherela", "url": f"{BASE}/coss4/mazk.htm", "work": "Мацьків — Гетьман Мазепа в західньоєвропейських джерелах", "author": "Мацьків Т.", "year": 1995, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "kohut-tsentralizm", "url": f"{BASE}/coss5/koh.htm", "work": "Когут — Російський централізм і українська автономія", "author": "Когут З.", "year": 1996, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "popovych-narys-kultury", "url": f"{BASE}/popovych/narys.htm", "work": "Попович — Нарис історії культури України", "author": "Попович М.", "year": 1998, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "istkult-t1-kyivska-rus", "url": f"{BASE}/istkult/ikult.htm", "work": "Історія української культури. Т.1. Київська Русь", "author": "Колектив", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "istkult-t2-xiii-xvii", "url": f"{BASE}/istkult2/ikult2.htm", "work": "Історія української культури. Т.2. XIII-XVII ст.", "author": "Колектив", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "krypyakevych-istkult", "url": f"{BASE}/krypcult/krcult.htm", "work": "Крип'якевич — Історія української культури (1937)", "author": "Крип'якевич І.", "year": 1937, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "antonovych-kultura", "url": f"{BASE}/cultur/cult.htm", "work": "Українська культура (лекції за ред. Антоновича)", "author": "Антонович Д.", "year": 1993, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "nalyvaiko-ochyma-zakhodu", "url": f"{BASE}/ochyma/ochrus.htm", "work": "Наливайко — Очима Заходу: Рецепція України XI-XVIII ст.", "author": "Наливайко Д.", "year": 2008, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "shevchenko-ukraina-skhid-zakhid", "url": f"{BASE}/ishevch/ishev.htm", "work": "Шевченко — Україна між Сходом і Заходом", "author": "Шевченко І.", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "ohiyenko-tserka", "url": f"{BASE}/ohienko/oh.htm", "work": "Огієнко — Українська церква", "author": "Огієнко І.", "year": 1993, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "antonovych-vybrani", "url": f"{BASE}/anton/ant.htm", "work": "Антонович — Вибрані праці", "author": "Антонович В.", "year": 1900, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "ukrxx-derzhavnist", "url": f"{BASE}/ukrxx/zmist.htm", "work": "Українська державність у XX столітті", "author": "Колектив", "year": 1996, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "statut-1566", "url": f"{BASE}/statut2/st1566.htm", "work": "Другий (Волинський) статут ВКЛ 1566 року", "author": "ВКЛ", "year": 1566, "genre": "legal", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    # Political thought
    {"slug": "entsyklopediia-ukrainoznavstva", "url": f"{BASE}/encycl/eu.htm", "work": "Енциклопедія українознавства", "author": "Колектив", "year": 1955, "genre": "encyclopedia", "period": "modern", "follow": True, "max_pages": 200},
    {"slug": "dzyuba-internatsionalizm", "url": f"{BASE}/idzuba/dz.htm", "work": "Дзюба — Інтернаціоналізм чи русифікація?", "author": "Дзюба І.", "year": 1968, "genre": "polemic", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "drahomanov-vybrani", "url": f"{BASE}/drag/drag.htm", "work": "Драгоманов — Вибрані праці", "author": "Драгоманов М.", "year": 1880, "genre": "polemic", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "hrinchenko-drahomanov", "url": f"{BASE}/drag/drag2.htm", "work": "Грінченко-Драгоманов — Діалоги про українську національну справу", "author": "Грінченко Б.", "year": 1894, "genre": "polemic", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "kostomarov-slovyanska-mifolohiia", "url": f"{BASE}/kostomar/kos.htm", "work": "Костомаров — Слов'янська міфологія", "author": "Костомаров М.", "year": 1847, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "thompson-trubadury", "url": f"{BASE}/thompson/tom.htm", "work": "Томпсон — Трубадури імперії", "author": "Томпсон Е.", "year": 2006, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "voloshyn-vybrani", "url": f"{BASE}/volosh/volosh.htm", "work": "Волошин — Вибрані твори", "author": "Волошин А.", "year": 2002, "genre": "polemic", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "grendzha-karpat-ukraina", "url": f"{BASE}/grendzha/grendzh.htm", "work": "Ґренджа-Донський — Щастя і горе Карпатської України", "author": "Ґренджа-Донський В.", "year": 2002, "genre": "memoir", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "heroes-ukr-kultura", "url": f"{BASE}/heroes/hero.htm", "work": "Героїчне та знаменитості в українській культурі", "author": "Колектив", "year": 1999, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 40},
    {"slug": "yushkov-feodalizm", "url": f"{BASE}/yushkov2/yush.htm", "work": "Юшков — Нариси з історії виникнення і початкового розвитку феодалізму", "author": "Юшков С.", "year": 1939, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "dzyuba-pavlenko-litopys-kultury", "url": f"{BASE}/dzuba/dzubapered.htm", "work": "Дзюба, Павленко — Літопис культурного життя X-XVII ст.", "author": "Дзюба О.", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
]

# ══════════════════════════════════════════════════════════════════════
# Wave 8: Literary Studies (inliter.htm)
# ══════════════════════════════════════════════════════════════════════
WAVE_8_LITERARY = [
    {"slug": "ukr-lit-entsyklopediia", "url": f"{BASE}/ulencycl/ule.htm", "work": "Українська літературна енциклопедія (1988-1995)", "author": "Колектив", "year": 1995, "genre": "encyclopedia", "period": "modern", "follow": True, "max_pages": 100},
    {"slug": "chyzhevsky-baroko", "url": f"{BASE}/chyzh/chyb.htm", "work": "Чижевський — Українське літературне бароко", "author": "Чижевський Д.", "year": 2003, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "chyzhevsky-filosofiia", "url": f"{BASE}/chyph/chyph.htm", "work": "Чижевський — Нариси з історії філософії на Україні", "author": "Чижевський Д.", "year": 1992, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "chyzhevsky-skovoroda", "url": f"{BASE}/chysk/chysk.htm", "work": "Чижевський — Філософія Сковороди", "author": "Чижевський Д.", "year": 2004, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "hrabovych-do-istoriyi", "url": f"{BASE}/hrabo/hr.htm", "work": "Грабович — До історії української літератури", "author": "Грабович Г.", "year": 1997, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "hensiorsky-gvl-process", "url": f"{BASE}/hens2/hs.htm", "work": "Генсьорський — ГВЛ як пам'ятка літератури (1958)", "author": "Генсьорський А.", "year": 1958, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "hensiorsky-gvl-mova", "url": f"{BASE}/hens1/hn.htm", "work": "Генсьорський — ГВЛ лексичні та стилістичні особливості", "author": "Генсьорський А.", "year": 1961, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "ohdruk-istoriia-drukarstva", "url": f"{BASE}/ohdruk/ohd.htm", "work": "Огієнко — Історія українського друкарства (1925)", "author": "Огієнко І.", "year": 1994, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "isaievych-knyhovydannia", "url": f"{BASE}/isaevych/is.htm", "work": "Ісаєвич — Українське книговидання", "author": "Ісаєвич Я.", "year": 2002, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "masliuk-poetyky-rytoryky", "url": f"{BASE}/masluk/mas.htm", "work": "Маслюк — Латиномовні поетики і риторики XVII-XVIII ст.", "author": "Маслюк В.", "year": 1983, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "biletsky-ruska-pravda-tekst", "url": f"{BASE}/bilets/bil.htm", "work": "Білецький — Руська Правда й історія її тексту", "author": "Білецький О.", "year": 1993, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "fdm-biobibliohrafichnyi", "url": f"{BASE}/fdm/fdm.htm", "work": "Філософська думка в Україні — біобібліографічний словник", "author": "Колектив", "year": 2002, "genre": "encyclopedia", "period": "modern", "follow": True, "max_pages": 80},
]

# ══════════════════════════════════════════════════════════════════════
# Wave 9: Linguistics (inmovozn.htm) + Grammars/Lexicons (inlex.htm)
# ══════════════════════════════════════════════════════════════════════
WAVE_9_LINGUISTICS = [
    {"slug": "shevelov-fonolohiia", "url": f"{BASE}/shevelov/shev.htm", "work": "Шевельов — Історична фонологія української мови", "author": "Шевельов Ю.", "year": 2002, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "ohiyenko-ist-lit-movy", "url": f"{BASE}/ohukr/ohu.htm", "work": "Огієнко — Історія української літературної мови (1949)", "author": "Огієнко І.", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "rusanivsky-ist-lit-movy", "url": f"{BASE}/rusaniv/ru.htm", "work": "Русанівський — Історія укр. літ. мови", "author": "Русанівський В.", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "skhidnoslov-hramatyky", "url": f"{BASE}/stsl/stsl.htm", "work": "Східнослов'янські граматики XVI-XVII ст. (статті)", "author": "Колектив", "year": 1982, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 30},
    {"slug": "pivtorak-pokhodzhennia", "url": f"{BASE}/pivtorak/pivt.htm", "work": "Півторак — Походження українців, росіян, білорусів та їхніх мов", "author": "Півторак Г.", "year": 2001, "genre": "scholarly", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "pravopys-2015", "url": f"{BASE}/pravopys/pravopys2015.htm", "work": "Український правопис 2015", "author": "НАН України", "year": 2015, "genre": "reference", "period": "modern", "follow": True, "max_pages": 50},
    # Lexicons & Grammars
    {"slug": "fedorovych-azbuka-1578", "url": f"{BASE}/fedorovych2/cf.htm", "work": "Іван Федорович — Азбука (Острог, 1578)", "author": "Федорович І.", "year": 1578, "genre": "grammar", "period": "middle_ukrainian", "follow": True, "max_pages": 20},
    {"slug": "verbytsky-bukvar-1627", "url": f"{BASE}/verbbuk/ver.htm", "work": "Тимофій Вербицький — Буквар (Київ, 1627)", "author": "Вербицький Т.", "year": 1627, "genre": "grammar", "period": "middle_ukrainian", "follow": True, "max_pages": 20},
    {"slug": "uzhevych-hramatyka", "url": f"{BASE}/uzhgram/uz.htm", "work": "Іван Ужевич — Граматика слов'янська (1643/1645)", "author": "Ужевич І.", "year": 1645, "genre": "grammar", "period": "middle_ukrainian", "follow": True, "max_pages": 30},
    {"slug": "uzhevych-paryzky", "url": f"{BASE}/uzhgram/uzp.htm", "work": "Ужевич — Паризький рукопис (переклад 1970)", "author": "Ужевич І.", "year": 1970, "genre": "grammar", "period": "middle_ukrainian", "follow": True, "max_pages": 20},
    {"slug": "rech-zhydovskoho-1282", "url": f"{BASE}/zyzlex/zyz101.htm", "work": "Речь жидовського язика (1282)", "author": "Невідомий", "year": 1282, "genre": "lexicon", "period": "old_east_slavic", "follow": True, "max_pages": 10},
    {"slug": "tlkovaniye-1431", "url": f"{BASE}/zyzlex/zyz102.htm", "work": "Тлкованіє неудобъ познаваємомъ... (1431)", "author": "Невідомий", "year": 1431, "genre": "lexicon", "period": "old_east_slavic", "follow": True, "max_pages": 10},
    {"slug": "synonima-slavenoroskaia", "url": f"{BASE}/zyzlex/zyz70.htm", "work": "Синоніма славеноросская", "author": "Невідомий", "year": 1650, "genre": "lexicon", "period": "middle_ukrainian", "follow": True, "max_pages": 20},
]

# ══════════════════════════════════════════════════════════════════════
# Wave 10: Shevchenko (taras_shevchenko.htm)
# ══════════════════════════════════════════════════════════════════════
WAVE_10_SHEVCHENKO = [
    {"slug": "shevchenko-tvory-t1", "url": f"{BASE}/shevchenko/shev.htm", "work": "Шевченко — Повне зібрання творів, т.1", "author": "Шевченко Т.", "year": 1961, "genre": "poetry", "period": "modern", "follow": True, "max_pages": 100},
    {"slug": "shevchenko-litopys-zhyttia", "url": f"{BASE}/shevchenko/litop.htm", "work": "Анісов, Середа — Літопис життя Шевченка", "author": "Анісов В., Середа В.", "year": 1976, "genre": "biography", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "shevchenkivsky-slovnyk", "url": f"{BASE}/shevchenko/slovn.htm", "work": "Шевченківський словник", "author": "Колектив", "year": 1977, "genre": "encyclopedia", "period": "modern", "follow": True, "max_pages": 100},
    {"slug": "spohady-pro-shevchenka", "url": f"{BASE}/shevchenko/spog.htm", "work": "Спогади про Шевченка (1982)", "author": "Колектив", "year": 1982, "genre": "memoir", "period": "modern", "follow": True, "max_pages": 80},
    {"slug": "shevchenko-epistoliariyi", "url": f"{BASE}/shevchenko/epis.htm", "work": "Шевченко в епістолярії (1966)", "author": "Колектив", "year": 1966, "genre": "letters", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "shevchenko-dokumenty", "url": f"{BASE}/shevchenko/docum.htm", "work": "Шевченко: Документи та матеріали (1982)", "author": "Колектив", "year": 1982, "genre": "documents", "period": "modern", "follow": True, "max_pages": 50},
    {"slug": "shevchenko-biohrafiia", "url": f"{BASE}/shevchenko/bio.htm", "work": "Шевченко. Біографія (1984)", "author": "Колектив", "year": 1984, "genre": "biography", "period": "modern", "follow": True, "max_pages": 60},
    {"slug": "konysky-shevchenko-khronika", "url": f"{BASE}/shevchenko/kony.htm", "work": "Кониський — Шевченко-Грушівський: Хроніка життя", "author": "Кониський О.", "year": 1991, "genre": "biography", "period": "modern", "follow": True, "max_pages": 60},
]

ALL_WAVES = {
    5: WAVE_5_OLDLIT,
    6: WAVE_6_CHRONICLES,
    7: WAVE_7_HISTORY,
    8: WAVE_8_LITERARY,
    9: WAVE_9_LINGUISTICS,
    10: WAVE_10_SHEVCHENKO,
}


def scrape_text(text: dict, wave_num: int, dry_run: bool = False) -> int:
    """Scrape a single text. Returns chunk count."""
    slug = text["slug"]
    output = Path(f"data/literary_texts/wave{wave_num}-{slug}.jsonl")

    if output.exists() and output.stat().st_size > 100:
        with open(output) as _f:
            count = sum(1 for _ in _f)
        print(f"  [skip] {slug} already exists ({count} chunks)")
        return 0

    cmd = [
        sys.executable, "scripts/rag/scrape_litopys.py",
        "--url", text["url"],
        "--work", text["work"],
        "--author", text["author"],
        "--year", str(text["year"]),
        "--genre", text["genre"],
        "--period", text["period"],
        "--output", str(output),
    ]
    if text.get("follow"):
        cmd.append("--follow-next")
        cmd.extend(["--max-pages", str(text.get("max_pages", 50))])

    if dry_run:
        print(f"  [dry-run] Would scrape: {slug} ({text['url']})")
        return 0

    print(f"  [scrape] {slug}: {text['work']}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"    [ERROR] {result.stderr[-200:] if result.stderr else 'unknown error'}")
        return 0

    if output.exists():
        with open(output) as _f:
            count = sum(1 for _ in _f)
        print(f"    -> {count} chunks")
        return count
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batch scrape izbornyk.org.ua")
    parser.add_argument("--wave", type=int, nargs="+", help="Wave(s) to scrape (5-10)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped")
    parser.add_argument("--start-from", type=str, help="Start from this slug (skip earlier)")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between texts (default: 2)")
    args = parser.parse_args()

    waves = args.wave or list(ALL_WAVES.keys())
    total = 0
    started = not args.start_from

    for wave_num in waves:
        texts = ALL_WAVES.get(wave_num, [])
        if not texts:
            print(f"Wave {wave_num}: no texts defined")
            continue

        print(f"\n{'='*60}")
        print(f"WAVE {wave_num}: {len(texts)} texts")
        print(f"{'='*60}")

        for text in texts:
            if not started:
                if text["slug"] == args.start_from:
                    started = True
                else:
                    print(f"  [skip] {text['slug']} (before --start-from)")
                    continue

            count = scrape_text(text, wave_num, dry_run=args.dry_run)
            total += count
            if count > 0 and not args.dry_run:
                time.sleep(args.delay)  # Be polite to the server

    print(f"\n{'='*60}")
    print(f"TOTAL: {total} new chunks scraped")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
