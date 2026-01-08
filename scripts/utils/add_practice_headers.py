import os

def add_practice_headers():
    base_dir = "curriculum/l2-uk-en"
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    
    updated_count = 0
    total_count = 0
    
    for level in levels:
        level_dir = os.path.join(base_dir, level)
        if not os.path.isdir(level_dir):
            continue
            
        for filename in os.listdir(level_dir):
            if filename.endswith(".md"):
                total_count += 1
                path = os.path.join(level_dir, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "## Need More Practice?" not in content:
                    # Append header to the end
                    # Ensure there is a newline before
                    if not content.endswith("\n\n"):
                        if content.endswith("\n"):
                            content += "\n"
                        else:
                            content += "\n\n"
                    
                    content += "---\n\n## Need More Practice?\n"
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated_count += 1

    print(f"Total modules checked: {total_count}")
    print(f"Updated {updated_count} modules with '## Need More Practice?' header.")

if __name__ == "__main__":
    add_practice_headers()
