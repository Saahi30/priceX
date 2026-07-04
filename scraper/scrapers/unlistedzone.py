import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

BASE_URL = "https://unlistedzone.com/shares?page={}"
TOTAL_PAGES = 11

def clean_price(price_str):
    if not price_str:
        return None
    cleaned = price_str.replace("₹", "").replace(",", "").replace(" ", "").strip()
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None

def scrape_unlistedzone(mode="all", priority_slugs=None):
    """
    Scrape unlistedzone using Playwright.
    Returns a list of dicts.
    """
    logger.info("Starting UnlistedZone scraper...")
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        for page_num in range(1, TOTAL_PAGES + 1):
            url = BASE_URL.format(page_num)
            logger.info(f"Scraping page {page_num}: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for .scard elements
                try:
                    page.wait_for_selector(".scard", timeout=10000)
                except Exception as e:
                    logger.warning(f"No .scard elements found on page {page_num}")
                    continue
                
                scards = page.locator(".scard").all()
                for card in scards:
                    try:
                        # Extract Name
                        nm_el = card.locator(".nm").first
                        name = nm_el.inner_text().strip() if nm_el.count() > 0 else None
                        
                        # Extract Price
                        p_el = card.locator(".price .p").first
                        price_str = p_el.inner_text().strip() if p_el.count() > 0 else None
                        
                        # Extract Detail Link
                        det_el = card.locator("a.det").first
                        detail_url = None
                        if det_el.count() > 0:
                            href = det_el.get_attribute("href")
                            if href:
                                if href.startswith("http"):
                                    detail_url = href
                                else:
                                    detail_url = "https://unlistedzone.com" + (href if href.startswith("/") else "/" + href)
                        
                        price = clean_price(price_str)
                        
                        if name and price is not None:
                            # Use slug as the identifier to merge correctly in storage
                            slug = detail_url.rstrip("/").split("/")[-1] if detail_url else None
                            
                            result_dict = {
                                "company": name,  # mapping to "company" to work with normalizer
                                "price": price,
                                "source": "unlistedzone",
                                "url": detail_url,
                                "slug": slug
                            }
                            results.append(result_dict)
                            
                            # Stream live data to Streamlit dashboard
                            import json
                            print(f'LIVE_DATA:{json.dumps({"company": name, "price": price, "source": "unlistedzone"})}')
                            
                    except Exception as e:
                        logger.error(f"Failed to parse a card on page {page_num}: {e}")
            except Exception as e:
                logger.error(f"Failed to scrape page {page_num}: {e}")
                
        browser.close()
        
    # Deduplicate by company name (taking the first occurrence)
    seen = set()
    deduped_results = []
    for r in results:
        comp = r.get("company")
        if comp and comp not in seen:
            seen.add(comp)
            deduped_results.append(r)
            
    logger.info(f"UnlistedZone scraping completed. Extracted {len(deduped_results)} unique stocks.")
    return deduped_results
