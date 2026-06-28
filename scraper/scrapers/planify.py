import re
from bs4 import BeautifulSoup
from scraper.utils import fetch_url

BASE_URL = "https://planify.in"

def scrape_planify(mode="all", priority_slugs=None):
    results = []
    print("   Loading listing page for Planify...")
    # TODO: Inspect API or HTML structure of Planify to extract shares
    # For now, returning an empty list as a stub.
    return results
