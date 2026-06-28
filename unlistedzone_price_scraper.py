import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# We use playwright to render JS.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

BASE_URL = "https://unlistedzone.com"
DELAY = 1.0
CSV_FILE = Path("prices.csv")
CONFIG_FILE = Path("priority_stocks.json")

def cv(v):
    """Clean value string."""
    return v.replace("₹", "").replace(",", "").strip()

def scrape_listing_page():
    """Fetches all share URLs from the listing page."""
    print("[+] Loading listing page for all stocks...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/shares", wait_until="networkidle", timeout=60000)
        time.sleep(3)

        clicks = 0
        while True:
            try:
                btns = page.locator("text=View More")
                clicked = False
                for i in range(btns.count()):
                    btn = btns.nth(i)
                    href = btn.get_attribute("href") or ""
                    if "javascript:void" in href and btn.is_visible(timeout=2000):
                        prev = page.locator("a[href*='/shares/']").count()
                        btn.click()
                        time.sleep(2)
                        page.wait_for_load_state("networkidle", timeout=15000)
                        curr = page.locator("a[href*='/shares/']").count()
                        clicks += 1
                        print(f"   View More #{clicks} — {curr} links")
                        if curr == prev:
                            time.sleep(3)
                            if page.locator("a[href*='/shares/']").count() == prev:
                                clicked = False
                                break
                        clicked = True
                        break
                if not clicked:
                    break
            except Exception:
                break

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    seen, urls = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/shares/"):
            full = BASE_URL + href
        elif "unlistedzone.com/shares/" in href:
            full = href.replace("https://www.unlistedzone.com", BASE_URL)
        else:
            continue
        path = full.replace(BASE_URL, "").rstrip("/")
        if path in ("/shares", "") or not re.match(r"^/shares/[a-z0-9]", path):
            continue
        clean = full.rstrip("/") + "/"
        if clean not in seen:
            seen.add(clean)
            urls.append(clean)

    print(f"[+] Found {len(urls)} unique shares.")
    return urls

def scrape_detail_price_only(url, page):
    """Scrape only name and price data to make it extremely fast."""
    data = {"URL": url}
    try:
        # We don't need networkidle here, domcontentloaded is usually enough for the basic price text.
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(1) # Short wait for React to hydrate
    except Exception as e:
        data["Error"] = str(e)
        return data

    soup = BeautifulSoup(page.content(), "html.parser")

    # Name
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)
        name = re.sub(r"\s*\[.*?\]\s*$", "", name)
        name = re.sub(r"\s*E\s*unread\s*messages\s*$", "", name, flags=re.I)
        data["Name"] = name.strip()

    # Price and Change
    h4 = soup.find("h4")
    if h4:
        t = h4.get_text(" ", strip=True)
        pm = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", t)
        if pm:
            data["Latest Price"] = cv(pm.group(1))
        cm = re.search(r"([-+]?\d+(?:\.\d+)?)\s*\(([-+]?\d+(?:\.\d+)?)(?:%|\))", t)
        if cm:
            data["Change Abs"] = cm.group(1)
            data["Change Pct"] = cm.group(2)

    return data

def load_existing_csv():
    """Load existing data to update it instead of overwriting."""
    existing = {}
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("URL")
                if url:
                    existing[url] = row
    return existing

def save_csv(data_dict):
    """Save the updated dictionary back to CSV."""
    if not data_dict:
        return
        
    fieldnames = ["URL", "Name", "Latest Price", "Change Abs", "Change Pct", "Last Updated", "Error"]
    
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for url, row in data_dict.items():
            # Filter row to only keys in fieldnames
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["high-priority", "all"], required=True, 
                        help="Scrape only priority stocks or all stocks.")
    args = parser.parse_args()

    urls = []
    if args.mode == "high-priority":
        print("[+] Mode: HIGH PRIORITY")
        raw_urls = []
        
        # Check environment variable first (for GitHub Secrets)
        env_stocks = os.environ.get("PRIORITY_STOCKS")
        if env_stocks:
            print("[+] Loading from PRIORITY_STOCKS environment variable...")
            try:
                # Try parsing as JSON array
                raw_urls = json.loads(env_stocks)
            except json.JSONDecodeError:
                # Fallback to comma-separated if user entered it as plain text
                raw_urls = [u.strip() for u in env_stocks.split(",") if u.strip()]
        
        # Fallback to config file if env var is empty
        elif CONFIG_FILE.exists():
            print(f"[+] Loading from local config file: {CONFIG_FILE}")
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                raw_urls = cfg.get("high_priority_stocks", [])
        else:
            print(f"[-] Missing config file {CONFIG_FILE} and PRIORITY_STOCKS env var is empty.")
            sys.exit(1)

        # Normalize URLs to always end with a slash for consistency in the CSV
        urls = [u.rstrip("/") + "/" for u in raw_urls]
        print(f"[+] Loaded {len(urls)} high-priority stocks.")
    else:
        print("[+] Mode: ALL STOCKS")
        urls = scrape_listing_page()

    if not urls:
        print("[-] No URLs to scrape.")
        sys.exit(0)

    existing_data = load_existing_csv()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[+] Scraping {len(urls)} URLs...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Block images and stylesheets for speed
        pg = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ).new_page()
        
        pg.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

        for i, url in enumerate(urls):
            slug = url.split("/shares/")[-1].rstrip("/")
            print(f"   [{i+1}/{len(urls)}] {slug[:40]}...", end=" ", flush=True)
            
            scraped = scrape_detail_price_only(url, pg)
            
            if "Error" in scraped:
                print(f"ERR: {scraped['Error'][:40]}")
            else:
                price = scraped.get("Latest Price", "N/A")
                print(f"OK (Price: Rs. {price})")
                
            scraped["Last Updated"] = timestamp
            
            # Merge into existing data
            if url in existing_data:
                existing_data[url].update(scraped)
            else:
                existing_data[url] = scraped

            time.sleep(DELAY)

        browser.close()

    print(f"\n[+] Saving {len(existing_data)} total records to {CSV_FILE}")
    save_csv(existing_data)
    print("[+] Done.")

if __name__ == "__main__":
    main()
