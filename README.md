# MDComputers Product Scraper

A Python script to scrape product listings from [MDComputers](https://mdcomputers.in) search results.

Example search URL: `https://mdcomputers.in/?route=product/search&search=external`

## Features

- Search products by keyword
- Automatic pagination across result pages
- Extracts name, URL, product ID, image, prices, and discount from listings
- Optional product-page details: SKU, model, availability, description
- Export results to JSON or CSV

## Requirements

- Python 3.10+

## Installation

```bash
git clone https://github.com/KhushiramMeena/scrap-data-script.git
cd scrap-data-script
pip install -r requirements.txt
```

## Usage

```bash
# Print results as JSON
python mdcomputers_scraper.py external --pretty

# Save all pages to JSON
python mdcomputers_scraper.py external -o results.json

# Scrape only the first 2 pages
python mdcomputers_scraper.py external --max-pages 2 -o results.json

# Include SKU, model, stock status, and description
python mdcomputers_scraper.py external --details -o results.json

# Export to CSV
python mdcomputers_scraper.py external -o results.csv
```

### Options

| Option | Description |
|--------|-------------|
| `search` | Search term (required) |
| `--max-pages` | Limit number of pages to scrape |
| `--details` | Fetch extra fields from each product page |
| `--delay` | Seconds to wait between requests (default: `1.0`) |
| `-o`, `--output` | Output file (`.json` or `.csv`) |
| `--pretty` | Print formatted JSON to stdout |

## Example Output

```json
{
  "name": "Seagate Expansion 1TB External Hard Drive",
  "url": "https://mdcomputers.in/product/seagate-expansion-1tb-external-hard-drive-stkm1000400",
  "product_id": "16447",
  "image_url": "https://mdcomputers.in/image/catalog/...",
  "original_price": "₹10,000",
  "sale_price": "₹9,160",
  "discount": "-8%",
  "sku": "SEAGATE",
  "model": "STKM1000400",
  "availability": "InStock",
  "description": "..."
}
```

## Notes

- MDComputers is protected by Cloudflare. The script uses `curl_cffi` with browser impersonation to make requests work reliably.
- Use `--delay` to avoid sending requests too quickly.
- Use `--details` only when you need SKU/model/stock data, since it makes one extra request per product.

## License

MIT
