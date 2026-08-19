import re
from collections import defaultdict
from functools import lru_cache

from scraper.mapping import SHARESCART_TO_UNLISTEDZONE

TRAILING_FLUFF = {
    "limited",
    "ltd",
    "unlisted",
    "share",
    "shares",
    "private",
    "pvt",
    "inc",
    "company",
    "co",
    "price",
    "online",
    "buy",
    "sell",
}

STOPWORDS = TRAILING_FLUFF | {
    "the",
    "of",
    "and",
    "india",
}

GENERIC_TOKENS = {
    "electric",
    "energy",
    "finance",
    "financial",
    "hospital",
    "steel",
    "power",
    "green",
    "tech",
    "technologies",
    "technology",
    "industries",
    "industry",
    "international",
    "bank",
    "insurance",
    "services",
    "service",
    "solutions",
    "solution",
    "holdings",
    "holding",
    "investment",
    "investments",
    "capital",
    "general",
    "health",
    "life",
    "renewable",
    "renewables",
    "infra",
    "market",
    "home",
    "housing",
    "exchange",
    "stock",
    "share",
    "equity",
    "fund",
    "mutual",
    "research",
    "clinical",
    "consumer",
    "ventures",
    "venture",
}

# Extra words that describe a company but should not drive unique-token matching.
DESCRIPTOR_TOKENS = GENERIC_TOKENS | {
    "software",
    "tool",
    "lab",
    "ent",
    "product",
    "system",
    "president",
    "series",
    "ccp",
    "ccps",
    "esop",
    "formerly",
    "known",
    "previous",
    "previously",
}


@lru_cache(maxsize=4096)
def name_variants(name):
    """Current name plus former-name / abbreviation variants."""
    if not name:
        return []
    parts = [name]
    parts.extend(re.findall(r"\(([^)]+)\)", name))
    parts.extend(re.split(r"\bformerly\b|\bpreviously\b|\bknown as\b", name, flags=re.I))
    variants = []
    seen = set()
    for part in parts:
        cleaned = (part or "").strip(" \t-–—,()")
        if len(cleaned) < 3:
            continue
        expanded = re.sub(r"\bent\b", "enterprise", cleaned, flags=re.I)
        expanded = re.sub(r"\blab\b", "laboratories", expanded, flags=re.I)
        for candidate in (cleaned, expanded):
            key = candidate.lower()
            if key not in seen:
                seen.add(key)
                variants.append(candidate)
    return variants


@lru_cache(maxsize=4096)
def canonical_match_name(name):
    if not name:
        return ""
    name = re.sub(r"\bent\b", "enterprise", name, flags=re.I)
    name = re.sub(r"\blab\b", "laboratories", name, flags=re.I)
    return name.strip()


@lru_cache(maxsize=4096)
def normalize_for_match(name):
    if not name:
        return ""
    s = canonical_match_name(name).lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    for w in ("limited", "ltd", "unlisted", "shares", "share", "private", "pvt", "inc", "company", "co"):
        s = s.replace(w, "")
    return s


def _stem(token):
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


@lru_cache(maxsize=4096)
def name_tokens(name):
    if not name:
        return set()
    lowered = canonical_match_name(name).lower()
    parts = re.findall(r"[a-z0-9]+", lowered)
    compact_parts = re.findall(r"[a-z0-9]+", re.sub(r"[-'/]", "", lowered))
    tokens = set()
    for p in parts + compact_parts:
        if p in STOPWORDS or len(p) <= 1:
            continue
        tokens.add(_stem(p))
    return tokens


def _significant_words(name, strip_limited=True):
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    fluff = set(TRAILING_FLUFF)
    if not strip_limited:
        fluff -= {"limited", "ltd"}
    while words and words[-1] in fluff:
        words.pop()
    return words


@lru_cache(maxsize=4096)
def acronyms_of(name):
    result = set()
    for strip_limited in (True, False):
        words = _significant_words(name, strip_limited=strip_limited)
        if len(words) >= 2:
            result.add("".join(w[0] for w in words))
    return {a for a in result if 2 <= len(a) <= 6}


@lru_cache(maxsize=4096)
def paren_chunks(name):
    chunks = []
    for inner in re.findall(r"\(([^)]+)\)", name or ""):
        chunks.append(inner)
        norm = normalize_for_match(inner)
        if norm:
            chunks.append(norm)
    return chunks


