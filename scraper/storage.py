import json
from datetime import datetime
from scraper.config import DATA_FILE

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {}

def save_data(data_dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)

def upsert_stocks(scraped_stocks):
    """
    scraped_stocks is a list of dictionaries.
    We upsert them into the data JSON using slug as the key.
    """
    existing_data = load_data()
    
    upserted_count = 0
    new_count = 0
    
    for stock in scraped_stocks:
        slug = stock.get("slug")
        if not slug:
            continue
            
        stock["updated_at"] = datetime.now().isoformat()
        
        if slug in existing_data:
            existing_data[slug].update({k: v for k, v in stock.items() if v is not None})
            upserted_count += 1
        else:
            existing_data[slug] = stock
            new_count += 1
            
    save_data(existing_data)
    return new_count, upserted_count
