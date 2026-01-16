#!/usr/bin/env python3
"""
Generate B2-HIST expansion: manifest entries and skeleton files.
Based on B2-HIST-CURRICULUM-PLAN-EXPANDED.md
"""

import os
from pathlib import Path

# Base paths
CURRICULUM_DIR = Path("/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist")

# Complete module list from expanded plan (140 modules)
# Format: (slug, title_uk, phase, is_new, is_expanded)
EXPANDED_MODULES = [
    # Phase HIST.1: Origins & Early Civilizations (M01-08)
    ("trypillian-civilization", "Трипільська цивілізація", "HIST.1", False, False),
    ("scythians-sarmatians", "Скіфи та сармати", "HIST.1", False, False),
    ("greeks-crimea-olbia", "Грецькі міста-держави: Ольвія, Херсонес", "HIST.1", True, False),
    ("sloviany-origins", "Слов'яни: Походження та розселення", "HIST.1", False, False),  # renamed from sloviany-na-ukrainskykh-zemliakh
    ("slavic-tribes", "Слов'янські племена на українських землях", "HIST.1", False, True),
    ("zasnuvannia-kyieva", "Заснування Києва: Легенда і археологія", "HIST.1", False, False),
    ("khozary-i-sloviany", "Хозарський каганат і слов'яни", "HIST.1", True, False),
    ("syntez-vytoky-1", "Синтез: Від Трипілля до Києва", "HIST.1", False, False),  # renamed from syntez-vytoky

    # Phase HIST.2: Kyivan Rus (M09-20)
    ("oleh-ihor", "Олег та Ігор: Перші правителі", "HIST.2", True, False),
    ("olha-sviatoslav", "Ольга та Святослав", "HIST.2", True, False),
    ("volodymyr-khreshchennia", "Володимир і Хрещення Русі", "HIST.2", False, False),  # renamed
    ("yaroslav-wise", "Ярослав Мудрий: Золота доба", "HIST.2", False, False),  # renamed
    ("ruska-pravda", "Руська Правда: Перший законодавчий кодекс", "HIST.2", True, False),
    ("sofiya-kyivska", "Софія Київська та культурний розквіт", "HIST.2", True, False),
    ("volodymyr-monomakh", "Володимир Мономах", "HIST.2", True, False),
    ("kultura-kyivskoi-rusi", "Культура Київської Русі", "HIST.2", False, False),
    ("kniazivski-usobiytsi", "Княжі усобиці та роздроблення", "HIST.2", False, True),  # renamed from zanepad-i-rozdroblennia
    ("ludy-rusi", "Люди Русі: Суспільство та побут", "HIST.2", True, False),
    ("rus-ta-susidy", "Русь та сусіди: Візантія, Польща, Угорщина", "HIST.2", True, False),
    ("syntez-kyivska-rus", "Синтез: Київська Русь — спадщина", "HIST.2", True, False),

    # Phase HIST.3: Mongol Era & Galicia-Volhynia (M21-28)
    ("mongolska-navala", "Монгольська навала 1240", "HIST.3", False, False),  # renamed
    ("mykhailo-chernigivskyi", "Михайло Чернігівський: Опір Орді", "HIST.3", True, False),
    ("danylo-halytskyi", "Данило Галицький: Король України", "HIST.3", False, True),
    ("galytsko-volynska-derzhava", "Галицько-Волинська держава", "HIST.3", False, False),  # renamed
    ("boiare-i-shliakhta", "Бояри і шляхта: Соціальні верстви", "HIST.3", True, False),
    ("kinets-halytsko-volyni", "Кінець Галицько-Волинської держави", "HIST.3", True, False),
    ("krymske-khanstvo", "Кримське ханство: Виникнення", "HIST.3", True, False),
    ("syntez-dvokniazivstvo", "Синтез: Від Русі до занепаду", "HIST.3", True, False),

    # Phase HIST.4: Lithuanian-Polish Era (M29-40)
    ("velyke-kniazivstvo-lytovske", "Велике князівство Литовське", "HIST.4", False, False),
    ("ukrainski-zemli-u-vkl", "Українські землі у ВКЛ", "HIST.4", True, False),
    ("liublinska-uniia", "Люблінська унія 1569", "HIST.4", True, False),
    ("rich-pospolyta", "Річ Посполита: Устрій", "HIST.4", False, False),
    ("beresteyska-uniia", "Берестейська унія: Церковний розкол", "HIST.4", True, False),
    ("pravoslavna-tserkva-17", "Православна церква XVII століття", "HIST.4", True, False),
    ("petro-mohyla", "Петро Могила: Реформатор церкви", "HIST.4", True, False),
    ("bratstva-i-osvita", "Братства та освіта: Острозька академія", "HIST.4", True, False),
    ("bukovyna-zakarpattia", "Буковина та Закарпаття під сусідами", "HIST.4", True, False),
    ("slobozhanshchyna", "Слобожанщина: Заселення і розвиток", "HIST.4", True, False),
    ("liudy-ricchi-pospolytoi", "Люди Речі Посполитої: Суспільство", "HIST.4", True, False),
    ("syntez-lytva-polska", "Синтез: Литовсько-польська доба", "HIST.4", True, False),

    # Phase HIST.5: Rise of Cossacks (M41-50)
    ("kozatstvo-vytoky", "Козацтво: Витоки", "HIST.5", False, False),
    ("zaporizka-sich", "Запорізька Січ: Республіка", "HIST.5", False, False),
    ("dmytro-vyshnevetskyi", "Дмитро Вишневецький: Перший кошовий", "HIST.5", True, False),
    ("kozatski-povstannia-16", "Козацькі повстання XVI століття", "HIST.5", True, False),
    ("petro-sahaidachnyi", "Петро Сагайдачний: Гетьман і меценат", "HIST.5", True, False),
    ("khotynska-viyna", "Хотинська війна 1621", "HIST.5", True, False),
    ("kozatska-kultura", "Козацька культура та побут", "HIST.5", False, False),
    ("kozatske-viisko", "Козацьке військо та озброєння", "HIST.5", True, False),
    ("morski-pokhody", "Морські походи козаків", "HIST.5", True, False),
    ("syntez-kozatstvo-vytoky", "Синтез: Становлення козацтва", "HIST.5", True, False),

    # Phase HIST.6: Khmelnytsky & Cossack State (M51-62)
    ("khmelnychchyna-prychyny", "Хмельниччина: Передумови", "HIST.6", False, True),  # renamed
    ("bohdan-khmelnytskyi", "Богдан Хмельницький: Постать", "HIST.6", False, True),
    ("bitva-pid-zhovtymy-vodamy", "Битва під Жовтими Водами", "HIST.6", True, False),
    ("zborivska-bila-tserkva", "Зборівська та Білоцерківська угоди", "HIST.6", True, False),
    ("kozatska-derzhava", "Козацька держава: Устрій", "HIST.6", False, False),  # from khmelnychchyna-ii-derzhava
    ("pereyaslavska-uhoda", "Переяславська угода: Суть і наслідки", "HIST.6", False, True),  # renamed
    ("yurii-nemyrych", "Юрій Немирич: Гадяцька угода", "HIST.6", True, False),
    ("ruina-i", "Руїна I: Виговський та розкол", "HIST.6", False, False),  # renamed
    ("ruina-ii", "Руїна II: Дорошенко", "HIST.6", False, False),  # renamed
    ("andrusivske-peremyrya", "Андрусівське перемир'я: Поділ України", "HIST.6", True, False),
    ("ivan-sirko", "Іван Сірко: Легендарний кошовий", "HIST.6", True, False),
    ("syntez-khmelnychchyna", "Синтез: Козацька революція", "HIST.6", True, False),

    # Phase HIST.7: Mazepa & End of Hetmanate (M63-74)
    ("ivan-mazepa-derzhavnyk", "Іван Мазепа I: Державник", "HIST.7", False, False),  # renamed
    ("ivan-mazepa-kultura", "Іван Мазепа II: Культура", "HIST.7", False, False),  # renamed
    ("kost-hordiyenko", "Кость Гордієнко та Січ", "HIST.7", True, False),
    ("ivan-mazepa-poltava", "Іван Мазепа III: Полтава", "HIST.7", False, False),  # renamed
    ("pylyp-orlyk-konstytutsiia", "Пилип Орлик: Перша конституція", "HIST.7", True, False),
    ("hryhorii-skovoroda", "Григорій Сковорода: Філософ", "HIST.7", False, False),
    ("pavlo-polubotok", "Павло Полуботок: Останній наказний", "HIST.7", True, False),
    ("danylo-apostol", "Данило Апостол та Кирило Розумовський", "HIST.7", True, False),
    ("koliivshchyna", "Коліївщина та Гайдамаки", "HIST.7", True, False),
    ("opryshky", "Опришки Карпат", "HIST.7", True, False),
    ("petro-kalnyshevskyi", "Петро Калнишевський: Останній кошовий", "HIST.7", True, False),
    ("kinets-hetmanshchyny", "Кінець Гетьманщини і Січі", "HIST.7", False, False),

    # Phase HIST.8: Imperial Era (M75-86)
    ("rosiiska-imperiia-ukraina", "Україна в Російській імперії", "HIST.8", False, True),  # renamed
    ("habsburzka-halichyna", "Габсбурзька Галичина", "HIST.8", False, True),  # renamed from austrian-galicia
    ("pivden-novorosiia", "Південь: «Новоросія» — колонізація", "HIST.8", True, False),
    ("nova-serbiya", "Нова Сербія та заселення степів", "HIST.8", True, False),
    ("krypatsvo-selo", "Кріпацтво та селянське життя", "HIST.8", True, False),
    ("kyrylo-mefodiivtsi", "Кирило-Мефодіївське братство", "HIST.8", True, False),
    ("shevchenko-awakening", "Тарас Шевченко: Пробудження нації", "HIST.8", False, False),
    ("valuevskyi-emskyi", "Валуєвський циркуляр та Емський указ", "HIST.8", False, True),  # renamed
    ("hromady", "Громадівський рух", "HIST.8", True, False),
    ("drahomanov", "Михайло Драгоманов", "HIST.8", False, False),  # renamed from ideolhy-drahomanov-kulish
    ("franko-lesia-hrinchenko", "Франко, Леся, Грінченко", "HIST.8", False, False),
    ("syntez-imperska-doba", "Синтез: Імперська доба", "HIST.8", True, False),

    # Phase HIST.9: WWI & Revolution (M87-98)
    ("hrushevskyi", "Михайло Грушевський: Історик і політик", "HIST.9", False, False),  # renamed
    ("persha-svitova", "Перша світова війна: Українські землі", "HIST.9", False, False),  # renamed
    ("sichovi-striltsi", "Січові стрільці", "HIST.9", True, False),
    ("tsentralna-rada", "Центральна Рада: УНР", "HIST.9", False, True),
    ("skoropadskyi", "Павло Скоропадський: Гетьманат", "HIST.9", True, False),
    ("zunr", "ЗУНР: Західноукраїнська Народна Республіка", "HIST.9", False, True),
    ("dyrektoriia", "Директорія УНР", "HIST.9", True, False),
    ("symon-petliura", "Симон Петлюра", "HIST.9", True, False),
    ("bilshovytsko-ukrainska-viyna", "Більшовицько-українська війна", "HIST.9", True, False),
    ("kholodnyi-yar", "Холодний Яр: Останній опір", "HIST.9", True, False),
    ("karpatska-ukraina", "Карпатська Україна 1938-1939", "HIST.9", True, False),
    ("syntez-revoliutsiia", "Синтез: Українська революція", "HIST.9", True, False),

    # Phase HIST.10: Soviet Period & Tragedies (M99-108)
    ("rozstriliane-vidrodzennia", "Розстріляне відродження", "HIST.10", False, False),  # renamed
    ("mekhanizm-teroru", "Механізм терору", "HIST.10", False, False),  # renamed
    ("holodomor-mekhanizm", "Голодомор: Механізм", "HIST.10", False, False),
    ("holodomor-pamiat", "Голодомор: Пам'ять та визнання", "HIST.10", False, False),  # renamed
    ("pacyfikatsiia", "Пацифікація: Поляки в Галичині", "HIST.10", True, False),
    ("oun", "ОУН: Формування", "HIST.10", True, False),
    ("druha-svitova-pochatok", "Друга світова: Початок", "HIST.10", False, True),  # renamed
    ("babyn-yar", "Бабин Яр та Голокост в Україні", "HIST.10", True, False),
    ("upa", "УПА: Збройний опір", "HIST.10", False, True),  # renamed
    ("syntez-trahedii", "Синтез: Трагедії XX століття", "HIST.10", False, False),  # renamed

    # Phase HIST.11: Post-War Soviet Ukraine (M109-118)
    ("povoienne-vidbudova", "Повоєнна відбудова", "HIST.11", True, False),
    ("deportatsii-ukraintsiv", "Депортації українців 1944-1951", "HIST.11", False, True),
    ("surgunlik", "Сургунлік: Депортація кримських татар", "HIST.11", False, False),  # renamed
    ("krym-1954", "Крим 1954: Передача УРСР", "HIST.11", True, False),
    ("destalinizatsiia", "Десталінізація в Україні", "HIST.11", True, False),
    ("shistdesiatnyky", "Шістдесятники", "HIST.11", False, False),
    ("ukrainska-helsinska-hrupa", "Українська Гельсінська група", "HIST.11", True, False),
    ("afhanistan", "Українці в Афганістані", "HIST.11", True, False),
    ("chornobyl", "Чорнобиль", "HIST.11", False, False),
    ("diaspora", "Діаспора: Ковчег держави", "HIST.11", False, False),  # renamed

    # Phase HIST.12: Independence & Modern Era (M119-130)
    ("shliakh-nezalezhnosti", "Шлях до незалежності", "HIST.12", False, False),  # renamed
    ("rukh", "Рух: Народний рух України", "HIST.12", True, False),
    ("nezalezhnist-1991", "Проголошення незалежності", "HIST.12", False, True),
    ("ukraine-90s", "Україна 1990-х: Кучма та олігархи", "HIST.12", True, False),
    ("pomara-revoliutsiia", "Помаранчева революція", "HIST.12", False, False),  # renamed
    ("tomos", "Томос: Духовна незалежність", "HIST.12", False, False),  # renamed
    ("yanukovych", "Епоха Януковича", "HIST.12", False, False),  # renamed
    ("movna-polityka", "Мовна політика незалежної України", "HIST.12", True, False),
    ("revoliutsiia-hidnosti", "Революція Гідності", "HIST.12", False, False),
    ("aneksiia-krymu", "Анексія Криму", "HIST.12", False, False),
    ("krymski-tatary-pislia-2014", "Кримські татари після 2014", "HIST.12", True, False),
    ("syntez-nezalezhnist", "Синтез: Незалежна Україна", "HIST.12", True, False),

    # Phase HIST.13: Russian Aggression (M131-140)
    ("viyna-donbas", "Війна на Донбасі 2014-2022", "HIST.13", False, False),  # renamed
    ("povnomasshtabne-vtorhnessnia", "Повномасштабне вторгнення", "HIST.13", False, False),  # renamed (fixed typo)
    ("mariupol-azovstal", "Маріуполь та Азовсталь", "HIST.13", True, False),
    ("bucha-irpin", "Буча та Ірпінь: Злочини", "HIST.13", True, False),
    ("kakhovska-hes", "Каховська ГЕС: Екоцид", "HIST.13", True, False),
    ("voienna-ekonomika", "Воєнна економіка України", "HIST.13", True, False),
    ("hromadske-suspilstvo", "Громадянське суспільство у війні", "HIST.13", True, False),
    ("mizhnarodna-pidtrymka", "Міжнародна підтримка", "HIST.13", True, False),
    ("zlochyny-stiikist", "Злочини і стійкість", "HIST.13", False, False),  # renamed
    ("syntez-viyna", "Синтез: Війна за існування", "HIST.13", False, False),  # renamed
]

