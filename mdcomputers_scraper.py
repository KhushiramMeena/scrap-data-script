#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

from bs4 import BeautifulSoup
from curl_cffi import requests

BASE_URL = "https://mdcomputers.in"
SEARCH_ROUTE = "/?route=product/search"
DEFAULT_IMPERSONATE = "chrome120"


@dataclass
class Product:
    name: str
    url: str
    product_id: str | None = None
    image_url: str | None = None
    original_price: str | None = None
    sale_price: str | None = None
    discount: str | None = None
    sku: str | None = None
    model: str | None = None
    availability: str | None = None
    description: str | None = None


@dataclass
class ScraperConfig:
    search_term: str
    max_pages: int | None = None
    fetch_details: bool = False
    delay_seconds: float = 1.0
    impersonate: str = DEFAULT_IMPERSONATE


class MDComputersScraper:
    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self.session = requests.Session(impersonate=config.impersonate)

    def scrape(self) -> list[Product]:
        products: list[Product] = []
        page = 1

        while True:
            html = self._fetch_search_page(page)
            page_products = self._parse_search_page(html)
            if not page_products:
                break

            products.extend(page_products)
            if self.config.max_pages is not None and page >= self.config.max_pages:
                break

            next_page = self._find_next_page(html, page)
            if next_page is None:
                break

            page = next_page
            time.sleep(self.config.delay_seconds)

        if self.config.fetch_details:
            for index, product in enumerate(products, start=1):
                self._enrich_product_details(product)
                if index < len(products):
                    time.sleep(self.config.delay_seconds)

        return products

    def _fetch_search_page(self, page: int) -> str:
        params = {"search": self.config.search_term}
        if page > 1:
            params["page"] = str(page)

        url = f"{BASE_URL}{SEARCH_ROUTE}&{urlencode(params)}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _parse_search_page(self, html: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        heading = soup.find("h2", string=lambda text: text and "Products meeting" in text)
        if heading is None:
            return []

        section = heading.find_parent("div", class_="row")
        if section is None:
            return []

        products: list[Product] = []
        for card in section.select(".product-grid-item"):
            product = self._parse_product_card(card)
            if product is not None:
                products.append(product)
        return products

    def _parse_product_card(self, card) -> Product | None:
        title_link = card.select_one("h3.product-entities-title a")
        if title_link is None:
            return None

        name = title_link.get_text(strip=True)
        url = title_link.get("href", "").strip()
        if not name or not url:
            return None

        image = card.select_one("img")
        label = card.select_one(".product-label")
        original_price, sale_price = self._parse_prices(card.select_one("span.price"))

        product_id = None
        button = card.select_one("button[onclick*='cart.add']")
        if button and button.get("onclick"):
            match = re.search(r"cart\.add\('(\d+)'\)", button["onclick"])
            if match:
                product_id = match.group(1)

        return Product(
            name=name,
            url=url,
            product_id=product_id,
            image_url=image.get("src") if image else None,
            original_price=original_price,
            sale_price=sale_price,
            discount=label.get_text(strip=True) if label else None,
        )

    @staticmethod
    def _parse_prices(price_element) -> tuple[str | None, str | None]:
        if price_element is None:
            return None, None

        original = price_element.select_one("span.del .amount")
        sale = price_element.select_one("span.ins .amount")

        original_price = original.get_text(strip=True) if original else None
        sale_price = sale.get_text(strip=True) if sale else None

        if original_price is None and sale_price is None:
            text = price_element.get_text(" ", strip=True)
            return None, text or None

        return original_price, sale_price

    def _find_next_page(self, html: str, current_page: int) -> int | None:
        soup = BeautifulSoup(html, "lxml")
        next_page = current_page + 1
        next_links = soup.select(".pagination a")

        for link in next_links:
            href = link.get("href")
            if not href:
                continue

            parsed = urlparse(urljoin(BASE_URL, href))
            page_values = parse_qs(parsed.query).get("page", [])
            if page_values and page_values[0] == str(next_page):
                return next_page

        return None

    def _enrich_product_details(self, product: Product) -> None:
        response = self.session.get(product.url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for script in soup.select('script[type="application/ld+json"]'):
            if not script.string:
                continue

            try:
                payload = json.loads(script.string)
            except json.JSONDecodeError:
                continue

            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict) or item.get("@type") != "Product":
                    continue

                product.sku = item.get("sku") or product.sku
                product.model = item.get("model") or product.model
                product.description = item.get("description") or product.description

                offers = item.get("offers")
                if isinstance(offers, dict):
                    availability = offers.get("availability", "")
                    if availability:
                        product.availability = availability.rsplit("/", 1)[-1]
                return


def write_json(products: Iterable[Product], output_path: str) -> None:
    data = [asdict(product) for product in products]
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def write_csv(products: Iterable[Product], output_path: str) -> None:
    rows = [asdict(product) for product in products]
    if not rows:
        return

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape MDComputers product search results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("search", help='Search term, e.g. "external"')
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of result pages to scrape",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Fetch each product page for SKU, model, availability, and description",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between requests",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write results to a JSON or CSV file (format inferred from extension)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print JSON results to stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = ScraperConfig(
        search_term=args.search,
        max_pages=args.max_pages,
        fetch_details=args.details,
        delay_seconds=args.delay,
    )
    scraper = MDComputersScraper(config)

    try:
        products = scraper.scrape()
    except requests.RequestsError as error:
        print(f"Request failed: {error}", file=sys.stderr)
        return 1

    if args.output:
        if args.output.lower().endswith(".csv"):
            write_csv(products, args.output)
        else:
            write_json(products, args.output)

    if args.pretty or not args.output:
        print(json.dumps([asdict(product) for product in products], indent=2, ensure_ascii=False))

    print(f"Scraped {len(products)} products for search term '{args.search}'.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
