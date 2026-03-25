import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    content = f.read()

# Delete English translations from the blocks I added
content = re.sub(r"\n> \(Hi! I am a student\. Now I study at the university\.\)", "", content)
content = re.sub(r"\n> \(I really want to become a good lawyer\. It is a difficult profession\.\)", "", content)
content = re.sub(r"\n> \(My father previously was a lawyer\. He worked as a lawyer for twenty years\.\)", "", content)
content = re.sub(r"\n> \(Now he works as a judge\. I also dream of working as a judge\.\)", "", content)
content = re.sub(r"\n> \(My mother is a doctor\. She works as a doctor in a large hospital\.\)", "", content)
content = re.sub(r"\n> \(Previously she was a nurse\. She became a doctor because she studied a lot\.\)", "", content)
content = re.sub(r"\n> \(We all love our professions\. Work is important!\)", "", content)

content = re.sub(r"\n> \(Hi, Maksym! I heard you found a new job\?\)", "", content)
content = re.sub(r"\n> \(Hi, Anna! Yes\. Previously I worked as a waiter\.\)", "", content)
content = re.sub(r"\n> \(As a waiter\? And now what do you work as\?\)", "", content)
content = re.sub(r"\n> \(Now I work as a manager\. I became a manager last month\.\)", "", content)
content = re.sub(r"\n> \(Congratulations! That is wonderful\. And I still work as a teacher\.\)", "", content)
content = re.sub(r"\n> \(Being a teacher is very interesting\. Do you want to become a director\?\)", "", content)
content = re.sub(r"\n> \(Maybe\. In the future I want to be the director of the school\.\)", "", content)

content = re.sub(r"\n> \(Serhiy always dreamed of being a programmer\.\)", "", content)
content = re.sub(r"\n> \(When he was a schoolboy, he loved computers\.\)", "", content)
content = re.sub(r"\n> \(Then he became a student\. He studied computer science\.\)", "", content)
content = re.sub(r"\n> \(After university he worked as an engineer\.\)", "", content)
content = re.sub(r"\n> \(But his dream is to be an IT professional\. Therefore he became a programmer\.\)", "", content)
content = re.sub(r"\n> \(Now he works as a programmer in the city of Kyiv\.\)", "", content)
content = re.sub(r"\n> \(His sister is also a programmer\. She works as a programmer\.\)", "", content)
content = re.sub(r"\n> \(They are happy because they have a good job\.\)", "", content)

large_ua_block = """
> **📖 Чита́ння: Кар'є́ра та життя́**
> 
> У суча́сному сві́ті бага́то люде́й змі́нюють профе́сію. Це́ норма́льно. Рані́ше люди́на працюва́ла на одні́й робо́ті все́ життя́. Тепе́р усе́ іна́кше.
> 
> Напри́клад, мі́й брат. Ві́н бу́в інжене́ром де́сять рокі́в. Але́ по́тім ві́н зрозумі́в, що́ йому́ ну́дно. Ві́н хоті́в ста́ти програмі́стом. Ві́н поча́в вчи́тися вве́чері. Це́ бу́ло ду́же скла́дно. Ві́н працюва́в інжене́ром вде́нь, а вве́чері става́в студе́нтом. Через два ро́ки ві́н знайшо́в нову́ робо́ту. За́раз ві́н працю́є програмі́стом і ду́же задово́лений.
> 
> Моя́ се́стра те́ж змінила́ профе́сію. Вона́ була́ вчи́телькою малюва́ння. Вона́ ду́же лю́бить діте́й. Але́ зарпла́та була́ мален́ькою. Тому́ вона́ ви́рішила ста́ти диза́йнеркою. Вона́ вчи́лася онла́йн. За́раз вона́ працю́є диза́йнеркою в ІТ-компа́нії. Її́ чолові́к — архіте́ктор. Вони́ ра́зом працю́ють над ціка́вими проє́ктами.
> 
> А я́ за́вжди хоті́ла бу́ти лі́каркою. Я́ вчи́лася в меди́чному університе́ті ші́сть рокі́в. Це́ бу́ли найва́жчі ро́ки в моє́му житті́. Але́ за́раз я́ працю́ю лі́каркою в дитя́чій ліка́рні. Я́ допомага́ю ді́тям. Я́ ніко́ли не́ хоті́ла зміни́ти профе́сію.
> 
> Ко́жна профе́сія важли́ва. Нема́є пога́них профе́сій. Якщо́ ви́ хо́чете ста́ти спеціалі́стом, ви́ по́винні бага́то працюва́ти. Мо́жна бу́ти хоро́шим лі́карем, таланови́тою вчи́телькою, креати́вним ме́неджером або́ розу́мним програмі́стом. Головне́ — люби́ти свою́ робо́ту і бу́ти кори́сним.
> 
> А ки́м ви́ мрі́єте ста́ти? Яка́ ва́ша ці́ль?
"""

content = content.replace("## Діалоги та кар'єрні плани", large_ua_block + "\n## Діалоги та кар'єрні плани")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(content)
