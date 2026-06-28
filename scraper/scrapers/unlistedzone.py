import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://unlistedzone.com"

def get_all_share_urls():
    """Fetches all share URLs from the listing page."""
    print("   Loading listing page for UnlistedZone...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/shares", wait_until="networkidle", timeout=60000)
        time.sleep(3)

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
                        if curr == prev:
                            time.sleep(3)
                            if page.locator("a[href*='/shares/']").count() == prev:
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
    urls = []
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
        if clean not in urls:
            urls.append(clean)

    return urls

def scrape_detail(url, page, mode="all"):
    """
    Scrapes detail for a single URL. 
    mode="high-priority" gets only name and price.
    mode="all" gets fundamentals.
    """
    data = {"source": "unlistedzone"}
    slug = url.split("/shares/")[-2] if url.endswith("/") else url.split("/shares/")[-1]
    data["slug"] = slug

    try:
        if mode == "high-priority":
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)
        else:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
    except Exception as e:
        return None

    soup = BeautifulSoup(page.content(), "html.parser")

    # Name
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)
        name = re.sub(r"\s*\[.*?\]\s*$", "", name)
        name = re.sub(r"\s*E\s*unread\s*messages\s*$", "", name, flags=re.I)
        data["company"] = name.strip()
    else:
        # If no h1, might be an invalid page
        return None

    # Price
    h4 = soup.find("h4")
    if h4:
        t = h4.get_text(" ", strip=True)
        pm = re.search(r"₹\s*([\d,]+(?:\.\d+)?)", t)
        if pm:
            data["price"] = pm.group(1)

    if mode == "high-priority":
        return data

    # Detailed scraping
    about_section = soup.find(string=re.compile(r"About\s", re.I))
    if about_section and about_section.find_parent():
        next_sib = about_section.find_parent().find_next_sibling()
        if next_sib:
            data["description"] = next_sib.get_text(" ", strip=True)[:1000]

    # Fundamentals parsing
    page_text = soup.get_text(" ", strip=True)
    mapping = {
        "Market Cap (in cr.)": "market_cap",
        "P/E Ratio": "pe",
        "P/B Ratio": "book_value", 
        "ROE (%)": "roe",
        "Face Value": "face_value",
        "ISIN Number": "isin"
    }
    
    for key, field in mapping.items():
        pattern = re.escape(key) + r"\s*[:\s]*₹?\s*([\w\d,]+(?:\.\d+)?%?)"
        match = re.search(pattern, page_text)
        if match:
            val = match.group(1).replace(",", "").replace("%", "")
            data[field] = val

    match = re.search(r"Book Value\s*[:\s]*₹?\s*([\d,]+(?:\.\d+)?)", page_text)
    if match:
        data["book_value"] = match.group(1).replace(",", "")
        
    # Extract any other key-value pairs present on the page into extra_data
    data["extra_data"] = {}
    all_kv_matches = re.finditer(r"([A-Za-z0-9\s/()\-]+)\s*:\s*([^:\n]+)", page_text)
    for match in all_kv_matches:
        key = match.group(1).strip()
        val = match.group(2).strip()
        # Clean up key/val noise
        if 2 <= len(key) <= 35 and 1 <= len(val) <= 100:
            if key not in mapping and key != "Book Value":
                data["extra_data"][key] = val

    # Extract document links (Annual Reports, Financials, etc.)
    data["documents"] = []
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

def scrape_unlistedzone(mode="all", priority_slugs=None):
    if mode == "high-priority" and priority_slugs:
        urls = [f"{BASE_URL}/shares/{s}/" for s in priority_slugs]
    else:
        urls = get_all_share_urls()

    results = []
    print(f"   Found {len(urls)} URLs to scrape for UnlistedZone")
    
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
