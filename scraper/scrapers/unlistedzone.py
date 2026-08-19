import json
import logging

from bs4 import BeautifulSoup

from scraper.utils import fetch_url

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

BASE_URL = "https://unlistedzone.com/shares?page={}"
MAX_PAGES = 40


def clean_price(price_str):
    if not price_str:
        return None
    cleaned = (
        str(price_str)
        .replace("₹", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("\n", "")
        .strip()
    )
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None


def _parse_cards(html):
    soup = BeautifulSoup(html, "lxml")
    parsed = []
    for card in soup.select(".scard"):
        nm_el = card.select_one(".nm")
        name = nm_el.get_text(" ", strip=True) if nm_el else None

        p_el = card.select_one(".price .p")
        price_str = p_el.get_text(" ", strip=True) if p_el else None

        det_el = card.select_one("a.det")
        detail_url = None
        if det_el and det_el.get("href"):
            href = det_el.get("href")
            if href.startswith("http"):
                detail_url = href
            else:
                detail_url = "https://unlistedzone.com" + (
                    href if href.startswith("/") else "/" + href
                )

        price = clean_price(price_str)
        if name and price is not None:
            slug = detail_url.rstrip("/").split("/")[-1] if detail_url else None
            parsed.append(
                {
                    "company": name,
                    "price": price,
                    "source": "unlistedzone",
                    "url": detail_url,
                    "slug": slug,
                }
            )
    return parsed


def _scrape_with_playwright():
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        empty_pages = 0
        for page_num in range(1, MAX_PAGES + 1):
            url = BASE_URL.format(page_num)
            logger.info(f"Playwright fallback page {page_num}: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_selector(".scard", timeout=8000)
                except Exception:
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                    continue
                parsed = _parse_cards(page.content())
                if not parsed:
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                    continue
                empty_pages = 0
                results.extend(parsed)
            except Exception as e:
                logger.error(f"Failed to scrape page {page_num}: {e}")
                empty_pages += 1
                if empty_pages >= 2:
                    break
        browser.close()
    return results


def scrape_unlistedzone(mode="all", priority_slugs=None):
    """
    Scrape UnlistedZone listing pages. HTML is server-rendered, so HTTP+BS4
    is the primary path; Playwright is only a fallback.
    """
    logger.info("Starting UnlistedZone scraper...")
    results = []
    empty_pages = 0

    try:
        for page_num in range(1, MAX_PAGES + 1):
            url = BASE_URL.format(page_num)
            logger.info(f"Scraping page {page_num}: {url}")
            try:
                response = fetch_url(url)
                parsed = _parse_cards(response.text)
                if not parsed:
                    logger.warning(f"No .scard elements found on page {page_num}")
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                    continue
                empty_pages = 0
                for item in parsed:
                    results.append(item)
                    print(
                        f'LIVE_DATA:{json.dumps({"company": item["company"], "price": item["price"], "source": "unlistedzone"})}'
                    )
            except Exception as e:
                logger.error(f"Failed to scrape page {page_num}: {e}")
                empty_pages += 1
                if empty_pages >= 2:
                    break
    except Exception as e:
        logger.error(f"HTTP scrape failed, trying Playwright: {e}")
        results = _scrape_with_playwright()
        for item in results:
            print(
                f'LIVE_DATA:{json.dumps({"company": item["company"], "price": item["price"], "source": "unlistedzone"})}'
            )

    if not results:
        logger.warning("HTTP scrape returned no cards; trying Playwright fallback")
        try:
            results = _scrape_with_playwright()
            for item in results:
                print(
                    f'LIVE_DATA:{json.dumps({"company": item["company"], "price": item["price"], "source": "unlistedzone"})}'
                )
        except Exception as e:
            logger.error(f"Playwright fallback failed: {e}")

    seen = set()
    deduped_results = []
    for r in results:
        slug = r.get("slug") or r.get("company")
        if slug and slug not in seen:
            seen.add(slug)
            deduped_results.append(r)

    logger.info(
        f"UnlistedZone scraping completed. Extracted {len(deduped_results)} unique stocks."
    )
    return deduped_results
