import json
from datetime import datetime

from scraper.config import DATA_FILE, BASE_DIR
from scraper.matcher import find_unlistedzone_slug

SKIP_MERGE_FIELDS = {
    "company",
    "slug",
    "source",
    "url",
    "updated_at",
    "price",
    "backup_price",
    "aliases",
    "short_name",
}


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {}


def save_data(data_dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)


def _meaningful(value):
    return value not in (None, "", [], {})


def _merge_sharescart_into_uz(uz_rec, sc_stock):
    aliases = set(uz_rec.get("aliases") or [])
    for name in (sc_stock.get("company"), sc_stock.get("short_name")):
        if name and name != uz_rec.get("company"):
            aliases.add(name)
    if aliases:
        uz_rec["aliases"] = sorted(aliases)

    price = sc_stock.get("price")
    if price is not None:
        uz_rec["backup_price"] = price

    for key, value in sc_stock.items():
        if key in SKIP_MERGE_FIELDS or not _meaningful(value):
            continue
        if not _meaningful(uz_rec.get(key)):
            uz_rec[key] = value


def _display_price(data):
    price = data.get("price")
    if price in (None, "", 0, 0.0):
        backup = data.get("backup_price")
        if backup not in (None, ""):
            return backup
    return price


def reconcile_sharescart_duplicates(existing_data):
    """Fold leftover SharesCart-only rows into UnlistedZone records and drop the dupes."""
    to_delete = []
    for slug, rec in existing_data.items():
        if rec.get("source") != "sharescart":
            continue
        stock = {
            "company": rec.get("company"),
            "short_name": rec.get("short_name") or rec.get("company"),
            "price": rec.get("price"),
        }
        matched = find_unlistedzone_slug(stock, existing_data)
        if matched and matched != slug:
            _merge_sharescart_into_uz(existing_data[matched], rec)
            to_delete.append(slug)
    for slug in to_delete:
        del existing_data[slug]
    return len(to_delete)


def upsert_stocks(scraped_stocks):
    """
    scraped_stocks is a list of dictionaries.
    UnlistedZone rows are canonical. SharesCart rows merge in as backup_price.
    """
    existing_data = load_data()

    upserted_count = 0
    new_count = 0

    for stock in scraped_stocks:
        source = stock.get("source")
        slug = stock.get("slug")
        if not slug:
            continue

        stock["updated_at"] = datetime.now().isoformat()

        if source == "sharescart":
            matched_slug = find_unlistedzone_slug(stock, existing_data)
            if matched_slug:
                _merge_sharescart_into_uz(existing_data[matched_slug], stock)
                existing_data[matched_slug]["updated_at"] = stock["updated_at"]
                upserted_count += 1
                continue

            # No UnlistedZone match: keep/update a SharesCart-only record.
            if slug in existing_data:
                existing = existing_data[slug]
                existing.update({k: v for k, v in stock.items() if v is not None})
                upserted_count += 1
            else:
                existing_data[slug] = stock
                new_count += 1
            continue

        if slug in existing_data:
            existing = existing_data[slug]
            for key, value in stock.items():
                if value is None:
                    continue
                if not _meaningful(value) and _meaningful(existing.get(key)):
                    continue
                existing[key] = value
            upserted_count += 1
        else:
            existing_data[slug] = stock
            new_count += 1

    removed = reconcile_sharescart_duplicates(existing_data)
    if removed:
        print(f"Reconciled and removed {removed} duplicate SharesCart records")

    save_data(existing_data)
    export_prices_json(existing_data)
    return new_count, upserted_count


def export_prices_json(existing_data):
    api_dir = BASE_DIR / "api" / "v1"
    api_dir.mkdir(parents=True, exist_ok=True)
    json_path = api_dir / "stocks.json"

    records = []
    for slug, data in existing_data.items():
        last_updated = data.get("updated_at", "")
        if last_updated:
            last_updated = last_updated.replace("T", " ")[:19]

        aliases = data.get("aliases") or []
        records.append({
            "URL": data.get("url", ""),
            "Name": data.get("company", ""),
            "Short Name": data.get("short_name") or (aliases[0] if aliases else ""),
            "Aliases": aliases,
            "ISIN": data.get("isin", ""),
            "Latest Price": _display_price(data),
            "Backup Price": data.get("backup_price", ""),
            "Change Abs": data.get("change_abs", "0.00"),
            "Change Pct": data.get("change_pct", "0.00"),
            "Last Updated": last_updated,
            "Error": data.get("error", ""),
        })

    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
