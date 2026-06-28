import argparse
import sys
from scraper.config import load_priority_stocks
from scraper.storage import upsert_stocks
from scraper.normalizer import normalize_stock

# Import scrapers as they become available
from scraper.scrapers.unlistedzone import scrape_unlistedzone
from scraper.scrapers.sharescart import scrape_sharescart
from scraper.scrapers.precize import scrape_precize
from scraper.scrapers.planify import scrape_planify
from scraper.scrapers.stockify import scrape_stockify
from scraper.scrapers.altius import scrape_altius

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["high-priority", "all"], required=True, 
                        help="Scrape only priority stocks or all stocks.")
    args = parser.parse_args()
    
    priority_slugs = []
    if args.mode == "high-priority":
        priority_urls = load_priority_stocks()
        if not priority_urls:
            print("[-] No priority stocks found. Exiting.")
            sys.exit(0)
        # Extract slug from URL or string
        for p in priority_urls:
            if "unlistedzone.com/shares/" in p:
                slug = p.split("/shares/")[-1].rstrip("/")
                priority_slugs.append(slug)
            else:
                priority_slugs.append(p)
        print(f"[+] Loaded {len(priority_slugs)} high-priority stocks.")

    all_raw_stocks = []
    
    # 1. Scrape UnlistedZone
    print("\n--- Scraping UnlistedZone ---")
    uz_stocks = scrape_unlistedzone(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(uz_stocks)
    
    # 2. Scrape SharesCart
    print("\n--- Scraping SharesCart ---")
    sc_stocks = scrape_sharescart(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(sc_stocks)
    
    # 3. Scrape Precize
    print("\n--- Scraping Precize ---")
    pr_stocks = scrape_precize(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(pr_stocks)
    
    # 4. Scrape Planify
    print("\n--- Scraping Planify ---")
    pl_stocks = scrape_planify(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(pl_stocks)
    
    # 5. Scrape Stockify
    print("\n--- Scraping Stockify ---")
    st_stocks = scrape_stockify(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(st_stocks)
    
    # 6. Scrape Altius
    print("\n--- Scraping Altius Investech ---")
    al_stocks = scrape_altius(mode=args.mode, priority_slugs=priority_slugs)
    all_raw_stocks.extend(al_stocks)
    
    # Normalize
    normalized_stocks = []
    for raw in all_raw_stocks:
        norm = normalize_stock(raw)
        if norm:
            normalized_stocks.append(norm)
            
    # Save
    new_count, upserted_count = upsert_stocks(normalized_stocks)
    
    print("\n--- Summary ---")
    print(f"Scraped total: {len(normalized_stocks)}")
    print(f"Inserted: {new_count}")
    print(f"Updated: {upserted_count}")
    print("Completed successfully")

if __name__ == "__main__":
    main()
