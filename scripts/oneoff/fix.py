import sys

with open("curriculum/l2-uk-en/a2/comparison.md", "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    # Fix 2-5: IPA brackets
    ("[Item A]", "{Item A}"),
    ("[Item B in Nominative]", "{Item B in Nominative}"),
    ("[Item B in Accusative]", "{Item B in Accusative}"),
    
    # Fix 18: порівня́ння
    ("сту́пені порівня́ння", "сту́пені порівняння"),
    
    # Fix 6 & 7 & 19: цікаві́ший, молоди́й, suffix separation
    ("add **-іший** (like *ціка́вий* → *цікаві́ший*)", "add the suffix **-іший** (for example, *ціка́вий* becomes *ціка́віший*)"),
    ("add **-ший** (like *молоди́й* → *моло́дший*)", "add the suffix **-ший** (for example, *молоди́й* becomes *моло́дший*)"),
    
    # Fix 19: цікаві́ший -> ціка́віший (others)
    ("цікаві́ший", "ціка́віший"),
    ("цікаві́ша", "ціка́віша"),
    ("цікаві́ші", "ціка́віші"),
    
    # Fix 20: приголо́сних
    ("чергува́ння приголо́сних", "чергува́ння при́голосних"),
    
    # Fix 21: доро́ -> до́ро
    ("доро́жч", "до́рожч"),
    ("доро́**ж**чий", "до́ро**ж**чий"),
    
    # Fix 22: складне́
    ("складне́", "складне"),
    
    # Fix 23: Її́
    ("Її́", "Її"),
    
    # Fix 8, 9, 24: Київ, Зима -> Слон, Січень, Киї́в
    ("Ки́їв **більший, ніж** Льві́в.", "Слон **бі́льший, ніж** кіт."),
    ("(Kyiv is bigger than Lviv.)", "(An elephant is bigger than a cat.)"),
    ("Ки́їв **більший за** Льві́в.", "Слон **бі́льший за** кота́."),
    
    ("Зима́ **холодні́ша, ніж** осінь.", "Сі́чень **холодні́ший, ніж** лю́тий."),
    ("Зима́ **холодні́ша за** осінь.", "Сі́чень **холодні́ший за** лю́тий."),
    ("(Winter is colder than autumn.)", "(January is colder than February.)"),
    
    ("Ки́їв", "Киї́в"),
    
    # Fix 10: чим
    ("більший чим", "бі́льше чим"),
    
    # Fix 11: піца -> суп
    ("А пі́ца тут **бі́льша, ніж** та́м?", "А суп тут **бі́льший, ніж** та́м?"),
    ("пі́ца тут **ме́нша**, але **більш сві́жа**.", "суп тут **ме́нший**, але **більш сві́жий**."),
    ("And is the pizza here bigger than there?", "And is the soup here bigger than there?"),
    ("the pizza here is smaller, but more fresh", "the soup here is smaller, but more fresh"),
    
    # Fix 25: йде́мо -> йдемо́
    ("йде́мо", "йдемо́"),
    
    # Fix 12: Здоров'я -> Час
    ("«Здоро́в'я — **найдорожчи́й** скарб.»", "«Час — **найдо́рожчий** скарб.»"),
    ("(Health is the most expensive/valuable treasure.", "(Time is the most valuable treasure."),
    
    # Fix 13, 26, 27: Яка пора року найгарніша
    ("Яка́ пора́ ро́ку **найгарні́ша**?", "Який мі́сяць ро́ку **найгарні́ший**?"),
    ("О́сінь — **найгарні́ша** пора́ ро́ку.", "Жо́втень — **найгарні́ший** мі́сяць ро́ку."),
    ("(Which season is the most beautiful?)", "(Which month of the year is the most beautiful?)"),
    ("(Autumn is the most beautiful season.)", "(October is the most beautiful month of the year.)"),
    
    # Fix 1, 17, 28, 29: Самий rule
    ("The \"Самий\" Rule:", "The Prefix Rule:"),
    ("Never use the word \"самий\" to form", "Never use a separate word like \"samyi\" to form"),
    ("Saying \"самий кращий\" is a direct translation", "Using such words is a direct translation"),
    ("❌ Непра́вильно: самий швидкий, самий розумний", "❌ Непра́вильно: додавати окреме слово замість префікса"),
    ("✅ Пра́вильно: найшвидши́й, найрозу́мніший", "✅ Пра́вильно: найшви́дший, найрозумні́ший"),
    ("Чому форма \"самий кращий\" є неправильною?", "Чому ви́раз \"найкра́щий\" пишеться ра́зом?"),
    ("(Why is the form \"самий кращий\" incorrect?)", "(Why is the expression \"найкра́щий\" written as one word?)"),
    
    # Fix 30: гора́х
    ("у гора́х", "у го́рах"),
    
    # Fix 14, 15, 32, 33: Міста України
    ("Льві́в **більш популя́рний** се́ред тури́стів.", "Льві́вські па́рки **більш популя́рні** се́ред тури́стів."),
    ("архітекту́ра у Льво́ві **кра́ща**, ніж в і́нших міста́х.", "парк у Льво́ві **кра́щий**, ніж в і́нших міста́х."),
    ("Lviv is more popular among tourists.", "Lviv parks are more popular among tourists."),
    ("the architecture in Lviv is better", "the park in Lviv is better"),
    ("та́кож", "та́ко́ж"),
    ("плюси́", "плю́си"),
    
    # Fix 16: гарячі́ша -> гарячі́ший (Кава -> Чай)
    ("Ка́ва сього́дні **тро́хи гарячі́ша**, ніж учо́ра.", "Чай сього́дні **тро́хи гарячі́ший**, ніж учо́ра."),
    ("The coffee today is slightly hotter", "The tea today is slightly hotter"),
    
    # Fix 34, 35: ста́рший, ме́не
    ("ста́рший", "старший"),
    ("ме́не.", "мене́.")
]

for old, new in replacements:
    text = text.replace(old, new)

with open("curriculum/l2-uk-en/a2/comparison.md", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixes applied.")
