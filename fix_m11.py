import sys, re, yaml

# Fix MD Quotes
md_path = 'curriculum/l2-uk-en/c1/11-summary-paraphrase.md'
try:
    with open(md_path, 'r') as f:
        md_content = f.read()
    md_content = re.sub(r'\"([^\"]*?)\"', r'«\1»', md_content)
    with open(md_path, 'w') as f:
        f.write(md_content)
    print("Fixed quotes in MD.")
except Exception as e:
    print(f"Error fixing MD: {e}")

# Fix YAML
yaml_path = 'curriculum/l2-uk-en/c1/activities/11-summary-paraphrase.yaml'
try:
    with open(yaml_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    
    # Context counters
    processed_count = 0
    
    current_type = ''
    in_options_block = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = line[:line.find(stripped)] if stripped else ''
        
        # Identify Type
        if '- type:' in line:
            current_type = line.split('type:')[1].strip()
        elif 'type:' in line and not stripped.startswith('-'):
             # Careful if it's an item property 'type' (unlikely)
             current_type = line.split('type:')[1].strip()
             
        # Check blocks
        if stripped == 'options:' or stripped == 'pairs:' or stripped == 'groups:':
            in_options_block = True
        elif stripped.startswith('- id:') or stripped.startswith('- type:') or stripped.startswith('items:'):
            in_options_block = False
            
        # 1. Fill-in Fix: replace '- text:' with '- sentence:' for items
        if current_type == 'fill-in' and stripped.startswith('- text:') and not in_options_block:
            new_lines.append(line.replace('text:', 'sentence:', 1))
            processed_count += 1
            continue
            
        # 2. True-False Fix: replace 'answer:' with 'correct:'
        if current_type == 'true-false' and stripped.startswith('answer:'):
             new_lines.append(line.replace('answer:', 'correct:', 1))
             processed_count += 1
             continue
             
        # 3. Quiz Missing Correct
        # Logic: If inside quiz options, and we have '- text:', check if next line is 'correct:'.
        if current_type == 'quiz' and stripped.startswith('- text:') and in_options_block:
            new_lines.append(line)
            # Peek next line
            if i + 1 < len(lines):
                next_line = lines[i+1]
                if not next_line.strip().startswith('correct:'):
                    # Add correct: false
                    # indent is usually same as line minus '- ' + '  '
                    # Or simpler: indent of line + 2 spaces or 4 spaces?
                    # YAML usually:
                    # - text: ...
                    #   correct: ...
                    # So indent of correct matches indent of text (Wait? No)
                    # Text is '- text'. 'correct' is sibling of 'text'? No, correct is property of option object.
                    # - text: foo
                    #   correct: false
                    # So correct is indented relative to '-' of parent list item.
                    # line: '    - text: ...'
                    # next: '      correct: ...'
                    # So indent = line indent + 2 spaces.
                    new_lines.append(indent + '  correct: false\n')
                    processed_count += 1
            continue
            
        # 4. Mark-the-words correct_words extraction
        if current_type == 'mark-the-words' and stripped.startswith('passage:'):
            new_lines.append(line)
            content = line.split('passage:')[1].strip()
            # Remove outer quotes if basic
            if (content.startswith('\'') and content.endswith('\'')) or (content.startswith('\"') and content.endswith('\"')):
                content = content[1:-1]
            
            matches = re.findall(r'\*([^*\s]+)\*', content)
            if matches:
                new_lines.append(indent + 'correct_words:\n')
                for m in matches:
                    new_lines.append(indent + '- ' + m + '\n')
                processed_count += 1
            continue

        # 5. Essay Prompt
        if current_type == 'essay-response' and stripped.startswith('min_words:'):
            new_lines.append(line)
            new_lines.append(indent + 'prompt: |\n')
            new_lines.append(indent + '  **Завдання:** Напишіть резюме тексту.\n\n')
            new_lines.append(indent + '  1. Оберіть текст\n')
            new_lines.append(indent + '  2. Виділіть головне\n')
            new_lines.append(indent + 'model_answer: \"Автор статті аналізує проблему зміни клімату (тема), стверджуючи, що головною причиною є антропогенний фактор (ідея). Підсумовуючи, стаття закликає до негайних дій (висновок).\"\n')
            processed_count += 1
            continue

        new_lines.append(line)
        
    with open(yaml_path, 'w') as f:
        f.writelines(new_lines)
    print(f"Fixed YAML. Processed {processed_count} lines.")
    
except Exception as e:
    print(f"Error fixing YAML: {e}")
