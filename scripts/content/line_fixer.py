import re

with open('curriculum/l2-uk-en/b1/relative-clauses-de-kudy-zvidky.md', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # 1. Euphony
    if i+1 == 21:
        line = line.replace("у єдину", "в єдину")
    if i+1 == 79:
        line = line.replace("в спальному", "у спальному")
    if i+1 == 130:
        line = line.replace("і або", "й або")
    if i+1 == 133:
        line = line.replace("в цьому", "у цьому")
    if i+1 == 134:
        line = line.replace("в цьому", "у цьому")
    if i+1 == 148:
        line = line.replace("часто і яскраво", "часто й яскраво")
    if i+1 == 198:
        line = line.replace("в вказуючи", "у вказуючи")
    if i+1 == 215:
        line = line.replace("перебуваєте і яку", "перебуваєте й яку")
    if i+1 == 317:
        line = line.replace("з чоловіком", "із чоловіком")
    if i+1 == 359:
        line = line.replace("з часом", "із часом")
    if i+1 == 369:
        line = line.replace("з самого", "із самого")

    # 2. Redundancy
    if "Ми з родиною ще остаточно не вирішили" in line:
        continue
    if "Поліція довго з'ясовувала" in line:
        continue

    # 3. Robotic Structure
    if line.startswith("1. [ ] ") or line.startswith("2. [ ] ") or line.startswith("3. [ ] ") or line.startswith("4. [ ] ") or line.startswith("5. [ ] "):
        line = line.replace("[ ] ", "")

    # 4. Long sentences (match first few words and split by finding conjunctions or commas)
    if "Хоча це слово має дещо" in line:
        line = re.sub(r"Хоча це слово має дещо(.*?)реченнях, воно кардинально", r"Хоча це слово має дещо\1реченнях. Проте воно кардинально", line)

    if "Ці короткі динамічні слова найкращим" in line:
        line = re.sub(r"Ці короткі динамічні слова найкращим(.*?)концепцію, яку ми", r"Ці короткі динамічні слова найкращим\1концепцію. Її ми", line)

    if "Якщо підрядне речення детально описує" in line:
        line = re.sub(r"Якщо підрядне речення детально описує(.*?)відліку, то ви", r"Якщо підрядне речення детально описує\1відліку. Тоді ви", line)

    if "Спуск на платформу займає понад" in line:
        line = re.sub(r"Спуск на платформу займає понад(.*?)хвилини, що робить", r"Спуск на платформу займає понад\1хвилини. Це робить", line)

    if "Захоплені іноземні туристи запитували" in line:
        line = re.sub(r"Захоплені іноземні туристи запитували, звідки вони", r"Захоплені іноземні туристи запитували дорогу. Звідки вони", line)
        line = line.replace("горі.", "горі?")

    if "Це саме те унікальне високогірне" in line:
        line = re.sub(r"Це саме те унікальне високогірне(.*?)селище, звідки традиційно", r"Це саме те унікальне високогірне\1селище. Звідки традиційно", line)

    if "Такі вдумливі аналітичні вправи поступово" in line:
        line = re.sub(r"Такі вдумливі аналітичні вправи поступово(.*?)допоможуть вам назавжди позбутися", r"Такі вдумливі аналітичні вправи поступово\1допоможуть вам. Ви зможете назавжди позбутися", line)

    if "Це мій персональний затишний тихий" in line:
        line = re.sub(r"Це мій персональний затишний тихий(.*?)куточок, де я можу", r"Це мій персональний затишний тихий\1куточок. Там я можу", line)

    if "Будь ласка, оберіть якесь одне" in line:
        line = re.sub(r"Будь ласка, оберіть якесь одне(.*?)місті, куди ви", r"Будь ласка, оберіть якесь одне\1місті. Розкажіть, куди ви", line)
        line = line.replace("вихідних.", "вихідних.")

    if "Ви повинні обов'язково описати" in line:
        line = re.sub(r"Ви повинні обов'язково описати(.*?)деталях, звідки ви", r"Ви повинні обов'язково описати\1деталях. Звідки ви", line)
        line = line.replace("зацікавила.", "зацікавила?")

    if "У цьому великому важливому навчальному модулі" in line:
        line = re.sub(r"У цьому великому важливому навчальному(.*?)слова, які відіграють", r"У цьому великому важливому навчальному\1слова. Вони відіграють", line)

    # 5. LLM Fingerprints
    line = re.sub(r'не просто\s+([^,]+),\s*а\s+([^,.]+)', r'як \1, так і \2', line)
    line = re.sub(r'не просто\s+([^,]+),\s*а\s+й\s+([^,.]+)', r'як \1, так і \2', line)

    new_lines.append(line)

with open('curriculum/l2-uk-en/b1/relative-clauses-de-kudy-zvidky.md', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Line-by-line fixes applied.")
