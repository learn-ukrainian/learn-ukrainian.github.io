
import sqlite3
import json
import sys

DB_PATH = 'curriculum/l2-uk-en/vocabulary.db.bak'
OUTPUT_FILE = 'recovery_enrichment.json'

def extract():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT uk, ipa, en, pos, gender, notes FROM lemmas WHERE ipa != '' OR en != ''")
        rows = cursor.fetchall()
        
        data = []
        for row in rows:
            data.append({
                'uk': row['uk'],
                'ipa': row['ipa'],
                'en': row['en'],
                'pos': row['pos'],
                'gender': row['gender'],
                'notes': row['notes']
            })
            
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Extracted {len(data)} enriched entries to {OUTPUT_FILE}")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    extract()
