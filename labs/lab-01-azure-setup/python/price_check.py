"""Look up current Azure list prices from the official Azure Retail Prices API.

No authentication is needed: https://prices.azure.com/api/retail/prices
Docs: https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices

Run in: WSL / Python (no virtual environment needed; standard library only).

    # ADLS Gen2 (hierarchical namespace) hot LRS capacity and operation prices
    python python/price_check.py --region westeurope

    # Anything else, e.g. Azure ML compute for a VM size
    python python/price_check.py --service "Virtual Machines" --region westeurope \
        --sku-contains "D4s v5" --meter-contains "D4s v5" --product-contains "Linux"

Prices are retail list prices in USD unless --currency is given; your agreement
may differ. The pricing calculator remains the authoritative estimate.
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request

API = "https://prices.azure.com/api/retail/prices"


def build_url(service: str, region: str, currency: str) -> str:
    flt = (f"serviceName eq '{service}' and armRegionName eq '{region}' "
           f"and priceType eq 'Consumption'")
    q = {"$filter": flt}
    if currency:
        q["currencyCode"] = currency
    return f"{API}?{urllib.parse.urlencode(q)}"


def matches(item: dict, product: str, sku: str, meter: str) -> bool:
    return (product.lower() in item.get("productName", "").lower()
            and sku.lower() in item.get("skuName", "").lower()
            and meter.lower() in item.get("meterName", "").lower())


def fetch(url: str, max_pages: int) -> list[dict]:
    items: list[dict] = []
    for _ in range(max_pages):
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (fixed https host)
            page = json.load(resp)
        items.extend(page.get("Items", []))
        url = page.get("NextPageLink")
        if not url:
            break
    return items


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--service", default="Storage")
    ap.add_argument("--region", default="westeurope")
    ap.add_argument("--product-contains", default="Hierarchical Namespace")
    ap.add_argument("--sku-contains", default="Hot LRS")
    ap.add_argument("--meter-contains", default="")
    ap.add_argument("--currency", default="")
    ap.add_argument("--max-pages", type=int, default=50)
    a = ap.parse_args(argv)

    url = build_url(a.service, a.region, a.currency)
    print(f"Querying {url}")
    rows = [i for i in fetch(url, a.max_pages) if matches(i, a.product_contains, a.sku_contains, a.meter_contains)]
    if not rows:
        print("No matching meters. Loosen --product-contains/--sku-contains, or check the region name.")
        return 1
    rows.sort(key=lambda i: (i["productName"], i["meterName"], i.get("tierMinimumUnits", 0)))
    print(f"{'product':<45} {'sku':<14} {'meter':<40} {'unit':<14} {'from':>8} {'price':>12}")
    for i in rows:
        print(f"{i['productName'][:45]:<45} {i['skuName'][:14]:<14} {i['meterName'][:40]:<40} "
              f"{i['unitOfMeasure']:<14} {i.get('tierMinimumUnits', 0):>8g} {i['retailPrice']:>12.6f} {i['currencyCode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
