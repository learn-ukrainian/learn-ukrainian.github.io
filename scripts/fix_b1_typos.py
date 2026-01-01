
import os
import yaml
import re

# Fixes map: old_lemma -> new_attributes
FIXES = {
    "скоросити": {"lemma": "скоротити", "ipa": "/skɔrɔˈtɪtɪ/", "translation": "to shorten"},
    "вибррати": {"lemma": "вибрати", "ipa": "/ˈvɪbratɪ/", "translation": "to choose"},
    "поверталати": {"lemma": "повертати", "ipa": "/pɔvɛrˈtatɪ/", "translation": "to return"},
    "відрігти": {"lemma": "відрізати", "ipa": "/vidˈrʲizatɪ/", "translation": "to cut off"},
    "закінти": {"lemma": "закінчити", "ipa": "/zaˈkʲint͡ʃɪtɪ/", "translation": "to finish"},
    "майстрин": {"lemma": "майстер", "ipa": "/ˈmajstɛr/", "translation": "master"},
    "скрина": {"lemma": "скриня", "ipa": "/ˈskrɪnʲa/", "translation": "chest"},
    "бігатий": {"lemma": "бігати", "ipa": "/ˈbihatɪ/", "translation": "to run"},
    "завтрашний": {"lemma": "завтрашній", "ipa": "/zau̯ˈtraʃnʲij/", "translation": "tomorrow's"},
    "зберати": {"lemma": "збирати", "ipa": "/zbɪˈratɪ/", "translation": "to collect"},
    "їдити": {"lemma": "їздити", "ipa": "/ˈjizdɪtɪ/", "translation": "to ride/go"},
    "адрега": {"lemma": "адреса", "ipa": "/aˈdrɛsa/", "translation": "address"},
    "плануюмій": {"lemma": "планувати", "ipa": "/planuˈvatɪ/", "translation": "to plan"},
    "дамати": {"lemma": "давати", "ipa": "/daˈvatɪ/", "translation": "to give"},
    "учис": {"lemma": "вчитися", "ipa": "/ˈvut͡ʃɪtɪsʲa/", "translation": "to learn"},
    "заучати": {"lemma": "завчати", "ipa": "/zau̯ˈt͡ʃatɪ/", "translation": "to memorize"},
    "зписати": {"lemma": "списати", "ipa": "/spɪˈsatɪ/", "translation": "to copy/cheat"},
    "кінчувати": {"lemma": "закінчувати", "ipa": "/zaˈkʲint͡ʃuvatɪ/", "translation": "to finish"},
    "витідний": {"lemma": "вихідний", "ipa": "/vɪxidˈnɪj/", "translation": "weekend"},
    "відпрати": {"lemma": "відправити", "ipa": "/vidˈpravɪtɪ/", "translation": "to send"},
    "передити": {"lemma": "передати", "ipa": "/pɛrɛˈdatɪ/", "translation": "to pass/transmit"},
    "пояснути": {"lemma": "пояснити", "ipa": "/pɔjasˈnɪtɪ/", "translation": "to explain"},
    "четверг": {"lemma": "четвер", "ipa": "/t͡ʃɛtˈvɛr/", "translation": "Thursday"},
    "дивити": {"lemma": "дивитися", "ipa": "/dɪˈvɪtɪsʲa/", "translation": "to look"},
    "похогти": {"lemma": "допомогти", "ipa": "/dɔpɔmɔhˈtɪ/", "translation": "to help"},
    "сдача": {"lemma": "здача", "ipa": "/ˈzdat͡ʃa/", "translation": "change (money)"},
    "тимати": {"lemma": "тримати", "ipa": "/trɪˈmatɪ/", "translation": "to hold"},
    "чіпити": {"lemma": "чіпляти", "ipa": "/t͡ʃiˈplʲatɪ/", "translation": "to hook/cling"},
    "бігити": {"lemma": "бігати", "ipa": "/ˈbihatɪ/", "translation": "to run"},
    "веста": {"lemma": "вести", "ipa": "/vɛsˈtɪ/", "translation": "to lead"},
    "водопа": {"lemma": "водоспад", "ipa": "/vɔdɔˈspad/", "translation": "waterfall"},
    "ганята": {"lemma": "ганяти", "ipa": "/haˈnʲatɪ/", "translation": "to chase"},
    "лазит": {"lemma": "лазити", "ipa": "/ˈlazɪtɪ/", "translation": "to crawl"},
    "лязти": {"lemma": "лізти", "ipa": "/ˈlʲiztɪ/", "translation": "to climb"},
    "ніш": {"lemma": "ніж", "ipa": "/nʲiʒ/", "translation": "knife"},
    "пливати": {"lemma": "плавати", "ipa": "/ˈplavatɪ/", "translation": "to swim"},
    "борисполь": {"lemma": "Бориспіль", "ipa": "/bɔˈrɪspilʲ/", "translation": "Boryspil"},
    "виплист": {"lemma": "виплисти", "ipa": "/ˈvɪplɪstɪ/", "translation": "to swim out"},
    "всередина": {"lemma": "всередину", "ipa": "/u̯sɛˈrɛdɪnu/", "translation": "inside (direction)"},
    "водійва": {"lemma": "водіння", "ipa": "/vɔˈdʲinʲːa/", "translation": "driving"},
    "світлофір": {"lemma": "світлофор", "ipa": "/svitlɔˈfɔr/", "translation": "traffic light"},
    "побаток": {"lemma": "початок", "ipa": "/pɔˈt͡ʃatɔk/", "translation": "beginning"},
    "поехати": {"lemma": "поїхати", "ipa": "/pɔˈjixatɪ/", "translation": "to go (by vehicle)"},
    "развестися": {"lemma": "розлучитися", "ipa": "/rɔzluˈt͡ʃɪtɪsʲa/", "translation": "to divorce"},
    "розвезати": {"lemma": "розв'язати", "ipa": "/rɔzvjuˈzatɪ/", "translation": "to untie/solve"},
    "підйти": {"lemma": "підійти", "ipa": "/pidiˈjtɪ/", "translation": "to approach"},
    "підїхати": {"lemma": "під'їхати", "ipa": "/pidˈjixatɪ/", "translation": "to drive up"},
    "довітися": {"lemma": "довідатися", "ipa": "/dɔˈvidadɪsʲa/", "translation": "to find out"},
    "напрол": {"lemma": "напролом", "ipa": "/naprɔˈlɔm/", "translation": "straight through"},
    "різнонапавлений": {"lemma": "різнонаправлений", "ipa": "/rʲiznɔnaˈprau̯lɛnɪj/", "translation": "multidirectional"},
    "ізсередина": {"lemma": "ізсередини", "ipa": "/izsɛˈrɛdɪnɪ/", "translation": "from inside"},
    "нишко": {"lemma": "нишком", "ipa": "/ˈnɪʃkɔm/", "translation": "stealthily"},
    "тишк": {"lemma": "тишком", "ipa": "/ˈtɪʃkɔm/", "translation": "quietly"},
    "біббліотека": {"lemma": "бібліотека", "ipa": "/biblʲiɔˈtɛka/", "translation": "library"},
    "варійка": {"lemma": "аварійка", "ipa": "/avaˈrʲijka/", "translation": "emergency lights"},
    "давшати": {"lemma": "довшати", "ipa": "/ˈdɔu̯ʃatɪ/", "translation": "to lengthen"},
    "лізити": {"lemma": "лізти", "ipa": "/lʲiztɪ/", "translation": "to climb"},
    "розклати": {"lemma": "розкласти", "ipa": "/rɔzˈklastɪ/", "translation": "to lay out"},
    "пересіти": {"lemma": "пересісти", "ipa": "/pɛrɛˈsʲistɪ/", "translation": "to change seats"},
    "полоннна": {"lemma": "полонина", "ipa": "/pɔlɔˈnɪna/", "translation": "mountain valley"},
    "підлет": {"lemma": "підліт", "ipa": "/pidˈlʲit/", "translation": "approach (flight)"},
    "летити": {"lemma": "летіти", "ipa": "/lɛˈtʲitɪ/", "translation": "to fly"},
    "небути": {"lemma": "не бути", "ipa": "/nɛ ˈbutɪ/", "translation": "not to be"},
    "допізний": {"lemma": "пізній", "ipa": "/ˈpiznʲij/", "translation": "late"},
    "риториця": {"lemma": "риторика", "ipa": "/rɪˈtɔrɪka/", "translation": "rhetoric"},
    "паралеле": {"lemma": "паралель", "ipa": "/paraˈlɛlʲ/", "translation": "parallel"},
    "попрости": {"lemma": "попросити", "ipa": "/pɔprɔˈsɪtɪ/", "translation": "to ask"},
    "прошедшее": {"lemma": "минуле", "ipa": "/mɪˈnulɛ/", "translation": "past"},
    "чтобы": {"lemma": "щоб", "ipa": "/ʃt͡ʃɔb/", "translation": "in order to"},
    "кипити": {"lemma": "кипіти", "ipa": "/kɪˈpʲitɪ/", "translation": "to boil"},
    "бы": {"lemma": "би", "ipa": "/bɪ/", "translation": "would"},
    "гравка": {"lemma": "гравець", "ipa": "/hraˈvɛt͡sʲ/", "translation": "player"},
    "щастивіший": {"lemma": "щасливіший", "ipa": "/ʃt͡ʃaslɪˈvʲiʃɪj/", "translation": "happier"},
    "пократи": {"lemma": "покрити", "ipa": "/pɔˈkrɪtɪ/", "translation": "to cover"},
    "который": {"lemma": "який", "ipa": "/jaˈkɪj/", "translation": "which"},
    "піднімти": {"lemma": "підняти", "ipa": "/pidˈnʲatɪ/", "translation": "to raise"},
    "хотяти": {"lemma": "хотіти", "ipa": "/xɔˈtʲitɪ/", "translation": "to want"},
    "переглянити": {"lemma": "переглянути", "ipa": "/pɛrɛˈhlʲanutɪ/", "translation": "to review"},
    "едва": {"lemma": "ледве", "ipa": "/ˈlɛdvɛ/", "translation": "barely"},
    "только": {"lemma": "тільки", "ipa": "/ˈtʲilʲkɪ/", "translation": "only"},
    "підходящий": {"lemma": "відповідний", "ipa": "/vidpɔˈvidnɪj/", "translation": "suitable"},
    "біжач": {"lemma": "бігун", "ipa": "/biˈhun/", "translation": "runner"},
    "радіватися": {"lemma": "радіти", "ipa": "/raˈdʲitɪ/", "translation": "to rejoice"},
    "їздіти": {"lemma": "їздити", "ipa": "/ˈjizdɪtɪ/", "translation": "to ride"},
    "прити": {"lemma": "прийти", "ipa": "/prɪjˈtɪ/", "translation": "to come"},
    "прочити": {"lemma": "прочитати", "ipa": "/prɔt͡ʃɪˈtatɪ/", "translation": "to read"},
    "бувший": {"lemma": "колишній", "ipa": "/kɔˈlɪʃnʲij/", "translation": "former"},
    "біднійший": {"lemma": "бідніший", "ipa": "/bidˈnʲiʃɪj/", "translation": "poorer"},
    "пожовкний": {"lemma": "пожовклий", "ipa": "/pɔˈʒɔu̯klɪj/", "translation": "yellowed"},
    "причастність": {"lemma": "причетність", "ipa": "/prɪˈt͡ʃɛtnʲisʲtʲ/", "translation": "involvement"},
    "проживаючь": {"lemma": "проживаючи", "ipa": "/prɔʒɪˈvajut͡ʃɪ/", "translation": "residing"},
    "слідуючий": {"lemma": "наступний", "ipa": "/naˈstupnɪj/", "translation": "next"},
    "співпадаючий": {"lemma": "що співпадає", "ipa": "/ʃt͡ʃɔ spiu̯paˈdajɛ/", "translation": "coinciding"},
    "одити": {"lemma": "ходити", "ipa": "/xɔˈdɪtɪ/", "translation": "to walk"},
    "одитий": {"lemma": "одягнений", "ipa": "/ɔˈdʲahnɛnɪj/", "translation": "dressed"},
    "прадавний": {"lemma": "прадавній", "ipa": "/praˈdau̯nʲij/", "translation": "ancient"},
    "зачинути": {"lemma": "зачинити", "ipa": "/zat͡ʃɪˈnɪtɪ/", "translation": "to close"},
    "пекати": {"lemma": "пекти", "ipa": "/pɛkˈtɪ/", "translation": "to bake"},
    "пекертися": {"lemma": "пектися", "ipa": "/pɛkˈtɪsʲa/", "translation": "to be baked"},
    "рішити": {"lemma": "вирішити", "ipa": "/vɪˈrʲiʃɪtɪ/", "translation": "to decide"},
    "водка": {"lemma": "горілка", "ipa": "/ɦɔˈrʲilka/", "translation": "vodka"},
    "матонький": {"lemma": "матінка", "ipa": "/ˈmatʲinka/", "translation": "mother (dim.)"},
    "плакал": {"lemma": "плакав", "ipa": "/ˈplakau̯/", "translation": "cried"},
    "сирк": {"lemma": "сирок", "ipa": "/sɪˈrɔk/", "translation": "curd snack/cheese"},
    "втора": {"lemma": "друга", "ipa": "/ˈdruha/", "translation": "second"},
    "півтор": {"lemma": "півтора", "ipa": "/piu̯tɔˈra/", "translation": "one and a half"},
    "штані": {"lemma": "штани", "ipa": "/ʃtaˈnɪ/", "translation": "pants"},
    "дроб": {"lemma": "дріб", "ipa": "/drib/", "translation": "fraction"},
    "провкта": {"lemma": "проєкт", "ipa": "/prɔˈjɛkt/", "translation": "project"},
    "сніданати": {"lemma": "снідати", "ipa": "/ˈsnʲidatɪ/", "translation": "to have breakfast"},
    "інструментарія": {"lemma": "інструментарій", "ipa": "/instrumɛnˈtarʲij/", "translation": "toolkit"},
    "ревати": {"lemma": "ревти", "ipa": "/rɛu̯ˈtɪ/", "translation": "to roar"}
}

