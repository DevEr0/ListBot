"""
Parser for List.am search-result HTML.

Returns normalized dictionaries:
{
    "id": str,
    "title": str,
    "price": str,
    "url": str,
    "image_url": str | None
}
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

BASE_URL = "https://www.list.am"
ITEM_RE = re.compile(r"/item/(\d+)")


def parse_listings(html: str) -> list[dict]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    listings = []
    candidates = soup.select('a[href*="/item/"]')

    for card in candidates:
        href = card.get("href", "")
        listing_id = _extract_id(href)
        if not listing_id:
            continue

        listings.append({
            "id": listing_id,
            "title": _extract_title(card),
            "price": _extract_price(card),
            "url": urljoin(BASE_URL, href.split("?")[0]),
            "image_url": _extract_image(card),
        })

    unique = []
    seen_ids = set()

    for listing in listings:
        if listing["id"] in seen_ids:
            continue
        seen_ids.add(listing["id"])
        unique.append(listing)

    return unique


def _extract_id(href: str) -> str | None:
    match = ITEM_RE.search(href or "")
    return match.group(1) if match else None


def _extract_title(card) -> str:
    el = card.select_one("div.l")
    if el:
        return el.get_text(" ", strip=True)

    text = card.get_text(" ", strip=True)
    return text[:120] if text else "Listing"


def _extract_price(card) -> str:
    el = card.select_one("div.p")
    if el:
        return el.get_text(" ", strip=True)
    return "Price not shown"


def _extract_image(card) -> str | None:
    img = card.select_one("img")
    if not img:
        return None

    src = (
        img.get("src")
        or img.get("data-src")
        or img.get("data-original")
    )

    if not src:
        return None

    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return BASE_URL + src

    return src
