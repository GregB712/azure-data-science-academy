"""Offline tests for price_check.py (the live API is not called)."""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import price_check as pc  # noqa: E402


def test_build_url_encodes_filter():
    url = pc.build_url("Storage", "westeurope", "EUR")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["$filter"] == ["serviceName eq 'Storage' and armRegionName eq 'westeurope' and priceType eq 'Consumption'"]
    assert q["currencyCode"] == ["EUR"]


def test_matches_is_case_insensitive_substring():
    item = {"productName": "General Block Blob v2 Hierarchical Namespace", "skuName": "Hot LRS",
            "meterName": "Hot LRS Data Stored"}
    assert pc.matches(item, "hierarchical namespace", "hot lrs", "data stored")
    assert not pc.matches(item, "hierarchical namespace", "cool", "")


def test_main_with_stubbed_fetch(monkeypatch, capsys):
    # Illustrative record shape only; the price is made up, not a quote.
    monkeypatch.setattr(pc, "fetch", lambda url, max_pages: [
        {"productName": "General Block Blob v2 Hierarchical Namespace", "skuName": "Hot LRS",
         "meterName": "Hot LRS Data Stored", "unitOfMeasure": "1 GB/Month", "tierMinimumUnits": 0,
         "retailPrice": 0.0208, "currencyCode": "USD"}])
    assert pc.main(["--region", "westeurope"]) == 0
    assert "Hot LRS Data Stored" in capsys.readouterr().out
