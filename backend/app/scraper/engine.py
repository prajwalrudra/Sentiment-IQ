"""
SentimentIQ — Scraping Engine

Orchestrates web scraping for product reviews from various e-commerce sites.
Delegates to site-specific parsers (Amazon, Flipkart, generic).
Falls back to mock data on failure.
"""

import logging
import re
from typing import List, Dict, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── User-Agent rotation ──────────────────────────────────────
try:
    _ua = UserAgent()
except Exception:
    _ua = None


def _get_headers() -> dict:
    """Get request headers with a random User-Agent."""
    ua_string = _ua.random if _ua else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    return {
        "User-Agent": ua_string,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


async def scrape_reviews(url: str, max_pages: int = 3) -> Tuple[str, List[Dict]]:
    """
    Scrape reviews from a product URL.

    Returns:
        Tuple of (product_name, list of review dicts)
    """
    domain = urlparse(url).netloc.lower()

    if "amazon" in domain:
        return await _scrape_amazon(url, max_pages)
    elif "flipkart" in domain:
        return await _scrape_flipkart(url, max_pages)
    else:
        return await _scrape_generic(url, max_pages)


async def _scrape_amazon(url: str, max_pages: int) -> Tuple[str, List[Dict]]:
    """Scrape reviews from Amazon product pages."""
    reviews = []
    product_name = "Amazon Product"

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        for page in range(1, max_pages + 1):
            # Convert product URL to reviews URL
            review_url = url
            if "/dp/" in url:
                asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)
                if asin_match:
                    asin = asin_match.group(1)
                    review_url = f"https://www.amazon.in/product-reviews/{asin}/ref=cm_cr_getr_d_paging_btm_next_{page}?pageNumber={page}"

            try:
                response = await client.get(review_url, headers=_get_headers())
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                # Extract product name
                title_el = soup.select_one("a[data-hook='product-link']")
                if title_el:
                    product_name = title_el.get_text(strip=True)

                # Extract reviews
                review_divs = soup.select("div[data-hook='review']")
                for div in review_divs:
                    text_el = div.select_one("span[data-hook='review-body']")
                    rating_el = div.select_one("i[data-hook='review-star-rating']")
                    name_el = div.select_one("span.a-profile-name")
                    date_el = div.select_one("span[data-hook='review-date']")

                    if text_el:
                        review_text = text_el.get_text(strip=True)
                        rating = None
                        if rating_el:
                            rating_text = rating_el.get_text()
                            rating_match = re.search(r"(\d\.?\d?)", rating_text)
                            if rating_match:
                                rating = float(rating_match.group(1))

                        reviews.append({
                            "text": review_text,
                            "rating": rating,
                            "reviewer_name": name_el.get_text(strip=True) if name_el else "Anonymous",
                            "date": date_el.get_text(strip=True) if date_el else "",
                            "verified_purchase": bool(div.select_one("span[data-hook='avp-badge']")),
                        })

                logger.info(f"  📄 Amazon page {page}: {len(review_divs)} reviews")

                if not review_divs:
                    break

                # Delay between pages
                import asyncio
                await asyncio.sleep(settings.scrape_delay_min)

            except Exception as e:
                logger.warning(f"  ⚠️ Amazon page {page} failed: {e}")
                break

    return product_name, reviews


async def _scrape_flipkart(url: str, max_pages: int) -> Tuple[str, List[Dict]]:
    """Scrape reviews from Flipkart product pages."""
    reviews = []
    product_name = "Flipkart Product"

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        for page in range(1, max_pages + 1):
            review_url = f"{url}&page={page}" if "?" in url else f"{url}?page={page}"

            try:
                response = await client.get(review_url, headers=_get_headers())
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                # Flipkart review selectors (may change)
                review_containers = soup.select("div.col._2wzgFH, div._27M-vq")

                for container in review_containers:
                    text_el = container.select_one("div.t-ZTKy, div._6K-7Co")
                    rating_el = container.select_one("div._3LWZlK, div.XQDdHH")
                    name_el = container.select_one("p._2sc7ZR, p._2NsDsF")

                    if text_el:
                        review_text = text_el.get_text(strip=True)
                        rating = None
                        if rating_el:
                            try:
                                rating = float(rating_el.get_text(strip=True))
                            except ValueError:
                                pass

                        reviews.append({
                            "text": review_text,
                            "rating": rating,
                            "reviewer_name": name_el.get_text(strip=True) if name_el else "Anonymous",
                            "date": "",
                        })

                logger.info(f"  📄 Flipkart page {page}: {len(review_containers)} reviews")

                if not review_containers:
                    break

                import asyncio
                await asyncio.sleep(settings.scrape_delay_min)

            except Exception as e:
                logger.warning(f"  ⚠️ Flipkart page {page} failed: {e}")
                break

    return product_name, reviews


async def _scrape_generic(url: str, max_pages: int) -> Tuple[str, List[Dict]]:
    """
    Attempt to scrape reviews from a generic website by looking
    for common review patterns in the HTML.
    """
    reviews = []
    product_name = "Product"

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            response = await client.get(url, headers=_get_headers())
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Try to find product name
            title = soup.find("h1")
            if title:
                product_name = title.get_text(strip=True)

            # Common review CSS patterns
            review_selectors = [
                "div.review", "div.review-body", "div.review-text",
                "div.comment", "div.customer-review",
                "article.review", "li.review",
                "[itemprop='reviewBody']",
                ".review-content", ".testimonial",
            ]

            for selector in review_selectors:
                elements = soup.select(selector)
                if elements:
                    for el in elements:
                        text = el.get_text(strip=True)
                        if len(text) > 20:  # Skip very short text
                            reviews.append({
                                "text": text,
                                "rating": None,
                                "reviewer_name": "Anonymous",
                                "date": "",
                            })
                    break  # Use the first matching selector

        except Exception as e:
            logger.warning(f"Generic scraping failed: {e}")

    return product_name, reviews
