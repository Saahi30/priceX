import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def scrape_sharescart(mode="all", priority_slugs=None):
    # For sharescart, we now use the quotes page directly
    url = "https://www.sharescart.com/unlisted-shares/unlisted-shares-quotes.php"
    results = []
    print(f"   Scraping SharesCart from {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pg = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ).new_page()
        
        # Abort images/fonts to speed up, but KEEP scripts/XHR because Angular needs them!
        pg.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        try:
            pg.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for the Angular cards to be attached
            try:
                pg.wait_for_selector('.card-cus', state='attached', timeout=15000)
                # Give Angular a moment to render the bindings
                time.sleep(2)
            except Exception as e:
                print("   SharesCart: Timeout waiting for .card-cus:", e)
                return results

            # Parse the rendered DOM
            soup = BeautifulSoup(pg.content(), "html.parser")
            cards = soup.find_all("div", class_="card-cus")
            print(f"   SharesCart: Found {len(cards)} companies")

            for card in cards:
                # Extract text blocks
                texts = [t.strip() for t in card.stripped_strings if t.strip()]
                if not texts:
                    continue
                
                # The first non-empty text is usually the company name
                company = texts[0]
                
                # Price is usually the next one, containing '/-' or just digits
                price = None
                for t in texts[1:]:
                    if '/-' in t:
                        price = t.replace('/-', '').strip().replace(',', '')
                        break
                
                # Fallback price regex if '/-' is missing
                if not price:
                    for t in texts[1:]:
                        pm = re.search(r"([\d,]+(?:\.\d+)?)", t)
                        if pm and float(pm.group(1).replace(',', '')) > 0:
                            price = pm.group(1).replace(',', '')
                            break
                            
                extra_data = {}
                market_cap = None
                pe = None
                
                for i, t in enumerate(texts):
                    if t == "Market Cap" and i + 1 < len(texts):
                        market_cap = texts[i+1].replace(',', '')
                        extra_data["Market Cap"] = texts[i+1]
                    if t == "P/E" and i + 1 < len(texts):
                        pe = texts[i+1].replace(',', '')
                        extra_data["P/E"] = texts[i+1]
                        
                if price:
                    data = {
                        "source": "sharescart",
                        "company": company,
                        "slug": slugify(company),
                        "price": price,
                        "extra_data": extra_data,
                        "documents": []
                    }
                    results.append(data)
                    
        except Exception as e:
            print("   SharesCart Error:", e)
        finally:
            browser.close()
            
    return results
