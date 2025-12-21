import os
import re
import glob

def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Header Standardization (H2 -> H1 for main sections)
    header_replacements = [
        (r'^##\s+(Summary|Підсумок)', r'# Підсумок'),
        (r'^##\s+(Activities|Вправи|Exercises)', r'# Вправи'),
        (r'^##\s+(Vocabulary|Словник)', r'# Словник'),
        (r'^#\s+Summary', r'# Підсумок'),
        (r'^#\s+Activities', r'# Вправи'),
        (r'^#\s+Vocabulary', r'# Словник'),
    ]
    
    new_content = content
    for pattern, repl in header_replacements:
        new_content = re.sub(pattern, repl, new_content, flags=re.MULTILINE | re.IGNORECASE)

    # 2. Vocabulary Table Standardization
    vocab_match = re.search(r'# Словник\s*\n\n(.*?)(?=\n\n#|\n---|\Z)', new_content, re.DOTALL | re.MULTILINE)
    if vocab_match:
        vocab_block = vocab_match.group(1)
        lines = vocab_block.split('\n')
        
        # Determine current table width
        header_row_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('|') and '---' not in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3: # Need at least 3 columns to identify
                    header_row_idx = i
                    break
        
        if header_row_idx != -1:
            header_line = lines[header_row_idx]
            parts = [p.strip() for p in header_line.split('|') if p.strip()]
            num_cols = len(parts)
            
            if num_cols == 5:
                # Just standardize headers if 5-column
                new_vocab_lines = lines[:header_row_idx]
                new_vocab_lines.append('| Слово | Вимова | Переклад | ЧМ | Примітка |')
                new_vocab_lines.append('|-------|--------|----------|-----|----------|')
                new_vocab_lines.extend(lines[header_row_idx+2:])
                updated_vocab_block = '\n'.join(new_vocab_lines)
                new_content = new_content.replace(vocab_block, updated_vocab_block)
            else:
                # Need to restructure
                new_vocab_lines = lines[:header_row_idx]
                new_vocab_lines.append('| Слово | Вимова | Переклад | ЧМ | Примітка |')
                new_vocab_lines.append('|-------|--------|----------|-----|----------|')
                
                for line in lines[header_row_idx+2:]:
                    if line.strip().startswith('|'):
                        row_parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(row_parts) == num_cols:
                            if num_cols == 3: # Word, English, Note
                                uk, en, note = row_parts
                                pos = '-'; note_lower = note.lower()
                                if 'noun' in note_lower or 'ім.' in note_lower: pos = 'ім.'
                                elif 'verb' in note_lower or 'дієсл' in note_lower: pos = 'дієсл.'
                                elif 'adj' in note_lower or 'прикм' in note_lower: pos = 'прикм.'
                                elif 'adv' in note_lower or 'присл' in note_lower: pos = 'присл.'
                                clean_note = re.sub(r'\(?noun\)?|ім\.|verb|дієсл\.|adj|прикм\.|adv|присл\.|,?\s*$', '', note, flags=re.IGNORECASE).strip()
                                new_vocab_lines.append(f'| {uk} | /.../ | {en} | {pos} | {clean_note} |')
                            elif num_cols == 4: # Слово, Переклад, ЧМ, Примітка
                                uk, en, pos, note = row_parts
                                # Optional: Standardize POS
                                if 'noun' in pos.lower(): pos = 'ім.'
                                elif 'verb' in pos.lower(): pos = 'дієсл.'
                                new_vocab_lines.append(f'| {uk} | /.../ | {en} | {pos} | {note} |')
                            elif num_cols == 6: # Word, IPA, Translation, POS, Gender, Note
                                uk, ipa, en, pos, gen, note = row_parts
                                if 'noun' in pos.lower(): pos = 'ім.'
                                elif 'verb' in pos.lower(): pos = 'дієсл.'
                                combined_note = f"{gen} | {note}".strip(' |')
                                new_vocab_lines.append(f'| {uk} | {ipa} | {en} | {pos} | {combined_note} |')
                            else:
                                # Fallback or skip
                                new_vocab_lines.append(line)
                        else:
                            new_vocab_lines.append(line)
                    else:
                        new_vocab_lines.append(line)
                
                updated_vocab_block = '\n'.join(new_vocab_lines)
                new_content = new_content.replace(vocab_block, updated_vocab_block)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    files = glob.glob('curriculum/l2-uk-en/b1/*.md')
    fixed_count = 0
    for f in files:
        if fix_file(f):
            print(f"Fixed: {f}")
            fixed_count += 1
    print(f"Total files fixed: {fixed_count}")
