import requests
from bs4 import BeautifulSoup
import json
import time
import os

def scrape_console(url, code):
    base_url = "https://www.pricecharting.com"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    data = []
    
    print(f"\n--- Scraping {code} from {url} ---")
    print(f"Fetching first page...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return

    while True:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', id='games_table')

        if not table:
            print("Could not find the games table on the page.")
            break

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
                game_url = base_url + a_tag.get('href') if a_tag and a_tag.get('href') else ""

                if title.lower() == "title" or not title:
                    continue

                data.append({
                    "title": title,
                    "loose_price": loose_price,
                    "cib_price": cib_price,
                    "url": game_url
                })
                page_count += 1
                
        print(f"Extracted {page_count} items from this page.")

        # Check for next page
        next_form = soup.find('form', class_='next_page')
        if next_form:
            cursor_input = next_form.find('input', {'name': 'cursor'})
            if cursor_input and cursor_input.get('value'):
                cursor = cursor_input.get('value')
                print(f"Found next page cursor: {cursor}. Fetching...")
                
                # Extract other hidden inputs to send with the POST request
                post_data = {}
                for input_tag in next_form.find_all('input', type='hidden'):
                    post_data[input_tag.get('name')] = input_tag.get('value')
                
                # Small delay to be polite
                time.sleep(1)
                
                try:
                    response = requests.post(url, headers=headers, data=post_data)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching next page: {e}")
                    break
            else:
                break
        else:
            break

    # Output as JSON
    output_filename = f"priceList_{code}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    print(f"Successfully scraped a total of {len(data)} games and saved to {output_filename}")

def main():
    config_file = 'configuration_priceCharting.json'
    
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found. Please create it.")
        return
        
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_file}: {e}")
        return
        
    consoles = config.get('consoles', [])
    
    if not consoles:
        print("No consoles found in configuration.")
        return
        
    for console in consoles:
        url = console.get('url')
        code = console.get('code')
        
        if not url or not code:
            print(f"Skipping invalid entry: {console}")
            continue
            
        scrape_console(url, code)

if __name__ == "__main__":
    main()