def token_jaccard(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def names_equivalent(a, b):
    na, nb = normalize_for_match(a), normalize_for_match(b)
    return bool(na and nb and na == nb)


def token_subset_match(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    smaller, larger = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if not smaller <= larger:
        return False
    return len(smaller) >= 2


def mapped_uz_name(company):
    if not company:
        return None
    if company in SHARESCART_TO_UNLISTEDZONE:
        return SHARESCART_TO_UNLISTEDZONE[company]
    nc = normalize_for_match(company)
    if not nc:
        return None
    for key, value in SHARESCART_TO_UNLISTEDZONE.items():
        if normalize_for_match(key) == nc:
            return value
    return None


def short_name_match(short_name, uz_name):
    if not short_name or not uz_name:
        return False
    if names_equivalent(short_name, uz_name):
        return True
    if token_subset_match(short_name, uz_name):
        return True
    short_norm = normalize_for_match(short_name)
    if short_norm and len(short_norm) >= 3:
        for chunk in paren_chunks(uz_name):
            if normalize_for_match(chunk) == short_norm or chunk.lower() == short_name.lower():
                return True
        if short_norm in acronyms_of(uz_name):
            return True
    return False


def unique_token_slug(stock_name, token_index):
    """Match when identity tokens all point at exactly one UnlistedZone record."""
    if not stock_name:
        return None
    identity = [
        t for t in name_tokens(stock_name)
        if t not in DESCRIPTOR_TOKENS and len(t) >= 4
    ]
    if not identity:
        return None
    present_sets = []
    for token in identity:
        slugs = token_index.get(token) or []
        if not slugs:
            return None
        present_sets.append(set(slugs))
    common = set.intersection(*present_sets)
    if len(common) == 1:
        return next(iter(common))
    return None


def unique_prefix_slug(stock_name, token_index, existing_data):
    """
    Last-resort: one unique identity token, and the normalized names share a prefix.
    Stops 'Ecosure Pulpmolding' from being left as a duplicate of 'Ecosure'.
    """
    identity = [
        t for t in name_tokens(stock_name)
        if t not in DESCRIPTOR_TOKENS and len(t) >= 4
    ]
    present = [t for t in identity if token_index.get(t)]
    if len(present) != 1 or len(token_index[present[0]]) != 1:
        return None
    slug = token_index[present[0]][0]
    rec = existing_data.get(slug) or {}
    uz_n = normalize_for_match(rec.get("company") or "")
    sc_n = normalize_for_match(stock_name)
    if uz_n and sc_n and len(uz_n) >= 4 and (sc_n.startswith(uz_n) or uz_n.startswith(sc_n)):
        return slug
    return None


def match_score(sc_company, sc_short_name, uz_name, mapped_name=None):
    if not uz_name:
        return 0
    uz_vars = name_variants(uz_name)
    sc_vars = name_variants(sc_company) + name_variants(sc_short_name)
    if mapped_name:
        sc_vars = name_variants(mapped_name) + sc_vars

    best = 0
    for sc in sc_vars:
        for uz in uz_vars:
            if names_equivalent(sc, uz):
                best = max(best, 95)
            elif token_subset_match(sc, uz):
                best = max(best, 88)
            elif short_name_match(sc, uz):
                best = max(best, 82)
            else:
                j = token_jaccard(sc, uz)
                if j >= 0.72 and len(name_tokens(sc) & name_tokens(uz)) >= 2:
                    best = max(best, 70)
    return best


def find_unlistedzone_slug(stock, existing_data):
    """
    Return the UnlistedZone slug that this SharesCart row should merge into, or None.
    """
    company = stock.get("company") or ""
    short_name = stock.get("short_name") or ""
    mapped = mapped_uz_name(company)

    token_index = defaultdict(list)
    uz_items = []
    for slug, rec in existing_data.items():
        if rec.get("source") != "unlistedzone":
            continue
        uz_name = rec.get("company") or ""
        uz_items.append((slug, uz_name))
        for token in name_tokens(uz_name):
            token_index[token].append(slug)

    scored = []
    for slug, uz_name in uz_items:
        score = match_score(company, short_name, uz_name, mapped_name=mapped)
        if score:
            scored.append((score, token_jaccard(company, uz_name), slug, uz_name))

    if not scored:
        for hint in (company, short_name):
            unique_slug = unique_token_slug(hint, token_index)
            if unique_slug:
                return unique_slug
        for hint in (company, short_name):
            prefix_slug = unique_prefix_slug(hint, token_index, existing_data)
            if prefix_slug:
                return prefix_slug
        return None

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = scored[0]
    if len(scored) > 1:
        second = scored[1]
        if best[0] == second[0] and abs(best[1] - second[1]) < 0.2 and best[0] < 95:
            return None
    return best[2]