# Mapping from old slugs to new slugs (for existing files that need renaming)
SLUG_RENAMES = {
    "sloviany-na-ukrainskykh-zemliakh": "sloviany-origins",
    "syntez-vytoky": "syntez-vytoky-1",
    "volodymyr-i-khreshchennia": "volodymyr-khreshchennia",
    "yaroslav-the-wise": "yaroslav-wise",
    "zanepad-i-rozdroblennia": "kniazivski-usobiytsi",
    "mongolska-navala-1240": "mongolska-navala",
    "galytsko-volynske-knyazivstvo": "galytsko-volynska-derzhava",
    "khmelnychchyna-i-povstannia": "khmelnychchyna-prychyny",
    "khmelnychchyna-ii-derzhava": "kozatska-derzhava",
    "pereiaslav-treaty": "pereyaslavska-uhoda",
    "ruina-i-vyhovsky": "ruina-i",
    "ruina-ii-doroshenko": "ruina-ii",
    "ivan-mazepa-i-derzhavnyk": "ivan-mazepa-derzhavnyk",
    "ivan-mazepa-ii-kultura": "ivan-mazepa-kultura",
    "ivan-mazepa-iii-poltava": "ivan-mazepa-poltava",
    "rosiiska-imperiia-emskyi-ukaz": "rosiiska-imperiia-ukraina",
    "austrian-galicia": "habsburzka-halichyna",
    "ideolhy-drahomanov-kulish": "drahomanov",
    "mykhailo-hrushevskyi": "hrushevskyi",
    "first-world-war": "persha-svitova",
    "unr-zunr": "tsentralna-rada",  # split/reorganized
    "rozstriliane-vidrodzennia-postati": "rozstriliane-vidrodzennia",
    "rozstriliane-vidrodzhennia-ii-mekhanizm-teroru": "mekhanizm-teroru",
    "holodomor-ii-pamiat": "holodomor-pamiat",
    "druha-svitova-okupatsii": "druha-svitova-pochatok",
    "upa-i-zbroinyi-opir": "upa",
    "surgunlik-deportatsiia-1944": "surgunlik",
    "diaspora-kovcheh-derzhavy": "diaspora",
    "syntez-trahedii-xx-stolittia": "syntez-trahedii",
    "shliakh-do-nezalezhnosti": "shliakh-nezalezhnosti",
    "pomarancheva-revoliutsiia": "pomara-revoliutsiia",
    "dukhovnyi-front-tomos": "tomos",
    "epokha-yanukovycha": "yanukovych",
    "ukraine-1991-2004": "nezalezhnist-1991",
    "viina-na-donbasi-2014-2022": "viyna-donbas",
    "pownomasshtabne-wtorhnessnia": "povnomasshtabne-vtorhnessnia",
    "zlochyny-i-stiikist": "zlochyny-stiikist",
    "syntez-viyna-za-isnuvannya": "syntez-viyna",
    "syntez-kozachchyna-1920": None,  # to be removed/replaced
    "vistovtsi-neoclassicists": None,  # moved elsewhere
    "rosiiski-mify-pro-ukrainu": None,  # decolonization - integrated
    "povoienne-radianske-panuvannia": "deportatsii-ukraintsiv",  # reorganized
    "shliakh-do-voli": None,  # synthesis - replaced
}

