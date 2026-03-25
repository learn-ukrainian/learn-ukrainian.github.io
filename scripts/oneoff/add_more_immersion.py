import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

reading_block_3 = """
> **📖 Чита́ння: Моя́ мрі́я (Reading: My Dream)**
> 
> Приві́т! Я́ студе́нтка. За́раз я́ вчу́ся в університе́ті. 
> (Hi! I am a student. Now I study at the university.)
> 
> Я́ ду́же хо́чу ста́ти хорошо́ю юри́сткою. Це́ скла́дна профе́сія.
> (I really want to become a good lawyer. It is a difficult profession.)
> 
> Мій ба́тько рані́ше бу́в юри́стом. Ві́н працюва́в юри́стом два́дцять рокі́в. 
> (My father previously was a lawyer. He worked as a lawyer for twenty years.)
> 
> Тепе́р ві́н працю́є судде́ю. Я́ те́ж мрі́ю працюва́ти судде́ю. 
> (Now he works as a judge. I also dream of working as a judge.)
> 
> Моя́ ма́ма — лі́карка. Вона́ працю́є лі́каркою у вели́кій ліка́рні. 
> (My mother is a doctor. She works as a doctor in a large hospital.)
> 
> Рані́ше вона́ була́ медсестро́ю. Вона́ ста́ла лі́каркою, бо́ бага́то вчи́лася.
> (Previously she was a nurse. She became a doctor because she studied a lot.)
> 
> Ми́ всі́ лю́бимо на́ші профе́сії. Робо́та — це́ важли́во!
> (We all love our professions. Work is important!)
"""

reading_block_4 = """
> **📖 Чита́ння: Нова́ робо́та (Reading: New Job)**
> 
> — Приві́т, Макси́ме! Я́ чу́ла, ти́ знайшо́в нову́ робо́ту?
> (Hi, Maksym! I heard you found a new job?)
> 
> — Приві́т, А́нно! Та́к. Рані́ше я́ працюва́в офіціа́нтом. 
> (Hi, Anna! Yes. Previously I worked as a waiter.)
> 
> — Офіціа́нтом? А за́раз ки́м ти́ працю́єш?
> (As a waiter? And now what do you work as?)
> 
> — За́раз я́ працю́ю ме́неджером. Я́ ста́в ме́неджером мину́лого мі́сяця.
> (Now I work as a manager. I became a manager last month.)
> 
> — Віта́ю! Це́ чудово́. А я́ до́сі працю́ю вчи́телькою.
> (Congratulations! That is wonderful. And I still work as a teacher.)
> 
> — Вчи́телькою бу́ти ду́же ціка́во. Ти́ хо́чеш ста́ти дире́кторкою?
> (Being a teacher is very interesting. Do you want to become a director?)
> 
> — Можли́во. У майбу́тньому я́ хо́чу бу́ти дире́кторкою шко́ли.
> (Maybe. In the future I want to be the director of the school.)
"""

reading_block_5 = """
> **📖 Чита́ння: Історія успіху (Reading: Success Story)**
> 
> Сергі́й за́вжди мрі́яв бу́ти програмі́стом. 
> (Serhiy always dreamed of being a programmer.)
> 
> Коли́ ві́н бу́в школяре́м, ві́н лю́бив комп'ю́тери. 
> (When he was a schoolboy, he loved computers.)
> 
> По́тім ві́н ста́в студе́нтом. Ві́н вивча́в інформа́тику. 
> (Then he became a student. He studied computer science.)
> 
> Пі́сля університе́ту ві́н працюва́в інжене́ром. 
> (After university he worked as an engineer.)
> 
> Але́ його́ мрі́я — бу́ти айтівце́м. Тому́ ві́н ста́в програмі́стом.
> (But his dream is to be an IT professional. Therefore he became a programmer.)
> 
> За́раз ві́н працю́є програмі́стом у мі́сті Ки́їв. 
> (Now he works as a programmer in the city of Kyiv.)
> 
> Його́ сестра́ те́ж програмі́стка. Вона́ працю́є програмі́сткою. 
> (His sister is also a programmer. She works as a programmer.)
> 
> Вони́ щасли́ві, бо́ ма́ють хоро́шу робо́ту.
> (They are happy because they have a good job.)
"""

content = content.replace("## Соціокультурний контекст", reading_block_3 + "\n## Соціокультурний контекст")
content = content.replace("## Практика та запобігання помилкам", reading_block_4 + "\n## Практика та запобігання помилкам")
content = content.replace("## Діалоги та кар'єрні плани", reading_block_5 + "\n## Діалоги та кар'єрні плани")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
