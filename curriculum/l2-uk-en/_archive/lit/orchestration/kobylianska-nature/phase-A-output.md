 आदिवासीthought
CRITICAL INSTRUCTION 1: I must use specific tools where available. For reading files, I should use `read_file`.
CRITICAL INSTRUCTION 2: Before making tool calls, I must explicitly list out any related tools for the task at hand. Here, the related tools are `read_file`, `run_shell_command` (with cat), `grep_search`. I will use `read_file` because it's the most specific and appropriate tool for reading files.

I will read the three requested files:
1. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/lit/research/kobylianska-nature-research.md`
2. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/lit/kobylianska-nature.yaml`
3. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/lit/meta/kobylianska-nature.yaml`

I'll issue parallel `read_file` calls for these three files.
Then, based on the content, I will generate the output.
Wait, I will only need the output at the end. No editing files in place. Let's read first.
Remember to Output ONLY text. Let's do this step by step. First read the files.
Wait, the `read_file` tool can be called concurrently. Let's do that.
I am in Orchestration Mode since the prompt has `ROLE: You are a TEXT GENERATOR`.
I just read the prompt constraints:
"OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output between delimiters. DO NOT WRITE OR EDIT ANY FILES."
I will read the files.
Oh, I just realized I need to produce text output to stdout in the end. I will use `read_file` to get the content into my context. Then I will generate the response.
Wait, if I just produce the text output right away in the chat, it counts as "produce text output between delimiters". Yes, the user will parse my response. I am the TEXT GENERATOR. My ultimate output should be the text with delimiters.

Let's read the files. I'll read them in parallel.
File paths:
1: `curriculum/l2-uk-en/lit/research/kobylianska-nature-research.md`
2: `curriculum/l2-uk-en/plans/lit/kobylianska-nature.yaml`
3: `curriculum/l2-uk-en/lit/meta/kobylianska-nature.yaml` (from the project dir)
Project dir is `/Users/krisztiankoos/projects/learn-ukrainian/`
I'll use `read_file` for all three.
Wait, I can just use absolute paths or relative paths. I'll use absolute as provided.
Let's call `read_file`.
1: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/lit/research/kobylianska-nature-research.md`
2: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/lit/kobylianska-nature.yaml`
3: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/lit/meta/kobylianska-nature.yaml`
Wait, do I need to run a shell command or read_file? `read_file` is the tool.
Let's do this.
I'll use the concurrent call format.
"
===META_OUTLINE_START===
content_outline:
  - section: "Вступ та культурний контекст: Епоха модернізму"
    words: 350
    points:
      - "Історичні умови появи твору: криза народництва і позитивізму в кінці ХІХ ст., перехід української літератури до неоромантизму."
      - "Захоплення філософією віталізму Ф. Ніцше (культ сили та волі), що радикально вплинула на світогляд авторки."
      - "Відхід від етнографічного шаблону до революційного для того часу розгляду природи як могутньої самостійної стихії."
  - section: "Вступ та культурний контекст: Місце у каноні"
    words: 350
    points:
      - "Місце в літературному каноні: Кобилянська як піонерка українського феміністичного дискурсу та ранньої екокритики."
      - "Спростування радянського міфу про неї як виключно «захисницю скривдженого селянства» (марксистська оптика)."
      - "Чому цей текст важливий сьогодні: новели «Природа» (1887) та «Битва» (1895) задають новий філософський горизонт у європейському каноні."
  - section: "Аналіз твору: Сюжет та структура — «Природа» і «Битва»"
    words: 400
    points:
      - "Ключові етапи розвитку сюжету: у «Природі» — зустріч «нової жінки» та українця-русина як каталізатор психологічних змін."
      - "Сюжет «Битви»: практично безсюжетна, епічна новела-симфонія, де ключовим етапом є безжальне нищення карпатського лісу."
      - "Впливи та джерела: відмова від традиційного лінійного сюжету під впливом європейських модерних течій на користь музичної композиції."
  - section: "Аналіз твору: Сюжет та структура — Конфлікт цивілізації"
    words: 400
    points:
      - "Конфлікт як рушійна сила: зіткнення органічного (велетенський карпатський ліс) та штучного (лісоруби як уособлення капіталу)."
      - "Екокритична алегорія: вирубка пралісу метафорично зображує агресивний наступ прагматичної цивілізації."
      - "Емансипація героїнь через відторгнення міщанської моралі задля збереження власної віталістичної ідентичності."
  - section: "Герменевтика та ключові образи: Символіка лісу"
    words: 400
    points:
      - "Детальний розбір символіки лісу: пантеїстичний організм, що наділений свідомістю та відчуває біль (цитата: «Плакали дерева, падали з глухим стогоном...»)."
      - "Архетипи та міфологічні підтексти: гори і ліс як первісний хаос, джерело істини та простір для прихованих архетипічних бажань."
      - "Природа як абсолютна територія вільної волі і втечі від лицемірства суспільства."
  - section: "Герменевтика та ключові образи: Жінка і віталізм"
    words: 400
    points:
      - "Система персонажів та їхня еволюція: формування «нової жінки», що відкидає чоловічий захист і черпає енергію безпосередньо від землі."
      - "Ніцшеанська ідея трансформації: вплив діонісійського начала на становлення жінки-аристократки духу."
      - "Природа як найвищий суддя, що легітимізує право жінки на свободу (цитата: «Хто знає, чи не була би я інакшою, коли б не вплив...»)."
  - section: "Мова, стиль та поетика: Стилістичні інновації"
    words: 350
    points:
      - "Стилістичні інновації автора: перехід до імпресіонізму, фіксація психологічних вражень, кольорів та настроїв («пейзаж душі»)."
      - "Робота з народною мовою: свідоме уникнення надмірного діалектного чи етнографічного забарвлення тексту."
      - "Творення рафінованої, урбаністичної за духом мови для опису найскладніших душевних станів та неоромантичних концептів."
  - section: "Мова, стиль та поетика: Музичність тексту"
    words: 350
    points:
      - "Особливості ритміки та синтаксису: феномен «ритмічної прози» із використанням лейтмотивів, повторів та модуляцій."
      - "Симфонізм тексту: вплив музики Вагнера і Шопена на побудову наративу, що створює «симфонію в словах»."
      - "Алітерації та асонанси як потужний звукопис для відтворення ілюзії живого лісу (шум вітру, стогін зрубаних дерев)."
  - section: "Деколонізаційний вимір: Руйнування міфу про провінційність"
    words: 350
    points:
      - "Який імперський міф руйнує цей текст: спростування стереотипу про Кобилянську як «регіональну» побутову письменницю."
      - "Органічна інтеграція її творчості в центральноєвропейський модерний дискурс (культурний простір Австро-Угорщини)."
      - "Тексти доводять: українська мова здатна артикулювати найскладніші філософські ідеї без посередництва російських чи німецьких центрів."
  - section: "Деколонізаційний вимір: Агентність і опір"
    words: 350
    points:
      - "Опір асиміляції: свідомий перехід від німецької (мови імперського престижу) до української як акт антиколоніального самоствердження."
      - "Агентність українського героя: відмова від ролі пасивної жертви історичних та соціальних обставин."
      - "Паралелі між культурним самоствердженням української нації, емансипацією жінки та боротьбою природи за виживання."
  - section: "Підсумок та рецепція"
    words: 300
    points:
      - "Вплив на наступні покоління письменників: сприйняття еко-феміністичних ідей Лесею Українкою, шістдесятниками та сучасними авторами (О. Забужко)."
      - "Світовий контекст твору: новела «Битва» як візіонерський гіперактуальний текст у межах глобальної еко-критики (ecocriticism)."
      - "Питання для дискусії: спадщина авторки в контексті сучасної екологічної катастрофи (антропоцену) та гендерної рівноваги."
===META_OUTLINE_END===

===FRICTION_START===
**Phase**: Phase A: Meta Outline Only (research-exists mode)
**Step**: Full meta outline
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: N/A
**Proposed Tooling Fix**: N/A
===FRICTION_END===