DELETES = {
    "лвжома", "тити", "укятися", "сла", "нарігти", "ущяти", "женувати", "кор", "перево", "дуза",
    "повер", "поверти", "лнестія", "стартя", "суперсити", "уваський", "ойно", "зос", "борка",
    "прошача", "спача", "юти", "відбуваючийся", "відбуваючіся", "маючий", "співпадаючий", 
    "вимо", "оти", "поба", "розба", "погадити", "ятко", "кищві", "меро", "сяодовні"
}

def fix_b1_vocab(root_dir="curriculum/l2-uk-en/b1"):
    vocab_dir = os.path.join(root_dir, "vocabulary")
    
    for filename in sorted(os.listdir(vocab_dir)):
        if not filename.endswith('.yaml'):
            continue
            
        filepath = os.path.join(vocab_dir, filename)
        md_filename = filename.replace('.yaml', '.md')
        md_filepath = os.path.join(root_dir, md_filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except:
                print(f"Skipping bad YAML: {filename}")
                continue
                
        if not data or 'items' not in data:
            continue
            
        new_items = []
        modified = False
        md_content = None
        
        # Load MD content if needed
        if os.path.exists(md_filepath):
            with open(md_filepath, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
        existing_lemmas = set()
        
        # First pass to check existing lemmas (excluding ones we want to delete/change)
        # Note: We need to handle the case where we change a lemma to one that already exists.
        # So we can't just build a set of all current lemmas.
        # Instead, let's process items.
        
        processed_items = []
        
        for item in data['items']:
            lemma = item.get('lemma')
            
            if lemma in DELETES:
                print(f"[{filename}] Deleting nonsense: {lemma}")
                modified = True
                continue
                
            if lemma in FIXES:
                fix = FIXES[lemma]
                print(f"[{filename}] Fixing typo: {lemma} -> {fix['lemma']}")
                
                # Update item
                item['lemma'] = fix['lemma']
                item['ipa'] = fix['ipa']
                item['translation'] = fix['translation']
                
                # Check for other fix fields if defined in FIXES (I didn't define many POS/gender changes but could)
                # For now just lemma/ipa/translation
                
                modified = True
                
                # Fix in MD if possible
                if md_content and lemma in md_content:
                    # Simple replace, maybe wary of partial matches? 
                    # Assuming lemma is usually a distinct word.
                    # Using regex word boundaries
                    pattern = r'\b' + re.escape(lemma) + r'\b'
                    if re.search(pattern, md_content):
                        print(f"  -> Fixing in MD: {lemma} -> {fix['lemma']}")
                        md_content = re.sub(pattern, fix['lemma'], md_content)
            
            processed_items.append(item)
            
        # Deduplication
        final_items = []
        seen_lemmas = set()
        for item in processed_items:
            lemma = item.get('lemma')
            if lemma in seen_lemmas:
                print(f"[{filename}] Duplicate lemma after fix (kept first): {lemma}")
                continue
            seen_lemmas.add(lemma)
            final_items.append(item)
            
        if modified:
            data['items'] = final_items
            
            # Write vocabulary
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
                
            # Write MD if changed
            if md_content and os.path.exists(md_filepath):
                # Check if MD actually changed content
                with open(md_filepath, 'r', encoding='utf-8') as f:
                    orig_md = f.read()
                if md_content != orig_md:
                    with open(md_filepath, 'w', encoding='utf-8') as f:
                        f.write(md_content)

if __name__ == "__main__":
    fix_b1_vocab()
