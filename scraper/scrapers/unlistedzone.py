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
RSC_HEADERS = {
    "Accept": "text/x-component",
    "RSC": "1",
    "Next-Url": "/shares",
}


def clean_price(price_str):
    if price_str is None or price_str == "":
        return None
    if isinstance(price_str, (int, float)):
        return float(price_str)
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


def _extract_json_array(text, key):
    needle = f'"{key}":['
    start = text.find(needle)
    if start < 0:
        return None
    i = start + len(needle) - 1
    depth = 0
    for j, ch in enumerate(text[i:], i):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[i : j + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _item_from_rsc(share):
    name = share.get("name")
    slug = share.get("slug")
    price = clean_price(share.get("price"))
    if not name or price is None:
        return None
    extra = {}
    if share.get("lot_size") is not None:
        extra["Lot Size"] = str(share.get("lot_size"))
    if share.get("as_of"):
        extra["As Of"] = str(share.get("as_of"))
    return {
        "company": name,
        "price": price,
        "source": "unlistedzone",
        "url": f"https://unlistedzone.com/shares/{slug}" if slug else None,
        "slug": slug,
        "sector": share.get("sector"),
        "logo": share.get("logo"),
        "extra_data": extra,
    }


def _parse_rsc(text):
    shares = _extract_json_array(text, "shares") or []
    parsed = []
    for share in shares:
        if isinstance(share, dict):
            item = _item_from_rsc(share)
            if item:
                parsed.append(item)
    return parsed


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


def scrape_unlistedzone(mode="all", priority_slugs=None):
    """
    Scrape UnlistedZone listing pages from the Next.js RSC JSON payload
    (typed price, slug, sector, logo). Falls back to HTML cards if needed.
    """
    logger.info("Starting UnlistedZone scraper...")
    results = []
    empty_pages = 0
    used_rsc = False

    for page_num in range(1, MAX_PAGES + 1):
        url = BASE_URL.format(page_num)
        logger.info(f"Scraping page {page_num}: {url}")
        parsed = []
        try:
            rsc = fetch_url(url, headers=RSC_HEADERS)
            parsed = _parse_rsc(rsc.text)
            if parsed:
                used_rsc = True
        except Exception as e:
            logger.warning(f"RSC fetch failed on page {page_num}: {e}")

        if not parsed:
            try:
                html = fetch_url(url)
                parsed = _parse_cards(html.text)
            except Exception as e:
                logger.error(f"HTML fetch failed on page {page_num}: {e}")

        if not parsed:
            logger.warning(f"No shares found on page {page_num}")
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

    seen = set()
    deduped_results = []
    for r in results:
        slug = r.get("slug") or r.get("company")
        if slug and slug not in seen:
            seen.add(slug)
            deduped_results.append(r)

    logger.info(
        "UnlistedZone scraping completed via %s. Extracted %s unique stocks.",
        "RSC" if used_rsc else "HTML",
        len(deduped_results),
    )
    return deduped_results
