import re
import time

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def scrape_sharescart(mode="all", priority_slugs=None):
    import requests
    import json
    
    url = "https://www.sharescart.com/web-services/unlisted-stocks-intermediary.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php"
    }
    data = "action=unlisted_shares_quotes_new&company_name=&mcap=all&price=all&industry=all&instaBuy=No"
    results = []
    print(f"   Scraping SharesCart from {url} via API")

    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        try:
            json_data = response.json()
            items = json_data.get("data", [])
            print(f"   SharesCart: Found {len(items)} companies")
            
            for item in items:
                company = item.get("UL_STOCKS_COMPNAME", "")
                price = str(item.get("UL_PD_BID_PRICE", ""))
                if not company or not price or float(price) <= 0:
                    continue
                    
                extra_data = {}
                mcap = item.get("MCAP")
                if mcap:
                    extra_data["Market Cap"] = str(mcap)
                pe = item.get("STOCK_PE")
                if pe:
                    extra_data["P/E"] = str(pe)
                pb = item.get("STOCK_PB")
                if pb:
                    extra_data["P/B"] = str(pb)
                lot_size = item.get("UL_STOCKS_LOT_SIZE")
                if lot_size:
                    extra_data["Lot Size"] = str(lot_size)
                    
                data_dict = {
                    "source": "sharescart",
                    "company": company,
                    "slug": slugify(company),
                    "price": price,
                    "extra_data": extra_data,
                    "documents": []
                }
                results.append(data_dict)
                print(f"       -> [{len(results)}] {company}: Fetched Price: Rs. {price}")
                log_data = {"company": company, "price": price, "source": "sharescart"}
                print(f"LIVE_DATA:{json.dumps(log_data)}")
                
        except json.JSONDecodeError:
            print("   SharesCart: Failed to parse JSON response")
            
    except Exception as e:
        print("   SharesCart Error:", e)
            
    return results