# Phase descriptions for manifest
PHASE_NAMES = {
    "HIST.1": "Origins & Early Civilizations",
    "HIST.2": "Kyivan Rus",
    "HIST.3": "Mongol Era & Galicia-Volhynia",
    "HIST.4": "Lithuanian-Polish Era",
    "HIST.5": "Rise of Cossacks",
    "HIST.6": "Khmelnytsky & Cossack State",
    "HIST.7": "Mazepa & End of Hetmanate",
    "HIST.8": "Imperial Era",
    "HIST.9": "WWI & Revolution",
    "HIST.10": "Soviet Period & Tragedies",
    "HIST.11": "Post-War Soviet Ukraine",
    "HIST.12": "Independence & Modern Era",
    "HIST.13": "Russian Aggression",
}


def generate_manifest_yaml():
    """Generate YAML manifest section for b2-hist."""
    lines = []
    lines.append("  b2-hist:")
    lines.append("    name: B2 History Track - Ukrainian History (Expanded)")
    lines.append("    description: Ukrainian history from prehistoric times to present (140 modules)")
    lines.append("    prerequisite: b2-core-70")
    lines.append("    modules:")

    for i, (slug, title, phase, is_new, is_expanded) in enumerate(EXPANDED_MODULES, 1):
        phase_name = PHASE_NAMES.get(phase, phase)
        status = "NEW" if is_new else ("EXPANDED" if is_expanded else "")

        lines.append(f"    - slug: {slug}")
        lines.append(f"      title: \"{title}\"")
        lines.append(f"      phase: {phase} [{phase_name}]")
        lines.append(f"      focus: history")
        if "syntez" in slug.lower() or "синтез" in title.lower():
            lines.append(f"      type: synthesis")
        lines.append(f"      tags:")
        lines.append(f"      - history")
        lines.append(f"      - {phase.lower()}")
        if is_new:
            lines.append(f"      - new")
        if is_expanded:
            lines.append(f"      - expanded")

    return "\n".join(lines)


