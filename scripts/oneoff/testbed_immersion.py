import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

reading_block_1 = """
> **📖 Чита́ння: Моя́ кар'є́ра (Reading: My Career)**
> 
> Приві́т! Мене́ зва́ти Іва́н. Я́ хо́чу розповісти́ про́ свою́ робо́ту. 
> (Hi! My name is Ivan. I want to tell about my work.)
> 
> П'я́ть рокі́в тому́ я́ бу́в студе́нтом. Я́ вивча́в економі́ку. 
> (Five years ago I was a student. I studied economics.)
> 
> Пі́сля університе́ту я́ ста́в економі́стом. Я́ працюва́в економі́стом у ба́нку два́ ро́ки. 
> (After university I became an economist. I worked as an economist in a bank for two years.)
> 
> Але́ по́тім я́ зрозумі́в, що́ це́ не́ моя́ мрі́я. Я́ хоті́в бу́ти програмі́стом. 
> (But then I realized that this is not my dream. I wanted to be a programmer.)
> 
> Я́ поча́в вчи́тися зно́ву. Це́ бу́ло скла́дно, але́ ду́же ціка́во. 
> (I started to study again. It was difficult, but very interesting.)
> 
> За́раз я́ працю́ю айтівце́м. Я́ ста́в хоро́шим програмі́стом і люблю́ свою́ нову́ профе́сію. 
> (Now I work as an IT professional. I became a good programmer and I love my new profession.)
> 
> Моя́ дружи́на, Окса́на, те́ж змінила́ профе́сію. Вона́ була́ вчи́телькою, а тепе́р працю́є ме́неджеркою. 
> (My wife, Oksana, also changed her profession. She was a teacher, and now works as a manager.)
> 
> Ми́ вважа́ємо, що́ ніко́ли не́ пі́зно ста́ти ти́м, ки́м ти́ хо́чеш бу́ти!
> (We believe that it is never too late to become who you want to be!)
"""

reading_block_2 = """
> **📖 Чита́ння: Інтерв'ю́ з дире́кторкою (Reading: Interview with a Director)**
> 
> — Добри́день, Олена́! Ви́ за́раз працю́єте дире́кторкою вели́кої компа́нії. Розкажі́ть, я́к ви́ ста́ли дире́кторкою?
> (Good afternoon, Olena! You now work as a director of a large company. Tell us, how did you become a director?)
> 
> — Добри́день! Мій шля́х бу́в до́вгим. Споча́тку я́ була́ звича́йною журналі́сткою. 
> (Good afternoon! My path was long. At first, I was an ordinary journalist.)
> 
> — Журналі́сткою? Це ду́же ціка́во. Чому́ ви́ зміни́ли профе́сію?
> (A journalist? That is very interesting. Why did you change your profession?)
> 
> — Я́ працювала́ журналі́сткою п'я́ть рокі́в, але́ по́тім я́ зрозумі́ла, що́ хо́чу працюва́ти в бі́знесі. 
> (I worked as a journalist for five years, but then I realized that I want to work in business.)
> 
> — І що́ ви́ зроби́ли?
> (And what did you do?)
> 
> — Я́ пішла́ вчи́тися і ста́ла ме́неджеркою. Я́ працювала́ ме́неджеркою дуже бага́то, і через три ро́ки ста́ла дире́кторкою.
> (I went to study and became a manager. I worked as a manager a lot, and after three years became a director.)
> 
> — Що́ ви́ пора́дите на́шим читача́м?
> (What would you advise our readers?)
> 
> — Не́ бі́йтеся зминюва́ти профе́сію. Якщо́ ви́ хо́чете ста́ти спеціалі́стом, ви́ ни́м ста́нете!
> (Don't be afraid to change your profession. If you want to become a specialist, you will become one!)
"""

content = content.replace("## Практика та запобігання помилкам", reading_block_1 + "\n## Практика та запобігання помилкам")
content = content.replace("## Діалоги та кар'єрні плани", reading_block_2 + "\n## Діалоги та кар'єрні плани")

# Let's add more Ukrainian dialogue to existing dialogue section
dialogue_addition = """
> — А ва́ші друзі́? Вони́ те́ж зміни́ли профе́сію? (And your friends? Did they also change profession?)
> — Та́к. Мій найкр́ащий друг рані́ше працюва́в юри́стом, але́ він за́вжди мрі́яв бу́ти лі́карем. (Yes. My best friend previously worked as a lawyer, but he always dreamed of being a doctor.)
> — Ого́! Це скла́дно. (Wow! That is difficult.)
> — Ві́н вчи́вся сі́м рокі́в і тепе́р працю́є лі́карем у ліка́рні. (He studied for seven years and now works as a doctor in a hospital.)
> — Це надиха́є! Зна́чить, я́ те́ж мо́жу ста́ти програмі́стом. (This is inspiring! It means I too can become a programmer.)
> — Зві́сно! Головне́ — бага́то вчи́тися. (Of course! The main thing is to study a lot.)
"""
content = content.replace("> — Дякую! І вам також! (Thank you! And to you too!)", "> — Дякую! І вам також! (Thank you! And to you too!)\n" + dialogue_addition)

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
