import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://sharescart.com"

def get_all_share_urls():
    print("   Loading listing page for SharesCart...")
    urls = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/unlisted-shares", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            # Scroll down to load all if they are lazy loaded
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
            soup = BeautifulSoup(page.content(), "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/unlisted-shares/" in href and href != "/unlisted-shares/":
                    full_url = href if href.startswith("http") else BASE_URL + href
                    if full_url not in urls:
                        urls.append(full_url)
        except Exception as e:
            print("   SharesCart Listing Error:", e)
        browser.close()
    return urls

def scrape_detail(url, page, mode="all"):
    data = {"source": "sharescart", "extra_data": {}, "documents": []}
    slug = url.split("/unlisted-shares/")[-1].rstrip("/")
    if not slug:
        slug = url.split("/unlisted-shares/")[-2]
    data["slug"] = slug

    try:
        page.goto(url, wait_until="networkidle" if mode == "all" else "domcontentloaded", timeout=30000)
        time.sleep(2 if mode == "all" else 1)
    except Exception:
        return None

    soup = BeautifulSoup(page.content(), "html.parser")

    # Basic Info
    h1 = soup.find("h1")
    if h1:
        data["company"] = h1.get_text(strip=True)
    else:
        return None

    page_text = soup.get_text(" ", strip=True)
    
    # Try to find price (₹ XXX)
    pm = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", page_text)
    if pm:
        data["price"] = pm.group(1).replace(",", "")
        
    if mode == "high-priority":
        return data

    # Extract all key-value pairs for extra_data
    all_kv_matches = re.finditer(r"([A-Za-z0-9\s/()\-]+)\s*:\s*([^:\n]+)", page_text)
    for match in all_kv_matches:
        key = match.group(1).strip()
        val = match.group(2).strip()
        if 2 <= len(key) <= 35 and 1 <= len(val) <= 100:
            data["extra_data"][key] = val

    # Documents
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if "pdf" in href.lower() or "report" in text.lower() or "financial" in text.lower():
            if not href.startswith("http"):
                href = BASE_URL + href if href.startswith("/") else BASE_URL + "/" + href
            if text and len(text) < 100:
                if not any(d["url"] == href for d in data["documents"]):
                    data["documents"].append({"title": text, "url": href})

    return data

def scrape_sharescart(mode="all", priority_slugs=None):
    if mode == "high-priority" and priority_slugs:
        urls = [f"{BASE_URL}/unlisted-shares/{s}" for s in priority_slugs]
    else:
        urls = get_all_share_urls()

    results = []
    print(f"   Found {len(urls)} URLs to scrape for SharesCart")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pg = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ).new_page()
        
        pg.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "media", "font"] else route.continue_())

        for i, url in enumerate(urls):
            print(f"   [{i+1}/{len(urls)}] Scraping {url}...")
            res = scrape_detail(url, pg, mode)
            if res:
                results.append(res)
            time.sleep(1)

        browser.close()
        
    return results
