"""
Parser layer.
Takes raw HTML, returns a list of normalized listing dicts:
    { "id": str, "title": str, "price": str, "url": str, "image_url": str | None }

If list.am changes its HTML structure, this is the only file you'll need to edit.
Verify selectors by opening the page in your browser and right-clicking a
listing → Inspect. As of writing, listing cards are <a class="gl"> or similar
inside a results container; each href looks like /item/12345678/....
"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.list.am"


def parse_listings(html: str) -> list[dict]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    listings = []

    # Listing cards. Selector is intentionally broad — if list.am tweaks
    # class names, we still catch /item/ links inside the main content area.
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

    # Same listing can appear twice (e.g. featured + regular). Dedup by ID.
    seen_ids = set()
    unique = []
    for l in listings:
        if l["id"] in seen_ids:
            continue
        seen_ids.add(l["id"])
        unique.append(l)
    return unique


def _extract_id(href: str) -> str | None:
    """Pull the numeric listing ID out of /item/12345678/optional-slug."""
    try:
        tail = href.split("/item/")[1]
        listing_id = tail.split("/")[0].split("?")[0]
        return listing_id if listing_id.isdigit() else None
    except IndexError:
        return None


def _extract_title(card) -> str:
    # list.am uses <div class="l"> for the title in gallery view.
    el = card.select_one("div.l")
    if el:
        return el.get_text(strip=True)
    # Fallback: any meaningful text in the card.
    text = card.get_text(" ", strip=True)
    return text[:120] if text else "Listing"


def _extract_price(card) -> str:
    # <div class="p"> holds the price in gallery view.
    el = card.select_one("div.p")
    if el:
        return el.get_text(strip=True)
    return "Price not shown"


def _extract_image(card) -> str | None:
    img = card.select_one("img")
    if not img:
        return None
    src = img.get("src") or img.get("data-src") or img.get("data-original")
    if not src:
        return None
    if src.startswith("//"):
        src = "https:" + src
    elif src.startswith("/"):
        src = BASE_URL + src
    return src
