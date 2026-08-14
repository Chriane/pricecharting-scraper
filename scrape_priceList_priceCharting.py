import os
import glob
from bs4 import BeautifulSoup
import sqlite3
import pathlib
import urllib.parse
import json

def parse_html_file(filepath, code_mapping):
    base_url = "https://www.pricecharting.com"
    code = os.path.splitext(os.path.basename(filepath))[0]
    
    code = code_mapping.get(code, code)

    data = []
    
    print(f"\n--- Parsing local file {filepath} (Code: {code}) ---")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', id='games_table')

    if not table:
        print(f"Could not find the games table in {filepath}.")
        return

    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
    page_count = 0

    for row in rows:
        title_td = row.find('td', class_='title')
        loose_td = row.find('td', class_='used_price')
        cib_td = row.find('td', class_='cib_price')

        if title_td:
            title = title_td.text.strip()
            loose_price = loose_td.text.strip() if loose_td else ""
            cib_price = cib_td.text.strip() if cib_td else ""

            a_tag = title_td.find('a')
            game_url = urllib.parse.urljoin(base_url, a_tag.get('href')) if a_tag and a_tag.get('href') else ""

            if title.lower() == "title" or not title:
                continue
                
            owned = 1 if 'in Collection' in row.text or 'In Collection' in row.text else 0

            data.append({
                "title": title,
                "loose_price": loose_price,
                "cib_price": cib_price,
                "url": game_url,
                "owned": owned
            })
            page_count += 1

    print(f"Extracted {page_count} items from {filepath}.")

    # Output to SQLite Database
    db_path = (pathlib.Path(__file__).resolve().parent / '../sqlLite/ads.db').resolve()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for item in data:
        cursor.execute('''
            INSERT INTO pricecharting_data (console_code, title, loose_price, cib_price, url, owned)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (code, item['title'], item['loose_price'], item['cib_price'], item['url'], item['owned']))

    conn.commit()
    conn.close()
        
    print(f"Successfully saved {len(data)} games from {filepath} to the database at {db_path}")

def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'console_codes.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            code_mapping = json.load(f)
    except Exception as e:
        print(f"Error loading console_codes.json: {e}")
        code_mapping = {}

    # Find all HTML files in the current directory
    html_files = glob.glob('*.html')
    
    if not html_files:
        print("No .html files found in the current directory.")
        return
        
    # Setup database and clear previous entries
    db_path = (pathlib.Path(__file__).resolve().parent / '../sqlLite/ads.db').resolve()
    os.makedirs(db_path.parent, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricecharting_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            console_code TEXT,
            title TEXT,
            loose_price TEXT,
            cib_price TEXT,
            url TEXT,
            owned INTEGER
        )
    ''')
    cursor.execute('DELETE FROM pricecharting_data')
    conn.commit()
    conn.close()

    for filepath in html_files:
        parse_html_file(filepath, code_mapping)

if __name__ == "__main__":
    main()
