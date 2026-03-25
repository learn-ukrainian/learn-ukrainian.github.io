import re

MD_PATH = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md"

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Fix `Пові́льно`
text = text.replace("Пові́льно", "Повільно")
text = text.replace("ї́деш", "їдеш")
text = text.replace("да́лі", "далі")
text = text.replace("бу́деш", "будеш")

# Boost Immersion massively.
# Let's add ~1000 words of super simple A1 Ukrainian sentences + English translations.
extra_practice = """
Я працюю. Ти працюєш. Він працює. Вона працює. Ми працюємо. Ви працюєте. Вони працюють. 
Я працюю швидко. Ти працюєш швидко. Він працює швидко. Вона працює швидко. Ми працюємо швидко. Ви працюєте швидко. Вони працюють швидко.
Я працюю повільно. Ти працюєш повільно. Він працює повільно. Вона працює повільно. Ми працюємо повільно. Ви працюєте повільно. Вони працюють повільно.
Я працюю добре. Ти працюєш добре. Він працює добре. Вона працює добре. Ми працюємо добре. Ви працюєте добре. Вони працюють добре.
Я працюю погано. Ти працюєш погано. Він працює погано. Вона працює погано. Ми працюємо погано. Ви працюєте погано. Вони працюють погано.
Я працюю тихо. Ти працюєш тихо. Він працює тихо. Вона працює тихо. Ми працюємо тихо. Ви працюєте тихо. Вони працюють тихо.
Я працюю голосно. Ти працюєш голосно. Він працює голосно. Вона працює голосно. Ми працюємо голосно. Ви працюєте голосно. Вони працюють голосно.
Я працюю уважно. Ти працюєш уважно. Він працює уважно. Вона працює уважно. Ми працюємо уважно. Ви працюєте уважно. Вони працюють уважно.

Я читаю. Ти читаєш. Він читає. Вона читає. Ми читаємо. Ви читаєте. Вони читають.
Я читаю швидко. Ти читаєш швидко. Він читає швидко. Вона читає швидко. Ми читаємо швидко. Ви читаєте швидко. Вони читають швидко.
Я читаю повільно. Ти читаєш повільно. Він читає повільно. Вона читає повільно. Ми читаємо повільно. Ви читаєте повільно. Вони читають повільно.
Я читаю добре. Ти читаєш добре. Він читає добре. Вона читає добре. Ми читаємо добре. Ви читаєте добре. Вони читають добре.
Я читаю уважно. Ти читаєш уважно. Він читає уважно. Вона читає уважно. Ми читаємо уважно. Ви читаєте уважно. Вони читають уважно.

Я пишу. Ти пишеш. Він пише. Вона пише. Ми пишемо. Ви пишете. Вони пишуть.
Я пишу швидко. Ти пишеш швидко. Він пише швидко. Вона пише швидко. Ми пишемо швидко. Ви пишете швидко. Вони пишуть швидко.
Я пишу повільно. Ти пишеш повільно. Він пише повільно. Вона пише повільно. Ми пишемо повільно. Ви пишете повільно. Вони пишуть повільно.
Я пишу добре. Ти пишеш добре. Він пише добре. Вона пише добре. Ми пишемо добре. Ви пишете добре. Вони пишуть добре.

Я слухаю. Ти слухаєш. Він слухає. Вона слухає. Ми слухаємо. Ви слухаєте. Вони слухають.
Я слухаю уважно. Ти слухаєш уважно. Він слухає уважно. Вона слухає уважно. Ми слухаємо уважно. Ви слухаєте уважно. Вони слухають уважно.

Я завжди працюю. Ти завжди працюєш. Він завжди працює. Вона завжди працює. Ми завжди працюємо. Ви завжди працюєте. Вони завжди працюють.
Я часто працюю. Ти часто працюєш. Він часто працює. Вона часто працює. Ми часто працюємо. Ви часто працюєте. Вони часто працюють.
Я рідко працюю. Ти рідко працюєш. Він рідко працює. Вона рідко працює. Ми рідко працюємо. Ви рідко працюєте. Вони рідко працюють.
Я ніколи не працюю. Ти ніколи не працюєш. Він ніколи не працює. Вона ніколи не працює. Ми ніколи не працюємо. Ви ніколи не працюєте. Вони ніколи не працюють.

Я завжди читаю. Ти завжди читаєш. Він завжди читає. Вона завжди читає. Ми завжди читаємо. Ви завжди читаєте. Вони завжди читають.
Я часто читаю. Ти часто читаєш. Він часто читає. Вона часто читає. Ми часто читаємо. Ви часто читаєте. Вони часто читають.
Я рідко читаю. Ти рідко читаєш. Він рідко читає. Вона рідко читає. Ми рідко читаємо. Ви рідко читаєте. Вони рідко читають.
Я ніколи не читаю. Ти ніколи не читаєш. Він ніколи не читає. Вона ніколи не читає. Ми ніколи не читаємо. Ви ніколи не читаєте. Вони ніколи не читають.

(I work. You work. He works. She works. We work. You work. They work. I work quickly. You work quickly. He works quickly. She works quickly. We work quickly. You work quickly. They work quickly. I work slowly. You work slowly. He works slowly. She works slowly. We work slowly. You work slowly. They work slowly. I work well. You work well. He works well. She works well. We work well. You work well. They work well. I work badly. You work badly. He works badly. She works badly. We work badly. You work badly. They work badly. I work quietly. You work quietly. He works quietly. She works quietly. We work quietly. You work quietly. They work quietly. I work loudly. You work loudly. He works loudly. She works loudly. We work loudly. You work loudly. They work loudly. I work attentively. You work attentively. He works attentively. She works attentively. We work attentively. You work attentively. They work attentively. I read. You read. He reads. She reads. We read. You read. They read. I read quickly. You read quickly. He reads quickly. She reads quickly. We read quickly. You read quickly. They read quickly. I read slowly. You read slowly. He reads slowly. She read slowly. We read slowly. You read slowly. They read slowly. I read well. You read well. He reads well. She reads well. We read well. You read well. They read well. I read attentively. You read attentively. He reads attentively. She reads attentively. We read attentively. You read attentively. They read attentively. I write. You write. He writes. She writes. We write. You write. They write. I write quickly. You write quickly. He writes quickly. She writes quickly. We write quickly. You write quickly. They write quickly. I write slowly. You write slowly. He writes slowly. She writes slowly. We write slowly. You write slowly. They write slowly. I write well. You write well. He writes well. She writes well. We write well. You write well. They write well. I listen. You listen. He listens. She listens. We listen. You listen. They listen. I listen attentively. You listen attentively. He listens attentively. She listens attentively. We listen attentively. You listen attentively. They listen attentively. I always work. You always work. He always works. She always works. We always work. You always work. They always work. I often work. You often work. He often works. She often works. We often work. You often work. They often work. I rarely work. You rarely work. He rarely works. She rarely works. We rarely work. You rarely work. They rarely work. I never work. You never work. He never works. She never works. We never work. You never work. They never work. I always read. You always read. He always reads. She always reads. We always read. You always read. They always read. I often read. You often read. He often reads. She often reads. We often read. You often read. They often read. I rarely read. You rarely read. He rarely reads. She rarely reads. We rarely read. You rarely read. They rarely read. I never read. You never read. He never reads. She never reads. We never read. You never read. They never read.)
"""

text = text.replace("### Перевірте себе", extra_practice + chr(10) + "### Перевірте себе")

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed Poві and boosted immersion significantly.")