def get_new_modules():
    """Get list of truly NEW modules that need skeleton files."""
    return [(slug, title, phase) for slug, title, phase, is_new, _ in EXPANDED_MODULES if is_new]


def generate_skeleton_content(slug, title, phase):
    """Generate minimal skeleton markdown content for a new module."""
    phase_name = PHASE_NAMES.get(phase, phase)

    return f'''---
module: {slug}
title: "{title}"
level: B2
track: history
phase: {phase}
status: skeleton
---

# {title}

<!-- TODO: Content to be developed -->

## Вступ

[Вступний текст]

## Основний зміст

### Розділ 1

[Зміст]

### Розділ 2

[Зміст]

## Історичне значення

[Аналіз]

## Ключові постаті

[Біографічні нариси]

## Первинні джерела

> [Цитата з джерела]

## Підсумок

[Висновки]
'''


def create_skeleton_files():
    """Create skeleton files for new modules."""
    new_modules = get_new_modules()
    created = []

    for slug, title, phase in new_modules:
        filepath = CURRICULUM_DIR / f"{slug}.md"
        if not filepath.exists():
            content = generate_skeleton_content(slug, title, phase)
            filepath.write_text(content, encoding='utf-8')
            created.append(slug)
            print(f"Created: {slug}.md")
        else:
            print(f"Skipped (exists): {slug}.md")

    return created


