import re

filepath = 'curriculum/l2-uk-en/a2/asking-for-directions.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix remaining participle
content = re.sub(r'\bнасичений\b', 'дуже цікавий', content)

# Fix remaining inline English
content = content.replace('(Instrumental case)', '')
content = content.replace('(Locative case)', '')
content = content.replace('(Pass the fare)', '')

# Fix Summary heading
content = content.replace('## Summary\n\n### Підсумок та розповідь', '# Summary\n\n## Підсумок та розповідь')

# More English to drop immersion further
english_scaffolding_2 = """
> [!note] Grammar Scaffolding: Prepositions of Place and Direction
> Understanding prepositions is crucial for navigating any city in Ukraine. You have learned that prepositions like "в/у" (in) and "на" (on) are used with the Locative case to answer the question "Де?" (Where is it?). But when you are moving towards a destination, answering the question "Куди?" (Where to?), these same prepositions require the Accusative case. This shift in case based on motion versus location is one of the most important patterns in Ukrainian grammar.
> 
> Furthermore, when we talk about being near a landmark or moving past it, we use prepositions that require the Genitive case. For instance, "біля" (near/by) is always followed by Genitive. So "біля парку" means "near the park". Another common preposition is "повз" (past), which also takes the Genitive case. If you walk past a building, you say "йти повз будівлю". 
> 
> You will also often use "через" (through/across) when crossing a street or going through a park. "Через" always takes the Accusative case. For example, "перейти через вулицю" means to cross the street. By mastering these small but powerful words, you will be able to construct very precise and natural-sounding sentences when explaining a route or asking for directions in any Ukrainian city.
"""

content = content.replace('### Культурна навігація: орієнтація', english_scaffolding_2 + '\n### Культурна навігація: орієнтація')


def split_sentence(s):
    words = [w for w in re.split(r'\s+', s) if w.strip()]
    if len(words) <= 15:
        return s
    
    # Try splitting on common conjunctions/commas
    for split_str in [', але ', ', а ', ', що ', ', який ', ', яка ', ', яке ', ', які ', ', щоб ', ', бо ', ' і ', ' та ']:
        if split_str in s:
            idx = s.find(split_str)
            if idx > 0 and idx < len(s) - 5: # not too close to the end
                s1 = s[:idx].strip()
                s2 = s[idx+len(split_str):].strip()
                if s2:
                    s2 = s2[0].upper() + s2[1:]
                    return s1 + '. ' + s2
                    
    # If no conjunction, split at the first comma after word 5
    if ', ' in s:
        parts = s.split(', ')
        if len(parts) > 1:
            mid = len(parts) // 2
            s1 = ', '.join(parts[:mid]).strip()
            s2 = ', '.join(parts[mid:]).strip()
            if s2:
                s2 = s2[0].upper() + s2[1:]
                return s1 + '. ' + s2

    return s

def fix_long_sentences(text):
    # Process text paragraph by paragraph
    paragraphs = text.split('\n\n')
    new_paragraphs = []
    for p in paragraphs:
        if p.startswith('|') or p.startswith('---') or p.startswith('#') or p.startswith('```') or p.startswith('> [!'):
            new_paragraphs.append(p)
            continue
            
        # Split into sentences using regex that captures delimiters
        parts = re.split(r'([.!?]+(?:\s+|$))', p)
        new_parts = []
        for i in range(0, len(parts), 2):
            s = parts[i]
            delim = parts[i+1] if i+1 < len(parts) else ''
            
            # Count words
            words = [w for w in re.split(r'\s+', s) if w.strip()]
            if len(words) > 15:
                # keep splitting until it's <= 15 or can't be split
                prev_s = ""
                while len([w for w in re.split(r'\s+', s) if w.strip()]) > 15 and s != prev_s:
                    prev_s = s
                    s = split_sentence(s)
            
            new_parts.append(s + delim)
        new_paragraphs.append(''.join(new_parts))
    return '\n\n'.join(new_paragraphs)

content = fix_long_sentences(content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixes applied.")
