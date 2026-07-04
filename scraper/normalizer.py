import re

def slugify(name):
    if not name:
        return ""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug

def parse_float(val):
    if val is None or val == "" or val == "N/A" or val == "-":
        return None
    try:
        if isinstance(val, str):
            val = val.replace("₹", "").replace(",", "").replace("%", "").strip()
        return float(val)
    except (ValueError, TypeError):
        return None

def normalize_stock(raw_stock):
    """
    Takes a raw scraped dictionary and converts it to the standard schema.
    Returns None if the stock is invalid.
    """
    company = raw_stock.get("company")
    if not company:
        return None
        
    slug = raw_stock.get("slug") or slugify(company)
    
    normalized = {
        "company": company,
        "slug": slug,
        "price": parse_float(raw_stock.get("price")),
        "market_cap": parse_float(raw_stock.get("market_cap")),
        "sector": raw_stock.get("sector"),
        "industry": raw_stock.get("industry"),
        "face_value": parse_float(raw_stock.get("face_value")),
        "isin": raw_stock.get("isin"),
        "pe": parse_float(raw_stock.get("pe")),
        "eps": parse_float(raw_stock.get("eps")),
        "book_value": parse_float(raw_stock.get("book_value")),
        "roe": parse_float(raw_stock.get("roe")),
        "roce": parse_float(raw_stock.get("roce")),
        "revenue": parse_float(raw_stock.get("revenue")),
        "profit": parse_float(raw_stock.get("profit")),
        "enterprise_value": parse_float(raw_stock.get("enterprise_value")),
        "logo": raw_stock.get("logo"),
        "description": raw_stock.get("description"),
        "documents": raw_stock.get("documents", []),
        "extra_data": raw_stock.get("extra_data", {}),
        "source": raw_stock.get("source"),
        "url": raw_stock.get("url")
    }
    
    return normalized
