import json
import re
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

def normalize_for_match(name):
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    for w in ['limited', 'ltd', 'unlisted', 'shares', 'private', 'pvt', 'inc', 'co']:
        s = s.replace(w, '')
    return s

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
        source = stock.get("source")
        
        # If Sharescart (the backup), try to fuzzy-match against UnlistedZone
        if source == "sharescart":
            matched_slug = None
            sc_match = normalize_for_match(stock.get("company", ""))
            
            if slug in existing_data:
                matched_slug = slug
            else:
                for ext_slug, ext_data in existing_data.items():
                    if ext_data.get("source") == "unlistedzone":
                        ext_match = normalize_for_match(ext_data.get("company", ""))
                        if sc_match and ext_match and len(sc_match) >= 3 and len(ext_match) >= 3:
                            if sc_match == ext_match or sc_match.startswith(ext_match) or ext_match.startswith(sc_match):
                                matched_slug = ext_slug
                                break
                                
            if matched_slug:
                ext = existing_data[matched_slug]
                # Merge missing fields
                for k, v in stock.items():
                    if v is not None and ext.get(k) is None:
                        ext[k] = v
                
                # Backup price logic
                if stock.get("price") is not None:
                    if ext.get("price") is None:
                        ext["price"] = stock.get("price")
                        ext["source"] = "sharescart" # We are relying on sharescart now
                    else:
                        ext["backup_price"] = stock.get("price")
                        
                upserted_count += 1
                continue

        # Standard upsert
        if slug in existing_data:
            existing_data[slug].update({k: v for k, v in stock.items() if v is not None})
            upserted_count += 1
        else:
            existing_data[slug] = stock
            new_count += 1
            
    save_data(existing_data)
    return new_count, upserted_count
