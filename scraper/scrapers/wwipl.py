import json
import logging
import re

from bs4 import BeautifulSoup

from scraper.utils import fetch_url

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

BASE_URL = "https://wwipl.com/unlisted-shares/{}"

# WWIPL company pages for stocks that neither UnlistedZone nor SharesCart list.
# Add a slug here (the last path segment of the WWIPL page) to start tracking it.
WWIPL_SLUGS = [
    "equentis-wealth-advisory-services-share-price",
]


def clean_price(price_str):
    if price_str is None:
        return None
    cleaned = re.sub(r"[₹,\s]", "", str(price_str))
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value > 0 else None


def _fields(soup):
    """The 'Company Fundamentals' grid: label → value."""
    out = {}
    for box in soup.select(".extra_options"):
        label = box.select_one(".label")
        value = box.select_one(".value")
        if label and value:
            out[label.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
    return out


def _ld_price(soup):
    """Price from the JSON-LD block: additionalProperty '<Scrip> Share Price'."""
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except json.JSONDecodeError:
            continue
        props = (data.get("mainEntity") or {}).get("additionalProperty") or []
        for prop in props:
            if str(prop.get("name", "")).endswith("Share Price"):
                price = clean_price(prop.get("value"))
                if price is not None:
                    return price
    return None


def _ltp_price(soup):
    """Fallback: the number next to the 'Last Traded Price' caption."""
    caption = soup.find("small", string=re.compile(r"Last Traded Price"))
    if not caption:
        return None
    block = caption.find_next_sibling("span")
    if not block:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", block.get_text(" ", strip=True))
    return clean_price(m.group(1)) if m else None


def scrape_detail(slug):
    url = BASE_URL.format(slug)
    html = fetch_url(url).text
    soup = BeautifulSoup(html, "lxml")
    fields = _fields(soup)

    company = fields.get("Company Name")
    price = _ld_price(soup) or _ltp_price(soup)
    if not company or price is None:
        logger.warning(f"WWIPL: no name/price on {url}")
        return None

    extra = {}
    if fields.get("Scrip Name"):
        extra["Short Name"] = fields["Scrip Name"]
    return {
        "company": company,
        "short_name": fields.get("Scrip Name"),
        "price": price,
        "source": "wwipl",
        "url": url,
        "slug": slug,
        "isin": fields.get("ISIN No."),
        "face_value": fields.get("Face Value"),
        "sector": fields.get("Sector"),
        "extra_data": extra,
    }


def scrape_wwipl(mode="all", priority_slugs=None):
    """Scrape the curated WWIPL company pages in WWIPL_SLUGS."""
    logger.info("Starting WWIPL scraper...")
    results = []
    for slug in WWIPL_SLUGS:
        try:
            item = scrape_detail(slug)
        except Exception as e:
            logger.error(f"WWIPL fetch failed for {slug}: {e}")
            continue
        if not item:
            continue
        results.append(item)
        print(
            f'LIVE_DATA:{json.dumps({"company": item["company"], "price": item["price"], "source": "wwipl"})}'
        )
    logger.info("WWIPL scraping completed. Extracted %s stocks.", len(results))
    return results