def create_skeleton_activities():
    """Create skeleton activity YAML files for new modules."""
    new_modules = get_new_modules()
    activities_dir = CURRICULUM_DIR / "activities"
    activities_dir.mkdir(exist_ok=True)
    created = []

    for slug, title, phase in new_modules:
        filepath = activities_dir / f"{slug}.yaml"
        if not filepath.exists():
            content = f'''# Activities for {title}
# Status: skeleton - to be developed

- type: comprehension-questions
  title: "Питання на розуміння"
  questions:
    - question: "[Питання 1]"
      answer: "[Відповідь]"
    - question: "[Питання 2]"
      answer: "[Відповідь]"
'''
            filepath.write_text(content, encoding='utf-8')
            created.append(slug)
            print(f"Created activity: {slug}.yaml")
        else:
            print(f"Skipped (exists): activities/{slug}.yaml")

    return created


def create_skeleton_vocabulary():
    """Create skeleton vocabulary YAML files for new modules."""
    new_modules = get_new_modules()
    vocab_dir = CURRICULUM_DIR / "vocabulary"
    vocab_dir.mkdir(exist_ok=True)
    created = []

    for slug, title, phase in new_modules:
        filepath = vocab_dir / f"{slug}.yaml"
        if not filepath.exists():
            content = f'''# Vocabulary for {title}
# Status: skeleton - to be developed
# Target: 24-30 terms

terms: []
'''
            filepath.write_text(content, encoding='utf-8')
            created.append(slug)
            print(f"Created vocabulary: {slug}.yaml")
        else:
            print(f"Skipped (exists): vocabulary/{slug}.yaml")

    return created


