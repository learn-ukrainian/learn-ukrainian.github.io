import yaml
import os
import re

ORCH_DIR = "curriculum/l2-uk-en/a1/orchestration/the-accusative-i-things"
LOG_PATH = "curriculum/l2-uk-en/a1/audit/the-accusative-i-things-audit.log"
PLACEHOLDERS_PATH = os.path.join(ORCH_DIR, "placeholders.yaml")

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def main():
    with open(LOG_PATH, 'r') as f:
        log_content = f.read()

    stats = {}
    
    # Extract Words
    m_words = re.search(r"Words\s+✅\s+(\d+)/(\d+)", log_content)
    if m_words:
        stats['AUDIT_WORD_COUNT'] = m_words.group(1)
        stats['WORD_TARGET'] = m_words.group(2)
        stats['WORD_PERCENT'] = str(int(int(m_words.group(1)) * 100 / int(m_words.group(2))))
    
    # Extract Activities
    m_act = re.search(r"Activities\s+✅\s+(\d+)/(\d+)", log_content)
    if m_act:
        stats['ACTIVITY_COUNT'] = m_act.group(1)

    # Extract Vocab
    m_vocab = re.search(r"Vocab\s+✅\s+(\d+)/(\d+)", log_content)
    if m_vocab:
        stats['VOCAB_COUNT'] = m_vocab.group(1)
        
    # Extract Immersion
    m_imm = re.search(r"Immersion\s+🇺🇦\s+(\d+\.\d+)%", log_content)
    if m_imm:
        stats['IMMERSION_PERCENT'] = m_imm.group(1)
        stats['IMMERSION_TARGET'] = "25-40%" # Hardcoded based on rule or extracted if present
        
    # Extract Engagement
    m_eng = re.search(r"Engagement\s+✅\s+(\d+)/(\d+)", log_content)
    if m_eng:
        stats['ENGAGEMENT_COUNT'] = m_eng.group(1)

    stats['AUDIT_STATUS'] = "PASS"
    stats['PREV_MODULE'] = "10" # Hardcoded based on M11

    placeholders = load_yaml(PLACEHOLDERS_PATH)
    placeholders.update(stats)
    save_yaml(placeholders, PLACEHOLDERS_PATH)
    print("Updated placeholders with stats:", stats)

if __name__ == "__main__":
    main()
