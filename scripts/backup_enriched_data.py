import sqlite3
import json
from pathlib import Path

DB_PATH = Path("curriculum/l2-uk-en/vocabulary.db")
BACKUP_FILE = "backup_enrichment.json"

def backup_data():
    if not DB_PATH.exists():
        print("No database to backup.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Select only rows that have enriched data
    cursor.execute("""
        SELECT uk, ipa, en, notes 
        FROM lemmas 
        WHERE ipa != '' OR en != ''
    """)
    
    columns = [col[0] for col in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Backed up {len(data)} enriched entries to {BACKUP_FILE}")
    conn.close()

if __name__ == "__main__":
    backup_data()