def create_skeleton_meta():
    """Create skeleton meta YAML files for new modules."""
    new_modules = get_new_modules()
    meta_dir = CURRICULUM_DIR / "meta"
    meta_dir.mkdir(exist_ok=True)
    created = []

    for slug, title, phase in new_modules:
        phase_name = PHASE_NAMES.get(phase, phase)
        filepath = meta_dir / f"{slug}.yaml"
        if not filepath.exists():
            content = f'''# Meta for {title}
slug: {slug}
title: "{title}"
level: B2
track: history
phase: "{phase} [{phase_name}]"
status: skeleton
focus: history
prerequisites: []
learning_outcomes: []
'''
            filepath.write_text(content, encoding='utf-8')
            created.append(slug)
            print(f"Created meta: {slug}.yaml")
        else:
            print(f"Skipped (exists): meta/{slug}.yaml")

    return created


if __name__ == "__main__":
    print("=" * 60)
    print("B2-HIST Expansion Generator")
    print("=" * 60)

    new_modules = get_new_modules()
    print(f"\nNew modules to create: {len(new_modules)}")

    print("\n--- Creating skeleton markdown files ---")
    created_md = create_skeleton_files()

    print("\n--- Creating skeleton activity files ---")
    created_act = create_skeleton_activities()

    print("\n--- Creating skeleton vocabulary files ---")
    created_vocab = create_skeleton_vocabulary()

    print("\n--- Creating skeleton meta files ---")
    created_meta = create_skeleton_meta()

    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  - Markdown files created: {len(created_md)}")
    print(f"  - Activity files created: {len(created_act)}")
    print(f"  - Vocabulary files created: {len(created_vocab)}")
    print(f"  - Meta files created: {len(created_meta)}")
    print("=" * 60)

    print("\n--- Manifest YAML (save to curriculum.yaml) ---")
    print(generate_manifest_yaml())
