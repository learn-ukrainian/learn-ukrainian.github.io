import re
import yaml

def refactor_cloze(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read as lines to preserve comments/order if possible, but for activity processing simpler to use full loader
        # We will use full loader and dump, then I might need to manual fixes if format looks bad
        # Actually, let's just parse the relevant blocks using regex to avoid reformatting the whole file.
        content = f.read()

    # Find cloze blocks
    # Pattern: - type: cloze ... passage: '...'
    
    # We will process the file content line by line statefully
    lines = content.split('\n')
    new_lines = []
    
    in_cloze = False
    cloze_indent = ""
    passage_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check start of cloze
        if line.strip() == "- type: cloze":
            in_cloze = True
            cloze_indent = line[:line.find("-")]
            new_lines.append(line)
            i += 1
            print(f"Found cloze at line {i}")
            continue
            
        if in_cloze:
            # If we hit next activity or end of file
            if line.strip().startswith("- type:") or (line.strip() and len(line) - len(line.lstrip()) < len(cloze_indent) + 2 and line.strip() != ''):
                 # End of cloze block
                 in_cloze = False
                 # We need to process the captured passage lines if valid
                 if passage_lines:
                     # Reconstruct passage
                     full_passage = " ".join([l.strip() for l in passage_lines])
                     # Process passage
                     new_passage, blanks = process_passage(full_passage)
                     
                     # Write new passage
                     # We need to correctly indent multiline string
                     indent = cloze_indent + "  "
                     new_lines.append(f"{indent}passage: |")
                     for p_line in wrap_text(new_passage, 80):
                         new_lines.append(f"{indent}  {p_line}")
                     
                     # Write blanks
                     new_lines.append(f"{indent}blanks:")
                     for blank in blanks:
                         new_lines.append(f"{indent}- id: {blank['id']}")
                         new_lines.append(f"{indent}  answer: \"{blank['answer']}\"")
                         new_lines.append(f"{indent}  options:")
                         for opt in blank['options']:
                             new_lines.append(f"{indent}  - \"{opt}\"")
                         
                     passage_lines = []
                 
                 new_lines.append(line)
                 i += 1
                 continue
            
            # Check for passage key
            if "passage:" in line:
                 # Start capturing passage
                 # It might be multiline with quotes or just multiline
                 # Simplest: assume it's followed by text
                 val = line.split("passage:", 1)[1].strip()
                 if val:
                     # remove starting quote if present
                     if val.startswith("'") or val.startswith('"'):
                         val = val[1:]
                     passage_lines.append(val)
                 i += 1
                 # Read subsequent indented lines
                 while i < len(lines):
                     sub_line = lines[i]
                     if not sub_line.strip():
                         i+=1
                         continue
                     # Check indent
                     sub_indent = len(sub_line) - len(sub_line.lstrip())
                     if sub_indent > len(cloze_indent) + 2:
                         # continuation of passage
                         val = sub_line.strip()
                         # Clean ending quote
                         if val.endswith("'") or val.endswith('"'):
                              val = val[:-1]
                         passage_lines.append(val)
                         i += 1
                     else:
                         break
                 continue
            
            # Keep other lines (title, instruction)
            new_lines.append(line)
            i += 1
        else:
            new_lines.append(line)
            i += 1

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

def process_passage(text):
    # Regex for {opt1|opt2...}
    # Handling potential newlines in regex?
    tokens = re.split(r'(\{.*?\}|__)', text)
    new_text_parts = []
    blanks = []
    
    blank_id = 1
    
    # Simple regex to find {a|b|c}
    # Note: text might contain "}" inside? Unlikely for this content.
    matches = list(re.finditer(r'\{([^}]+)\}(__)?', text))
    
    if not matches:
        return text.strip(), []
        
    last_pos = 0
    for m in matches:
        # Append text before
        new_text_parts.append(text[last_pos:m.start()])
        
        # Process options
        content = m.group(1)
        options = [o.strip() for o in content.split('|')]
        answer = options[0] # Assume first is correct
        
        # Add placeholder
        new_text_parts.append(f"{{{blank_id}}}")
        
        blanks.append({
            'id': blank_id,
            'answer': answer,
            'options': options
        })
        
        blank_id += 1
        last_pos = m.end()
        
    new_text_parts.append(text[last_pos:])
    
    return "".join(new_text_parts).strip(), blanks

def wrap_text(text, width):
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    for w in words:
        if current_len + len(w) + 1 > width:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
        else:
            current_line.append(w)
            current_len += len(w) + 1
    if current_line:
        lines.append(" ".join(current_line))
    return lines

if __name__ == "__main__":
    refactor_cloze('curriculum/l2-uk-en/b2/activities/02-past-passive-participles.yaml')
