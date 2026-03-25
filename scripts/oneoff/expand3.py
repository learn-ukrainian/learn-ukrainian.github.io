import re

def main():
    filepath = "curriculum/l2-uk-en/bio/berta-rapoport.md"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Expand conclusion slightly
    s7_old = "а пам'ять про її незламний дух увічнено в Одесі."
    if s7_old in content:
        s7_new = s7_old + " Її життєвий подвиг залишається вічним джерелом натхнення."
        content = content.replace(s7_old, s7_new)


    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
